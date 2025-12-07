#!/usr/bin/env python3
"""
Open Dremio in browser using Playwright and wait 60 seconds
"""
import asyncio
from playwright.async_api import async_playwright
from datetime import datetime

async def open_dremio():
    async with async_playwright() as p:
        print("🚀 Launching browser...")

        # Launch browser in non-headless mode so you can see it
        browser = await p.chromium.launch(
            headless=False,
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )

        # Create context with proper locale to avoid the hanging issue
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            locale='en-US'  # Fix for the locale issue
        )

        page = await context.new_page()

        print(f"📍 Navigating to Dremio at http://localhost:9047...")
        await page.goto('http://localhost:9047', wait_until='networkidle')

        # Take a screenshot
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_path = f'/home/jerem/zeek-iceberg-demo/screenshots/{timestamp}_dremio_browser.png'
        await page.screenshot(path=screenshot_path)
        print(f"📸 Screenshot saved: {screenshot_path}")

        # Check current state
        current_url = page.url
        print(f"✅ Dremio opened successfully: {current_url}")

        if '/login' in current_url:
            print("📋 Status: On LOGIN page - Please enter your credentials")
        elif '/signup' in current_url:
            print("📋 Status: On SIGNUP page - Please create your admin account")
        else:
            print("📋 Status: Appears to be logged in or on main page")

        print("\n⏰ Waiting 60 seconds for you to interact with the page...")
        print("   The browser window is open for you to:")
        print("   - Login if needed")
        print("   - Check MinIO connection")
        print("   - Navigate to your data\n")

        # Wait 60 seconds
        for i in range(60, 0, -1):
            print(f"   {i} seconds remaining...", end='\r')
            await asyncio.sleep(1)

        print("\n\n✅ 60 seconds complete!")

        # Take a final screenshot
        final_screenshot = f'/home/jerem/zeek-iceberg-demo/screenshots/{timestamp}_dremio_final.png'
        await page.screenshot(path=final_screenshot)
        print(f"📸 Final screenshot saved: {final_screenshot}")

        final_url = page.url
        if final_url != current_url:
            print(f"📍 You navigated to: {final_url}")

        print("\n🛑 Closing browser...")
        await browser.close()
        print("✅ Browser closed successfully")

if __name__ == "__main__":
    print("="*80)
    print("OPENING DREMIO IN BROWSER (60 SECOND WINDOW)")
    print("="*80)
    asyncio.run(open_dremio())