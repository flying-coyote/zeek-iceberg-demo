#!/usr/bin/env python3
"""
Check Dremio Reflections Status (with authentication)

Usage:
    export DREMIO_PASSWORD="your_password"
    python3 scripts/check_reflections_auto.py
"""

import requests
import os
import sys

DREMIO_URL = "http://localhost:9047"
DREMIO_USERNAME = os.getenv("DREMIO_USERNAME", "admin")
DREMIO_PASSWORD = os.getenv("DREMIO_PASSWORD", "")

def main():
    print("=" * 70)
    print("Dremio Reflection Status Check")
    print("=" * 70)
    print()

    if not DREMIO_PASSWORD:
        print("❌ DREMIO_PASSWORD environment variable is required")
        print()
        print("Usage:")
        print('  export DREMIO_PASSWORD="your_password"')
        print("  python3 scripts/check_reflections_auto.py")
        return 1

    # Authenticate
    print("Authenticating with Dremio...")
    auth_url = f"{DREMIO_URL}/apiv2/login"

    try:
        response = requests.post(
            auth_url,
            json={"userName": DREMIO_USERNAME, "password": DREMIO_PASSWORD},
            timeout=10
        )

        if response.status_code != 200:
            print(f"❌ Authentication failed: {response.text}")
            return 1

        token = response.json()["token"]
        print("✓ Authenticated successfully")
        print()

    except Exception as e:
        print(f"❌ Authentication error: {e}")
        return 1

    # Get reflections
    print("Fetching reflections...")
    headers = {
        "Authorization": f"_dremio{token}",
        "Content-Type": "application/json"
    }

    reflection_url = f"{DREMIO_URL}/api/v3/reflection"

    try:
        response = requests.get(reflection_url, headers=headers, timeout=10)

        if response.status_code != 200:
            print(f"❌ Failed to get reflections: {response.status_code}")
            print(f"Response: {response.text}")
            return 1

        reflections = response.json().get("data", [])

        print("=" * 70)
        print(f"Found {len(reflections)} reflections")
        print("=" * 70)
        print()

        if not reflections:
            print("⚠️  NO REFLECTIONS FOUND")
            print()
            print("Reflections have not been set up yet.")
            print()
            print("To create reflections, run:")
            print('  export DREMIO_PASSWORD="your_password"')
            print("  python3 scripts/create_reflections_auto.py")
            print()
            return 0

        # Show reflection details
        available = 0
        refreshing = 0
        failed = 0
        other = 0

        for i, r in enumerate(reflections, 1):
            name = r.get("name", "Unknown")
            r_type = r.get("type", "Unknown")
            dataset_id = r.get("datasetId", "N/A")
            status = r.get("status", {})
            availability = status.get("availability", "UNKNOWN")
            config = status.get("config", "UNKNOWN")

            # Count by status
            if availability == "AVAILABLE":
                icon = "✅"
                available += 1
            elif availability == "REFRESHING":
                icon = "⏳"
                refreshing += 1
            elif availability == "FAILED":
                icon = "❌"
                failed += 1
            else:
                icon = "⚠️ "
                other += 1

            print(f"{icon} Reflection {i}: {name}")
            print(f"   Type: {r_type}")
            print(f"   Status: {availability}")
            print(f"   Config: {config}")
            print(f"   Dataset ID: {dataset_id[:20]}..." if len(dataset_id) > 20 else f"   Dataset ID: {dataset_id}")
            print()

        # Summary
        print("=" * 70)
        print("Summary:")
        print(f"  ✅ Available: {available}")
        print(f"  ⏳ Refreshing: {refreshing}")
        print(f"  ❌ Failed: {failed}")
        print(f"  ⚠️  Other: {other}")
        print("=" * 70)
        print()

        # Overall status
        if available == len(reflections) and available > 0:
            print("🎉 ALL REFLECTIONS ARE AVAILABLE AND READY!")
            print()
            print("Your queries will be accelerated 10-100x.")
            print()
            print("Test with this query:")
            print('  SELECT activity_name, COUNT(*) as events')
            print('  FROM minio."zeek-data"."network-activity-ocsf"')
            print('  GROUP BY activity_name;')
            print()
            print("Check the Profile tab for green Reflection nodes.")
            return 0

        elif refreshing > 0:
            print("⏳ REFLECTIONS ARE STILL BUILDING")
            print()
            print(f"{refreshing} reflection(s) are refreshing.")
            print("Wait 2-5 minutes for them to complete.")
            print()
            print("Check status again:")
            print("  python3 scripts/check_reflections_auto.py")
            return 0

        elif failed > 0:
            print("❌ SOME REFLECTIONS FAILED")
            print()
            print(f"{failed} reflection(s) failed to build.")
            print()
            print("To fix:")
            print("1. Go to Dremio UI: http://localhost:9047")
            print("2. Navigate to dataset Reflections tab")
            print("3. Disable and re-enable failed reflections")
            print()
            print("Or delete and recreate:")
            print("  python3 scripts/create_reflections_auto.py")
            return 1

        else:
            print("⚠️  REFLECTIONS IN UNKNOWN STATE")
            print()
            print("Check manually in Dremio UI.")
            return 1

    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
