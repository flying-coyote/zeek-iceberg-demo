#!/usr/bin/env python3
"""
Dremio Diagnostic Tool using Playwright
Navigates to Dremio UI and diagnoses issues with the minio source and datasets
"""

import asyncio
import sys
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
from pathlib import Path
from datetime import datetime

# Create screenshots directory
SCREENSHOTS_DIR = Path(__file__).parent.parent / "screenshots"
SCREENSHOTS_DIR.mkdir(exist_ok=True)

async def take_screenshot(page, name):
    """Take a screenshot with timestamp"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = SCREENSHOTS_DIR / f"{timestamp}_{name}.png"
    await page.screenshot(path=str(filepath), full_page=True)
    print(f"📸 Screenshot saved: {filepath}")
    return filepath

async def diagnose_dremio(username=None, password=None):
    """Main diagnostic function"""
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=False)
        # FIX: Set explicit locale to avoid "en-US@posix" error
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            locale='en-US'  # Use standard BCP 47 locale tag
        )
        page = await context.new_page()

        # Enable console logging
        page.on("console", lambda msg: print(f"🖥️  CONSOLE: {msg.text}"))
        page.on("pageerror", lambda err: print(f"❌ PAGE ERROR: {err}"))

        print("=" * 80)
        print("DREMIO DIAGNOSTIC TOOL")
        print("=" * 80)

        try:
            # Step 1: Navigate to Dremio
            print("\n1️⃣  Navigating to http://localhost:9047...")
            await page.goto("http://localhost:9047", wait_until="networkidle", timeout=30000)
            await asyncio.sleep(2)
            await take_screenshot(page, "01_initial_load")

            # Step 2: Check what page we're on
            print("\n2️⃣  Checking current page state...")
            url = page.url
            print(f"   Current URL: {url}")

            # Check for login page
            is_login_page = await page.locator('input[type="password"]').count() > 0
            if is_login_page:
                print("   ✅ On LOGIN page")
                await take_screenshot(page, "02_login_page")

                if username and password:
                    # Try to login with provided credentials
                    print(f"\n3️⃣  Attempting login with credentials ({username}/*****)...")
                    await page.fill('input[name="userName"]', username)
                    await page.fill('input[type="password"]', password)
                    await take_screenshot(page, "03_login_filled")

                    # Click login button
                    await page.click('button[type="submit"]')
                    await asyncio.sleep(3)
                    await page.wait_for_load_state("networkidle", timeout=30000)
                    await take_screenshot(page, "04_after_login")
                    print("   ✅ Login attempted")
                else:
                    print("\n⚠️  No credentials provided. Please login manually in the browser window.")
                    print("   Press Enter after logging in to continue...")
                    input()
                    await take_screenshot(page, "03_after_manual_login")
            else:
                print("   ✅ Already logged in or on different page")

            # Step 3: Check for dashboard
            print("\n4️⃣  Checking for main dashboard...")
            await asyncio.sleep(2)
            await take_screenshot(page, "05_dashboard")

            # Step 4: Look for minio source in sidebar
            print("\n5️⃣  Looking for 'minio' source in sidebar...")

            # Try multiple selectors for the sidebar
            selectors = [
                'text="minio"',
                '[data-qa="source-minio"]',
                'a:has-text("minio")',
                'div:has-text("minio")',
            ]

            minio_found = False
            for selector in selectors:
                count = await page.locator(selector).count()
                if count > 0:
                    print(f"   ✅ Found 'minio' using selector: {selector} (count: {count})")
                    minio_found = True
                    break

            if not minio_found:
                print("   ❌ 'minio' source NOT found in sidebar")
                print("   🔍 Checking all text on page...")
                page_text = await page.text_content('body')
                if 'minio' in page_text.lower():
                    print("   ⚠️  'minio' text exists somewhere on page")
                else:
                    print("   ❌ 'minio' text not found anywhere on page")
                await take_screenshot(page, "06_minio_not_found")

                # Print page structure
                print("\n   📋 Page structure:")
                nav_items = await page.locator('[class*="nav"]').all()
                print(f"   Found {len(nav_items)} nav-like elements")

                return

            # Step 5: Navigate to minio source
            print("\n6️⃣  Clicking on 'minio' source...")
            await page.click('text="minio"')
            await asyncio.sleep(2)
            await page.wait_for_load_state("networkidle", timeout=30000)
            await take_screenshot(page, "07_minio_clicked")

            # Step 6: Look for zeek-data folder
            print("\n7️⃣  Looking for 'zeek-data' folder...")
            zeek_data_selectors = [
                'text="zeek-data"',
                '[data-qa*="zeek-data"]',
                'a:has-text("zeek-data")',
                'div:has-text("zeek-data")',
            ]

            zeek_found = False
            for selector in zeek_data_selectors:
                count = await page.locator(selector).count()
                if count > 0:
                    print(f"   ✅ Found 'zeek-data' using selector: {selector} (count: {count})")
                    zeek_found = True
                    break

            if not zeek_found:
                print("   ❌ 'zeek-data' folder NOT found")
                await take_screenshot(page, "08_zeek_data_not_found")
                return

            # Step 7: Navigate to zeek-data
            print("\n8️⃣  Clicking on 'zeek-data' folder...")
            await page.click('text="zeek-data"')
            await asyncio.sleep(2)
            await page.wait_for_load_state("networkidle", timeout=30000)
            await take_screenshot(page, "09_zeek_data_clicked")

            # Step 8: Look for network-activity-ocsf
            print("\n9️⃣  Looking for 'network-activity-ocsf' dataset...")
            ocsf_selectors = [
                'text="network-activity-ocsf"',
                '[data-qa*="network-activity-ocsf"]',
                'a:has-text("network-activity-ocsf")',
                'div:has-text("network-activity-ocsf")',
            ]

            ocsf_found = False
            for selector in ocsf_selectors:
                count = await page.locator(selector).count()
                if count > 0:
                    print(f"   ✅ Found 'network-activity-ocsf' using selector: {selector} (count: {count})")
                    ocsf_found = True
                    break

            if not ocsf_found:
                print("   ❌ 'network-activity-ocsf' dataset NOT found")
                await take_screenshot(page, "10_ocsf_not_found")
                return

            # Step 9: Click on network-activity-ocsf
            print("\n🔟 Clicking on 'network-activity-ocsf' dataset...")
            await page.click('text="network-activity-ocsf"')
            await asyncio.sleep(3)
            await page.wait_for_load_state("networkidle", timeout=30000)
            await take_screenshot(page, "11_ocsf_clicked")

            # Step 10: Check for loading indicators or errors
            print("\n1️⃣1️⃣  Checking for loading indicators or errors...")

            # Look for loading spinners
            loading_selectors = [
                '[class*="loading"]',
                '[class*="spinner"]',
                '[class*="progress"]',
            ]

            for selector in loading_selectors:
                count = await page.locator(selector).count()
                if count > 0:
                    print(f"   ⚠️  Found loading indicator: {selector} (count: {count})")

            # Look for error messages
            error_selectors = [
                '[class*="error"]',
                '[class*="alert"]',
                'text="error"',
                'text="Error"',
                'text="failed"',
                'text="Failed"',
            ]

            for selector in error_selectors:
                count = await page.locator(selector).count()
                if count > 0:
                    print(f"   ❌ Found error indicator: {selector} (count: {count})")
                    element = page.locator(selector).first
                    error_text = await element.text_content()
                    print(f"   Error text: {error_text[:200]}")

            # Step 11: Try to run a query
            print("\n1️⃣2️⃣  Attempting to run test query...")

            # Look for SQL editor or query button
            sql_editor_selectors = [
                'button:has-text("Query")',
                '[data-qa="sql-editor"]',
                'textarea[class*="sql"]',
                '[placeholder*="SQL"]',
            ]

            query_button_found = False
            for selector in sql_editor_selectors:
                count = await page.locator(selector).count()
                if count > 0:
                    print(f"   ✅ Found query interface: {selector}")
                    query_button_found = True

                    # Try to click query button if it's a button
                    if selector.startswith('button'):
                        await page.click(selector)
                        await asyncio.sleep(2)
                        await take_screenshot(page, "12_query_button_clicked")
                    break

            if not query_button_found:
                print("   ⚠️  Could not find SQL editor interface")
                await take_screenshot(page, "13_no_sql_editor")
            else:
                # Try to enter query
                print("\n1️⃣3️⃣  Entering test query...")
                test_query = 'SELECT COUNT(*) FROM minio."zeek-data"."network-activity-ocsf"'

                # Look for SQL input field
                sql_input_selectors = [
                    'textarea[class*="sql"]',
                    '[contenteditable="true"]',
                    'textarea[placeholder*="SQL"]',
                ]

                for selector in sql_input_selectors:
                    count = await page.locator(selector).count()
                    if count > 0:
                        print(f"   ✅ Found SQL input: {selector}")
                        await page.fill(selector, test_query)
                        await asyncio.sleep(1)
                        await take_screenshot(page, "14_query_entered")

                        # Look for run button
                        run_selectors = [
                            'button:has-text("Run")',
                            '[data-qa="run-query"]',
                            'button[class*="run"]',
                        ]

                        for run_sel in run_selectors:
                            run_count = await page.locator(run_sel).count()
                            if run_count > 0:
                                print(f"   ✅ Found run button: {run_sel}")
                                await page.click(run_sel)
                                print("   ⏳ Waiting for query to execute...")
                                await asyncio.sleep(5)
                                await take_screenshot(page, "15_query_running")

                                # Wait a bit more to see results
                                await asyncio.sleep(5)
                                await take_screenshot(page, "16_query_results")
                                break
                        break

            print("\n" + "=" * 80)
            print("DIAGNOSTIC COMPLETE")
            print("=" * 80)
            print(f"\n📁 Screenshots saved to: {SCREENSHOTS_DIR}")

            # Keep browser open for manual inspection
            print("\n⏸️  Browser will stay open for 30 seconds for manual inspection...")
            await asyncio.sleep(30)

        except PlaywrightTimeout as e:
            print(f"\n❌ Timeout error: {e}")
            await take_screenshot(page, "error_timeout")
        except Exception as e:
            print(f"\n❌ Error occurred: {e}")
            await take_screenshot(page, "error_general")
            import traceback
            traceback.print_exc()
        finally:
            await browser.close()

if __name__ == "__main__":
    import sys
    import os

    # Get credentials from command line args or environment
    username = sys.argv[1] if len(sys.argv) > 1 else os.environ.get('DREMIO_USER')
    password = sys.argv[2] if len(sys.argv) > 2 else os.environ.get('DREMIO_PASSWORD')

    if not username or not password:
        print("Usage: python diagnose_dremio.py [username] [password]")
        print("Or set DREMIO_USER and DREMIO_PASSWORD environment variables")
        print("\nRunning in manual login mode...")

    asyncio.run(diagnose_dremio(username, password))
