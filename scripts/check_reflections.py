#!/usr/bin/env python3
"""
Check if Dremio reflections are set up

This script checks the current status of reflections without requiring authentication.
It attempts to access the public API endpoints.
"""

import requests
import json
import sys
import os

DREMIO_URL = "http://localhost:9047"

def check_reflections_no_auth():
    """Try to check reflections without authentication"""
    print("Checking Dremio reflection status...")
    print("=" * 70)

    # Try to access reflections endpoint (may require auth)
    url = f"{DREMIO_URL}/api/v3/reflection"

    try:
        response = requests.get(url, timeout=5)

        if response.status_code == 200:
            reflections = response.json().get("data", [])
            print(f"\n✓ Found {len(reflections)} reflections")

            if reflections:
                print("\nReflection Details:")
                print("-" * 70)
                for r in reflections:
                    name = r.get("name", "Unknown")
                    r_type = r.get("type", "Unknown")
                    status = r.get("status", {})
                    availability = status.get("availability", "UNKNOWN")

                    icon = "✓" if availability == "AVAILABLE" else "⏳" if availability == "REFRESHING" else "✗"
                    print(f"{icon} {name}")
                    print(f"   Type: {r_type}")
                    print(f"   Status: {availability}")
                    print(f"   Dataset ID: {r.get('datasetId', 'N/A')}")
                    print()

                # Count by status
                available = sum(1 for r in reflections if r.get("status", {}).get("availability") == "AVAILABLE")
                refreshing = sum(1 for r in reflections if r.get("status", {}).get("availability") == "REFRESHING")
                other = len(reflections) - available - refreshing

                print("=" * 70)
                print(f"Summary: {available} available, {refreshing} refreshing, {other} other")

                if available == len(reflections):
                    print("\n✅ All reflections are AVAILABLE and ready to use!")
                elif refreshing > 0:
                    print("\n⏳ Some reflections are still building. Wait 2-5 minutes.")
                else:
                    print("\n⚠️  Some reflections may need attention.")

                return 0
            else:
                print("\n⚠️  No reflections found.")
                print("\nReflections have NOT been set up yet.")
                print("\nTo set them up, run:")
                print('  export DREMIO_PASSWORD="your_password"')
                print("  python3 scripts/create_reflections_auto.py")
                return 1

        elif response.status_code == 401:
            print("\n⚠️  Authentication required to check reflections")
            print("\nTo check with authentication, run:")
            print('  export DREMIO_PASSWORD="your_password"')
            print("  python3 scripts/create_reflections_auto.py")
            return 2
        else:
            print(f"\n✗ API returned status code: {response.status_code}")
            print(f"Response: {response.text[:200]}")
            return 1

    except requests.exceptions.ConnectionError:
        print("\n✗ Cannot connect to Dremio at http://localhost:9047")
        print("\nCheck if Dremio is running:")
        print("  docker ps | grep dremio")
        return 1
    except Exception as e:
        print(f"\n✗ Error: {e}")
        return 1

def check_with_password():
    """Check reflections with authentication"""
    password = os.getenv("DREMIO_PASSWORD")

    if not password:
        print("DREMIO_PASSWORD not set")
        return None

    print("\nAuthenticating with Dremio...")

    # Login
    auth_url = f"{DREMIO_URL}/apiv2/login"
    try:
        response = requests.post(
            auth_url,
            json={"userName": "admin", "password": password},
            timeout=10
        )

        if response.status_code == 200:
            token = response.json()["token"]
            print("✓ Authenticated successfully")

            # Get reflections
            headers = {
                "Authorization": f"_dremio{token}",
                "Content-Type": "application/json"
            }

            reflection_url = f"{DREMIO_URL}/api/v3/reflection"
            response = requests.get(reflection_url, headers=headers, timeout=10)

            if response.status_code == 200:
                reflections = response.json().get("data", [])
                return reflections
            else:
                print(f"Failed to get reflections: {response.status_code}")
                return None
        else:
            print(f"Authentication failed: {response.text}")
            return None

    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    # First try without authentication
    result = check_reflections_no_auth()

    # If that requires auth, try with password if available
    if result == 2 and os.getenv("DREMIO_PASSWORD"):
        print("\nAttempting authenticated check...")
        reflections = check_with_password()
        if reflections is not None:
            result = 0 if reflections else 1

    sys.exit(result)
