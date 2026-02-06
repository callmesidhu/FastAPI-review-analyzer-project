import asyncio
import sys
import os

sys.path.append(os.getcwd())
from services.scraper import extract_product_details, scrape_reviews

URL = "https://www.amazon.in/Samsung-Galaxy-S23-Ultra-5G/dp/B0BZDZM6N3/" # Use a known product

async def test_scraper():
    print("--- Testing Product Extraction (BS4) ---")
    try:
        details = extract_product_details(URL)
        print("Product Details Result:", details)
    except Exception as e:
        print(f"Product Extraction Failed: {e}")

    print("\n--- Testing Review Scraper (BS4) ---")
    try:
        generator = scrape_reviews(URL, product_id="TEST_ID", limit=10)
        async for event in generator:
            print(f"Event: {event['type']} - {event.get('message', '')}")
            if event['type'] == 'result':
                print(f"Found {len(event['reviews'])} reviews.")
    except Exception as e:
        print(f"Review Scraping Failed: {e}")

if __name__ == "__main__":
    with open("repro_output.txt", "w", encoding="utf-8") as f:
        sys.stdout = f
        sys.stderr = f
        asyncio.run(test_scraper())
