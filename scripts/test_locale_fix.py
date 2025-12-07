#!/usr/bin/env python3
"""
Test if the locale fix resolves the Dremio rendering issue
"""

import asyncio
from playwright.async_api import async_playwright
from pathlib import Path
from datetime import datetime

SCREENSHOTS_DIR = Path(__file__).parent.parent / "screenshots"
SCREENSHOTS_DIR.mkdir(exist_ok=True)

async def test_locale_fix():
    """Test with explicit locale setting"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        # Track errors
        errors = []

        context = await browser.new_context(
            locale='en-US',  # FIX: Explicit standard locale
            viewport={'width': 1920, 'height': 1080}
        )
        page = await context.new_page()

        page.on("pageerror", lambda err: errors.append(str(err)))

        try:
            print("Testing locale fix...")
            print("Navigating to http://localhost:9047...")

            await page.goto("http://localhost:9047", wait_until="networkidle", timeout=20000)
            await asyncio.sleep(3)

            url = page.url
            body_text = await page.text_content('body')

            print(f"\nURL: {url}")
            print(f"Body text length: {len(body_text) if body_text else 0}")

            # Check for errors
            if errors:
                print(f"\n❌ JavaScript Errors Found:")
                for err in errors:
                    print(f"   {err}")
            else:
                print("\n✅ No JavaScript errors!")

            # Check if React rendered
            root_html = await page.locator('#root').inner_html()
            print(f"\n#root innerHTML length: {len(root_html)}")

            if len(root_html) > 0:
                print("✅ SUCCESS! React is rendering!")

                # Take screenshot
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                screenshot = SCREENSHOTS_DIR / f"{timestamp}_locale_fix_success.png"
                await page.screenshot(path=str(screenshot), full_page=True)
                print(f"Screenshot: {screenshot}")

                # Check what page we're on
                if "/login" in url:
                    print("\n📋 Status: On LOGIN page (expected)")
                elif "setup" in url.lower() or "setup" in body_text.lower()[:500]:
                    print("\n📋 Status: On FIRST-TIME SETUP page")
                else:
                    print("\n📋 Status: On DASHBOARD (already logged in)")

            else:
                print("❌ FAILED: React still not rendering")

                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                screenshot = SCREENSHOTS_DIR / f"{timestamp}_locale_fix_failed.png"
                await page.screenshot(path=str(screenshot), full_page=True)
                print(f"Screenshot: {screenshot}")

        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(test_locale_fix())
