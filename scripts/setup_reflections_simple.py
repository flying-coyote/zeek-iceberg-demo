#!/usr/bin/env python3
"""
Simple Dremio Reflection Setup via REST API

This script creates reflections on the OCSF dataset using Dremio's REST API.
It provides step-by-step output and error handling.
"""

import requests
import json
import time
import sys

# Dremio Configuration
DREMIO_URL = "http://localhost:9047"
DREMIO_USERNAME = "flying-coyote"  # Your actual Dremio username

# Note: You'll be prompted for password, or set it here
DREMIO_PASSWORD = None  # Set to your password or leave None to prompt


def get_password():
    """Get Dremio password"""
    global DREMIO_PASSWORD
    if DREMIO_PASSWORD:
        return DREMIO_PASSWORD

    # Try to get from environment
    import os
    env_pass = os.environ.get('DREMIO_PASSWORD')
    if env_pass:
        return env_pass

    # Prompt user
    import getpass
    return getpass.getpass(f"Enter Dremio password for {DREMIO_USERNAME}: ")


def login(url, username, password):
    """Login to Dremio and get auth token"""
    print(f"Logging in to Dremio as {username}...")

    auth_url = f"{url}/apiv2/login"
    response = requests.post(
        auth_url,
        json={"userName": username, "password": password}
    )

    if response.status_code == 200:
        token = response.json()["token"]
        print("✓ Successfully authenticated")
        return token
    else:
        print(f"✗ Login failed: {response.text}")
        sys.exit(1)


def find_dataset(session, url, path):
    """Find dataset by path"""
    print(f"\nSearching for dataset: {' > '.join(path)}")

    # Search for the dataset
    catalog_url = f"{url}/api/v3/catalog"

    # Try to find by path
    search_url = f"{catalog_url}/by-path/{'/'.join(path)}"
    response = session.get(search_url)

    if response.status_code == 200:
        dataset = response.json()
        dataset_id = dataset.get('id')
        print(f"✓ Found dataset ID: {dataset_id}")
        return dataset_id
    else:
        print(f"✗ Dataset not found at path: {'/'.join(path)}")
        print(f"  Response: {response.status_code} - {response.text[:200]}")
        return None


def list_reflections(session, url, dataset_id):
    """List existing reflections for a dataset"""
    print(f"\nChecking existing reflections...")

    reflection_url = f"{url}/api/v3/reflection"
    response = session.get(reflection_url)

    if response.status_code == 200:
        all_reflections = response.json().get("data", [])
        dataset_reflections = [
            r for r in all_reflections
            if r.get("datasetId") == dataset_id
        ]

        if dataset_reflections:
            print(f"✓ Found {len(dataset_reflections)} existing reflections:")
            for r in dataset_reflections:
                print(f"  - {r.get('name', 'Unnamed')} ({r.get('type')})")
        else:
            print("✓ No existing reflections found")

        return dataset_reflections
    else:
        print(f"✗ Failed to list reflections: {response.text[:200]}")
        return []


def create_raw_reflection(session, url, dataset_id):
    """Create raw reflection"""
    print("\nCreating raw reflection...")

    reflection_config = {
        "datasetId": dataset_id,
        "type": "RAW",
        "name": "OCSF Raw Reflection",
        "enabled": True,
        "partitionDistributionStrategy": "CONSOLIDATED",
        "displayFields": [
            {"name": "class_uid"},
            {"name": "class_name"},
            {"name": "activity_id"},
            {"name": "activity_name"},
            {"name": "src_endpoint_ip"},
            {"name": "src_endpoint_port"},
            {"name": "dst_endpoint_ip"},
            {"name": "dst_endpoint_port"},
            {"name": "traffic_bytes_in"},
            {"name": "traffic_bytes_out"},
            {"name": "connection_info_protocol_name"},
            {"name": "event_date"},
            {"name": "time"}
        ],
        "partitionFields": [{"name": "event_date"}],
        "sortFields": [],
        "distributionFields": []
    }

    reflection_url = f"{url}/api/v3/reflection"
    response = session.post(reflection_url, json=reflection_config)

    if response.status_code in [200, 201]:
        reflection = response.json()
        print(f"✓ Created raw reflection: {reflection.get('id')}")
        return reflection.get('id')
    else:
        print(f"✗ Failed to create raw reflection: {response.text[:500]}")
        return None


