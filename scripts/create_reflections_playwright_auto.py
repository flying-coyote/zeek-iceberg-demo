#!/usr/bin/env python3
"""
Automatically Create Dremio Reflections via Playwright

This script uses Playwright to automate clicking through the Dremio UI
to create reflections. More reliable than REST API for complex UI interactions.

Requirements:
    pip install playwright
    playwright install chromium

Usage:
    export DREMIO_USERNAME="admin"
    export DREMIO_PASSWORD="your_password"
    python3 scripts/create_reflections_playwright_auto.py
"""

import asyncio
import logging
import sys
import os
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
DREMIO_URL = "http://localhost:9047"
DREMIO_USERNAME = os.getenv("DREMIO_USERNAME", "admin")
DREMIO_PASSWORD = os.getenv("DREMIO_PASSWORD", "")


async def login_to_dremio(page, username: str, password: str):
    """Login to Dremio"""
    logger.info("Navigating to Dremio...")
    await page.goto(DREMIO_URL, wait_until='networkidle', timeout=30000)

    # Check if already logged in
    current_url = page.url
    if '/home' in current_url or '/space' in current_url or '/sources' in current_url:
        logger.info("✓ Already logged in")
        return True

    logger.info("Logging in...")

    try:
        # Fill username
        await page.fill('input[name="username"]', username, timeout=5000)
        logger.info(f"  ✓ Entered username: {username}")

        # Fill password
        await page.fill('input[name="password"]', password)
        logger.info("  ✓ Entered password")

        # Click login button
        await page.click('button[type="submit"]', timeout=5000)
        logger.info("  ✓ Clicked login")

        # Wait for navigation
        await page.wait_for_url('**/home**', timeout=10000)
        logger.info("✓ Successfully logged in")
        return True

    except Exception as e:
        logger.error(f"Login failed: {e}")
        return False


async def navigate_to_dataset(page):
    """Navigate to the OCSF dataset"""
    logger.info("Navigating to dataset...")

    try:
        # Go to sources page
        await page.goto(f"{DREMIO_URL}/#/sources", wait_until='networkidle', timeout=30000)
        logger.info("  ✓ On sources page")

        await asyncio.sleep(2)

        # Click through: minio > zeek-data > network-activity-ocsf
        steps = ["minio", "zeek-data", "network-activity-ocsf"]

        for step in steps:
            logger.info(f"  Looking for: {step}")

            # Try multiple strategies to find and click
            clicked = False

            # Strategy 1: Try exact text match
            try:
                await page.click(f'text="{step}"', timeout=5000)
                clicked = True
                logger.info(f"    ✓ Clicked: {step}")
            except:
                pass

            # Strategy 2: Try partial text match
            if not clicked:
                try:
                    elements = await page.query_selector_all(f'text=/.*{step}.*/i')
                    if elements:
                        await elements[0].click()
                        clicked = True
                        logger.info(f"    ✓ Clicked: {step} (partial match)")
                except:
                    pass

            # Strategy 3: Try data-qa or aria-label
            if not clicked:
                try:
                    await page.click(f'[data-qa*="{step}"]', timeout=3000)
                    clicked = True
                    logger.info(f"    ✓ Clicked: {step} (data-qa)")
                except:
                    pass

            if not clicked:
                logger.warning(f"    ⚠ Could not find: {step}")
                await page.screenshot(path=f"/tmp/dremio_nav_{step}.png")
                logger.info(f"    Screenshot: /tmp/dremio_nav_{step}.png")

            # Wait after each click
            await asyncio.sleep(3)

        logger.info("✓ Navigation complete")
        return True

    except Exception as e:
        logger.error(f"Navigation failed: {e}")
        await page.screenshot(path="/tmp/dremio_nav_error.png")
        return False


async def click_reflections_tab(page):
    """Click the Reflections tab"""
    logger.info("Opening Reflections tab...")

    try:
        # Try different selectors for Reflections tab
        selectors = [
            'text="Reflections"',
            '[data-qa*="reflection"]',
            'button:has-text("Reflections")',
            'a:has-text("Reflections")',
            '[role="tab"]:has-text("Reflections")'
        ]

        for selector in selectors:
            try:
                await page.click(selector, timeout=3000)
                logger.info("  ✓ Clicked Reflections tab")
                await asyncio.sleep(2)
                return True
            except:
                continue

        logger.warning("  ⚠ Could not find Reflections tab")
        await page.screenshot(path="/tmp/dremio_no_reflections_tab.png")
        return False

    except Exception as e:
        logger.error(f"Error clicking Reflections tab: {e}")
        return False


