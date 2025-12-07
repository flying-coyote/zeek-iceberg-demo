#!/usr/bin/env python3
"""
Setup Dremio Reflections via Playwright Browser Automation

This script automates the creation of Dremio reflections through the UI
since the REST API requires authentication credentials.

Requirements:
    pip install playwright
    playwright install chromium

Usage:
    python3 scripts/setup_reflections_playwright.py

Note: You'll need to enter your Dremio password when prompted
"""

import asyncio
import logging
import sys
import getpass
from pathlib import Path
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
DREMIO_URL = "http://localhost:9047"
DREMIO_USERNAME = "admin"
DATASET_PATH = ["minio", "zeek-data", "network-activity-ocsf"]


async def login_to_dremio(page, username: str, password: str):
    """Login to Dremio"""
    logger.info("Navigating to Dremio...")
    await page.goto(DREMIO_URL, timeout=30000)

    # Wait for login page to load
    await page.wait_for_load_state('networkidle', timeout=10000)

    # Check if already logged in (might redirect to home)
    current_url = page.url
    if '/home' in current_url or '/space' in current_url:
        logger.info("✓ Already logged in")
        return True

    logger.info("Entering credentials...")

    # Wait for username field
    try:
        await page.wait_for_selector('input[name="username"]', timeout=5000)
        await page.fill('input[name="username"]', username)
        logger.info(f"  ✓ Entered username: {username}")
    except PlaywrightTimeout:
        logger.error("Could not find username field")
        return False

    # Enter password
    try:
        await page.fill('input[name="password"]', password)
        logger.info("  ✓ Entered password")
    except Exception as e:
        logger.error(f"Could not enter password: {e}")
        return False

    # Click login button
    try:
        # Try different possible selectors for login button
        login_button = None
        selectors = [
            'button[type="submit"]',
            'button:has-text("Sign In")',
            'button:has-text("Log In")',
            '.login-button'
        ]

        for selector in selectors:
            try:
                login_button = await page.wait_for_selector(selector, timeout=2000)
                if login_button:
                    break
            except:
                continue

        if login_button:
            await login_button.click()
            logger.info("  ✓ Clicked login button")
        else:
            # Try pressing Enter
            await page.keyboard.press('Enter')
            logger.info("  ✓ Pressed Enter to submit")

    except Exception as e:
        logger.error(f"Could not click login button: {e}")
        return False

    # Wait for redirect to home page
    try:
        await page.wait_for_url('**/home**', timeout=10000)
        logger.info("✓ Successfully logged in")
        return True
    except PlaywrightTimeout:
        # Check if we're on a different authenticated page
        current_url = page.url
        if '/space' in current_url or 'sources' in current_url:
            logger.info("✓ Successfully logged in (on different page)")
            return True
        else:
            logger.error(f"Login may have failed - current URL: {current_url}")
            return False


async def navigate_to_dataset(page, path: list):
    """Navigate to the OCSF dataset"""
    logger.info(f"Navigating to dataset: {' > '.join(path)}")

    # Go to sources/datasets page
    await page.goto(f"{DREMIO_URL}/#/sources", timeout=30000)
    await page.wait_for_load_state('networkidle', timeout=10000)

    # Navigate through the path
    for i, segment in enumerate(path):
        logger.info(f"  Clicking: {segment}")

        try:
            # Wait a bit for UI to settle
            await asyncio.sleep(2)

            # Try to find and click the segment
            # Dremio uses different selectors, try multiple approaches
            clicked = False

            # Approach 1: Direct text match
            try:
                element = await page.wait_for_selector(f'text="{segment}"', timeout=5000)
                if element:
                    await element.click()
                    clicked = True
                    logger.info(f"    ✓ Clicked {segment}")
            except:
                pass

            # Approach 2: Try data-qa attributes
            if not clicked:
                try:
                    element = await page.wait_for_selector(f'[data-qa*="{segment}"]', timeout=3000)
                    if element:
                        await element.click()
                        clicked = True
                        logger.info(f"    ✓ Clicked {segment} (data-qa)")
                except:
                    pass

            # Approach 3: Contains text
            if not clicked:
                try:
                    element = await page.wait_for_selector(f'text=/.*{segment}.*/i', timeout=3000)
                    if element:
                        await element.click()
                        clicked = True
                        logger.info(f"    ✓ Clicked {segment} (contains)")
                except:
                    pass

            if not clicked:
                logger.warning(f"    ⚠ Could not find/click {segment}")
                # Take screenshot for debugging
                screenshot_path = f"/tmp/dremio_nav_{segment}.png"
                await page.screenshot(path=screenshot_path)
                logger.info(f"    Screenshot saved: {screenshot_path}")

            # Wait for navigation/loading
            await asyncio.sleep(3)

        except Exception as e:
            logger.error(f"    Error navigating to {segment}: {e}")
            screenshot_path = f"/tmp/dremio_error_{segment}.png"
            await page.screenshot(path=screenshot_path)
            logger.info(f"    Error screenshot: {screenshot_path}")

    logger.info("  ✓ Navigation complete")
    return True


