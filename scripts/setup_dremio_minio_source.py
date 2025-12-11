#!/usr/bin/env python3
"""
Setup MinIO Source in Dremio via Playwright

This script automates adding MinIO as a data source in Dremio.

Requirements:
    pip install playwright
    playwright install chromium

Usage:
    export DREMIO_USERNAME="admin"
    export DREMIO_PASSWORD="your_password"
    python3 scripts/setup_dremio_minio_source.py
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

# MinIO Configuration
MINIO_ENDPOINT = "minio:9000"
MINIO_ACCESS_KEY = "minioadmin"
MINIO_SECRET_KEY = "minioadmin"
MINIO_SOURCE_NAME = "minio"


async def setup_minio_source(page):
    """Setup MinIO as a source in Dremio"""
    logger.info("Setting up MinIO source in Dremio...")

    try:
        # Navigate to sources page
        logger.info("  Navigating to sources page...")
        await page.goto(f"{DREMIO_URL}/#/sources", wait_until='networkidle', timeout=30000)
        await asyncio.sleep(3)

        # Check if MinIO source already exists
        logger.info("  Checking if MinIO source already exists...")
        minio_exists = await page.query_selector(f'text="{MINIO_SOURCE_NAME}"')
        if minio_exists:
            logger.info("  ✓ MinIO source already exists!")
            return True

        # Click "Add Source" button
        logger.info("  Looking for 'Add Source' button...")
        add_source_selectors = [
            'button:has-text("Add Source")',
            'text="Add Source"',
            '[data-qa*="add-source"]',
            'button:has-text("+")'
        ]

        clicked_add = False
        for selector in add_source_selectors:
            try:
                await page.click(selector, timeout=3000)
                logger.info("  ✓ Clicked 'Add Source'")
                clicked_add = True
                await asyncio.sleep(2)
                break
            except:
                continue

        if not clicked_add:
            logger.warning("  ⚠ Could not find 'Add Source' button")
            await page.screenshot(path="/tmp/dremio_no_add_source.png")
            logger.info("  Screenshot: /tmp/dremio_no_add_source.png")
            return False

        # Select "Amazon S3" or "S3" source type
        logger.info("  Looking for S3 source type...")
        s3_selectors = [
            'text="Amazon S3"',
            'text="S3"',
            '[data-qa*="s3"]',
            'div:has-text("Amazon S3")',
            'button:has-text("Amazon S3")'
        ]

        clicked_s3 = False
        for selector in s3_selectors:
            try:
                await page.click(selector, timeout=3000)
                logger.info("  ✓ Selected S3 source type")
                clicked_s3 = True
                await asyncio.sleep(2)
                break
            except:
                continue

        if not clicked_s3:
            logger.warning("  ⚠ Could not find S3 source option")
            await page.screenshot(path="/tmp/dremio_no_s3_option.png")
            logger.info("  Screenshot: /tmp/dremio_no_s3_option.png")
            logger.info("")
            logger.info("  Manual setup required:")
            logger.info("  1. Click 'Add Source' in Dremio UI")
            logger.info("  2. Select 'Amazon S3' or 'S3'")
            logger.info("  3. Fill in the MinIO details")
            return False

        # Fill in source configuration
        logger.info("  Filling in source configuration...")

        # Source name
        try:
            await page.fill('input[name="name"]', MINIO_SOURCE_NAME, timeout=5000)
            logger.info(f"    ✓ Name: {MINIO_SOURCE_NAME}")
        except:
            logger.warning("    ⚠ Could not fill source name")

        # Connection settings - look for "Connection Properties" or similar
        logger.info("  Looking for connection settings...")

        # Enable path-style access (required for MinIO)
        try:
            # Look for "Enable compatibility mode" or path-style checkbox
            path_style_selectors = [
                'input[type="checkbox"]:has-text("path")',
                'input[type="checkbox"]:has-text("compatibility")',
                'label:has-text("Enable compatibility mode")',
                'label:has-text("path-style")'
            ]

            for selector in path_style_selectors:
                try:
                    await page.click(selector, timeout=2000)
                    logger.info("    ✓ Enabled path-style access")
                    break
                except:
                    continue
        except:
            logger.info("    ⚠ Could not enable path-style (may not be visible)")

        # Fill connection properties
        logger.info("  Looking for connection property fields...")

        # Try to find and fill endpoint
        try:
            endpoint_selectors = [
                'input[placeholder*="endpoint"]',
                'input[name*="endpoint"]',
                'input[label*="Endpoint"]'
            ]

            for selector in endpoint_selectors:
                try:
                    await page.fill(selector, f"http://{MINIO_ENDPOINT}", timeout=2000)
                    logger.info(f"    ✓ Endpoint: http://{MINIO_ENDPOINT}")
                    break
                except:
                    continue
        except:
            logger.warning("    ⚠ Could not fill endpoint")

        # Access key
        try:
            access_key_selectors = [
                'input[name="accessKey"]',
                'input[name="config.accessKey"]',
                'input[placeholder*="Access Key"]'
            ]

            for selector in access_key_selectors:
                try:
                    await page.fill(selector, MINIO_ACCESS_KEY, timeout=2000)
                    logger.info(f"    ✓ Access Key: {MINIO_ACCESS_KEY}")
                    break
                except:
                    continue
        except:
            logger.warning("    ⚠ Could not fill access key")

        # Secret key
        try:
            secret_key_selectors = [
                'input[name="secretKey"]',
                'input[name="config.secretKey"]',
                'input[placeholder*="Secret Key"]',
                'input[type="password"]'
            ]

            for selector in secret_key_selectors:
                try:
                    await page.fill(selector, MINIO_SECRET_KEY, timeout=2000)
                    logger.info(f"    ✓ Secret Key: {MINIO_SECRET_KEY}")
                    break
                except:
                    continue
        except:
            logger.warning("    ⚠ Could not fill secret key")

        # Save the source
        logger.info("  Looking for Save button...")
        await asyncio.sleep(2)

        save_selectors = [
            'button:has-text("Save")',
            'button[type="submit"]',
            'button:has-text("Create")',
            '[data-qa*="save"]'
        ]

        saved = False
        for selector in save_selectors:
            try:
                await page.click(selector, timeout=3000)
                logger.info("  ✓ Clicked Save")
                saved = True
                await asyncio.sleep(5)  # Wait for source to be created
                break
            except:
                continue

        if not saved:
            logger.warning("  ⚠ Could not find Save button")
            await page.screenshot(path="/tmp/dremio_no_save_button.png")
            logger.info("  Screenshot: /tmp/dremio_no_save_button.png")
            logger.info("")
            logger.info("  ⚠️  Automated setup incomplete.")
            logger.info("  Please complete setup manually in the open browser.")
            logger.info("")
            logger.info("  Browser will stay open for 60 seconds...")
            await asyncio.sleep(60)
            return False

        logger.info("✓ MinIO source created successfully!")
        return True

    except Exception as e:
        logger.error(f"Error setting up MinIO source: {e}")
        await page.screenshot(path="/tmp/dremio_source_setup_error.png")
        logger.info("Screenshot: /tmp/dremio_source_setup_error.png")
        return False


async def main():
    """Main execution"""

    logger.info("=" * 70)
    logger.info("Dremio MinIO Source Setup via Playwright")
    logger.info("=" * 70)
    logger.info("")

    # Check credentials
    if not DREMIO_PASSWORD:
        logger.error("DREMIO_PASSWORD environment variable is required")
        logger.info("")
        logger.info("Usage:")
        logger.info('  export DREMIO_USERNAME="admin"')
        logger.info('  export DREMIO_PASSWORD="your_password"')
        logger.info("  python3 scripts/setup_dremio_minio_source.py")
        return 1

    logger.info(f"Username: {DREMIO_USERNAME}")
    logger.info(f"Password: {'*' * len(DREMIO_PASSWORD)}")
    logger.info("")

    async with async_playwright() as p:
        logger.info("Launching browser...")
        browser = await p.chromium.launch(
            headless=False,
            slow_mo=1000
        )

        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            locale='en-US'
        )

        page = await context.new_page()

        try:
            # Navigate to Dremio and check login
            logger.info("Opening Dremio...")
            await page.goto(DREMIO_URL, wait_until='networkidle', timeout=30000)
            await asyncio.sleep(3)

            # Check if we need to login
            current_url = page.url
            if 'login' in current_url.lower() or '/home' not in current_url:
                logger.info("Login required - please log in manually in the browser")
                logger.info("Waiting 30 seconds for you to log in...")
                await asyncio.sleep(30)

            # Setup MinIO source
            success = await setup_minio_source(page)

            if success:
                logger.info("")
                logger.info("=" * 70)
                logger.info("✅ MinIO source setup complete!")
                logger.info("=" * 70)
                logger.info("")
                logger.info("Next steps:")
                logger.info("1. Verify you can see 'minio' in sources")
                logger.info("2. Navigate to: minio > zeek-data > network-activity-ocsf")
                logger.info("3. Format the folder as Parquet if needed")
                logger.info("4. Run reflection setup script")
                logger.info("")
                logger.info("Browser will stay open for 30 seconds...")
                await asyncio.sleep(30)
                return 0
            else:
                logger.info("")
                logger.info("=" * 70)
                logger.info("⚠️  Automated setup incomplete")
                logger.info("=" * 70)
                logger.info("")
                logger.info("Please complete the setup manually:")
                logger.info("1. In the open browser, click 'Add Source'")
                logger.info("2. Select 'Amazon S3'")
                logger.info("3. Fill in:")
                logger.info(f"   - Name: {MINIO_SOURCE_NAME}")
                logger.info("   - Enable compatibility mode: YES")
                logger.info(f"   - Endpoint: http://{MINIO_ENDPOINT}")
                logger.info(f"   - Access Key: {MINIO_ACCESS_KEY}")
                logger.info(f"   - Secret Key: {MINIO_SECRET_KEY}")
                logger.info("4. Click Save")
                logger.info("")
                logger.info("Browser will stay open for 120 seconds...")
                await asyncio.sleep(120)
                return 1

        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
            await page.screenshot(path="/tmp/dremio_setup_error.png")
            return 1

        finally:
            await browser.close()

    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
