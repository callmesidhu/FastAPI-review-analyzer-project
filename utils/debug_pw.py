from playwright.sync_api import sync_playwright
print("Imported Playwright")
try:
    with sync_playwright() as p:
        print("Launched Playwright")
        browser = p.chromium.launch()
        print("Launched Browser")
        browser.close()
    print("Success")
except Exception as e:
    print(f"Error: {e}")