async def create_raw_reflection(page):
    """Create a raw reflection via UI"""
    logger.info("Creating raw reflection...")

    try:
        # Look for Reflections tab
        logger.info("  Looking for Reflections tab...")
        await asyncio.sleep(2)

        # Try to click Reflections tab
        reflections_tab = None
        selectors = [
            'text="Reflections"',
            '[data-qa*="reflection"]',
            'button:has-text("Reflections")',
            'a:has-text("Reflections")'
        ]

        for selector in selectors:
            try:
                reflections_tab = await page.wait_for_selector(selector, timeout=3000)
                if reflections_tab:
                    await reflections_tab.click()
                    logger.info("  ✓ Clicked Reflections tab")
                    await asyncio.sleep(2)
                    break
            except:
                continue

        if not reflections_tab:
            logger.warning("  ⚠ Could not find Reflections tab")
            await page.screenshot(path="/tmp/dremio_no_reflections_tab.png")
            logger.info("  Screenshot saved: /tmp/dremio_no_reflections_tab.png")
            return False

        # Look for "Create Reflection" or "New Reflection" button
        logger.info("  Looking for Create Reflection button...")
        create_button = None
        selectors = [
            'text="Create Reflection"',
            'text="New Reflection"',
            'button:has-text("Create")',
            '[data-qa*="create-reflection"]'
        ]

        for selector in selectors:
            try:
                create_button = await page.wait_for_selector(selector, timeout=3000)
                if create_button:
                    await create_button.click()
                    logger.info("  ✓ Clicked Create Reflection button")
                    await asyncio.sleep(2)
                    break
            except:
                continue

        if not create_button:
            logger.warning("  ⚠ Could not find Create Reflection button")
            await page.screenshot(path="/tmp/dremio_no_create_button.png")
            logger.info("  Screenshot saved: /tmp/dremio_no_create_button.png")
            return False

        # Select "Raw Reflection"
        logger.info("  Selecting Raw Reflection type...")
        raw_option = None
        selectors = [
            'text="Raw Reflection"',
            '[data-qa*="raw"]',
            'label:has-text("Raw")'
        ]

        for selector in selectors:
            try:
                raw_option = await page.wait_for_selector(selector, timeout=3000)
                if raw_option:
                    await raw_option.click()
                    logger.info("  ✓ Selected Raw Reflection")
                    await asyncio.sleep(2)
                    break
            except:
                continue

        # Look for Save/Create button
        logger.info("  Looking for Save button...")
        save_button = None
        selectors = [
            'button:has-text("Save")',
            'button:has-text("Create")',
            'button[type="submit"]',
            '[data-qa*="save"]'
        ]

        for selector in selectors:
            try:
                save_button = await page.wait_for_selector(selector, timeout=3000)
                if save_button:
                    await save_button.click()
                    logger.info("  ✓ Clicked Save button")
                    await asyncio.sleep(3)
                    break
            except:
                continue

        logger.info("✓ Raw reflection created (or attempted)")
        return True

    except Exception as e:
        logger.error(f"Error creating raw reflection: {e}")
        await page.screenshot(path="/tmp/dremio_reflection_error.png")
        logger.info("Error screenshot: /tmp/dremio_reflection_error.png")
        return False


async def create_aggregation_reflection(page, name: str, dimensions: list, measures: list):
    """Create an aggregation reflection via UI"""
    logger.info(f"Creating aggregation reflection: {name}")

    try:
        # Click Create Reflection again
        create_button = await page.wait_for_selector('text="Create Reflection"', timeout=5000)
        if create_button:
            await create_button.click()
            await asyncio.sleep(2)

        # Select Aggregation Reflection
        agg_option = await page.wait_for_selector('text="Aggregation"', timeout=3000)
        if agg_option:
            await agg_option.click()
            await asyncio.sleep(2)
            logger.info(f"  ✓ Selected Aggregation type")

        # Add dimensions and measures
        # (This would require more specific UI automation based on Dremio's form structure)
        logger.info(f"  Dimensions: {', '.join(dimensions)}")
        logger.info(f"  Measures: {', '.join(measures)}")

        # For now, just log that we would create it
        logger.info(f"  ⚠ Manual configuration needed for: {name}")

        return True

    except Exception as e:
        logger.error(f"Error creating aggregation reflection: {e}")
        return False


async def main():
    """Main execution flow"""

    logger.info("=" * 70)
    logger.info("Dremio Reflection Setup via Playwright")
    logger.info("=" * 70)
    logger.info("")

    # Get password
    password = getpass.getpass(f"Enter Dremio password for {DREMIO_USERNAME}: ")

    if not password:
        logger.error("Password is required")
        return 1

    async with async_playwright() as p:
        # Launch browser
        logger.info("Launching browser...")
        browser = await p.chromium.launch(
            headless=False,  # Show browser so user can see progress
            slow_mo=500  # Slow down actions for visibility
        )

        # Create context with proper locale
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            locale='en-US'  # Fix for locale issue
        )

        page = await context.new_page()

        try:
            # Step 1: Login
            login_success = await login_to_dremio(page, DREMIO_USERNAME, password)
            if not login_success:
                logger.error("Login failed - cannot continue")
                await page.screenshot(path="/tmp/dremio_login_failed.png")
                logger.info("Screenshot saved: /tmp/dremio_login_failed.png")
                return 1

            logger.info("")

            # Step 2: Navigate to dataset
            nav_success = await navigate_to_dataset(page, DATASET_PATH)
            if not nav_success:
                logger.error("Navigation failed - cannot continue")
                return 1

            logger.info("")

            # Step 3: Create raw reflection
            raw_success = await create_raw_reflection(page)

            logger.info("")
            logger.info("=" * 70)
            logger.info("Playwright automation complete")
            logger.info("=" * 70)
            logger.info("")
            logger.info("Browser will remain open for 60 seconds for manual verification")
            logger.info("You can manually create additional reflections if needed")
            logger.info("")

            # Keep browser open for manual inspection
            await asyncio.sleep(60)

        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
            await page.screenshot(path="/tmp/dremio_unexpected_error.png")
            logger.info("Screenshot saved: /tmp/dremio_unexpected_error.png")
            return 1

        finally:
            await browser.close()

    logger.info("✓ Browser closed")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
