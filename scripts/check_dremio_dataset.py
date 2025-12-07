#!/usr/bin/env python3
"""
Check if OCSF dataset exists in Dremio and run test query

This verifies that the data is accessible before creating reflections.
"""

import json
import logging
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
DREMIO_USERNAME = "admin"
DREMIO_PASSWORD = "admin123"


class DremioClient:
    """Simple Dremio client for dataset operations"""

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

    def run_query(self, sql: str) -> Dict:
        """Execute SQL query"""
        url = f"{self.url}/api/v3/sql"
        response = self.session.post(url, json={"sql": sql})

        if response.status_code == 200:
            job_id = response.json()["id"]
            logger.info(f"Query job submitted: {job_id}")

            # Wait for job to complete
            job_url = f"{self.url}/api/v3/job/{job_id}"
            while True:
                job_response = self.session.get(job_url)
                if job_response.status_code == 200:
                    job_data = job_response.json()
                    state = job_data.get("jobState")
                    if state in ["COMPLETED", "FAILED", "CANCELLED"]:
                        if state == "COMPLETED":
                            # Get results
                            results_url = f"{self.url}/api/v3/job/{job_id}/results"
                            results_response = self.session.get(results_url)
                            if results_response.status_code == 200:
                                return results_response.json()
                        else:
                            logger.error(f"Query failed with state: {state}")
                            logger.error(f"Error: {job_data.get('errorMessage')}")
                            return {}
        else:
            logger.error(f"Failed to submit query: {response.text}")
            return {}


def main():
    """Check dataset and run test queries"""

    logger.info("=" * 70)
    logger.info("Dremio OCSF Dataset Checker")
    logger.info("=" * 70)
    logger.info("")

    try:
        # Connect to Dremio
        client = DremioClient(DREMIO_URL, DREMIO_USERNAME, DREMIO_PASSWORD)

        # Test queries
        queries = [
            # 1. Check if dataset exists
            (
                "Dataset Count",
                'SELECT COUNT(*) as record_count FROM minio."zeek-data"."network-activity-ocsf" LIMIT 1'
            ),
            # 2. Check OCSF fields
            (
                "Sample OCSF Record",
                '''SELECT
                    class_uid,
                    class_name,
                    src_endpoint_ip,
                    dst_endpoint_ip,
                    traffic_bytes_in,
                    traffic_bytes_out,
                    activity_name
                FROM minio."zeek-data"."network-activity-ocsf"
                LIMIT 5'''
            ),
            # 3. Quick aggregation
            (
                "Protocol Distribution",
                '''SELECT
                    connection_info_protocol_name,
                    COUNT(*) as count
                FROM minio."zeek-data"."network-activity-ocsf"
                GROUP BY connection_info_protocol_name
                ORDER BY count DESC'''
            )
        ]

        for query_name, sql in queries:
            logger.info(f"\nRunning: {query_name}")
            logger.info("-" * 40)

            result = client.run_query(sql)

            if result:
                rows = result.get("rows", [])
                columns = result.get("schema", [])

                if rows:
                    # Show column names
                    col_names = [col.get("name", "?") for col in columns]
                    logger.info(f"Columns: {', '.join(col_names)}")

                    # Show first few rows
                    for i, row in enumerate(rows[:10]):
                        logger.info(f"  Row {i+1}: {row}")

                    if len(rows) > 10:
                        logger.info(f"  ... and {len(rows) - 10} more rows")

                    logger.info(f"✓ Query successful - {len(rows)} rows returned")
                else:
                    logger.warning("Query returned no rows")
            else:
                logger.error("Query failed")
                logger.info("")
                logger.info("Possible issues:")
                logger.info("1. Dataset not formatted in Dremio UI")
                logger.info("2. Dataset path incorrect")
                logger.info("3. Dremio needs restart")
                logger.info("")
                logger.info("To fix:")
                logger.info("1. Open Dremio UI: http://localhost:9047")
                logger.info("2. Navigate to: Sources > minio > zeek-data")
                logger.info("3. Click on 'network-activity-ocsf' folder")
                logger.info("4. Click 'Format Folder' and choose 'Parquet'")
                return 1

        logger.info("")
        logger.info("=" * 70)
        logger.info("✓ Dataset is accessible and OCSF fields are available!")
        logger.info("=" * 70)
        logger.info("")
        logger.info("Next step: Run create_dremio_reflections.py to accelerate queries")

        return 0

    except Exception as e:
        logger.error(f"Failed to check dataset: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())