#!/usr/bin/env python3
"""
Automatically Create Dremio Reflections via REST API

This script creates reflections using Dremio's REST API without requiring
interactive password entry. Set DREMIO_PASSWORD environment variable.

Requirements:
    pip install requests

Usage:
    export DREMIO_PASSWORD="your_password"
    python3 scripts/create_reflections_auto.py

    OR (inline):
    DREMIO_PASSWORD="your_password" python3 scripts/create_reflections_auto.py
"""

import json
import logging
import os
import sys
import time
import requests
from typing import Dict, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Dremio Configuration
DREMIO_URL = "http://localhost:9047"
DREMIO_USERNAME = os.getenv("DREMIO_USERNAME", "admin")
DREMIO_PASSWORD = os.getenv("DREMIO_PASSWORD", "")

# Dataset Configuration
DATASET_PATH = ["minio", "zeek-data", "network-activity-ocsf"]


class DremioClient:
    """Dremio REST API client"""

    def __init__(self, url: str, username: str, password: str):
        self.url = url.rstrip('/')
        self.session = requests.Session()
        self.token = None
        self.login(username, password)

    def login(self, username: str, password: str):
        """Authenticate with Dremio"""
        auth_url = f"{self.url}/apiv2/login"

        logger.info("Authenticating with Dremio...")
        response = self.session.post(
            auth_url,
            json={"userName": username, "password": password},
            timeout=10
        )

        if response.status_code == 200:
            self.token = response.json()["token"]
            self.session.headers.update({
                "Authorization": f"_dremio{self.token}",
                "Content-Type": "application/json"
            })
            logger.info("✓ Successfully authenticated")
        else:
            raise Exception(f"Authentication failed: {response.text}")

    def get_dataset_id(self, path: List[str]) -> Optional[str]:
        """Get dataset ID from path by navigating catalog"""
        logger.info(f"Looking up dataset: {' > '.join(path)}")

        catalog_url = f"{self.url}/api/v3/catalog"
        current_id = None

        for segment in path:
            # Get catalog listing
            if current_id:
                url = f"{catalog_url}/{current_id}"
            else:
                url = catalog_url

            response = self.session.get(url, timeout=10)
            if response.status_code != 200:
                logger.error(f"Failed to get catalog: {response.text}")
                return None

            data = response.json()
            children = data.get("children", []) if current_id else data.get("data", [])

            # Find segment in children
            found = False
            for child in children:
                child_path = child.get("path", [])
                if child_path and child_path[-1] == segment:
                    current_id = child.get("id")
                    found = True
                    logger.info(f"  Found: {segment} (id: {current_id})")
                    break

            if not found:
                logger.error(f"  Could not find: {segment}")
                return None

        logger.info(f"✓ Dataset ID: {current_id}")
        return current_id

    def list_reflections(self, dataset_id: str = None) -> List[Dict]:
        """List reflections (optionally filtered by dataset)"""
        url = f"{self.url}/api/v3/reflection"
        response = self.session.get(url, timeout=10)

        if response.status_code == 200:
            all_reflections = response.json().get("data", [])

            if dataset_id:
                return [r for r in all_reflections if r.get("datasetId") == dataset_id]
            return all_reflections
        else:
            logger.error(f"Failed to list reflections: {response.text}")
            return []

    def delete_reflection(self, reflection_id: str) -> bool:
        """Delete a reflection"""
        url = f"{self.url}/api/v3/reflection/{reflection_id}"
        response = self.session.delete(url, timeout=10)
        return response.status_code in [200, 204]

    def create_raw_reflection(self, dataset_id: str, name: str = "OCSF Raw Reflection") -> Dict:
        """Create a raw reflection"""
        logger.info(f"Creating raw reflection: {name}")

        reflection_config = {
            "datasetId": dataset_id,
            "type": "RAW",
            "name": name,
            "enabled": True,
            "partitionDistributionStrategy": "CONSOLIDATED"
        }

        url = f"{self.url}/api/v3/reflection"
        response = self.session.post(url, json=reflection_config, timeout=10)

        if response.status_code in [200, 201]:
            logger.info(f"  ✓ Created: {name}")
            return response.json()
        else:
            logger.error(f"  ✗ Failed: {response.text}")
            return {}

    def create_aggregation_reflection(
        self,
        dataset_id: str,
        name: str,
        dimensions: List[str],
        measures: List[Dict]
    ) -> Dict:
        """Create an aggregation reflection"""
        logger.info(f"Creating aggregation reflection: {name}")

        # Format dimensions
        dimension_fields = [{"name": dim} for dim in dimensions]

        # Format measures
        measure_fields = []
        for measure in measures:
            field_name = measure.get("field")
            measure_types = measure.get("types", ["SUM"])
            measure_fields.append({
                "name": field_name,
                "measureTypes": measure_types
            })

        reflection_config = {
            "datasetId": dataset_id,
            "type": "AGGREGATION",
            "name": name,
            "enabled": True,
            "partitionDistributionStrategy": "CONSOLIDATED",
            "dimensionFields": dimension_fields,
            "measureFields": measure_fields
        }

        url = f"{self.url}/api/v3/reflection"
        response = self.session.post(url, json=reflection_config, timeout=10)

        if response.status_code in [200, 201]:
            logger.info(f"  ✓ Created: {name}")
            return response.json()
        else:
            logger.error(f"  ✗ Failed: {response.text}")
            return {}

    def wait_for_reflections(self, dataset_id: str, timeout: int = 300):
        """Wait for reflections to become available"""
        logger.info("Waiting for reflections to build...")
        logger.info("(This typically takes 2-5 minutes for 1M records)")

        start_time = time.time()
        last_status = {}

        while time.time() - start_time < timeout:
            reflections = self.list_reflections(dataset_id)

            if not reflections:
                logger.info("  No reflections found yet...")
                time.sleep(10)
                continue

            all_available = True
            current_status = {}

            for reflection in reflections:
                name = reflection.get("name", "Unknown")
                status = reflection.get("status", {})
                availability = status.get("availability", "UNKNOWN")

                current_status[name] = availability

                if availability != "AVAILABLE":
                    all_available = False

            # Log status changes
            if current_status != last_status:
                for name, status in current_status.items():
                    if status == "AVAILABLE":
                        icon = "✓"
                    elif status == "REFRESHING":
                        icon = "⏳"
                    else:
                        icon = "○"
                    logger.info(f"  {icon} {name}: {status}")
                last_status = current_status.copy()

            if all_available and reflections:
                elapsed = int(time.time() - start_time)
                logger.info(f"✓ All {len(reflections)} reflections available! (took {elapsed}s)")
                return True

            time.sleep(10)

        logger.warning(f"Timeout after {timeout}s - some reflections may still be building")
        return False


