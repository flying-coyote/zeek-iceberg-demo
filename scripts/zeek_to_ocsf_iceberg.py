#!/usr/bin/env python3
"""
Zeek → OCSF → Iceberg Pipeline
Transforms Zeek network logs to OCSF schema and writes to Iceberg tables

Based on production SQL views from ~/Zeek-to-OCSF-mapping/
OCSF Version: 1.4.0
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, lit, struct, from_unixtime, to_date,
    unix_timestamp, when, coalesce
)
from pyspark.sql.types import (
    StructType, StructField, StringType, LongType,
    IntegerType, TimestampType, BooleanType
)
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_spark_session():
    """
    Create Spark session with Iceberg and S3 support
    """
    logger.info("Creating Spark session with Iceberg support")

    spark = SparkSession.builder \
        .appName("Zeek-OCSF-Iceberg-Pipeline") \
        .config("spark.sql.extensions", "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions") \
        .config("spark.sql.catalog.demo", "org.apache.iceberg.spark.SparkCatalog") \
        .config("spark.sql.catalog.demo.type", "hive") \
        .config("spark.sql.catalog.demo.uri", "thrift://hive-metastore:9083") \
        .config("spark.sql.catalog.demo.warehouse", "s3a://iceberg-warehouse/") \
        .config("spark.sql.catalog.demo.io-impl", "org.apache.iceberg.aws.s3.S3FileIO") \
        .config("spark.hadoop.fs.s3a.endpoint", "http://minio:9000") \
        .config("spark.hadoop.fs.s3a.access.key", "minioadmin") \
        .config("spark.hadoop.fs.s3a.secret.key", "minioadmin") \
        .config("spark.hadoop.fs.s3a.path.style.access", "true") \
        .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "false") \
        .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \
        .config("spark.jars.packages",
                "org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.5.0,"
                "org.apache.hadoop:hadoop-aws:3.3.4,"
                "com.amazonaws:aws-java-sdk-bundle:1.12.262") \
        .getOrCreate()

    spark.sparkContext.setLogLevel("WARN")
    logger.info("Spark session created successfully")
    return spark


def create_ocsf_database(spark):
    """
    Create OCSF database and network_activity table if not exists
    """
    logger.info("Creating OCSF database and tables")

    # Create database
    spark.sql("CREATE DATABASE IF NOT EXISTS demo.security_data")
    logger.info("Database demo.security_data created/verified")

    # Create network_activity table (OCSF class 4001)
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS demo.security_data.network_activity (
        -- OCSF Metadata
        ocsf_version STRING,
        activity_name STRING,
        category_uid INT,
        category_name STRING,
        class_uid INT,
        class_name STRING,

        -- Time
        time BIGINT COMMENT 'Unix timestamp in milliseconds',
        event_date DATE COMMENT 'Partition key - date of event',

        -- Connection Info
        connection_info STRUCT<
            uid: STRING COMMENT 'Zeek connection UID',
            protocol_num: INT COMMENT 'Protocol number (6=TCP, 17=UDP)',
            protocol_name: STRING COMMENT 'Protocol name',
            service_name: STRING COMMENT 'Identified service',
            boundary: STRING COMMENT 'Network boundary (Internal/External)',
            direction: STRING COMMENT 'Traffic direction'
        >,

        -- Source Endpoint
        src_endpoint STRUCT<
            ip: STRING COMMENT 'Source IP address',
            port: INT COMMENT 'Source port',
            is_local: BOOLEAN COMMENT 'Is source IP local',
            mac: STRING COMMENT 'Source MAC address',
            country: STRING COMMENT 'Source country code',
            vlan_uid: STRING COMMENT 'VLAN ID'
        >,

        -- Destination Endpoint
        dst_endpoint STRUCT<
            ip: STRING COMMENT 'Destination IP address',
            port: INT COMMENT 'Destination port',
            is_local: BOOLEAN COMMENT 'Is destination IP local',
            mac: STRING COMMENT 'Destination MAC address',
            country: STRING COMMENT 'Destination country code',
            vlan_uid: STRING COMMENT 'VLAN ID'
        >,

        -- Traffic Stats
        traffic STRUCT<
            bytes_in: BIGINT COMMENT 'Bytes received (responder → originator)',
            bytes_out: BIGINT COMMENT 'Bytes sent (originator → responder)',
            packets_in: BIGINT COMMENT 'Packets received',
            packets_out: BIGINT COMMENT 'Packets sent',
            bytes_dropped: BIGINT COMMENT 'Missed bytes due to packet loss'
        >,

        -- Duration
        duration BIGINT COMMENT 'Connection duration in milliseconds',

        -- Detection
        activity_id INT COMMENT 'OCSF activity ID (from conn_state)',
        conn_state STRING COMMENT 'Zeek connection state',

        -- Application
        app STRING COMMENT 'Identified application',

        -- Additional Zeek-specific fields
        zeek_metadata STRUCT<
            log_name: STRING COMMENT 'Zeek log type (_path)',
            tunnel_parents: STRING COMMENT 'Tunnel parent connections',
            community_id: STRING COMMENT 'Community ID hash'
        >
    )
    USING iceberg
    PARTITIONED BY (event_date)
    TBLPROPERTIES (
        'format-version' = '2',
        'write.parquet.compression-codec' = 'snappy',
        'write.metadata.compression-codec' = 'gzip'
    )
    """

    spark.sql(create_table_sql)
    logger.info("Table demo.security_data.network_activity created/verified")


