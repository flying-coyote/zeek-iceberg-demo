#!/usr/bin/env python3
"""
Deep diagnostic of Dremio page loading issues
"""

import asyncio
from playwright.async_api import async_playwright
from pathlib import Path
from datetime import datetime
import json

SCREENSHOTS_DIR = Path(__file__).parent.parent / "screenshots"
SCREENSHOTS_DIR.mkdir(exist_ok=True)

async def deep_diagnose():
    """Deep diagnostic of Dremio"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        # Collect all console messages
        console_messages = []
        page.on("console", lambda msg: console_messages.append({
            'type': msg.type,
            'text': msg.text,
            'location': msg.location
        }))

        # Collect all errors
        errors = []
        page.on("pageerror", lambda err: errors.append(str(err)))

        # Collect all network requests
        network_requests = []
        page.on("request", lambda req: network_requests.append({
            'url': req.url,
            'method': req.method,
            'resourceType': req.resource_type
        }))

        # Collect all network responses
        network_responses = []
        page.on("response", lambda resp: network_responses.append({
            'url': resp.url,
            'status': resp.status,
            'statusText': resp.status_text
        }))

        try:
            print("=" * 80)
            print("DEEP DREMIO DIAGNOSTIC")
            print("=" * 80)

            print("\n1. Navigating to http://localhost:9047...")
            await page.goto("http://localhost:9047", wait_until="networkidle", timeout=30000)

            # Wait a bit for any async loading
            print("2. Waiting for page to fully load...")
            await asyncio.sleep(5)

            url = page.url
            title = await page.title()

            print(f"\n3. Page Information:")
            print(f"   URL: {url}")
            print(f"   Title: {title}")

            # Get HTML content
            html_content = await page.content()
            print(f"   HTML Length: {len(html_content)} bytes")

            # Save HTML to file
            html_file = SCREENSHOTS_DIR / "dremio_page.html"
            with open(html_file, 'w') as f:
                f.write(html_content)
            print(f"   HTML saved to: {html_file}")

            # Get body text
            body_text = await page.text_content('body')
            print(f"   Body Text Length: {len(body_text) if body_text else 0} chars")
            if body_text:
                print(f"   Body Text: {body_text[:200]}")

            # Take screenshot
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_path = SCREENSHOTS_DIR / f"{timestamp}_deep_diagnostic.png"
            await page.screenshot(path=str(screenshot_path), full_page=True)
            print(f"   Screenshot: {screenshot_path}")

            # Check for React or other JS frameworks
            print("\n4. Checking for JavaScript frameworks:")
            react_check = await page.evaluate("() => typeof React !== 'undefined'")
            print(f"   React: {'YES' if react_check else 'NO'}")

            vue_check = await page.evaluate("() => typeof Vue !== 'undefined'")
            print(f"   Vue: {'YES' if vue_check else 'NO'}")

            # Check if there's a root div
            root_divs = ['#root', '#app', '[data-reactroot]', '.app']
            for selector in root_divs:
                count = await page.locator(selector).count()
                if count > 0:
                    print(f"   Found root div: {selector}")
                    # Get innerHTML
                    inner_html = await page.locator(selector).first.inner_html()
                    print(f"   Inner HTML length: {len(inner_html)}")

            # Print console messages
            print(f"\n5. Console Messages ({len(console_messages)} total):")
            for msg in console_messages[:20]:  # First 20
                print(f"   [{msg['type']}] {msg['text'][:100]}")

            # Print errors
            print(f"\n6. JavaScript Errors ({len(errors)} total):")
            for err in errors:
                print(f"   ERROR: {err}")

            # Print failed network requests
            print(f"\n7. Network Requests ({len(network_requests)} total):")
            failed_responses = [r for r in network_responses if r['status'] >= 400]
            print(f"   Failed requests ({len(failed_responses)}):")
            for resp in failed_responses[:20]:
                print(f"   [{resp['status']}] {resp['url']}")

            # Save diagnostic data
            diagnostic_file = SCREENSHOTS_DIR / "dremio_diagnostic.json"
            with open(diagnostic_file, 'w') as f:
                json.dump({
                    'url': url,
                    'title': title,
                    'console_messages': console_messages,
                    'errors': errors,
                    'network_responses': network_responses
                }, f, indent=2)
            print(f"\n8. Full diagnostic data saved to: {diagnostic_file}")

        except Exception as e:
            print(f"\nERROR: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(deep_diagnose())