def main():
    """Main execution"""

    logger.info("=" * 70)
    logger.info("Dremio Reflection Auto-Setup")
    logger.info("=" * 70)
    logger.info("")

    # Check for password
    if not DREMIO_PASSWORD:
        logger.error("DREMIO_PASSWORD environment variable is required")
        logger.info("")
        logger.info("Usage:")
        logger.info('  export DREMIO_PASSWORD="your_password"')
        logger.info("  python3 scripts/create_reflections_auto.py")
        logger.info("")
        logger.info("OR (inline):")
        logger.info('  DREMIO_PASSWORD="your_password" python3 scripts/create_reflections_auto.py')
        return 1

    try:
        # Connect to Dremio
        client = DremioClient(DREMIO_URL, DREMIO_USERNAME, DREMIO_PASSWORD)

        # Get dataset ID
        dataset_id = client.get_dataset_id(DATASET_PATH)
        if not dataset_id:
            logger.error("Could not find dataset - check that it's formatted in Dremio")
            return 1

        logger.info("")

        # Check for existing reflections
        existing = client.list_reflections(dataset_id)
        if existing:
            logger.info(f"Found {len(existing)} existing reflections:")
            for r in existing:
                logger.info(f"  - {r.get('name')} ({r.get('type')})")

            # Delete existing reflections
            logger.info("")
            logger.info("Deleting existing reflections...")
            for r in existing:
                if client.delete_reflection(r['id']):
                    logger.info(f"  ✓ Deleted: {r.get('name')}")

            logger.info("")

        # Create raw reflection
        logger.info("Creating reflections...")
        logger.info("")

        raw_result = client.create_raw_reflection(
            dataset_id,
            name="OCSF Raw Reflection"
        )

        # Create aggregation reflections
        agg1 = client.create_aggregation_reflection(
            dataset_id,
            name="Protocol Activity Aggregation",
            dimensions=[
                "connection_info_protocol_name",
                "activity_name",
                "src_endpoint_ip",
                "dst_endpoint_ip"
            ],
            measures=[
                {"field": "traffic_bytes_in", "types": ["SUM", "MIN", "MAX"]},
                {"field": "traffic_bytes_out", "types": ["SUM", "MIN", "MAX"]}
            ]
        )

        agg2 = client.create_aggregation_reflection(
            dataset_id,
            name="Security Analysis Aggregation",
            dimensions=[
                "src_endpoint_is_local",
                "dst_endpoint_is_local",
                "activity_name",
                "connection_info_protocol_name"
            ],
            measures=[
                {"field": "traffic_bytes_out", "types": ["SUM"]},
                {"field": "traffic_bytes_in", "types": ["SUM"]}
            ]
        )

        agg3 = client.create_aggregation_reflection(
            dataset_id,
            name="Time-based Aggregation",
            dimensions=[
                "event_date",
                "class_name",
                "category_name"
            ],
            measures=[
                {"field": "traffic_bytes", "types": ["SUM", "MIN", "MAX"]}
            ]
        )

        logger.info("")
        logger.info("=" * 70)
        logger.info("Reflections created successfully!")
        logger.info("=" * 70)
        logger.info("")

        # Wait for reflections to build
        client.wait_for_reflections(dataset_id, timeout=300)

        logger.info("")
        logger.info("=" * 70)
        logger.info("✓ Setup complete!")
        logger.info("=" * 70)
        logger.info("")
        logger.info("Next steps:")
        logger.info("1. Run queries in Dremio to test acceleration")
        logger.info("2. Check query profiles for reflection usage (green checkmark)")
        logger.info("3. Compare query times before/after reflections")
        logger.info("")

        return 0

    except Exception as e:
        logger.error(f"Failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
