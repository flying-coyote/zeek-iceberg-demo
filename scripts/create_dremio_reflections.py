#!/usr/bin/env python3
"""
Create Dremio Reflections for OCSF Data

This script creates aggregation and raw reflections on the OCSF dataset
to accelerate query performance. Reflections are Dremio's query acceleration
technology that pre-computes and caches data structures.

Requirements:
    pip install requests

Usage:
    python3 scripts/create_dremio_reflections.py
"""

import json
import logging
import requests
from typing import Dict, List, Optional
import time
import os
import getpass

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


class DremioReflectionManager:
    """Manage Dremio reflections via REST API"""

    def __init__(self, url: str, username: str, password: str):
        self.url = url.rstrip('/')
        self.session = requests.Session()
        self.token = None
        self.login(username, password)

    def login(self, username: str, password: str):
        """Authenticate with Dremio"""
        auth_url = f"{self.url}/apiv2/login"
        response = self.session.post(
            auth_url,
            json={"userName": username, "password": password}
        )

        if response.status_code == 200:
            self.token = response.json()["token"]
            self.session.headers.update({
                "Authorization": f"_dremio{self.token}",
                "Content-Type": "application/json"
            })
            logger.info("✓ Successfully authenticated with Dremio")
        else:
            raise Exception(f"Failed to login: {response.text}")

    def get_dataset_id(self, path: List[str]) -> Optional[str]:
        """Get dataset ID from path"""
        catalog_url = f"{self.url}/api/v3/catalog"

        # Navigate through the catalog to find the dataset
        current_path = []
        parent_id = None

        for segment in path:
            current_path.append(segment)

            # Get children of current level
            if parent_id:
                url = f"{catalog_url}/{parent_id}"
            else:
                url = catalog_url

            response = self.session.get(url)
            if response.status_code != 200:
                logger.error(f"Failed to get catalog: {response.text}")
                return None

            data = response.json()

            # Find the segment in children
            found = False
            children = data.get("children", []) if parent_id else data.get("data", [])

            for child in children:
                if child.get("path", [])[-1] == segment:
                    parent_id = child.get("id")
                    found = True
                    break

            if not found:
                logger.warning(f"Could not find {segment} in path {current_path}")
                return None

        logger.info(f"✓ Found dataset ID: {parent_id}")
        return parent_id

    def create_raw_reflection(self, dataset_id: str, fields: List[str]) -> Dict:
        """Create a raw reflection (for SELECT * queries)"""

        reflection_config = {
            "datasetId": dataset_id,
            "type": "RAW",
            "name": "OCSF Raw Reflection",
            "enabled": True,
            "partitionDistributionStrategy": "CONSOLIDATED",
            "displayFields": fields,  # All fields for raw reflection
            "sortFields": [],  # Can add sort fields if needed
            "partitionFields": ["event_date"],  # Partition by date
            "distributionFields": []
        }

        url = f"{self.url}/api/v3/reflection"
        response = self.session.post(url, json=reflection_config)

        if response.status_code in [200, 201]:
            logger.info("✓ Created raw reflection")
            return response.json()
        else:
            logger.error(f"Failed to create raw reflection: {response.text}")
            return {}

    def create_aggregation_reflection(self, dataset_id: str) -> Dict:
        """Create aggregation reflections (for GROUP BY queries)"""

        # Reflection 1: Protocol and Activity aggregation
        reflection1 = {
            "datasetId": dataset_id,
            "type": "AGGREGATION",
            "name": "OCSF Protocol Activity Aggregation",
            "enabled": True,
            "partitionDistributionStrategy": "CONSOLIDATED",
            "dimensionFields": [
                {"name": "connection_info_protocol_name"},
                {"name": "activity_name"},
                {"name": "src_endpoint_ip"},
                {"name": "dst_endpoint_ip"}
            ],
            "measureFields": [
                {"name": "traffic_bytes_in", "measureTypes": ["SUM", "MIN", "MAX"]},
                {"name": "traffic_bytes_out", "measureTypes": ["SUM", "MIN", "MAX"]},
                {"name": "traffic_packets_in", "measureTypes": ["SUM"]},
                {"name": "traffic_packets_out", "measureTypes": ["SUM"]}
            ],
            "partitionFields": ["event_date"],
            "distributionFields": []
        }

        # Reflection 2: Time-based aggregation
        reflection2 = {
            "datasetId": dataset_id,
            "type": "AGGREGATION",
            "name": "OCSF Time-based Aggregation",
            "enabled": True,
            "partitionDistributionStrategy": "CONSOLIDATED",
            "dimensionFields": [
                {"name": "event_date"},
                {"name": "class_name"},
                {"name": "category_name"}
            ],
            "measureFields": [
                {"name": "traffic_bytes", "measureTypes": ["SUM", "MIN", "MAX"]},
                {"name": "traffic_packets", "measureTypes": ["SUM"]},
                {"name": "src_endpoint_ip", "measureTypes": ["COUNT_DISTINCT"]},
                {"name": "dst_endpoint_ip", "measureTypes": ["COUNT_DISTINCT"]}
            ],
            "partitionFields": ["event_date"],
            "distributionFields": []
        }

        # Reflection 3: Security analysis aggregation
        reflection3 = {
            "datasetId": dataset_id,
            "type": "AGGREGATION",
            "name": "OCSF Security Analysis Aggregation",
            "enabled": True,
            "partitionDistributionStrategy": "CONSOLIDATED",
            "dimensionFields": [
                {"name": "src_endpoint_is_local"},
                {"name": "dst_endpoint_is_local"},
                {"name": "activity_name"},
                {"name": "connection_info_protocol_name"}
            ],
            "measureFields": [
                {"name": "traffic_bytes_out", "measureTypes": ["SUM"]},
                {"name": "traffic_bytes_in", "measureTypes": ["SUM"]},
                {"name": "connection_info_uid", "measureTypes": ["COUNT_DISTINCT"]}
            ],
            "partitionFields": [],
            "distributionFields": []
        }

        results = []
        for i, reflection in enumerate([reflection1, reflection2, reflection3], 1):
            url = f"{self.url}/api/v3/reflection"
            response = self.session.post(url, json=reflection)

            if response.status_code in [200, 201]:
                logger.info(f"✓ Created aggregation reflection {i}")
                results.append(response.json())
            else:
                logger.error(f"Failed to create aggregation reflection {i}: {response.text}")

        return results

    def list_reflections(self, dataset_id: str) -> List[Dict]:
        """List all reflections for a dataset"""

        url = f"{self.url}/api/v3/reflection"
        response = self.session.get(url)

        if response.status_code == 200:
            all_reflections = response.json().get("data", [])
            dataset_reflections = [
                r for r in all_reflections
                if r.get("datasetId") == dataset_id
            ]
            return dataset_reflections
        else:
            logger.error(f"Failed to list reflections: {response.text}")
            return []

    def refresh_reflection(self, reflection_id: str):
        """Manually trigger reflection refresh"""

        url = f"{self.url}/api/v3/reflection/{reflection_id}/refresh"
        response = self.session.post(url)

        if response.status_code in [200, 202]:
            logger.info(f"✓ Triggered refresh for reflection {reflection_id}")
            return True
        else:
            logger.error(f"Failed to refresh reflection: {response.text}")
            return False

    def wait_for_reflections(self, dataset_id: str, timeout: int = 300):
        """Wait for reflections to be built"""

        logger.info("Waiting for reflections to build...")
        start_time = time.time()

        while time.time() - start_time < timeout:
            reflections = self.list_reflections(dataset_id)

            all_ready = True
            for reflection in reflections:
                status = reflection.get("status", {})
                if status.get("availability") != "AVAILABLE":
                    all_ready = False
                    logger.info(f"  Reflection '{reflection.get('name')}': {status.get('availability', 'UNKNOWN')}")

            if all_ready and reflections:
                logger.info("✓ All reflections are ready!")
                return True

            time.sleep(10)  # Check every 10 seconds

        logger.warning(f"Timeout waiting for reflections after {timeout} seconds")
        return False


