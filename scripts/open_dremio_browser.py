#!/usr/bin/env python3
"""
Open Dremio in browser using Playwright and keep it open for manual interaction
"""
import asyncio
from playwright.async_api import async_playwright
import sys
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
            locale='en-US'  # Fix for the locale issue that caused hanging
        )

        page = await context.new_page()

        print(f"📍 Navigating to Dremio at http://localhost:9047...")
        await page.goto('http://localhost:9047', wait_until='networkidle')

        # Take a screenshot for reference
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_path = f'/home/jerem/zeek-iceberg-demo/screenshots/{timestamp}_dremio_opened.png'
        await page.screenshot(path=screenshot_path)
        print(f"📸 Screenshot saved: {screenshot_path}")

        # Check current state
        current_url = page.url
        print(f"✅ Page loaded: {current_url}")

        if '/login' in current_url:
            print("\n📋 You're on the LOGIN page")
            print("   Enter your credentials to login")
        elif '/signup' in current_url:
            print("\n📋 You're on the SIGNUP page")
            print("   Create your admin account")
        else:
            print("\n📋 You appear to be logged in")

        print("\n⏰ Browser will stay open for you to interact with Dremio...")
        print("   You can:")
        print("   - Login with your credentials")
        print("   - Check the MinIO connection")
        print("   - Run queries on your data")
        print("\n⚠️  Press Ctrl+C when you're done to close the browser\n")

        # Keep the browser open
        try:
            while True:
                await asyncio.sleep(15)
                print(f"   Browser still open... (Current URL: {page.url})")

                # Optionally take periodic screenshots
                if page.url != current_url:
                    current_url = page.url
                    print(f"   📍 Navigated to: {current_url}")

        except KeyboardInterrupt:
            print("\n🛑 Closing browser...")
            await browser.close()
            print("✅ Browser closed")

if __name__ == "__main__":
    print("="*80)
    print("DREMIO BROWSER LAUNCHER")
    print("="*80)
    asyncio.run(open_dremio())