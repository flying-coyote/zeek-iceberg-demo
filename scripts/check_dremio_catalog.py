#!/usr/bin/env python3
"""
Check Dremio Catalog - List sources and datasets without authentication
Uses public catalog endpoints
"""

import requests
import json

DREMIO_URL = "http://localhost:9047"

def check_sources():
    """List all sources"""
    print("Checking Dremio sources...")

    # Try public catalog endpoint
    catalog_url = f"{DREMIO_URL}/apiv2/source"

    try:
        response = requests.get(catalog_url, timeout=5)
        if response.status_code == 200:
            sources = response.json().get('data', [])
            print(f"✓ Found {len(sources)} sources:")
            for source in sources:
                print(f"  - {source.get('name')} (type: {source.get('type')})")
            return sources
        else:
            print(f"Response: {response.status_code}")
            print(f"Error: {response.text[:500]}")
            return []
    except Exception as e:
        print(f"✗ Error: {e}")
        return []

def main():
    print("=" * 70)
    print("Dremio Catalog Check")
    print("=" * 70)
    print()

    sources = check_sources()

    print("\n" + "=" * 70)
    print("Note: To configure reflections, you need to:")
    print("1. Set DREMIO_PASSWORD environment variable")
    print("2. Run: setup_reflections_simple.py")
    print()
    print("Or manually in Dremio UI:")
    print("1. Navigate to: minio > zeek-data > network-activity-ocsf")
    print("2. Format folder as Parquet")
    print("3. Create reflections")
    print("=" * 70)

if __name__ == "__main__":
    main()
