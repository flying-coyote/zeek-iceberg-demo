#!/usr/bin/env python3
"""
Load Real Zeek Data → Parquet → MinIO

Bypasses Hive Metastore (auth issues) and writes directly to MinIO.
Works with the proven MinIO + Dremio direct S3 architecture.

Requirements:
    pip install pyarrow pandas boto3

Usage:
    python3 scripts/load_real_zeek_to_parquet.py --records 100000
    python3 scripts/load_real_zeek_to_parquet.py --all  # Load all 1M records
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
FOLDER = "network-activity-real"
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


def transform_zeek_to_flat_schema(zeek_records: List[Dict]) -> pd.DataFrame:
    """
    Transform Zeek conn logs to flat Parquet schema

    Simpler than full OCSF - matches the sample data schema for compatibility.

    Args:
        zeek_records: List of Zeek log dictionaries

    Returns:
        Pandas DataFrame ready for Parquet
    """
    logger.info("Transforming Zeek records to Parquet schema")

    transformed = []

    for record in zeek_records:
        try:
            # Parse timestamp
            ts = float(record.get('ts', 0))
            timestamp = datetime.fromtimestamp(ts)
            event_date = timestamp.date()

            # Extract connection tuple (handle both formats)
            src_ip = record.get('id.orig_h') or record.get('id', {}).get('orig_h')
            src_port = record.get('id.orig_p') or record.get('id', {}).get('orig_p')
            dst_ip = record.get('id.resp_h') or record.get('id', {}).get('resp_h')
            dst_port = record.get('id.resp_p') or record.get('id', {}).get('resp_p')

            # Build flat record
            flat_record = {
                'timestamp': timestamp,
                'src_ip': src_ip,
                'dst_ip': dst_ip,
                'src_port': src_port,
                'dst_port': dst_port,
                'protocol': record.get('proto', 'unknown').upper(),
                'bytes_sent': record.get('orig_bytes', 0),
                'bytes_received': record.get('resp_bytes', 0),
                'packets': (record.get('orig_pkts', 0) or 0) + (record.get('resp_pkts', 0) or 0),
                'duration': float(record.get('duration', 0.0)) if record.get('duration') else 0.0,
                'event_date': event_date.isoformat(),
                'conn_state': record.get('conn_state'),
                'service': record.get('service'),
                'uid': record.get('uid'),
            }

            transformed.append(flat_record)

        except Exception as e:
            logger.warning(f"Error transforming record: {e}")
            continue

    df = pd.DataFrame(transformed)
    logger.info(f"✓ Transformed {len(df):,} records")
    return df


def upload_partition_to_minio(df: pd.DataFrame, year: int, month: int, day: int) -> None:
    """
    Write DataFrame to Parquet and upload to MinIO with partitioning

    Args:
        df: DataFrame for this partition
        year, month, day: Partition values
    """
    # Create temporary file
    with tempfile.NamedTemporaryFile(suffix='.parquet', delete=False) as tmp:
        tmp_path = Path(tmp.name)

    try:
        # Write to Parquet with compression
        table = pa.Table.from_pandas(df)
        pq.write_table(
            table,
            tmp_path,
            compression='snappy',
            use_dictionary=True,
            write_statistics=True
        )

        # Upload to MinIO
        key = f'{FOLDER}/year={year}/month={month:02d}/day={day:02d}/data.parquet'
        S3_CLIENT.upload_file(str(tmp_path), BUCKET, key)

        file_size_mb = tmp_path.stat().st_size / 1024 / 1024
        logger.info(f"  ✓ Uploaded {key} ({len(df):,} records, {file_size_mb:.1f} MB)")

    finally:
        tmp_path.unlink(missing_ok=True)


def load_to_minio(df: pd.DataFrame) -> None:
    """
    Partition DataFrame by date and upload to MinIO

    Args:
        df: DataFrame with Zeek data
    """
    logger.info(f"Uploading {len(df):,} records to MinIO bucket: {BUCKET}/{FOLDER}")

    # Group by date partition
    df['_partition_date'] = pd.to_datetime(df['event_date'])
    df['_year'] = df['_partition_date'].dt.year
    df['_month'] = df['_partition_date'].dt.month
    df['_day'] = df['_partition_date'].dt.day

    # Drop temporary columns before upload
    partition_cols = ['_partition_date', '_year', '_month', '_day']

    # Group and upload
    for (year, month, day), group_df in df.groupby(['_year', '_month', '_day']):
        # Remove partition columns from data
        data_df = group_df.drop(columns=partition_cols)
        upload_partition_to_minio(data_df, int(year), int(month), int(day))

    logger.info(f"✓ Upload complete")


def main():
    """Main execution flow"""
    parser = argparse.ArgumentParser(description='Load real Zeek data to MinIO')
    parser.add_argument('--records', type=int, default=100000,
                        help='Number of records to load (default: 100000)')
    parser.add_argument('--all', action='store_true',
                        help='Load all records from 1M record file')
    parser.add_argument('--file', type=str,
                        help='Specific Zeek JSON file to load')
    args = parser.parse_args()

    logger.info("=" * 70)
    logger.info("Real Zeek Data → Parquet → MinIO Loader")
    logger.info("=" * 70)

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
                logger.error(f"No Zeek files found matching {pattern} in {ZEEK_DATA_DIR}")
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

        # Step 2: Transform to Parquet schema
        df = transform_zeek_to_flat_schema(zeek_records)

        if df.empty:
            logger.error("No records after transformation")
            return 1

        # Show sample
        logger.info("")
        logger.info("Sample transformed record:")
        logger.info(df.iloc[0].to_dict())
        logger.info("")

        # Show date range
        date_range = df['event_date'].agg(['min', 'max'])
        logger.info(f"Date range: {date_range['min']} to {date_range['max']}")
        logger.info("")

        # Step 3: Upload to MinIO
        load_to_minio(df)

        logger.info("")
        logger.info("=" * 70)
        logger.info("✓ Pipeline completed successfully!")
        logger.info("=" * 70)
        logger.info("")
        logger.info("Next steps:")
        logger.info("1. Open Dremio: http://localhost:9047")
        logger.info("2. Navigate to: minio > zeek-data > network-activity-real")
        logger.info("3. Format folder as Parquet")
        logger.info("4. Run query:")
        logger.info(f'   SELECT * FROM minio."zeek-data"."network-activity-real" LIMIT 10;')
        logger.info("")
        logger.info(f"Total records loaded: {len(df):,}")
        logger.info(f"Storage location: s3://{BUCKET}/{FOLDER}/")

        return 0

    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
