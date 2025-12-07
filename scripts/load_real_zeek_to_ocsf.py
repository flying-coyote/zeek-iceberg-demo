#!/usr/bin/env python3
"""
Load Real Zeek Data → OCSF-Compliant Parquet → MinIO

Uses the pragmatic OCSF flat schema implementation that maintains semantic
compliance while optimizing for query performance in Dremio.

Requirements:
    pip install pyarrow pandas boto3

Usage:
    python3 scripts/load_real_zeek_to_ocsf.py --records 100000
    python3 scripts/load_real_zeek_to_ocsf.py --all  # Load all 1M records
"""

import argparse
import json
import logging
from datetime import datetime
from pathlib import Path
import tempfile
from typing import List, Dict
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import boto3
import sys

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))
from transform_zeek_to_ocsf_flat import (
    transform_zeek_to_ocsf_flat,
    validate_ocsf_compliance,
    write_ocsf_parquet
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# MinIO Configuration
S3_CLIENT = boto3.client(
    's3',
    endpoint_url='http://localhost:9000',
    aws_access_key_id='minioadmin',
    aws_secret_access_key='minioadmin'
)

# Data Configuration
ZEEK_DATA_DIR = Path("/home/jerem/splunk-db-connect-benchmark/data/samples")
BUCKET = "zeek-data"
FOLDER = "network-activity-ocsf"  # New folder for OCSF-compliant data
BATCH_SIZE = 50000  # Process 50K records at a time


def read_zeek_json(file_path: Path, limit: int = None) -> List[Dict]:
    """
    Read Zeek conn logs from NDJSON file

    Args:
        file_path: Path to Zeek JSON file
        limit: Maximum number of records to read (None = all)

    Returns:
        List of Zeek log dictionaries
    """
    logger.info(f"Reading Zeek logs from {file_path.name}")
    logger.info(f"File size: {file_path.stat().st_size / 1024 / 1024:.1f} MB")

    records = []
    with open(file_path, 'r') as f:
        for i, line in enumerate(f):
            if limit and i >= limit:
                break

            if i > 0 and i % 100000 == 0:
                logger.info(f"  Read {i:,} records...")

            try:
                record = json.loads(line.strip())
                records.append(record)
            except json.JSONDecodeError as e:
                logger.warning(f"Skipping malformed JSON on line {i+1}: {e}")
                continue

    logger.info(f"✓ Read {len(records):,} Zeek records")
    return records


def upload_partition_to_minio(df: pd.DataFrame, year: int, month: int, day: int) -> None:
    """
    Write OCSF DataFrame to Parquet and upload to MinIO with partitioning

    Args:
        df: OCSF-compliant DataFrame for this partition
        year, month, day: Partition values
    """
    # Create temporary file
    with tempfile.NamedTemporaryFile(suffix='.parquet', delete=False) as tmp:
        tmp_path = Path(tmp.name)

    try:
        # Write to Parquet with OCSF optimizations
        write_ocsf_parquet(df, tmp_path, compression='snappy')

        # Upload to MinIO
        key = f'{FOLDER}/year={year}/month={month:02d}/day={day:02d}/data.parquet'
        S3_CLIENT.upload_file(str(tmp_path), BUCKET, key)

        file_size_mb = tmp_path.stat().st_size / 1024 / 1024
        logger.info(f"  ✓ Uploaded {key} ({len(df):,} records, {file_size_mb:.1f} MB)")

    finally:
        tmp_path.unlink(missing_ok=True)


def load_to_minio(df: pd.DataFrame) -> None:
    """
    Partition OCSF DataFrame by date and upload to MinIO

    Args:
        df: OCSF-compliant DataFrame with Zeek data
    """
    logger.info(f"Uploading {len(df):,} OCSF records to MinIO bucket: {BUCKET}/{FOLDER}")

    # Parse event_date for partitioning
    df['_partition_date'] = pd.to_datetime(df['event_date'])
    df['_year'] = df['_partition_date'].dt.year
    df['_month'] = df['_partition_date'].dt.month
    df['_day'] = df['_partition_date'].dt.day

    # Drop temporary columns before upload
    partition_cols = ['_partition_date', '_year', '_month', '_day']

    # Group and upload
    partitions_count = 0
    for (year, month, day), group_df in df.groupby(['_year', '_month', '_day']):
        # Remove partition columns from data
        data_df = group_df.drop(columns=partition_cols)
        upload_partition_to_minio(data_df, int(year), int(month), int(day))
        partitions_count += 1

    logger.info(f"✓ Upload complete - {partitions_count} partitions created")


def show_ocsf_sample_queries():
    """Display sample OCSF queries for Dremio"""
    queries = """
Sample OCSF Queries for Dremio:

1. Network Activity Overview (OCSF fields):
   SELECT
     activity_name,
     class_name,
     COUNT(*) as events,
     SUM(traffic_bytes_in + traffic_bytes_out) as total_bytes
   FROM minio."zeek-data"."network-activity-ocsf"
   WHERE category_uid = 4
   GROUP BY activity_name, class_name
   ORDER BY total_bytes DESC;

2. Top Talkers by Protocol (OCSF compliance):
   SELECT
     src_endpoint_ip,
     dst_endpoint_ip,
     connection_info_protocol_name,
     SUM(traffic_bytes_in + traffic_bytes_out) as total_bytes,
     COUNT(*) as connection_count
   FROM minio."zeek-data"."network-activity-ocsf"
   WHERE class_uid = 4001  -- Network Activity
   GROUP BY src_endpoint_ip, dst_endpoint_ip, connection_info_protocol_name
   ORDER BY total_bytes DESC
   LIMIT 20;

3. Security Analysis - Egress Traffic (OCSF):
   SELECT
     activity_name,
     src_endpoint_is_local,
     dst_endpoint_is_local,
     COUNT(*) as events,
     SUM(traffic_bytes_out) as egress_bytes
   FROM minio."zeek-data"."network-activity-ocsf"
   WHERE
     class_uid = 4001
     AND src_endpoint_is_local = true
     AND dst_endpoint_is_local = false
   GROUP BY activity_name, src_endpoint_is_local, dst_endpoint_is_local
   ORDER BY egress_bytes DESC;

4. Time-based Analysis (OCSF time fields):
   SELECT
     DATE_TRUNC('hour', FROM_UNIXTIME(time / 1000)) as hour,
     COUNT(*) as events,
     COUNT(DISTINCT src_endpoint_ip) as unique_sources,
     COUNT(DISTINCT dst_endpoint_ip) as unique_destinations
   FROM minio."zeek-data"."network-activity-ocsf"
   GROUP BY DATE_TRUNC('hour', FROM_UNIXTIME(time / 1000))
   ORDER BY hour;
"""
    print(queries)


def main():
    """Main execution flow"""
    parser = argparse.ArgumentParser(description='Load real Zeek data to OCSF-compliant MinIO')
    parser.add_argument('--records', type=int, default=100000,
                        help='Number of records to load (default: 100000)')
    parser.add_argument('--all', action='store_true',
                        help='Load all records from 1M record file')
    parser.add_argument('--file', type=str,
                        help='Specific Zeek JSON file to load')
    parser.add_argument('--validate', action='store_true',
                        help='Run OCSF compliance validation')
    args = parser.parse_args()

    logger.info("=" * 70)
    logger.info("Real Zeek Data → OCSF-Compliant Parquet → MinIO Loader")
    logger.info("=" * 70)
    logger.info("Using pragmatic flat schema with OCSF field semantics")
    logger.info("")

    try:
        # Find Zeek files
        if args.file:
            zeek_file = Path(args.file)
            if not zeek_file.exists():
                logger.error(f"File not found: {zeek_file}")
                return 1
        else:
            # Use the 1M record file if --all, otherwise 100K file
            if args.all:
                pattern = "zeek_1000000_*.json"
                limit = None
            else:
                pattern = "zeek_100000_*.json"
                limit = args.records

            zeek_files = list(ZEEK_DATA_DIR.glob(pattern))
            if not zeek_files:
                # Try alternative location
                alt_dir = Path("/home/jerem/zeek-iceberg-demo/data")
                zeek_files = list(alt_dir.glob(pattern))
                if not zeek_files:
                    logger.error(f"No Zeek files found matching {pattern}")
                    logger.error(f"Searched: {ZEEK_DATA_DIR} and {alt_dir}")
                    return 1

            zeek_file = zeek_files[0]

        logger.info(f"Source file: {zeek_file}")
        logger.info(f"Record limit: {limit if limit else 'ALL'}")
        logger.info("")

        # Step 1: Read Zeek data
        zeek_records = read_zeek_json(zeek_file, limit=limit)

        if not zeek_records:
            logger.error("No records read from file")
            return 1

        # Step 2: Transform to OCSF-compliant schema
        logger.info("Applying OCSF transformation...")
        df = transform_zeek_to_ocsf_flat(zeek_records)

        if df.empty:
            logger.error("No records after OCSF transformation")
            return 1

        # Step 3: Validate OCSF compliance
        if args.validate:
            logger.info("")
            logger.info("Validating OCSF compliance...")
            compliance = validate_ocsf_compliance(df)
            for check, result in sorted(compliance.items()):
                status = "✓" if result else "✗"
                logger.info(f"  {status} {check}: {result}")

            if not compliance.get('overall_compliance'):
                logger.error("OCSF compliance validation failed!")
                return 1
            logger.info("")

        # Show sample OCSF record
        logger.info("Sample OCSF-compliant record:")
        sample_fields = [
            'class_uid', 'class_name',
            'src_endpoint_ip', 'src_endpoint_port',
            'dst_endpoint_ip', 'dst_endpoint_port',
            'traffic_bytes_in', 'traffic_bytes_out',
            'connection_info_protocol_name',
            'activity_name', 'metadata_product_name'
        ]
        sample_record = {}
        for field in sample_fields:
            if field in df.columns:
                sample_record[field] = df[field].iloc[0]
        for key, value in sample_record.items():
            logger.info(f"  {key}: {value}")
        logger.info("")

        # Show statistics
        logger.info("OCSF Data Statistics:")
        logger.info(f"  Total records: {len(df):,}")
        logger.info(f"  OCSF fields: {len(df.columns)}")
        logger.info(f"  Date range: {df['event_date'].min()} to {df['event_date'].max()}")

        # Protocol distribution
        if 'connection_info_protocol_name' in df.columns:
            proto_counts = df['connection_info_protocol_name'].value_counts().head(5)
            logger.info("  Top protocols:")
            for proto, count in proto_counts.items():
                logger.info(f"    {proto}: {count:,} ({count/len(df)*100:.1f}%)")

        # Activity distribution
        if 'activity_name' in df.columns:
            activity_counts = df['activity_name'].value_counts().head(5)
            logger.info("  Top activities:")
            for activity, count in activity_counts.items():
                logger.info(f"    {activity}: {count:,} ({count/len(df)*100:.1f}%)")
        logger.info("")

        # Step 4: Upload to MinIO
        load_to_minio(df)

        logger.info("")
        logger.info("=" * 70)
        logger.info("✓ OCSF Pipeline completed successfully!")
        logger.info("=" * 70)
        logger.info("")
        logger.info("Next steps:")
        logger.info("1. Open Dremio: http://localhost:9047")
        logger.info("2. Navigate to: minio > zeek-data > network-activity-ocsf")
        logger.info("3. Format folder as Parquet")
        logger.info("4. Run OCSF queries (examples below)")
        logger.info("")
        logger.info(f"Total OCSF records loaded: {len(df):,}")
        logger.info(f"OCSF fields implemented: {len(df.columns)}")
        logger.info(f"Storage location: s3://{BUCKET}/{FOLDER}/")
        logger.info("")

        # Show sample queries
        show_ocsf_sample_queries()

        return 0

    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())