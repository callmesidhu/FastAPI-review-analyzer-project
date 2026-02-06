import requests
from bs4 import BeautifulSoup
import re
import time
import asyncio
import random
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


async def scrape_reviews(url: str, product_id=None, limit=100):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Cache-Control": "max-age=0",
    }

    try:
        # Add delay to avoid being blocked
        await asyncio.sleep(2)
        
        # Ensure we are checking the main product page or reviews page
        print(f"📡 Processing URL: {url}")
        yield {"type": "progress", "count": 0, "total": limit, "message": f"Processing URL..."}
        
        target_url = url
        # If it's a direct product link, try to construct the reviews URL
        if "/dp/" in url and "product-reviews" not in url:
            try:
                # Extract clean product ID
                prod_id = url.split("/dp/")[1].split("/")[0].split("?")[0]
                target_url = f"https://www.amazon.in/product-reviews/{prod_id}/ref=cm_cr_dp_d_show_all_btm?ie=UTF8&reviewerType=all_reviews"
            except:
                pass # Fallback to original URL if extraction fails
        
        print(f"📡 Fetching reviews from: {target_url}")
        yield {"type": "progress", "count": 0, "total": limit, "message": "Fetching first page of reviews..."}
        
        # Note: requests is blocking. For full async benefit, use aiohttp/httpx.
        # But this wrapper is enough to solve the "async for" TypeError.
        res = requests.get(target_url, headers=headers, timeout=15)
        
        # Check for bot detection/captcha (status 503 or 200 with captcha text)
        if res.status_code == 503 or "Enter the characters you see below" in res.text:
            print("⚠️ Amazon blocked the request (Captcha/Bot Detection).")
            yield {"type": "error", "message": "Amazon blocked the request (Captcha/Bot Detection)."}
            return

        res.raise_for_status()
        
        soup = BeautifulSoup(res.text, "html.parser")
        reviews = []
        page_num = 1

        # Updated selectors for 2024/2025 Amazon structure
        review_selectors = [
            "div[data-hook='review']",
            "div.a-section.review",
            "div[id^='customer_review']" 
        ]
        
        while len(reviews) < limit:
            print(f"Scraping page {page_num} for URL: {target_url}")
            yield {"type": "progress", "count": len(reviews), "total": limit, "message": f"Scraping page {page_num}..."}
            
            # Find elements on current page
            page_blocks = []
            for selector in review_selectors:
                elements = soup.select(selector)
                if elements:
                    print(f"✅ Found {len(elements)} reviews on page {page_num}")
                    page_blocks = elements
                    break
            
            if not page_blocks:
                print(f"⚠️ No reviews found on page {page_num}")
                break

            for block in page_blocks:
                try:
                    if len(reviews) >= limit:
                        break

                    # Title
                    title_elem = block.select_one("[data-hook='review-title']") or \
                                 block.select_one(".review-title")
                    
                    review_title = "Review"
                    if title_elem:
                        review_title = title_elem.get_text(strip=True)
                        review_title = re.sub(r'^\d\.\d out of 5 stars\s*', '', review_title) # clean stars
                        review_title = re.sub(r'^\d\.\d out of 5 stars', '', review_title) # double check

                    # Text
                    text_elem = block.select_one("[data-hook='review-body']") or \
                                block.select_one(".review-text-content")
                    
                    review_text = "No review text."
                    if text_elem:
                        # Use separator to avoid jamming words together
                        review_text = text_elem.get_text(" ", strip=True)

                    # Rating
                    rating_value = 3.0
                    rating_elem = block.select_one("[data-hook='review-star-rating']") or \
                                  block.select_one(".a-icon-star")
                    
                    if rating_elem:
                        rating_text = rating_elem.get_text(strip=True)
                        match = re.search(r'(\d+(\.\d+)?)', rating_text)
                        if match:
                            rating_value = float(match.group(1))

                    reviews.append({
                        "product_id": product_id,
                        "review_title": review_title.strip(),
                        "review_text": review_text,
                        "rating": rating_value
                    })
                except Exception as e:
                    print(f"⚠️ Error processing review: {e}")
                    continue
            
            print(f"Collected {len(reviews)}/{limit} reviews so far.")
            yield {"type": "progress", "count": len(reviews), "total": limit, "message": f"Collected {len(reviews)} reviews..."}
            
            if len(reviews) >= limit:
                break

            # Pagination Logic
            next_page = soup.select_one("li.a-last a") or soup.select_one("a.a-pagination-next")
            if next_page and 'href' in next_page.attrs:
                next_url = urljoin("https://www.amazon.in", next_page['href'])
                print(f"Navigating to next page: {next_url}")
                await asyncio.sleep(random.uniform(2, 5)) 
                
                try:
                    res = requests.get(next_url, headers=headers, timeout=15)
                    # Check for blocking again
                    if res.status_code == 503 or "Enter the characters you see below" in res.text:
                        print("⚠️ Amazon blocked the next page request.")
                        break
                    
                    res.raise_for_status()
                    soup = BeautifulSoup(res.text, "html.parser")
                    page_num += 1
                    target_url = next_url # Update for logging
                except Exception as e:
                    print(f"Failed to fetch next page: {e}")
                    break
            else:
                print("No next page found.")
                break

        print(f"✅ Successfully scraped {len(reviews)} reviews")
        yield {"type": "result", "reviews": reviews}
        
    except Exception as e:
        print(f"❌ Error scraping reviews: {str(e)}")
        yield {"type": "error", "message": f"Failed to retrieve reviews: {str(e)}"}
