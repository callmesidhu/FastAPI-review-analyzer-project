from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from configs.database import init_db, get_db
from services.scraper import scrape_reviews
from services.sentiment import analyze_sentiment
from services.stats import calculate_stats

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="template")


@app.on_event("startup")
def startup():
    init_db()


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("index.jinja2", {"request": request})


@app.post("/scrape")
def scrape(
    url: str = Form(...),
    product_name: str = Form("Amazon Product")
):
    try:
        print(f"🔍 Starting scrape for: {product_name}")
        print(f"🔗 URL: {url}")
        
        raw_reviews = scrape_reviews(url=url, product_name=product_name, limit=10)
        
        if not raw_reviews:
            print("⚠️ No reviews found")
            return RedirectResponse(url="/reviews?error=no_reviews", status_code=303)
        
        conn = get_db()
        cursor = conn.cursor()
        
        saved_count = 0
        for r in raw_reviews:
            try:
                sentiment, polarity = analyze_sentiment(r["review_text"])
                
                cursor.execute("""
                    INSERT INTO reviews (product_name, review_title, review_text, rating, sentiment, polarity)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    r["product_name"],
                    r["review_title"],
                    r["review_text"],
                    r["rating"],
                    sentiment,
                    polarity
                ))
                saved_count += 1
                print(f"💾 Saved review: {r['review_title'][:30]}...")
                
            except Exception as e:
                print(f"❌ Error saving review: {str(e)}")
                continue
        
        conn.commit()
        conn.close()
        
        print(f"✅ Successfully saved {saved_count} reviews to database")
        return RedirectResponse(url="/reviews", status_code=303)
        
    except Exception as e:
        print(f"❌ Error in scrape route: {str(e)}")
        return RedirectResponse(url="/reviews?error=scrape_failed", status_code=303)


@app.get("/reviews", response_class=HTMLResponse)
def reviews_page(request: Request):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM reviews ORDER BY id DESC")
    reviews = cursor.fetchall()

    conn.close()

    return templates.TemplateResponse("reviews.jinja2", {"request": request, "reviews": reviews})


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT sentiment, rating FROM reviews")
    rows = cursor.fetchall()

    conn.close()

    reviews = [{"sentiment": r["sentiment"], "rating": r["rating"]} for r in rows]
    stats = calculate_stats(reviews)

    return templates.TemplateResponse("dashboard.jinja2", {"request": request, "stats": stats})


@app.get("/clear")
def clear_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM reviews")
    conn.commit()
    conn.close()

    return RedirectResponse(url="/reviews", status_code=303)
