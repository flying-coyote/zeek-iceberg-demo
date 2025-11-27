# Quick Start Guide - 5 Minutes to Running Demo

## Prerequisites Check

```bash
# Check Docker (must be running)
docker ps

# Check Java (required for Spark/Hive)
java -version

# If Java not installed:
sudo apt update && sudo apt install -y openjdk-11-jdk
```

## Step 1: Start the Demo (2 minutes)

```bash
cd ~/zeek-iceberg-demo
./start-demo.sh
```

**What this does**:
- Starts MinIO (S3 storage)
- Starts Hive Metastore (Iceberg catalog)
- Starts Spark (data processing)
- Starts Dremio (query acceleration)
- Creates necessary S3 buckets
- Waits for all services to be healthy

**You'll see**:
```
================================================
Demo Lab Started Successfully!
================================================

Access the following services:

  🗂️  MinIO Console:   http://localhost:9001
      User: minioadmin / Password: minioadmin

  ⚡ Spark Master UI: http://localhost:8080

  🚀 Dremio UI:       http://localhost:9047
      (Create admin account on first visit)
```

## Step 2: Load Data (2 minutes)

```bash
./run-pipeline.sh
```

**What this does**:
- Reads Zeek conn logs (393MB, ~1M records)
- Transforms to OCSF Network Activity schema
- Writes to Iceberg table on S3
- Registers with Hive Metastore

**You'll see**:
```
[INFO] Read 1,000,000 Zeek conn records
[INFO] Transformed 1,000,000 records to OCSF schema
[INFO] Data written to Iceberg successfully
✓ Pipeline completed successfully!
```

## Step 3: Query with Dremio (1 minute)

1. **Open Dremio**: http://localhost:9047
2. **First-time setup**: Create admin account (any email/password)
3. **Add Hive Source**:
   - Click **Add Source**
   - Select **Hive**
   - Name: `hive_metastore`
   - Hive Metastore Host: `hive-metastore`
   - Port: `9083`
   - Click **Save**

4. **Run Query**:
   ```sql
   SELECT
     src_endpoint.ip as source_ip,
     dst_endpoint.ip as dest_ip,
     connection_info.protocol_name,
     COUNT(*) as connections,
     SUM(traffic.bytes_out + traffic.bytes_in) as total_traffic
   FROM hive_metastore.security_data.network_activity
   GROUP BY src_endpoint.ip, dst_endpoint.ip, connection_info.protocol_name
   ORDER BY total_traffic DESC
   LIMIT 20;
   ```

## Troubleshooting

### "Docker is not running"
```bash
# Start Docker Desktop
# OR restart Docker service
sudo systemctl restart docker
```

### "Java not found"
```bash
sudo apt update
sudo apt install -y openjdk-11-jdk
```

### "No Zeek JSON files found"
```bash
# Copy sample data
cp ~/splunk-db-connect-benchmark/data/samples/zeek_*.json ~/zeek-iceberg-demo/data/
```

### Services won't start
```bash
# Check Docker resources (need ~25GB RAM)
docker system df

# View logs
docker compose logs -f

# Restart specific service
docker compose restart <service_name>
```

### Pipeline fails
```bash
# Check Spark logs
docker logs zeek-demo-spark-master

# Check Hive Metastore
docker logs zeek-demo-hive-metastore

# Verify MinIO buckets
docker exec zeek-demo-minio mc ls myminio
```

## Stop the Demo

```bash
# Stop services (keep data)
docker compose down

# Stop and remove all data
docker compose down -v
```

## What's Next?

### Create Dremio Reflections (Materialized Views)

1. In Dremio, navigate to `hive_metastore.security_data.network_activity`
2. Click **Reflections** tab
3. Create **Aggregation Reflection**:
   - Dimensions: `src_endpoint.ip`, `dst_endpoint.ip`, `connection_info.protocol_name`
   - Measures: `SUM(traffic.bytes_in)`, `SUM(traffic.bytes_out)`, `COUNT(*)`
4. Re-run query → automatically accelerated!

### Add More OCSF Classes

Extend the pipeline to support:
- DNS Activity (OCSF 4003) - `zeek_dns_ocsf.sql`
- HTTP Activity (OCSF 4002) - `zeek_http_ocsf.sql`
- SSH Activity - `zeek_ssh_ocsf.sql`

SQL views available at: `~/Zeek-to-OCSF-mapping/output-deliverables/sql-views/`

### Performance Testing

```bash
# Load larger dataset
cp ~/splunk-db-connect-benchmark/data/samples/zeek_1000000_*.json ~/zeek-iceberg-demo/data/

# Re-run pipeline
./run-pipeline.sh

# Benchmark queries in Dremio
```

### Production Deployment

See `README.md` for:
- High availability configuration
- Security hardening (RBAC, encryption)
- Monitoring setup (Prometheus + Grafana)
- Scale testing recommendations

---

**Total Time**: ~5 minutes
**Data Loaded**: ~1 million Zeek network connections
**Query Ready**: OCSF-standardized security data on Iceberg lakehouse