def create_aggregation_reflection(session, url, dataset_id, name, dimensions, measures):
    """Create aggregation reflection"""
    print(f"\nCreating aggregation reflection: {name}...")

    reflection_config = {
        "datasetId": dataset_id,
        "type": "AGGREGATION",
        "name": name,
        "enabled": True,
        "partitionDistributionStrategy": "CONSOLIDATED",
        "dimensionFields": [{"name": d} for d in dimensions],
        "measureFields": measures,
        "partitionFields": [],
        "distributionFields": []
    }

    reflection_url = f"{url}/api/v3/reflection"
    response = session.post(reflection_url, json=reflection_config)

    if response.status_code in [200, 201]:
        reflection = response.json()
        print(f"✓ Created aggregation reflection: {reflection.get('id')}")
        return reflection.get('id')
    else:
        print(f"✗ Failed to create aggregation reflection: {response.text[:500]}")
        return None


def main():
    """Main execution"""
    print("=" * 70)
    print("Dremio OCSF Reflection Setup")
    print("=" * 70)

    # Get password
    password = get_password()

    # Login
    token = login(DREMIO_URL, DREMIO_USERNAME, password)

    # Create session with auth
    session = requests.Session()
    session.headers.update({
        "Authorization": f"_dremio{token}",
        "Content-Type": "application/json"
    })

    # Find the OCSF dataset
    dataset_path = ["minio", "zeek-data", "network-activity-ocsf"]
    dataset_id = find_dataset(session, DREMIO_URL, dataset_path)

    if not dataset_id:
        print("\n✗ Could not find OCSF dataset")
        print("\nPossible reasons:")
        print("1. Dataset hasn't been formatted in Dremio yet")
        print("2. Path is incorrect")
        print("\nTo fix:")
        print("1. Open Dremio: http://localhost:9047")
        print("2. Navigate to: minio > zeek-data > network-activity-ocsf")
        print("3. Click 'Format Folder' and choose 'Parquet'")
        sys.exit(1)

    # Check existing reflections
    existing = list_reflections(session, DREMIO_URL, dataset_id)

    # Ask user if they want to proceed
    if existing:
        response = input("\nExisting reflections found. Delete and recreate? (y/n): ")
        if response.lower() != 'y':
            print("Exiting without changes")
            sys.exit(0)

        # Delete existing reflections
        print("\nDeleting existing reflections...")
        for r in existing:
            delete_url = f"{DREMIO_URL}/api/v3/reflection/{r['id']}"
            session.delete(delete_url)
            print(f"  ✓ Deleted: {r.get('name', 'Unnamed')}")

    # Create raw reflection
    raw_id = create_raw_reflection(session, DREMIO_URL, dataset_id)

    # Create aggregation reflection 1: Protocol & Activity
    agg1_id = create_aggregation_reflection(
        session, DREMIO_URL, dataset_id,
        name="OCSF Protocol Activity Aggregation",
        dimensions=[
            "connection_info_protocol_name",
            "activity_name",
            "src_endpoint_ip",
            "dst_endpoint_ip"
        ],
        measures=[
            {"name": "traffic_bytes_in", "measureTypes": ["SUM", "MIN", "MAX"]},
            {"name": "traffic_bytes_out", "measureTypes": ["SUM", "MIN", "MAX"]}
        ]
    )

    # Create aggregation reflection 2: Security Analysis
    agg2_id = create_aggregation_reflection(
        session, DREMIO_URL, dataset_id,
        name="OCSF Security Analysis Aggregation",
        dimensions=[
            "src_endpoint_is_local",
            "dst_endpoint_is_local",
            "activity_name",
            "connection_info_protocol_name"
        ],
        measures=[
            {"name": "traffic_bytes_out", "measureTypes": ["SUM"]},
            {"name": "traffic_bytes_in", "measureTypes": ["SUM"]}
        ]
    )

    # Summary
    print("\n" + "=" * 70)
    print("✓ Reflection Setup Complete!")
    print("=" * 70)

    created = sum([1 for x in [raw_id, agg1_id, agg2_id] if x])
    print(f"\nCreated {created} reflections:")
    if raw_id:
        print(f"  ✓ Raw Reflection (ID: {raw_id})")
    if agg1_id:
        print(f"  ✓ Protocol Activity Aggregation (ID: {agg1_id})")
    if agg2_id:
        print(f"  ✓ Security Analysis Aggregation (ID: {agg2_id})")

    print("\nReflections are now building...")
    print("This typically takes 2-5 minutes for 1M records")
    print("\nMonitor progress:")
    print("1. Open Dremio: http://localhost:9047")
    print("2. Go to Jobs (left sidebar)")
    print("3. Filter by Type: 'Reflection'")
    print("4. Wait for status: 'AVAILABLE'")
    print("\nExpected acceleration: 10-100x query speedup!")


if __name__ == "__main__":
    main()
