#!/usr/bin/env python3
"""
Use Playwright to automatically navigate to the OCSF dataset in Dremio
"""
import asyncio
from playwright.async_api import async_playwright
from datetime import datetime
import sys

async def navigate_to_dataset(username=None, password=None):
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

        # Step 1: Navigate to Dremio
        print(f"📍 Navigating to Dremio...")
        await page.goto('http://localhost:9047', wait_until='networkidle')
        await page.screenshot(path=f'screenshots/{timestamp}_01_initial.png')

        current_url = page.url
        print(f"   Current URL: {current_url}")

        # Step 2: Login if needed
        if '/login' in current_url:
            print("\n🔐 Login required...")

            if not username or not password:
                print("   No credentials provided. Please login manually.")
                print("   Waiting 15 seconds for you to login...")
                await asyncio.sleep(15)
            else:
                print(f"   Logging in as: {username}")
                await page.fill('input[name="userName"]', username)
                await page.fill('input[name="password"]', password)
                await page.screenshot(path=f'screenshots/{timestamp}_02_login_filled.png')

                await page.click('button[type="submit"]')
                await page.wait_for_load_state('networkidle')
                print("   ✅ Login submitted")

        await page.screenshot(path=f'screenshots/{timestamp}_03_logged_in.png')

        # Step 3: Navigate to MinIO source
        print("\n📂 Navigating to MinIO source...")

        # Look for minio in the sidebar
        try:
            # Wait for the sources section to be visible
            await page.wait_for_selector('text=Sources', timeout=5000)
            print("   Found Sources section")

            # Click on minio source
            minio_selector = 'text=minio'
            await page.wait_for_selector(minio_selector, timeout=5000)
            print("   Found 'minio' source")

            await page.click(minio_selector)
            await asyncio.sleep(2)  # Wait for expansion
            await page.screenshot(path=f'screenshots/{timestamp}_04_minio_clicked.png')
            print("   ✅ Clicked on minio")

        except Exception as e:
            print(f"   ⚠️ Could not find minio source: {e}")
            await page.screenshot(path=f'screenshots/{timestamp}_04_error_no_minio.png')

        # Step 4: Navigate to zeek-data bucket
        print("\n📦 Looking for zeek-data bucket...")
        try:
            zeek_data_selector = 'text=zeek-data'
            await page.wait_for_selector(zeek_data_selector, timeout=5000)
            print("   Found 'zeek-data' bucket")

            await page.click(zeek_data_selector)
            await asyncio.sleep(2)
            await page.screenshot(path=f'screenshots/{timestamp}_05_zeek_data_clicked.png')
            print("   ✅ Clicked on zeek-data")

        except Exception as e:
            print(f"   ⚠️ Could not find zeek-data bucket: {e}")
            await page.screenshot(path=f'screenshots/{timestamp}_05_error_no_bucket.png')

        # Step 5: Navigate to network-activity-ocsf folder
        print("\n📊 Looking for network-activity-ocsf dataset...")
        try:
            dataset_selector = 'text=network-activity-ocsf'
            await page.wait_for_selector(dataset_selector, timeout=5000)
            print("   Found 'network-activity-ocsf' dataset")

            await page.click(dataset_selector)
            await asyncio.sleep(3)  # Wait for data to load
            await page.screenshot(path=f'screenshots/{timestamp}_06_dataset_opened.png')
            print("   ✅ Opened network-activity-ocsf dataset")

            # Check if we can see data
            try:
                # Look for common indicators of data being loaded
                data_indicators = [
                    'text=activity_name',
                    'text=class_uid',
                    'text=src_endpoint_ip',
                    'table',
                    '.grid'
                ]

                for indicator in data_indicators:
                    try:
                        await page.wait_for_selector(indicator, timeout=2000)
                        print(f"   ✅ Data visible - found: {indicator}")
                        break
                    except:
                        continue

            except Exception as e:
                print(f"   ⚠️ Data may not be visible yet")

        except Exception as e:
            print(f"   ⚠️ Could not find network-activity-ocsf dataset: {e}")
            await page.screenshot(path=f'screenshots/{timestamp}_06_error_no_dataset.png')

        # Step 6: Try to open SQL editor and run a test query
        print("\n💻 Attempting to open SQL editor...")
        try:
            # Look for "New Query" button or similar
            new_query_selectors = [
                'text=New Query',
                'button:has-text("Query")',
                '[aria-label="New Query"]'
            ]

            for selector in new_query_selectors:
                try:
                    await page.wait_for_selector(selector, timeout=2000)
                    await page.click(selector)
                    await asyncio.sleep(2)
                    print("   ✅ Opened SQL editor")
                    await page.screenshot(path=f'screenshots/{timestamp}_07_sql_editor.png')
                    break
                except:
                    continue

        except Exception as e:
            print(f"   ℹ️ SQL editor not opened (not critical)")

        # Final screenshot and status
        await page.screenshot(path=f'screenshots/{timestamp}_08_final_state.png')

        print("\n" + "="*80)
        print("✅ Navigation Complete!")
        print("="*80)
        print(f"Current URL: {page.url}")
        print(f"Screenshots saved in: screenshots/")
        print("\n⏰ Keeping browser open for 60 seconds for you to interact...")

        # Keep browser open for interaction
        for i in range(60, 0, -1):
            print(f"   {i} seconds remaining...", end='\r')
            await asyncio.sleep(1)

        print("\n\n🛑 Closing browser...")
        await browser.close()
        print("✅ Browser closed")

if __name__ == "__main__":
    print("="*80)
    print("DREMIO DATASET NAVIGATOR")
    print("="*80)

    # Get credentials from command line or environment
    import os
    username = sys.argv[1] if len(sys.argv) > 1 else os.getenv('DREMIO_USER')
    password = sys.argv[2] if len(sys.argv) > 2 else os.getenv('DREMIO_PASSWORD')

    if username and password:
        print(f"Using credentials for: {username}")
    else:
        print("No credentials provided - will wait for manual login")
        print("Usage: python navigate_to_dataset.py [username] [password]")
        print("Or set DREMIO_USER and DREMIO_PASSWORD environment variables")

    print()
    asyncio.run(navigate_to_dataset(username, password))