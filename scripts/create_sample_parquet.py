#!/usr/bin/env python3
"""
Create sample Parquet files in MinIO for Dremio testing
"""
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from datetime import datetime, timedelta
import random
import tempfile
import boto3
from pathlib import Path

# MinIO configuration
s3_client = boto3.client(
    's3',
    endpoint_url='http://localhost:9000',
    aws_access_key_id='minioadmin',
    aws_secret_access_key='minioadmin'
)

# Create sample network activity data
def create_sample_data(num_records=1000):
    """Generate sample network activity data"""
    base_time = datetime.now() - timedelta(days=1)
    
    data = {
        'timestamp': [base_time + timedelta(seconds=i*10) for i in range(num_records)],
        'src_ip': [f'192.168.{random.randint(1,255)}.{random.randint(1,255)}' for _ in range(num_records)],
        'dst_ip': [f'10.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,255)}' for _ in range(num_records)],
        'src_port': [random.randint(1024, 65535) for _ in range(num_records)],
        'dst_port': [random.choice([80, 443, 22, 3389, 8080, 8443]) for _ in range(num_records)],
        'protocol': [random.choice(['TCP', 'UDP', 'ICMP']) for _ in range(num_records)],
        'bytes_sent': [random.randint(100, 100000) for _ in range(num_records)],
        'bytes_received': [random.randint(100, 100000) for _ in range(num_records)],
        'packets': [random.randint(1, 1000) for _ in range(num_records)],
        'duration': [random.uniform(0.1, 300.0) for _ in range(num_records)],
    }
    
    return pd.DataFrame(data)

def upload_to_minio(df, bucket, key):
    """Write DataFrame to Parquet and upload to MinIO"""
    # Create temporary file
    with tempfile.NamedTemporaryFile(suffix='.parquet', delete=False) as tmp:
        tmp_path = tmp.name
        
    try:
        # Write to Parquet
        table = pa.Table.from_pandas(df)
        pq.write_table(table, tmp_path, compression='snappy')
        
        # Upload to MinIO
        s3_client.upload_file(tmp_path, bucket, key)
        print(f"✓ Uploaded {key} to {bucket} ({len(df):,} records)")
        
    finally:
        Path(tmp_path).unlink(missing_ok=True)

def main():
    bucket = 'zeek-data'
    
    print("Creating sample network activity data...")
    
    # Create multiple files to demonstrate partitioning
    for day in range(3):
        date = datetime.now() - timedelta(days=day)
        date_str = date.strftime('%Y-%m-%d')
        
        df = create_sample_data(1000)
        df['event_date'] = date_str
        
        key = f'network-activity/year={date.year}/month={date.month:02d}/day={date.day:02d}/data.parquet'
        upload_to_minio(df, bucket, key)
    
    print("\n✓ Sample data created successfully!")
    print(f"\nData location: s3://{bucket}/network-activity/")
    print("You can now configure this in Dremio to query the data")

if __name__ == '__main__':
    main()