async def create_raw_reflection(page):
    """Create a raw reflection"""
    logger.info("Creating raw reflection...")

    try:
        # Click "Create Reflection" button
        create_selectors = [
            'button:has-text("Create Reflection")',
            'text="Create Reflection"',
            '[data-qa*="create-reflection"]'
        ]

        clicked_create = False
        for selector in create_selectors:
            try:
                await page.click(selector, timeout=3000)
                logger.info("  ✓ Clicked Create Reflection")
                clicked_create = True
                await asyncio.sleep(2)
                break
            except:
                continue

        if not clicked_create:
            logger.warning("  ⚠ Could not find Create Reflection button")
            return False

        # Select "Raw Reflection" option
        raw_selectors = [
            'text="Raw Reflection"',
            '[data-qa*="raw"]',
            'label:has-text("Raw")',
            'input[value="RAW"]'
        ]

        clicked_raw = False
        for selector in raw_selectors:
            try:
                await page.click(selector, timeout=3000)
                logger.info("  ✓ Selected Raw Reflection")
                clicked_raw = True
                await asyncio.sleep(1)
                break
            except:
                continue

        # Click Save button
        save_selectors = [
            'button:has-text("Save")',
            'button:has-text("Create")',
            'button[type="submit"]',
            '[data-qa*="save"]'
        ]

        for selector in save_selectors:
            try:
                await page.click(selector, timeout=3000)
                logger.info("  ✓ Clicked Save")
                await asyncio.sleep(3)
                logger.info("✓ Raw reflection created")
                return True
            except:
                continue

        logger.warning("  ⚠ Could not find Save button")
        return False

    except Exception as e:
        logger.error(f"Error creating raw reflection: {e}")
        await page.screenshot(path="/tmp/dremio_create_reflection_error.png")
        return False


async def main():
    """Main execution"""

    logger.info("=" * 70)
    logger.info("Dremio Reflection Setup via Playwright")
    logger.info("=" * 70)
    logger.info("")

    # Check credentials
    if not DREMIO_PASSWORD:
        logger.error("DREMIO_PASSWORD environment variable is required")
        logger.info("")
        logger.info("Usage:")
        logger.info('  export DREMIO_USERNAME="admin"')
        logger.info('  export DREMIO_PASSWORD="your_password"')
        logger.info("  python3 scripts/create_reflections_playwright_auto.py")
        return 1

    logger.info(f"Username: {DREMIO_USERNAME}")
    logger.info(f"Password: {'*' * len(DREMIO_PASSWORD)}")
    logger.info("")

    async with async_playwright() as p:
        logger.info("Launching browser...")
        browser = await p.chromium.launch(
            headless=False,  # Show browser
            slow_mo=1000  # Slow down for visibility
        )

        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            locale='en-US'
        )

        page = await context.new_page()

        try:
            # Step 1: Login
            if not await login_to_dremio(page, DREMIO_USERNAME, DREMIO_PASSWORD):
                logger.error("Login failed")
                return 1

            logger.info("")

            # Step 2: Navigate to dataset
            if not await navigate_to_dataset(page):
                logger.error("Navigation failed")
                return 1

            logger.info("")

            # Step 3: Open Reflections tab
            if not await click_reflections_tab(page):
                logger.error("Could not open Reflections tab")
                return 1

            logger.info("")

            # Step 4: Create raw reflection
            if not await create_raw_reflection(page):
                logger.error("Could not create raw reflection")
                return 1

            logger.info("")
            logger.info("=" * 70)
            logger.info("✅ Reflection creation initiated!")
            logger.info("=" * 70)
            logger.info("")
            logger.info("The reflection is now building in the background.")
            logger.info("This typically takes 2-5 minutes for 1M records.")
            logger.info("")
            logger.info("Browser will stay open for 60 seconds so you can:")
            logger.info("1. See the reflection in the Reflections tab")
            logger.info("2. Create additional reflections manually if desired")
            logger.info("3. Monitor build progress")
            logger.info("")

            # Keep browser open
            await asyncio.sleep(60)

        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
            await page.screenshot(path="/tmp/dremio_error.png")
            return 1

        finally:
            await browser.close()

    logger.info("✓ Browser closed")
    logger.info("")
    logger.info("Next steps:")
    logger.info("1. Wait 2-5 minutes for reflection to build")
    logger.info("2. Check status in Dremio UI: http://localhost:9047")
    logger.info("3. Test query performance!")
    logger.info("")

    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
