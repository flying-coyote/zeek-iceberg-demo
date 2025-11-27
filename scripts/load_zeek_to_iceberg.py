#!/usr/bin/env python3
"""
Zeek → OCSF → Iceberg Loader (Standalone Python)
Alternative to Spark pipeline - uses PyIceberg directly

Requirements:
    pip install pyiceberg[s3fs,hive] pyarrow pandas

Usage:
    python3 load_zeek_to_iceberg.py
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict
import pandas as pd
import pyarrow as pa
from pyiceberg.catalog import load_catalog
from pyiceberg.schema import Schema
from pyiceberg.types import (
    NestedField, StringType, IntegerType, LongType,
    BooleanType, StructType, TimestampType, DateType
)
from pyiceberg.partitioning import PartitionSpec, PartitionField
from pyiceberg.transforms import DayTransform

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_ocsf_schema():
    """
    Define OCSF Network Activity (class 4001) schema for Iceberg
    """
    return Schema(
        # OCSF Metadata
        NestedField(1, "ocsf_version", StringType(), required=False),
        NestedField(2, "activity_name", StringType(), required=False),
        NestedField(3, "category_uid", IntegerType(), required=False),
        NestedField(4, "category_name", StringType(), required=False),
        NestedField(5, "class_uid", IntegerType(), required=False),
        NestedField(6, "class_name", StringType(), required=False),

        # Time fields
        NestedField(7, "time", LongType(), required=True, doc="Unix timestamp in milliseconds"),
        NestedField(8, "event_date", DateType(), required=True, doc="Partition key"),

        # Connection Info (nested struct)
        NestedField(9, "connection_info", StructType(
            NestedField(91, "uid", StringType(), required=False),
            NestedField(92, "protocol_num", IntegerType(), required=False),
            NestedField(93, "protocol_name", StringType(), required=False),
            NestedField(94, "service_name", StringType(), required=False),
            NestedField(95, "boundary", StringType(), required=False),
            NestedField(96, "direction", StringType(), required=False),
        ), required=False),

        # Source Endpoint (nested struct)
        NestedField(10, "src_endpoint", StructType(
            NestedField(101, "ip", StringType(), required=False),
            NestedField(102, "port", IntegerType(), required=False),
            NestedField(103, "is_local", BooleanType(), required=False),
            NestedField(104, "mac", StringType(), required=False),
            NestedField(105, "country", StringType(), required=False),
            NestedField(106, "vlan_uid", StringType(), required=False),
        ), required=False),

        # Destination Endpoint (nested struct)
        NestedField(11, "dst_endpoint", StructType(
            NestedField(111, "ip", StringType(), required=False),
            NestedField(112, "port", IntegerType(), required=False),
            NestedField(113, "is_local", BooleanType(), required=False),
            NestedField(114, "mac", StringType(), required=False),
            NestedField(115, "country", StringType(), required=False),
            NestedField(116, "vlan_uid", StringType(), required=False),
        ), required=False),

        # Traffic Stats (nested struct)
        NestedField(12, "traffic", StructType(
            NestedField(121, "bytes_in", LongType(), required=False),
            NestedField(122, "bytes_out", LongType(), required=False),
            NestedField(123, "packets_in", LongType(), required=False),
            NestedField(124, "packets_out", LongType(), required=False),
            NestedField(125, "bytes_dropped", LongType(), required=False),
        ), required=False),

        # Duration
        NestedField(13, "duration", LongType(), required=False),

        # Activity
        NestedField(14, "activity_id", IntegerType(), required=False),
        NestedField(15, "conn_state", StringType(), required=False),

        # Application
        NestedField(16, "app", StringType(), required=False),

        # Zeek Metadata (nested struct)
        NestedField(17, "zeek_metadata", StructType(
            NestedField(171, "log_name", StringType(), required=False),
            NestedField(172, "tunnel_parents", StringType(), required=False),
            NestedField(173, "community_id", StringType(), required=False),
        ), required=False),
    )


def read_zeek_json(file_path: str, limit: int = None) -> List[Dict]:
    """
    Read Zeek conn logs from JSON file

    Args:
        file_path: Path to Zeek JSON file
        limit: Maximum number of records to read (None = all)

    Returns:
        List of Zeek log dictionaries
    """
    logger.info(f"Reading Zeek logs from {file_path}")

    records = []
    with open(file_path, 'r') as f:
        for i, line in enumerate(f):
            if limit and i >= limit:
                break
            try:
                record = json.loads(line.strip())
                records.append(record)
            except json.JSONDecodeError as e:
                logger.warning(f"Skipping malformed JSON on line {i+1}: {e}")
                continue

    logger.info(f"Read {len(records):,} Zeek records")
    return records


def transform_zeek_to_ocsf(zeek_records: List[Dict]) -> pd.DataFrame:
    """
    Transform Zeek conn logs to OCSF Network Activity schema

    Args:
        zeek_records: List of Zeek log dictionaries

    Returns:
        Pandas DataFrame with OCSF schema
    """
    logger.info("Transforming Zeek logs to OCSF schema")

    ocsf_records = []

    for record in zeek_records:
        try:
            # Parse Zeek timestamp
            ts = float(record.get('ts', 0))
            timestamp_ms = int(ts * 1000)
            event_date = datetime.fromtimestamp(ts).date()

            # Map protocol to number
            proto = record.get('proto', 'unknown').lower()
            proto_num = {
                'tcp': 6,
                'udp': 17,
                'icmp': 1
            }.get(proto, 0)

            # Build OCSF record
            ocsf_record = {
                # OCSF Metadata
                'ocsf_version': '1.4.0',
                'activity_name': 'Traffic',
                'category_uid': 4,
                'category_name': 'Network Activity',
                'class_uid': 4001,
                'class_name': 'Network Activity',

                # Time
                'time': timestamp_ms,
                'event_date': event_date,

                # Connection Info
                'connection_info': {
                    'uid': record.get('uid'),
                    'protocol_num': proto_num,
                    'protocol_name': proto,
                    'service_name': record.get('service'),
                    'boundary': record.get('history'),
                    'direction': 'Unknown',
                },

                # Source Endpoint
                'src_endpoint': {
                    'ip': record.get('id.orig_h') or record.get('id', {}).get('orig_h'),
                    'port': record.get('id.orig_p') or record.get('id', {}).get('orig_p'),
                    'is_local': record.get('local_orig'),
                    'mac': record.get('orig_l2_addr'),
                    'country': record.get('orig_cc'),
                    'vlan_uid': record.get('vlan'),
                },

                # Destination Endpoint
                'dst_endpoint': {
                    'ip': record.get('id.resp_h') or record.get('id', {}).get('resp_h'),
                    'port': record.get('id.resp_p') or record.get('id', {}).get('resp_p'),
                    'is_local': record.get('local_resp'),
                    'mac': record.get('resp_l2_addr'),
                    'country': record.get('resp_cc'),
                    'vlan_uid': record.get('inner_vlan'),
                },

                # Traffic
                'traffic': {
                    'bytes_in': record.get('resp_bytes'),
                    'bytes_out': record.get('orig_bytes'),
                    'packets_in': record.get('resp_pkts'),
                    'packets_out': record.get('orig_pkts'),
                    'bytes_dropped': record.get('missed_bytes'),
                },

                # Duration
                'duration': int(float(record.get('duration', 0)) * 1000) if record.get('duration') else None,

                # Activity
                'activity_id': 6,  # Traffic
                'conn_state': record.get('conn_state'),

                # Application
                'app': record.get('app'),

                # Zeek Metadata
                'zeek_metadata': {
                    'log_name': record.get('_path'),
                    'tunnel_parents': record.get('tunnel_parents'),
                    'community_id': record.get('community_id'),
                },
            }

            ocsf_records.append(ocsf_record)

        except Exception as e:
            logger.warning(f"Error transforming record: {e}")
            continue

    logger.info(f"Transformed {len(ocsf_records):,} records to OCSF")
    return pd.DataFrame(ocsf_records)


def load_to_iceberg(df: pd.DataFrame, catalog_name: str = "demo",
                    database: str = "security_data", table: str = "network_activity"):
    """
    Load DataFrame to Iceberg table

    Args:
        df: Pandas DataFrame with OCSF data
        catalog_name: Iceberg catalog name
        database: Database/namespace name
        table: Table name
    """
    logger.info(f"Loading {len(df):,} records to Iceberg table {catalog_name}.{database}.{table}")

    # Load catalog configuration
    # Note: Using localhost because script runs on host, not in Docker network
    catalog = load_catalog(
        catalog_name,
        **{
            "type": "hive",
            "uri": "thrift://localhost:9083",
            "warehouse": "s3a://iceberg-warehouse/",
            "s3.endpoint": "http://localhost:9000",
            "s3.access-key-id": "minioadmin",
            "s3.secret-access-key": "minioadmin",
            "s3.path-style-access": "true",
        }
    )

    # Create namespace if it doesn't exist
    try:
        catalog.create_namespace(database)
        logger.info(f"Created namespace {database}")
    except Exception as e:
        logger.info(f"Namespace {database} already exists or error: {e}")

    # Define partition spec (partition by date)
    partition_spec = PartitionSpec(
        PartitionField(
            source_id=8,  # event_date field
            field_id=1000,
            transform=DayTransform(),
            name="event_date"
        )
    )

    # Create or get table
    full_table_name = f"{database}.{table}"
    try:
        iceberg_table = catalog.create_table(
            identifier=full_table_name,
            schema=create_ocsf_schema(),
            partition_spec=partition_spec,
        )
        logger.info(f"Created table {full_table_name}")
    except Exception as e:
        logger.info(f"Table exists or error creating: {e}")
        iceberg_table = catalog.load_table(full_table_name)
        logger.info(f"Loaded existing table {full_table_name}")

    # Convert DataFrame to PyArrow Table
    arrow_table = pa.Table.from_pandas(df)

    # Append data to Iceberg table
    iceberg_table.append(arrow_table)

    logger.info(f"Successfully loaded {len(df):,} records to {full_table_name}")

    # Show table info
    logger.info(f"Table location: {iceberg_table.location()}")
    logger.info(f"Table snapshots: {len(list(iceberg_table.snapshots()))}")


def main():
    """
    Main execution flow
    """
    logger.info("=" * 60)
    logger.info("Zeek → OCSF → Iceberg Data Loader")
    logger.info("=" * 60)

    # Configuration
    DATA_DIR = Path("/home/jerem/zeek-iceberg-demo/data")
    SAMPLE_SIZE = 10000  # Start with 10K records for testing

    # Find Zeek JSON files
    zeek_files = list(DATA_DIR.glob("zeek_conn_*.json"))
    if not zeek_files:
        logger.error(f"No Zeek JSON files found in {DATA_DIR}")
        return 1

    logger.info(f"Found {len(zeek_files)} Zeek file(s)")

    # Use the smaller file for testing
    zeek_file = min(zeek_files, key=lambda f: f.stat().st_size)
    logger.info(f"Using file: {zeek_file} ({zeek_file.stat().st_size / 1024 / 1024:.1f} MB)")

    try:
        # Step 1: Read Zeek logs
        zeek_records = read_zeek_json(str(zeek_file), limit=SAMPLE_SIZE)

        if not zeek_records:
            logger.error("No records read from Zeek file")
            return 1

        # Step 2: Transform to OCSF
        ocsf_df = transform_zeek_to_ocsf(zeek_records)

        if ocsf_df.empty:
            logger.error("No records after transformation")
            return 1

        logger.info(f"DataFrame shape: {ocsf_df.shape}")
        logger.info(f"Sample record:\n{ocsf_df.iloc[0].to_dict()}")

        # Step 3: Load to Iceberg
        load_to_iceberg(ocsf_df)

        logger.info("=" * 60)
        logger.info("✓ Pipeline completed successfully!")
        logger.info("=" * 60)
        logger.info("")
        logger.info("Next steps:")
        logger.info("1. Open Dremio: http://localhost:9047")
        logger.info("2. Navigate to: hive_metastore.security_data.network_activity")
        logger.info("3. Run query: SELECT * FROM hive_metastore.security_data.network_activity LIMIT 10;")

        return 0

    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
