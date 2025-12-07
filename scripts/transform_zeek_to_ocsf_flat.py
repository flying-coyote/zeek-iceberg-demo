#!/usr/bin/env python3
"""
Transform Zeek to OCSF-Compliant Flat Schema

This implements OCSF field semantics with a denormalized (flat) schema
optimized for analytical query performance in Dremio, Athena, and similar engines.

Rationale:
- OCSF compliance = standardized field names and semantics
- Flat structure = optimal query performance
- Production validated = AWS Security Lake uses similar approach
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

logger = logging.getLogger(__name__)

# OCSF Protocol mappings
PROTOCOL_MAP = {
    'tcp': 6,
    'udp': 17,
    'icmp': 1,
    'ipv6-icmp': 58,
}

# OCSF Connection State mappings
CONN_STATE_MAP = {
    'S0': 1,    # Connection attempt seen, no reply
    'S1': 2,    # Connection established, not terminated
    'SF': 3,    # Normal establishment and termination
    'REJ': 4,   # Connection rejected
    'S2': 5,    # Connection established and close attempt
    'S3': 6,    # Connection established and closed
    'RSTO': 7,  # Connection reset
    'RSTR': 8,  # Established, reset by responder
    'RSTOS0': 9,  # Originator reset, no SYN ACK
    'RSTRH': 10, # Responder reset, half open
    'SH': 11,   # Originator sent SYN followed by FIN
    'SHR': 12,  # Responder sent SYN ACK followed by FIN
    'OTH': 99,  # Other/Unknown
}

# OCSF Activity Types for Network Activity (class_uid 4001)
ACTIVITY_ID_MAP = {
    'traffic': 6,      # General network traffic
    'dns': 1,          # DNS query
    'http': 2,         # HTTP activity
    'ssh': 3,          # SSH activity
    'ssl': 4,          # TLS/SSL activity
    'smtp': 5,         # SMTP email
}

def transform_zeek_to_ocsf_flat(zeek_records: List[Dict]) -> pd.DataFrame:
    """
    Transform Zeek conn logs to OCSF-compliant flat schema.

    This creates a denormalized structure with OCSF field naming conventions,
    optimized for analytical workloads while maintaining semantic compliance.

    Args:
        zeek_records: List of Zeek conn log dictionaries

    Returns:
        DataFrame with OCSF-compliant flat schema
    """
    logger.info(f"Transforming {len(zeek_records):,} Zeek records to OCSF flat schema")

    transformed = []

    for record in zeek_records:
        try:
            # Parse timestamp
            ts = float(record.get('ts', 0))
            timestamp = datetime.fromtimestamp(ts)
            event_date = timestamp.date()

            # Extract connection data
            src_ip = record.get('id.orig_h') or record.get('id', {}).get('orig_h')
            src_port = record.get('id.orig_p') or record.get('id', {}).get('orig_p')
            dst_ip = record.get('id.resp_h') or record.get('id', {}).get('resp_h')
            dst_port = record.get('id.resp_p') or record.get('id', {}).get('resp_p')

            # Protocol mapping
            proto = record.get('proto', 'unknown').lower()
            protocol_num = PROTOCOL_MAP.get(proto, 0)

            # Service detection
            service = record.get('service')
            activity_id = ACTIVITY_ID_MAP.get(service, 6) if service else 6

            # Connection state mapping
            conn_state = record.get('conn_state', 'OTH')
            conn_state_id = CONN_STATE_MAP.get(conn_state, 99)

            # Build OCSF-compliant flat record
            ocsf_record = {
                # === OCSF Metadata Fields ===
                'activity_id': activity_id,
                'activity_name': service if service else 'Traffic',
                'category_uid': 4,  # Network Activity
                'category_name': 'Network Activity',
                'class_uid': 4001,  # Network Activity class
                'class_name': 'Network Activity',
                'confidence': 100,  # High confidence (direct observation)
                'severity_id': 1,   # Informational (normal traffic)
                'type_uid': 400106, # Network Traffic (4001 * 100 + activity_id)
                'type_name': f'Network Activity: {service if service else "Traffic"}',

                # === OCSF Time Fields ===
                'time': int(ts * 1000),  # OCSF uses milliseconds
                'event_time': int(ts * 1000),
                'metadata_logged_time': int(ts * 1000),
                'metadata_processed_time': int(datetime.now().timestamp() * 1000),

                # === Source Endpoint (Flattened) ===
                'src_endpoint_ip': src_ip,
                'src_endpoint_port': int(src_port) if src_port else None,
                'src_endpoint_domain': None,  # Could be enriched
                'src_endpoint_hostname': None,  # Could be enriched
                'src_endpoint_is_local': record.get('local_orig', False),
                'src_endpoint_location_country': record.get('orig_cc'),
                'src_endpoint_mac': record.get('orig_l2_addr'),

                # === Destination Endpoint (Flattened) ===
                'dst_endpoint_ip': dst_ip,
                'dst_endpoint_port': int(dst_port) if dst_port else None,
                'dst_endpoint_domain': None,  # Could be enriched
                'dst_endpoint_hostname': None,  # Could be enriched
                'dst_endpoint_is_local': record.get('local_resp', False),
                'dst_endpoint_location_country': record.get('resp_cc'),
                'dst_endpoint_mac': record.get('resp_l2_addr'),

                # === Connection Info (Flattened) ===
                'connection_info_uid': record.get('uid'),
                'connection_info_protocol_num': protocol_num,
                'connection_info_protocol_name': proto.upper(),
                'connection_info_protocol_ver': 'IPv4',  # Could detect IPv6
                'connection_info_tcp_flags': record.get('history'),
                'connection_info_direction': 'Unknown',  # Could be enriched
                'connection_info_boundary': 'Unknown',  # Could be enriched based on local_orig/resp

                # === Traffic Metrics (Flattened) ===
                'traffic_bytes_in': int(record.get('resp_bytes', 0)) if record.get('resp_bytes') is not None else 0,
                'traffic_bytes_out': int(record.get('orig_bytes', 0)) if record.get('orig_bytes') is not None else 0,
                'traffic_packets_in': int(record.get('resp_pkts', 0)) if record.get('resp_pkts') is not None else 0,
                'traffic_packets_out': int(record.get('orig_pkts', 0)) if record.get('orig_pkts') is not None else 0,
                'traffic_bytes': (
                    int(record.get('resp_bytes', 0) or 0) +
                    int(record.get('orig_bytes', 0) or 0)
                ),
                'traffic_packets': (
                    int(record.get('resp_pkts', 0) or 0) +
                    int(record.get('orig_pkts', 0) or 0)
                ),

                # === Network Metadata (Flattened) ===
                'metadata_product_name': 'Zeek',
                'metadata_product_vendor_name': 'Zeek Project',
                'metadata_product_version': '5.0.0',  # Could be parameterized
                'metadata_log_name': 'conn',
                'metadata_log_version': '1.0.0',

                # === Observables (for threat hunting) ===
                'observables_name_src_ip': src_ip,
                'observables_name_dst_ip': dst_ip,
                'observables_name_src_port': str(src_port) if src_port else None,
                'observables_name_dst_port': str(dst_port) if dst_port else None,
                'observables_type_src_ip': 'IP Address',
                'observables_type_dst_ip': 'IP Address',

                # === Additional Zeek-specific fields (OCSF unmapped namespace) ===
                'unmapped_conn_state': conn_state,
                'unmapped_conn_state_id': conn_state_id,
                'unmapped_duration': float(record.get('duration', 0.0)) if record.get('duration') else 0.0,
                'unmapped_missed_bytes': int(record.get('missed_bytes', 0)) if record.get('missed_bytes') is not None else 0,
                'unmapped_tunnel_parents': json.dumps(record.get('tunnel_parents', [])),
                'unmapped_vlan': record.get('vlan'),
                'unmapped_inner_vlan': record.get('inner_vlan'),
                'unmapped_community_id': record.get('community_id'),

                # === Partitioning ===
                'event_date': event_date.isoformat(),
            }

            transformed.append(ocsf_record)

        except Exception as e:
            logger.warning(f"Error transforming record: {e}")
            logger.debug(f"Problematic record: {record}")
            continue

    # Create DataFrame
    df = pd.DataFrame(transformed)

    # Ensure correct data types
    int_columns = [col for col in df.columns if col.endswith('_id') or col.endswith('_uid') or col.endswith('_num')]
    for col in int_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype('Int64')

    logger.info(f"✓ Transformed {len(df):,} records to OCSF flat schema")
    logger.info(f"  Schema has {len(df.columns)} fields")

    return df

def validate_ocsf_compliance(df: pd.DataFrame) -> Dict[str, bool]:
    """
    Validate that the DataFrame meets OCSF compliance requirements.

    Args:
        df: DataFrame with OCSF fields

    Returns:
        Dictionary of compliance checks and results
    """
    checks = {}

    # Required OCSF fields for Network Activity (class_uid 4001)
    required_fields = [
        'activity_id', 'category_uid', 'class_uid', 'time',
        'src_endpoint_ip', 'dst_endpoint_ip'
    ]

    # Check required fields exist
    for field in required_fields:
        checks[f'has_{field}'] = field in df.columns

    # Check metadata fields
    metadata_fields = [
        'metadata_product_name', 'metadata_product_vendor_name',
        'metadata_log_name'
    ]
    for field in metadata_fields:
        checks[f'has_{field}'] = field in df.columns

    # Check value ranges
    if 'activity_id' in df.columns:
        checks['activity_id_valid'] = df['activity_id'].between(0, 99).all()

    if 'category_uid' in df.columns:
        checks['category_uid_is_4'] = (df['category_uid'] == 4).all()

    if 'class_uid' in df.columns:
        checks['class_uid_is_4001'] = (df['class_uid'] == 4001).all()

    # Overall compliance
    checks['overall_compliance'] = all(checks.values())

    return checks

def write_ocsf_parquet(df: pd.DataFrame, output_path: Path,
                       compression: str = 'snappy') -> None:
    """
    Write OCSF-compliant DataFrame to Parquet with appropriate settings.

    Args:
        df: OCSF DataFrame
        output_path: Where to write the Parquet file
        compression: Compression algorithm (snappy, gzip, lz4, zstd)
    """
    # Define schema with appropriate types
    # This ensures consistent data types for analytics engines

    # Create Parquet schema
    table = pa.Table.from_pandas(df)

    # Write with optimizations
    pq.write_table(
        table,
        output_path,
        compression=compression,
        use_dictionary=True,  # Dictionary encoding for repeated values
        write_statistics=True,  # Statistics for query optimization
        row_group_size=50000,  # Optimize for query performance
        data_page_size=1024*1024,  # 1MB pages
        version='2.6'  # Latest Parquet format
    )

    file_size_mb = output_path.stat().st_size / 1024 / 1024
    logger.info(f"✓ Wrote OCSF Parquet: {output_path}")
    logger.info(f"  Size: {file_size_mb:.1f} MB")
    logger.info(f"  Compression: {compression}")
    logger.info(f"  Records: {len(df):,}")

def main():
    """Example usage"""
    import sys

    # Example Zeek record
    sample_zeek = [{
        "ts": 1699886400.123456,
        "uid": "CXk4fz3LjsKVwF7fJf",
        "id.orig_h": "192.168.1.100",
        "id.orig_p": 49152,
        "id.resp_h": "93.184.216.34",
        "id.resp_p": 443,
        "proto": "tcp",
        "service": "ssl",
        "duration": 120.5,
        "orig_bytes": 5242,
        "resp_bytes": 12451,
        "conn_state": "SF",
        "local_orig": True,
        "local_resp": False,
        "missed_bytes": 0,
        "history": "ShADadfF",
        "orig_pkts": 42,
        "resp_pkts": 38,
        "tunnel_parents": []
    }]

    # Transform
    df = transform_zeek_to_ocsf_flat(sample_zeek)

    # Validate
    compliance = validate_ocsf_compliance(df)
    print("\nOCSF Compliance Checks:")
    for check, result in compliance.items():
        status = "✓" if result else "✗"
        print(f"  {status} {check}: {result}")

    # Show sample fields
    print("\nSample OCSF Fields:")
    sample_fields = [
        'class_uid', 'class_name',
        'src_endpoint_ip', 'dst_endpoint_ip',
        'traffic_bytes_in', 'traffic_bytes_out',
        'connection_info_protocol_name'
    ]
    for field in sample_fields:
        if field in df.columns:
            print(f"  {field}: {df[field].iloc[0]}")

    # Write to Parquet
    output_path = Path("/tmp/ocsf_sample.parquet")
    write_ocsf_parquet(df, output_path)

    print(f"\n✓ OCSF-compliant Parquet written to {output_path}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()