#!/usr/bin/env python3
"""
Check what's on the Dremio page and take a screenshot with longer wait times
"""
import asyncio
from playwright.async_api import async_playwright
from datetime import datetime

async def check_dremio():
    async with async_playwright() as p:
        print("🚀 Launching browser...")

        browser = await p.chromium.launch(
            headless=False,
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )

        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            locale='en-US'
        )

        page = await context.new_page()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        print(f"📍 Navigating to Dremio...")
        await page.goto('http://localhost:9047', wait_until='networkidle')

        print(f"✅ Page URL: {page.url}")

        # Wait a bit for page to fully load
        await asyncio.sleep(3)

        # Take screenshot of current state
        await page.screenshot(path=f'screenshots/{timestamp}_current_state.png', full_page=True)
        print(f"📸 Screenshot saved: screenshots/{timestamp}_current_state.png")

        # Try to find the minio source and navigate to it properly
        print("\n🔍 Looking for MinIO source...")

        try:
            # Click on minio in sidebar
            await page.click('text=minio')
            print("   Clicked minio")
            await asyncio.sleep(5)  # Wait longer for S3 to respond

            await page.screenshot(path=f'screenshots/{timestamp}_after_minio_click.png', full_page=True)
            print(f"📸 Screenshot: screenshots/{timestamp}_after_minio_click.png")

            # Now try clicking zeek-data
            print("\n🔍 Looking for zeek-data bucket...")
            await page.click('text=zeek-data')
            print("   Clicked zeek-data")
            await asyncio.sleep(8)  # Wait even longer for bucket contents

            await page.screenshot(path=f'screenshots/{timestamp}_after_zeekdata_click.png', full_page=True)
            print(f"📸 Screenshot: screenshots/{timestamp}_after_zeekdata_click.png")

            # Look for network-activity-ocsf
            print("\n🔍 Looking for network-activity-ocsf folder...")

            # Try to find it in the page
            dataset_visible = await page.locator('text=network-activity-ocsf').count()
            if dataset_visible > 0:
                print(f"   ✅ Found network-activity-ocsf ({dataset_visible} matches)")
                await page.click('text=network-activity-ocsf')
                print("   Clicked network-activity-ocsf")
                await asyncio.sleep(5)

                await page.screenshot(path=f'screenshots/{timestamp}_dataset_opened.png', full_page=True)
                print(f"📸 Screenshot: screenshots/{timestamp}_dataset_opened.png")
            else:
                print("   ⚠️ network-activity-ocsf not found yet")
                # Take a screenshot of what we do see
                page_text = await page.content()
                print(f"   Page contains {len(page_text)} characters")

        except Exception as e:
            print(f"   ⚠️ Error: {e}")
            await page.screenshot(path=f'screenshots/{timestamp}_error.png', full_page=True)

        print("\n⏰ Keeping browser open for 90 seconds for manual interaction...")
        for i in range(90, 0, -1):
            print(f"   {i} seconds remaining...", end='\r')
            await asyncio.sleep(1)

        print("\n\n🛑 Closing browser...")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(check_dremio())
