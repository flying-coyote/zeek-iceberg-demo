#!/bin/bash
# Zeek → Iceberg → Dremio Demo - Startup Script

set -e  # Exit on error

echo "================================================"
echo "Zeek → Iceberg → Dremio Demo Lab"
echo "================================================"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check Docker
echo -e "${YELLOW}[1/6] Checking Docker...${NC}"
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}ERROR: Docker is not running${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Docker is running${NC}"
echo ""

# Check Java
echo -e "${YELLOW}[2/6] Checking Java...${NC}"
if ! java -version > /dev/null 2>&1; then
    echo -e "${YELLOW}WARNING: Java not found. Installing...${NC}"
    echo "Please run: sudo apt update && sudo apt install -y openjdk-11-jdk"
    echo "Then re-run this script"
    exit 1
fi
echo -e "${GREEN}✓ Java is installed${NC}"
echo ""

# Check data files
echo -e "${YELLOW}[3/6] Checking Zeek sample data...${NC}"
DATA_FILES=$(find data/ -name "*.json" 2>/dev/null | wc -l)
if [ "$DATA_FILES" -eq 0 ]; then
    echo -e "${RED}ERROR: No Zeek JSON files found in data/ directory${NC}"
    echo "Please run: cp ~/splunk-db-connect-benchmark/data/samples/zeek_*.json ~/zeek-iceberg-demo/data/"
    exit 1
fi
echo -e "${GREEN}✓ Found $DATA_FILES Zeek JSON file(s)${NC}"
ls -lh data/*.json
echo ""

# Start Docker Compose
echo -e "${YELLOW}[4/6] Starting Docker Compose stack...${NC}"
docker compose up -d

echo ""
echo -e "${YELLOW}[5/6] Waiting for services to be healthy...${NC}"
echo "This may take 30-60 seconds..."

# Wait for MinIO
echo -n "  - MinIO: "
for i in {1..30}; do
    if curl -s http://localhost:9000/minio/health/live > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC}"
        break
    fi
    sleep 2
done

# Wait for Hive Metastore
echo -n "  - Hive Metastore: "
for i in {1..60}; do
    if docker exec zeek-demo-hive-metastore pgrep -f metastore > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC}"
        break
    fi
    sleep 2
done

# Wait for Spark Master
echo -n "  - Spark Master: "
for i in {1..30}; do
    if curl -s http://localhost:8080 > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC}"
        break
    fi
    sleep 2
done

# Wait for Dremio
echo -n "  - Dremio: "
for i in {1..60}; do
    if curl -s http://localhost:9047 > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC}"
        break
    fi
    sleep 2
done

echo ""
echo -e "${YELLOW}[6/6] Service Status${NC}"
docker compose ps
echo ""

echo "================================================"
echo -e "${GREEN}Demo Lab Started Successfully!${NC}"
echo "================================================"
echo ""
echo "Access the following services:"
echo ""
echo "  🗂️  MinIO Console:   http://localhost:9001"
echo "      User: minioadmin / Password: minioadmin"
echo ""
echo "  ⚡ Spark Master UI: http://localhost:8080"
echo ""
echo "  🚀 Dremio UI:       http://localhost:9047"
echo "      (Create admin account on first visit)"
echo ""
echo "  📓 Jupyter Lab:     http://localhost:8888"
echo "      (Check logs for token: docker logs zeek-demo-jupyter)"
echo ""
echo "================================================"
echo "Next Steps:"
echo "================================================"
echo ""
echo "1. Load data into Iceberg:"
echo "   ./run-pipeline.sh"
echo ""
echo "2. Query with Dremio:"
echo "   Open http://localhost:9047"
echo "   Add Hive source (URI: thrift://hive-metastore:9083)"
echo "   Navigate to: security_data.network_activity"
echo ""
echo "3. View logs:"
echo "   docker compose logs -f"
echo ""
echo "4. Stop demo:"
echo "   docker compose down"
echo ""
