#!/usr/bin/env python3
"""
List all datasets in Dremio catalog

This helps debug path issues when setting up reflections.
"""

import requests
import json
import sys
import getpass

DREMIO_URL = "http://localhost:9047"
DREMIO_USERNAME = "flying-coyote"


def login(url, username, password):
    """Login to Dremio"""
    auth_url = f"{url}/apiv2/login"
    response = requests.post(auth_url, json={"userName": username, "password": password})

    if response.status_code == 200:
        return response.json()["token"]
    else:
        print(f"Login failed: {response.text}")
        sys.exit(1)


def list_catalog(session, url, path=None):
    """List catalog entries"""
    if path:
        catalog_url = f"{url}/api/v3/catalog/{path}"
    else:
        catalog_url = f"{url}/api/v3/catalog"

    response = session.get(catalog_url)

    if response.status_code == 200:
        return response.json()
    else:
        return None


def explore_path(session, url, path_parts, indent=0):
    """Recursively explore a path"""
    prefix = "  " * indent

    if not path_parts:
        return

    current = path_parts[0]
    remaining = path_parts[1:]

    # Get catalog at current level
    catalog = list_catalog(session, url)
    if not catalog:
        return

    # Find the current item
    items = catalog.get("data", [])
    for item in items:
        item_path = item.get("path", [])
        if item_path and item_path[-1] == current:
            item_type = item.get("containerType") or item.get("datasetType", "UNKNOWN")
            print(f"{prefix}✓ Found: {current} (type: {item_type}, id: {item.get('id', 'N/A')})")

            # If there are more path parts, explore children
            if remaining:
                item_id = item.get("id")
                if item_id:
                    children_data = list_catalog(session, url, item_id)
                    if children_data and "children" in children_data:
                        print(f"{prefix}  Children:")
                        for child in children_data["children"]:
                            child_name = child.get("path", [])[-1] if child.get("path") else "?"
                            child_type = child.get("containerType") or child.get("datasetType", "UNKNOWN")
                            print(f"{prefix}    - {child_name} (type: {child_type})")

                        # Continue exploring
                        explore_path(session, url, remaining, indent + 1)
            return

    print(f"{prefix}✗ Not found: {current}")


def main():
    print("=" * 70)
    print("Dremio Catalog Explorer")
    print("=" * 70)

    password = getpass.getpass(f"Enter Dremio password for {DREMIO_USERNAME}: ")

    # Login
    token = login(DREMIO_URL, DREMIO_USERNAME, password)

    session = requests.Session()
    session.headers.update({
        "Authorization": f"_dremio{token}",
        "Content-Type": "application/json"
    })

    print("\nExploring path: minio → zeek-data → network-activity-ocsf\n")

    explore_path(session, DREMIO_URL, ["minio", "zeek-data", "network-activity-ocsf"])

    print("\n" + "=" * 70)
    print("\nIf 'network-activity-ocsf' is not found or shows as 'FOLDER':")
    print("1. It needs to be formatted as a Parquet dataset in Dremio")
    print("2. Open: http://localhost:9047")
    print("3. Navigate to: minio > zeek-data > network-activity-ocsf")
    print("4. Right-click (or click ⋮) → 'Format Folder' → Choose 'Parquet'")


if __name__ == "__main__":
    main()
