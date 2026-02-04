import requests
from bs4 import BeautifulSoup
import re
import time
from urllib.parse import urljoin

def extract_product_details(url):
    """Extract product details from Amazon product page"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    }
    
    try:
        # Get the main product page (not reviews page)
        if "product-reviews" in url:
            # Extract product ID and create main product URL
            product_id = url.split("/product-reviews/")[1].split("/")[0]
            url = f"https://www.amazon.in/dp/{product_id}"
        
        print(f"🛍️ Fetching product details from: {url}")
        res = requests.get(url, headers=headers, timeout=15)
        res.raise_for_status()
        
        soup = BeautifulSoup(res.text, "html.parser")
        
        # Extract product name
        name_selectors = [
            "#productTitle",
            "h1.a-size-large", 
            ".product-title",
            "h1 span"
        ]
        product_name = "Unknown Product"
        for selector in name_selectors:
            name_elem = soup.select_one(selector)
            if name_elem:
                product_name = name_elem.get_text(strip=True)
                break
        
        # Extract product image
        image_selectors = [
            "#landingImage",
            ".a-dynamic-image",
            "img.a-image-wrapper img",
            "#imgBlkFront"
        ]
        product_image = ""
        for selector in image_selectors:
            img_elem = soup.select_one(selector)
            if img_elem:
                product_image = img_elem.get("src") or img_elem.get("data-src") or ""
                if product_image:
                    break
        
        # Extract product price
        price_selectors = [
            ".a-price-whole",
            ".a-offscreen",
            ".a-price .a-offscreen",
            "#corePrice_feature_div .a-price .a-offscreen",
            ".a-size-medium.a-color-price"
        ]
        product_price = "Price not available"
        for selector in price_selectors:
            price_elem = soup.select_one(selector)
            if price_elem:
                product_price = price_elem.get_text(strip=True)
                break
        
        product_details = {
            "product_name": product_name,
            "product_url": url,
            "product_image": product_image,
            "product_price": product_price
        }
        
        print(f"✅ Product details extracted: {product_name}")
        return product_details
        
    except Exception as e:
        print(f"❌ Error extracting product details: {str(e)}")
        return {
            "product_name": "Unknown Product",
            "product_url": url,
            "product_image": "",
            "product_price": "Price not available"
        }

def scrape_reviews(url: str, product_id=None, limit=10):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    }

    try:
        # Add small delay to avoid being blocked
        time.sleep(1)
        
        # Check if URL needs to be modified to go to reviews page
        if "/dp/" in url and "customerreviews" not in url:
            # Extract product ID and create reviews URL
            product_id = url.split("/dp/")[1].split("/")[0].split("?")[0]
            url = f"https://www.amazon.in/product-reviews/{product_id}/ref=cm_cr_dp_d_show_all_btm?ie=UTF8&reviewerType=all_reviews"
        
        print(f"📡 Fetching reviews from: {url}")
        res = requests.get(url, headers=headers, timeout=15)
        res.raise_for_status()
        
        soup = BeautifulSoup(res.text, "html.parser")
        reviews = []

        # Multiple selectors to try for Amazon reviews
        review_selectors = [
            "div[data-hook='review']",
            "div.review",
            "div.a-section.review",
            "[data-hook='review-body'] span"
        ]
        
        review_blocks = []
        for selector in review_selectors:
            review_blocks = soup.select(selector)
            if review_blocks:
                print(f"✅ Found {len(review_blocks)} reviews using selector: {selector}")
                break
        
        if not review_blocks:
            print("⚠️ No review blocks found. Trying alternative approach...")
            # Try to find any text that looks like reviews
            review_texts = soup.find_all(text=re.compile(r'.{50,}'))
            for i, text in enumerate(review_texts[:limit]):
                if len(text.strip()) > 50:
                    reviews.append({
                        "product_id": product_id,
                        "review_title": f"Review {i+1}",
                        "review_text": text.strip()[:500],
                        "rating": 3.0  # Default rating
                    })
            return reviews

        for i, block in enumerate(review_blocks[:limit]):
            try:
                # Try multiple selectors for title
                title_selectors = [
                    "[data-hook='review-title'] span",
                    "[data-hook='review-title']",
                    "h5 a span",
                    ".review-title"
                ]
                title = None
                for selector in title_selectors:
                    title = block.select_one(selector)
                    if title:
                        break
                
                # Try multiple selectors for review text  
                text_selectors = [
                    "[data-hook='review-body'] span",
                    "[data-hook='review-body']",
                    ".review-text",
                    "span[data-hook='review-body']"
                ]
                text = None
                for selector in text_selectors:
                    text = block.select_one(selector)
                    if text and len(text.get_text(strip=True)) > 10:
                        break
                
                # Try multiple selectors for rating
                rating_selectors = [
                    "[data-hook='review-star-rating'] span",
                    "[data-hook='review-star-rating']",
                    ".review-rating",
                    "i.a-icon-star span"
                ]
                rating = None
                for selector in rating_selectors:
                    rating = block.select_one(selector)
                    if rating:
                        break

                # Extract rating number
                rating_value = 0.0
                if rating:
                    rating_text = rating.get_text(strip=True)
                    rating_match = re.search(r'(\d+\.\d+|\d+)', rating_text)
                    if rating_match:
                        rating_value = float(rating_match.group(1))

                review_title = title.get_text(strip=True) if title else f"Review {i+1}"
                review_text = text.get_text(" ", strip=True) if text else "No review text found"
                
                # Skip if review text is too short
                if len(review_text) < 10:
                    continue
                    
                reviews.append({
                    "product_id": product_id,
                    "review_title": review_title,
                    "review_text": review_text,
                    "rating": rating_value
                })
                
                print(f"📝 Scraped review {i+1}: {review_title[:30]}...")
                
            except Exception as e:
                print(f"⚠️ Error processing review {i+1}: {str(e)}")
                continue
        
        print(f"✅ Successfully scraped {len(reviews)} reviews")
        return reviews
        
    except Exception as e:
        print(f"❌ Error scraping reviews: {str(e)}")
        # Return some sample data for testing
        return [{
            "product_id": product_id,
            "review_title": "Sample Review (Scraping Failed)",
            "review_text": f"Unable to scrape live reviews due to: {str(e)}. This is a sample review for testing purposes.",
            "rating": 4.0
        }]
