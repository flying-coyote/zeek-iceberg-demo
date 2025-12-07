#!/bin/bash

# Setup Impala for OCSF Data Access
# This script configures Impala to query the OCSF Parquet data in MinIO

set -e

echo "======================================================================="
echo "Impala Setup for OCSF Data"
echo "======================================================================="
echo ""

# Check if Impala is running
if ! docker ps | grep -q "zeek-demo-impala-daemon"; then
    echo "Starting Impala services..."
    docker-compose -f docker-compose.yml -f docker-compose.impala.yml up -d

    echo "Waiting for Impala to be ready (this may take 1-2 minutes)..."
    sleep 30

    # Wait for Impala daemon to be ready
    for i in {1..30}; do
        if docker exec zeek-demo-impala-daemon impala-shell -q "SELECT 1;" 2>/dev/null | grep -q "1"; then
            echo "✓ Impala is ready!"
            break
        fi
        echo "  Waiting for Impala... ($i/30)"
        sleep 5
    done
else
    echo "✓ Impala is already running"
fi

echo ""
echo "Creating OCSF database and external table..."
echo ""

# Create the SQL commands file
cat > /tmp/impala_ocsf_setup.sql << 'EOF'
-- Create database for OCSF data
CREATE DATABASE IF NOT EXISTS ocsf_security
COMMENT 'OCSF-compliant security data from Zeek';

USE ocsf_security;

-- Drop table if exists (for re-runs)
DROP TABLE IF EXISTS network_activity;

-- Create external table pointing to OCSF Parquet data in MinIO
CREATE EXTERNAL TABLE network_activity (
    -- OCSF Core Fields
    activity_id INT,
    activity_name STRING,
    category_name STRING,
    category_uid INT,
    class_name STRING,
    class_uid INT,

    -- Source Endpoint (Flattened)
    src_endpoint_ip STRING,
    src_endpoint_port INT,
    src_endpoint_is_local BOOLEAN,
    src_endpoint_mac STRING,
    src_endpoint_hostname STRING,

    -- Destination Endpoint (Flattened)
    dst_endpoint_ip STRING,
    dst_endpoint_port INT,
    dst_endpoint_is_local BOOLEAN,
    dst_endpoint_mac STRING,
    dst_endpoint_hostname STRING,

    -- Connection Information (Flattened)
    connection_info_protocol_name STRING,
    connection_info_protocol_num INT,
    connection_info_protocol_version STRING,
    connection_info_direction STRING,
    connection_info_uid STRING,
    connection_info_tcp_flags INT,

    -- Traffic Metrics (Flattened)
    traffic_bytes_in BIGINT,
    traffic_bytes_out BIGINT,
    traffic_packets_in BIGINT,
    traffic_packets_out BIGINT,
    traffic_bytes BIGINT,
    traffic_packets BIGINT,

    -- Metadata (Flattened)
    metadata_event_code STRING,
    metadata_log_name STRING,
    metadata_log_provider STRING,
    metadata_original_time BIGINT,
    metadata_processed_time BIGINT,
    metadata_product_name STRING,
    metadata_product_vendor_name STRING,
    metadata_product_version STRING,
    metadata_profiles STRING,
    metadata_sequence INT,
    metadata_uid STRING,
    metadata_version STRING,

    -- Observables (Flattened)
    observables_count INT,
    observables_names STRING,
    observables_types STRING,
    observables_type_ids STRING,

    -- Time Fields
    duration BIGINT,
    end_time BIGINT,
    start_time BIGINT,
    time BIGINT,
    timezone_offset INT,

    -- Other OCSF Fields
    confidence INT,
    impact INT,
    risk_level INT,
    risk_score INT,
    severity STRING,
    severity_id INT,
    status STRING,
    status_code INT,
    status_detail STRING,
    status_id INT,
    type_name STRING,
    type_uid BIGINT,
    unmapped STRING,

    -- Partitioning field
    event_date STRING
)
STORED AS PARQUET
LOCATION 's3a://zeek-data/network-activity-ocsf/'
TBLPROPERTIES (
    'compression'='snappy',
    'parquet.compression'='SNAPPY'
);

-- Compute statistics for better query performance
COMPUTE STATS network_activity;

-- Show table info
DESCRIBE network_activity;

-- Count records to verify
SELECT COUNT(*) as total_records FROM network_activity;

-- Show sample records
SELECT
    class_name,
    activity_name,
    src_endpoint_ip,
    dst_endpoint_ip,
    traffic_bytes_in,
    traffic_bytes_out,
    connection_info_protocol_name
FROM network_activity
LIMIT 10;

-- Show protocol distribution
SELECT
    connection_info_protocol_name,
    COUNT(*) as count,
    SUM(traffic_bytes_in + traffic_bytes_out) as total_bytes
FROM network_activity
GROUP BY connection_info_protocol_name
ORDER BY count DESC;

-- Show activity distribution
SELECT
    activity_name,
    COUNT(*) as count
FROM network_activity
GROUP BY activity_name
ORDER BY count DESC
LIMIT 10;

EOF

# Execute the SQL setup
echo "Running Impala SQL setup..."
docker exec -i zeek-demo-impala-daemon impala-shell -f /dev/stdin < /tmp/impala_ocsf_setup.sql

echo ""
echo "======================================================================="
echo "✓ Impala Setup Complete!"
echo "======================================================================="
echo ""
echo "Access Methods:"
echo "1. Impala Shell:"
echo "   docker exec -it zeek-demo-impala-daemon impala-shell"
echo ""
echo "2. Impala Web UI:"
echo "   http://localhost:21050"
echo ""
echo "3. JDBC Connection:"
echo "   jdbc:impala://localhost:21000/ocsf_security"
echo ""
echo "Sample Queries:"
echo ""
echo "-- Top talkers"
echo "SELECT src_endpoint_ip, dst_endpoint_ip,"
echo "       SUM(traffic_bytes_in + traffic_bytes_out) as total_bytes"
echo "FROM ocsf_security.network_activity"
echo "GROUP BY src_endpoint_ip, dst_endpoint_ip"
echo "ORDER BY total_bytes DESC"
echo "LIMIT 20;"
echo ""
echo "-- Protocol analysis"
echo "SELECT connection_info_protocol_name,"
echo "       COUNT(*) as connections,"
echo "       SUM(traffic_bytes_in) as bytes_in,"
echo "       SUM(traffic_bytes_out) as bytes_out"
echo "FROM ocsf_security.network_activity"
echo "GROUP BY connection_info_protocol_name;"
echo ""

# Clean up
rm -f /tmp/impala_ocsf_setup.sql