def read_zeek_conn_logs(spark, input_path):
    """
    Read Zeek conn logs from JSON

    Args:
        spark: SparkSession
        input_path: Path to Zeek JSON files

    Returns:
        DataFrame with Zeek conn logs
    """
    logger.info(f"Reading Zeek conn logs from {input_path}")

    # Read JSON with schema inference
    zeek_df = spark.read.json(input_path)

    record_count = zeek_df.count()
    logger.info(f"Read {record_count:,} Zeek conn records")

    return zeek_df


def transform_zeek_to_ocsf(zeek_df):
    """
    Transform Zeek conn logs to OCSF Network Activity (class 4001)

    Based on production SQL view: zeek_conn_ocsf.sql

    Args:
        zeek_df: DataFrame with Zeek conn logs

    Returns:
        DataFrame with OCSF schema
    """
    logger.info("Transforming Zeek logs to OCSF schema")

    # OCSF Network Activity (class 4001) transformation
    ocsf_df = zeek_df.select(
        # OCSF Metadata
        lit("1.4.0").alias("ocsf_version"),
        lit("Traffic").alias("activity_name"),
        lit(4).alias("category_uid"),
        lit("Network Activity").alias("category_name"),
        lit(4001).alias("class_uid"),
        lit("Network Activity").alias("class_name"),

        # Time (convert Zeek timestamp to milliseconds)
        (col("ts") * 1000).cast("bigint").alias("time"),
        to_date(from_unixtime(col("ts"))).alias("event_date"),

        # Connection Info
        struct(
            col("uid").alias("uid"),
            when(col("proto") == "tcp", 6)
                .when(col("proto") == "udp", 17)
                .when(col("proto") == "icmp", 1)
                .otherwise(0).alias("protocol_num"),
            col("proto").alias("protocol_name"),
            col("service").alias("service_name"),
            col("history").alias("boundary"),  # Simplified - production would need mapping
            lit("Unknown").alias("direction")   # Simplified - production would infer from IPs
        ).alias("connection_info"),

        # Source Endpoint
        struct(
            col("id.orig_h").alias("ip"),
            col("id.orig_p").cast("int").alias("port"),
            col("local_orig").cast("boolean").alias("is_local"),
            col("orig_l2_addr").alias("mac"),
            col("orig_cc").alias("country"),
            col("vlan").alias("vlan_uid")
        ).alias("src_endpoint"),

        # Destination Endpoint
        struct(
            col("id.resp_h").alias("ip"),
            col("id.resp_p").cast("int").alias("port"),
            col("local_resp").cast("boolean").alias("is_local"),
            col("resp_l2_addr").alias("mac"),
            col("resp_cc").alias("country"),
            col("inner_vlan").alias("vlan_uid")
        ).alias("dst_endpoint"),

        # Traffic Stats
        struct(
            col("resp_bytes").cast("bigint").alias("bytes_in"),
            col("orig_bytes").cast("bigint").alias("bytes_out"),
            col("resp_pkts").cast("bigint").alias("packets_in"),
            col("orig_pkts").cast("bigint").alias("packets_out"),
            col("missed_bytes").cast("bigint").alias("bytes_dropped")
        ).alias("traffic"),

        # Duration (convert to milliseconds)
        (col("duration") * 1000).cast("bigint").alias("duration"),

        # Activity (map conn_state to activity_id)
        lit(6).alias("activity_id"),  # Simplified - production would map conn_state
        col("conn_state").alias("conn_state"),

        # Application
        col("app").alias("app"),

        # Zeek Metadata
        struct(
            col("_path").alias("log_name"),
            col("tunnel_parents").alias("tunnel_parents"),
            col("community_id").alias("community_id")
        ).alias("zeek_metadata")
    )

    logger.info(f"Transformed {ocsf_df.count():,} records to OCSF schema")
    return ocsf_df


