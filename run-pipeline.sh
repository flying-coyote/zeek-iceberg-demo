#!/bin/bash
# Run Zeek → OCSF → Iceberg Data Pipeline

set -e  # Exit on error

echo "================================================"
echo "Zeek → OCSF → Iceberg Data Pipeline"
echo "================================================"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if services are running
echo -e "${YELLOW}[1/3] Checking services...${NC}"
if ! docker ps | grep -q zeek-demo-spark-master; then
    echo -e "${RED}ERROR: Spark Master is not running${NC}"
    echo "Please run: ./start-demo.sh"
    exit 1
fi
echo -e "${GREEN}✓ Services are running${NC}"
echo ""

# Submit Spark job
echo -e "${YELLOW}[2/3] Submitting Spark job...${NC}"
echo "This will:"
echo "  1. Read Zeek conn logs from data/*.json"
echo "  2. Transform to OCSF Network Activity (class 4001)"
echo "  3. Write to Iceberg table: demo.security_data.network_activity"
echo ""

docker exec zeek-demo-spark-master spark-submit \
  --master spark://spark-master:7077 \
  --deploy-mode client \
  --driver-memory 2g \
  --executor-memory 2g \
  --conf spark.sql.extensions=org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions \
  --conf spark.sql.catalog.demo=org.apache.iceberg.spark.SparkCatalog \
  --conf spark.sql.catalog.demo.type=hive \
  --conf spark.sql.catalog.demo.uri=thrift://hive-metastore:9083 \
  --conf spark.sql.catalog.demo.warehouse=s3a://iceberg-warehouse/ \
  --conf spark.sql.catalog.demo.io-impl=org.apache.iceberg.aws.s3.S3FileIO \
  --conf spark.hadoop.fs.s3a.endpoint=http://minio:9000 \
  --conf spark.hadoop.fs.s3a.access.key=minioadmin \
  --conf spark.hadoop.fs.s3a.secret.key=minioadmin \
  --conf spark.hadoop.fs.s3a.path.style.access=true \
  --conf spark.hadoop.fs.s3a.connection.ssl.enabled=false \
  --conf spark.hadoop.fs.s3a.impl=org.apache.hadoop.fs.s3a.S3AFileSystem \
  --packages org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.5.0,org.apache.hadoop:hadoop-aws:3.3.4,com.amazonaws:aws-java-sdk-bundle:1.12.262 \
  /opt/spark-apps/zeek_to_ocsf_iceberg.py

PIPELINE_STATUS=$?

echo ""
if [ $PIPELINE_STATUS -eq 0 ]; then
    echo -e "${GREEN}✓ Pipeline completed successfully!${NC}"
else
    echo -e "${RED}✗ Pipeline failed with status $PIPELINE_STATUS${NC}"
    exit $PIPELINE_STATUS
fi

echo ""
echo -e "${YELLOW}[3/3] Verifying data in MinIO...${NC}"
echo ""
docker exec zeek-demo-minio mc ls myminio/iceberg-warehouse/ --recursive | head -20

echo ""
echo "================================================"
echo -e "${GREEN}Data Successfully Loaded!${NC}"
echo "================================================"
echo ""
echo "Next Steps:"
echo ""
echo "1. Open Dremio: http://localhost:9047"
echo ""
echo "2. Add Hive Source:"
echo "   - Settings → Add Source → Hive"
echo "   - Name: hive_metastore"
echo "   - Hive Metastore URI: thrift://hive-metastore:9083"
echo ""
echo "3. Query the data:"
echo "   SELECT * FROM hive_metastore.security_data.network_activity LIMIT 10;"
echo ""
echo "4. Create Reflections for acceleration!"
echo ""
