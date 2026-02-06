from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from configs.database import init_db, get_db
from services.scraper import scrape_reviews, extract_product_details
from services.sentiment import analyze_sentiment
from services.stats import calculate_stats, calculate_correlations, calculate_detailed_sentiment_distribution, calculate_advanced_metrics, get_sentiment_by_rating
from services.plots import (
    generate_review_length_plot, 
    generate_sentiment_polarity_plot,
    generate_length_by_rating_plot,
    generate_rating_spread_plot
)

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="template")


@app.on_event("startup")
def startup():
    init_db()


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("index.jinja2", {"request": request})


import json
import asyncio

@app.post("/api/scrape")
async def scrape_stream(request: Request):
    form = await request.form()
    url = form.get("url")
    
    if not url:
         return Response(json.dumps({"error": "URL is required"}), media_type="application/json")

    # Fix URL if it doesn't have protocol
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
            
    print(f"Starting analysis for URL: {url}")

    async def event_generator():
        conn = get_db()
        cursor = conn.cursor()
        
        try:
             # Check if product already exists
            cursor.execute("SELECT product_id, product_name FROM products WHERE product_url = ?", (url,))
            existing_product = cursor.fetchone()
            
            if existing_product:
                print(f"Product already exists: {existing_product['product_name']}")
                yield json.dumps({"type": "completed", "message": "Product already exists"}) + "\n"
                return

            yield json.dumps({"type": "progress", "count": 0, "total": 100, "message": "Extracting product details..."}) + "\n"
            
            # Extract product details
            product_details = extract_product_details(url)
            
            # Insert product into database
            cursor.execute("""
                INSERT INTO products (product_name, product_url, product_image, product_price)
                VALUES (?, ?, ?, ?)
            """, (
                product_details["product_name"],
                product_details["product_url"],
                product_details["product_image"],
                product_details["product_price"]
            ))
            
            # Get the product_id of the inserted product
            cursor.execute("SELECT product_id FROM products WHERE product_url = ?", (url,))
            product_record = cursor.fetchone()
            product_id = product_record["product_id"]
            
            print(f"Product saved with ID: {product_id}")
            
            # Scrape reviews
            reviews_generator = scrape_reviews(url=url, product_id=product_id, limit=100)
            
            raw_reviews = []
            async for event in reviews_generator:
                if event["type"] == "progress":
                    yield json.dumps(event) + "\n"
                elif event["type"] == "result":
                    raw_reviews = event["reviews"]

            if not raw_reviews:
                 print("⚠️ No reviews found. Saving product details only.")
                 yield json.dumps({"type": "progress", "count": 0, "total": 0, "message": "No reviews found. Saving product details only..."}) + "\n"
            else:
                yield json.dumps({"type": "progress", "count": len(raw_reviews), "total": 100, "message": "Creating sentiment analysis..."}) + "\n"

            saved_count = 0
            for r in raw_reviews:
                try:
                    sentiment, polarity = analyze_sentiment(r["review_text"])
                    
                    cursor.execute("""
                        INSERT INTO reviews (product_id, review_title, review_text, rating, sentiment, polarity)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        r["product_id"],
                        r["review_title"],
                        r["review_text"],
                        r["rating"],
                        sentiment,
                        polarity
                    ))
                    saved_count += 1
                    
                except Exception as e:
                    print(f"Error saving review: {str(e)}")
                    continue
            
            conn.commit()
            print(f"Successfully saved product and {saved_count} reviews to database")
            
            completion_msg = "Analysis complete!"
            if not raw_reviews:
                completion_msg = "Product saved (no reviews found)."
                
            yield json.dumps({"type": "completed", "message": completion_msg}) + "\n"

        except Exception as e:
            print(f"Error in streaming scrape: {repr(e)}")
            yield json.dumps({"type": "error", "message": f"{str(e)} ({type(e).__name__})"}) + "\n"
        finally:
            conn.close()

    return StreamingResponse(event_generator(), media_type="application/x-ndjson")

@app.post("/scrape")
def scrape(
    url: str = Form(...)
):
    # Backward compatibility or fallback
    return RedirectResponse(url="/dashboard", status_code=303)


@app.get("/reviews", response_class=HTMLResponse)
def reviews_page(request: Request):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT r.*, p.product_name, p.product_image, p.product_price 
        FROM reviews r 
        LEFT JOIN products p ON r.product_id = p.product_id 
        ORDER BY r.id DESC
    """)
    reviews = cursor.fetchall()

    conn.close()

    return templates.TemplateResponse("reviews.jinja2", {"request": request, "reviews": reviews})