def write_to_iceberg(ocsf_df, table_name="demo.security_data.network_activity"):
    """
    Write OCSF DataFrame to Iceberg table

    Args:
        ocsf_df: DataFrame with OCSF schema
        table_name: Fully qualified Iceberg table name
    """
    logger.info(f"Writing OCSF data to Iceberg table: {table_name}")

    # Write to Iceberg using append mode
    ocsf_df.writeTo(table_name).append()

    logger.info("Data written to Iceberg successfully")


def show_sample_data(spark, table_name="demo.security_data.network_activity", limit=5):
    """
    Display sample data from Iceberg table
    """
    logger.info(f"Showing sample data from {table_name}")

    sample_df = spark.sql(f"""
        SELECT
            ocsf_version,
            activity_name,
            from_unixtime(time/1000) as event_time,
            src_endpoint.ip as source_ip,
            dst_endpoint.ip as dest_ip,
            connection_info.protocol_name,
            traffic.bytes_out,
            traffic.bytes_in,
            duration
        FROM {table_name}
        ORDER BY time DESC
        LIMIT {limit}
    """)

    sample_df.show(truncate=False)


def get_table_stats(spark, table_name="demo.security_data.network_activity"):
    """
    Display table statistics
    """
    logger.info(f"Getting statistics for {table_name}")

    stats = spark.sql(f"""
        SELECT
            COUNT(*) as total_records,
            COUNT(DISTINCT event_date) as unique_dates,
            COUNT(DISTINCT src_endpoint.ip) as unique_source_ips,
            COUNT(DISTINCT dst_endpoint.ip) as unique_dest_ips,
            SUM(traffic.bytes_in + traffic.bytes_out) as total_traffic_bytes
        FROM {table_name}
    """)

    stats.show(truncate=False)


def main():
    """
    Main pipeline execution
    """
    logger.info("Starting Zeek → OCSF → Iceberg pipeline")

    # Configuration
    ZEEK_INPUT_PATH = "/opt/spark-data/zeek_*.json"
    TABLE_NAME = "demo.security_data.network_activity"

    try:
        # Create Spark session
        spark = create_spark_session()

        # Create database and tables
        create_ocsf_database(spark)

        # Read Zeek logs
        zeek_df = read_zeek_conn_logs(spark, ZEEK_INPUT_PATH)

        # Transform to OCSF
        ocsf_df = transform_zeek_to_ocsf(zeek_df)

        # Write to Iceberg
        write_to_iceberg(ocsf_df, TABLE_NAME)

        # Show sample data
        show_sample_data(spark, TABLE_NAME)

        # Show statistics
        get_table_stats(spark, TABLE_NAME)

        logger.info("Pipeline completed successfully!")
        return 0

    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}", exc_info=True)
        return 1

    finally:
        if 'spark' in locals():
            spark.stop()


if __name__ == "__main__":
    sys.exit(main())