def main():
    """Main execution flow"""

    logger.info("=" * 70)
    logger.info("Dremio Reflection Creator for OCSF Data")
    logger.info("=" * 70)
    logger.info("")

    try:
        # Get password if not set
        password = DREMIO_PASSWORD
        if not password:
            password = getpass.getpass(f"Enter password for {DREMIO_USERNAME}: ")

        # Connect to Dremio
        manager = DremioReflectionManager(DREMIO_URL, DREMIO_USERNAME, password)

        # Get dataset ID
        dataset_id = manager.get_dataset_id(DATASET_PATH)
        if not dataset_id:
            logger.error(f"Could not find dataset at path: {'/'.join(DATASET_PATH)}")
            logger.info("Make sure you have:")
            logger.info("1. Formatted the folder as Parquet in Dremio")
            logger.info("2. The dataset is visible in Dremio UI")
            return 1

        # Check existing reflections
        existing = manager.list_reflections(dataset_id)
        if existing:
            logger.info(f"Found {len(existing)} existing reflections:")
            for r in existing:
                logger.info(f"  - {r.get('name')} ({r.get('type')})")
            logger.info("")

            # Option to delete existing reflections
            response = input("Delete existing reflections? (y/n): ")
            if response.lower() == 'y':
                for r in existing:
                    url = f"{manager.url}/api/v3/reflection/{r['id']}"
                    manager.session.delete(url)
                    logger.info(f"  Deleted: {r.get('name')}")
                logger.info("")

        # Get dataset schema to know which fields are available
        catalog_url = f"{manager.url}/api/v3/catalog/{dataset_id}"
        response = manager.session.get(catalog_url)
        if response.status_code == 200:
            dataset_info = response.json()
            fields = [f["name"] for f in dataset_info.get("fields", [])]
            logger.info(f"Dataset has {len(fields)} fields")

            # Show key OCSF fields
            key_fields = [
                "class_uid", "class_name", "activity_name",
                "src_endpoint_ip", "dst_endpoint_ip",
                "traffic_bytes_in", "traffic_bytes_out",
                "connection_info_protocol_name"
            ]
            logger.info("Key OCSF fields available:")
            for field in key_fields:
                if field in fields:
                    logger.info(f"  ✓ {field}")
            logger.info("")

        # Create reflections
        logger.info("Creating reflections...")

        # Create raw reflection
        raw_result = manager.create_raw_reflection(dataset_id, fields[:50])  # Limit to 50 fields

        # Create aggregation reflections
        agg_results = manager.create_aggregation_reflection(dataset_id)

        # Wait for reflections to build
        manager.wait_for_reflections(dataset_id, timeout=300)

        # Show final status
        logger.info("")
        logger.info("=" * 70)
        logger.info("✓ Reflection creation complete!")
        logger.info("=" * 70)
        logger.info("")

        logger.info("Created reflections will accelerate these query patterns:")
        logger.info("1. SELECT * queries (raw reflection)")
        logger.info("2. Protocol/Activity aggregations")
        logger.info("3. Time-based aggregations")
        logger.info("4. Security analysis (local vs external traffic)")
        logger.info("")

        logger.info("Test acceleration with these queries in Dremio:")
        logger.info("1. Top talkers by protocol")
        logger.info("2. Traffic volume over time")
        logger.info("3. Egress traffic analysis")
        logger.info("")

        logger.info("View reflection status at:")
        logger.info(f"  {DREMIO_URL}/reflections")

        return 0

    except Exception as e:
        logger.error(f"Failed to create reflections: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())