@app.get("/products", response_class=HTMLResponse)
def products_page(request: Request):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT p.*, COUNT(r.id) as review_count 
        FROM products p 
        LEFT JOIN reviews r ON p.product_id = r.product_id 
        GROUP BY p.product_id 
        ORDER BY p.id DESC
    """)
    products = cursor.fetchall()

    conn.close()

    return templates.TemplateResponse("products.jinja2", {"request": request, "products": products})

@app.get("/api/product-reviews/{product_id}")
def get_product_reviews(product_id: str):
    print(f"API called for product_id: {product_id}")
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT review_title, review_text, rating, sentiment, polarity, created_at
        FROM reviews 
        WHERE product_id = ? 
        ORDER BY id DESC
        LIMIT 25
    """, (product_id,))
    
    rows = cursor.fetchall()
    print(f"Found {len(rows)} reviews for product_id: {product_id}")
    
    reviews = [{
        "review_title": row["review_title"],
        "review_text": row["review_text"],
        "rating": row["rating"],
        "sentiment": row["sentiment"],
        "polarity": row["polarity"],
        "created_at": row["created_at"]
    } for row in rows]
    
    conn.close()
    print(f"Returning {len(reviews)} reviews")
    return reviews

@app.get("/debug/database")
def debug_database():
    conn = get_db()
    cursor = conn.cursor()
    
    # Check products
    cursor.execute("SELECT product_id, product_name FROM products LIMIT 5")
    products = cursor.fetchall()
    
    # Check reviews
    cursor.execute("SELECT product_id, review_title FROM reviews LIMIT 5")
    reviews = cursor.fetchall()
    
    # Count reviews
    cursor.execute("SELECT COUNT(*) as count FROM reviews")
    review_count = cursor.fetchone()
    
    conn.close()
    
    return {
        "products": [dict(p) for p in products],
        "reviews": [dict(r) for r in reviews],
        "total_reviews": dict(review_count)["count"]
    }


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT r.sentiment, r.rating, r.polarity, r.review_text, p.product_name 
        FROM reviews r 
        LEFT JOIN products p ON r.product_id = p.product_id
    """)
    rows = cursor.fetchall()

    conn.close()

    reviews = [{"sentiment": r["sentiment"], "rating": r["rating"], "polarity": r["polarity"], "review_text": r["review_text"]} for r in rows]
    stats = calculate_stats(reviews)
    correlations = calculate_correlations(reviews)
    detailed_sentiment = calculate_detailed_sentiment_distribution(reviews)
    advanced_metrics = calculate_advanced_metrics(reviews)

    # Calculate sentiment by rating for charts
    sentiment_by_rating = get_sentiment_by_rating(reviews)

    return templates.TemplateResponse("dashboard.jinja2", {
        "request": request, 
        "stats": stats, 
        "correlations": correlations,
        "detailed_sentiment": detailed_sentiment,
        "advanced_metrics": advanced_metrics,
        "sentiment_by_rating": sentiment_by_rating
    })


@app.get("/clear")
def clear_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM reviews")
    cursor.execute("DELETE FROM products")
    conn.commit()
    conn.close()

    return RedirectResponse(url="/", status_code=303)


@app.get("/plots/review_length")
def plot_review_length():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT review_text FROM reviews")
    reviews = [{"review_text": row["review_text"]} for row in cursor.fetchall()]
    conn.close()
    
    img = generate_review_length_plot(reviews)
    return Response(content=img.getvalue(), media_type="image/png")


@app.get("/plots/sentiment_polarity")
def plot_sentiment_polarity():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT polarity FROM reviews")
    reviews = [{"polarity": row["polarity"]} for row in cursor.fetchall()]
    conn.close()

    img = generate_sentiment_polarity_plot(reviews)
    return Response(content=img.getvalue(), media_type="image/png")


@app.get("/plots/length_by_rating")
def plot_length_by_rating():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT rating, review_text FROM reviews")
    reviews = [{"rating": row["rating"], "review_text": row["review_text"]} for row in cursor.fetchall()]
    conn.close()

    img = generate_length_by_rating_plot(reviews)
    return Response(content=img.getvalue(), media_type="image/png")

@app.get("/plots/rating_spread")
def plot_rating_spread():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT rating FROM reviews")
    reviews = [{"rating": row["rating"]} for row in cursor.fetchall()]
    conn.close()

    img = generate_rating_spread_plot(reviews)
    return Response(content=img.getvalue(), media_type="image/png")
