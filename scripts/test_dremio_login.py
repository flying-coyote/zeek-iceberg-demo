#!/usr/bin/env python3
"""
Quick test to try different Dremio login credentials
"""

import asyncio
from playwright.async_api import async_playwright
from pathlib import Path
from datetime import datetime

SCREENSHOTS_DIR = Path(__file__).parent.parent / "screenshots"
SCREENSHOTS_DIR.mkdir(exist_ok=True)

# Common credential combinations to try
CREDENTIAL_COMBINATIONS = [
    ("admin", "admin123"),
    ("admin", "Admin123"),
    ("dremio", "dremio123"),
    ("dremio", "Dremio123"),
    ("admin", "password"),
    ("root", "root"),
]

async def test_login(username, password):
    """Test a single login combination"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        try:
            print(f"\nTrying: {username} / {'*' * len(password)}")

            # Navigate to login page
            await page.goto("http://localhost:9047", timeout=10000)
            await asyncio.sleep(1)

            # Check if we're on login page
            if "/login" not in page.url:
                print("  Not on login page - might already be logged in or different page")
                return None

            # Fill credentials
            await page.fill('input[name="userName"]', username)
            await page.fill('input[type="password"]', password)

            # Click login
            await page.click('button[type="submit"]')
            await asyncio.sleep(2)

            # Check result
            current_url = page.url

            # Look for error message
            error_elements = await page.locator('[class*="error"], [class*="alert"]').count()

            if "/login" not in current_url and error_elements == 0:
                print(f"  ✅ SUCCESS! Credentials work: {username} / {password}")
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                await page.screenshot(path=str(SCREENSHOTS_DIR / f"{timestamp}_successful_login.png"))
                return (username, password)
            else:
                print(f"  ❌ Failed")
                return None

        except Exception as e:
            print(f"  ❌ Error: {e}")
            return None
        finally:
            await browser.close()

async def main():
    print("=" * 60)
    print("DREMIO LOGIN CREDENTIAL TESTER")
    print("=" * 60)

    for username, password in CREDENTIAL_COMBINATIONS:
        result = await test_login(username, password)
        if result:
            print("\n" + "=" * 60)
            print(f"FOUND WORKING CREDENTIALS: {result[0]} / {result[1]}")
            print("=" * 60)
            return result

    print("\n" + "=" * 60)
    print("NO WORKING CREDENTIALS FOUND")
    print("=" * 60)
    print("\nYou may need to:")
    print("1. Create a new admin account (first-time setup)")
    print("2. Reset Dremio data: docker-compose down -v && docker-compose up -d dremio")
    print("3. Check documentation for your specific credentials")

    return None

if __name__ == "__main__":
    asyncio.run(main())
