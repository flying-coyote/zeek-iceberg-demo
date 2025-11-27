# Zeek → Iceberg → Dremio Demo Lab

**Production-validated demo** showing Cloudera Hive/Impala customers how to migrate to modern S3 + Iceberg lakehouse while maintaining Impala compatibility and adding OCSF standardization.

---

## 🚀 Quick Win Path (Working Now - 5 Minutes)

**Want to see it working immediately?** Use the simplified setup:

```
Sample Data → MinIO (S3) → Dremio (Direct S3 access)
```

**See:** [WORKING-SETUP.md](WORKING-SETUP.md) for the proven, tested configuration.

**What you get:**
- ✅ Working SQL queries in <5 minutes
- ✅ No Hive Metastore authentication issues
- ✅ Direct S3 → Dremio connection
- ✅ Sample data pre-generated (3,000 network activity records)
- ✅ Query acceleration via Reflections

**Critical success factor:** Enable the "Enable compatibility mode" checkbox in Dremio's S3 source configuration. [See solution guide](SOLUTION-COMPATIBILITY-MODE.md).

---

## Full Architecture Path (Advanced - 20 Minutes)

### Prerequisites

1. **Install Java** (required):
   ```bash
   sudo apt update
   sudo apt install -y openjdk-11-jdk
   java -version
   ```

2. **Verify Docker** (should already be installed):
   ```bash
   docker --version
   docker compose version
   ```

3. **Copy Zeek Sample Data**:
   ```bash
   cp ~/splunk-db-connect-benchmark/data/samples/zeek_*.json ~/zeek-iceberg-demo/data/
   ls -lh ~/zeek-iceberg-demo/data/
   ```

### Start the Stack

```bash
cd ~/zeek-iceberg-demo

# Start all services
docker compose up -d

# Watch logs (optional)
docker compose logs -f

# Check service health
docker compose ps
```

**Services will start on**:
- **MinIO Console**: http://localhost:9001 (user: `minioadmin`, password: `minioadmin`)
- **Spark Master UI**: http://localhost:8080
- **Dremio UI**: http://localhost:9047 (create admin account on first visit)
- **Jupyter Lab**: http://localhost:8888 (check logs for token)

### Load Data into Iceberg

```bash
# Run the Zeek → OCSF → Iceberg pipeline
docker exec zeek-demo-spark-master spark-submit \
  --master spark://spark-master:7077 \
  --deploy-mode client \
  --conf spark.sql.extensions=org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions \
  --conf spark.sql.catalog.demo=org.apache.iceberg.spark.SparkCatalog \
  --conf spark.sql.catalog.demo.type=hive \
  --conf spark.sql.catalog.demo.uri=thrift://hive-metastore:9083 \
  --conf spark.sql.catalog.demo.warehouse=s3a://iceberg-warehouse/ \
  --packages org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.5.0,org.apache.hadoop:hadoop-aws:3.3.4,com.amazonaws:aws-java-sdk-bundle:1.12.262 \
  /opt/spark-apps/zeek_to_ocsf_iceberg.py
```

### Query with Dremio

1. Open **Dremio UI**: http://localhost:9047
2. **First-time setup**: Create admin account
3. **Add Sources**:
   - **Hive**: Settings → Add Source → Hive
     - Name: `hive_metastore`
     - Hive Metastore URI: `thrift://hive-metastore:9083`
   - **S3 (MinIO)**: Settings → Add Source → S3
     - Name: `minio`
     - AWS Access Key: `minioadmin`
     - AWS Secret Key: `minioadmin`
     - Enable compatibility mode: ✓
     - Root Path: `/`
     - Connection Properties:
       - `fs.s3a.endpoint` = `http://minio:9000`
       - `fs.s3a.path.style.access` = `true`

4. **Navigate to table**:
   - Hive → `security_data` → `network_activity`

5. **Run query**:
   ```sql
   SELECT
     src_endpoint.ip as source_ip,
     dst_endpoint.ip as dest_ip,
     connection_info.protocol_name,
     SUM(traffic.bytes_out + traffic.bytes_in) as total_traffic
   FROM hive_metastore.security_data.network_activity
   WHERE event_date >= CURRENT_DATE - INTERVAL '7' DAY
   GROUP BY src_endpoint.ip, dst_endpoint.ip, connection_info.protocol_name
   ORDER BY total_traffic DESC
   LIMIT 20;
   ```

### Create Dremio Reflections (Materialized Views)

1. In Dremio, navigate to `hive_metastore.security_data.network_activity`
2. Click **Reflections** tab
3. Create **Aggregation Reflection**:
   - **Dimensions**: `src_endpoint.ip`, `dst_endpoint.ip`, `connection_info.protocol_name`, `event_date`
   - **Measures**: `SUM(traffic.bytes_in)`, `SUM(traffic.bytes_out)`, `COUNT(*)`
   - **Partition By**: `event_date`
   - **Sort By**: `src_endpoint.ip`

4. **Enable reflection** and wait for build (check status in Jobs)

5. **Re-run query** - Dremio will automatically use reflection for acceleration

## Architecture

```
Zeek Logs (JSON, 357MB)
    ↓
Transform to OCSF (PySpark)
    ↓
Write to Iceberg Tables
    ↓
Register with Hive Metastore
    ↓
Query Engines:
  - Dremio (with Reflections)
  - Impala (future: requires Iceberg-compatible build)
```

## Components

| Component | Purpose | Port |
|-----------|---------|------|
| **MinIO** | S3-compatible storage | 9000 (API), 9001 (Console) |
| **Hive Metastore** | Iceberg catalog | 9083 |
| **Spark** | ETL pipeline (Zeek → OCSF → Iceberg) | 8080 (UI), 7077 (Master) |
| **Dremio** | Query acceleration with reflections | 9047 (UI), 31010 (JDBC) |
| **Jupyter** | Interactive notebooks | 8888 |
| **PostgreSQL** | Hive Metastore backend | 5432 |

## OCSF Schema

The pipeline transforms Zeek conn logs to **OCSF Network Activity (class 4001)**:

```json
{
  "ocsf_version": "1.4.0",
  "category_uid": 4,
  "class_uid": 4001,
  "activity_name": "Traffic",
  "time": 1699886400123,
  "src_endpoint": {
    "ip": "192.168.1.100",
    "port": 49152
  },
  "dst_endpoint": {
    "ip": "93.184.216.34",
    "port": 443
  },
  "connection_info": {
    "protocol_name": "tcp",
    "service_name": "ssl"
  },
  "traffic": {
    "bytes_out": 5242,
    "bytes_in": 12451
  },
  "duration": 120500
}
```

## Demo Script

### Scene 1: The Problem (2 min)
"Cloudera customers need to modernize to S3 + Iceberg while maintaining Impala compatibility"

### Scene 2: The Data (5 min)
1. Show Zeek JSON logs (network traffic)
2. Explain OCSF standardization (vendor-neutral schema)
3. Run transformation pipeline

### Scene 3: The Pipeline (5 min)
1. Execute `zeek_to_ocsf_iceberg.py`
2. Show data written to MinIO S3
3. Verify Iceberg tables in Hive Metastore

### Scene 4: Query Acceleration (10 min)
1. Query with Dremio (raw data)
2. Create Reflection (materialized view)
3. Re-run query (accelerated by reflection)
4. Show performance improvement

### Scene 5: Impala Compatibility (5 min - Future)
1. Connect Impala to Hive Metastore
2. Run same queries from Impala
3. Demonstrate seamless migration path

## Production Deployment Considerations

### Scale Testing
- Load full Zeek dataset (not just samples)
- Benchmark query performance (P50, P95, P99)
- Test ingestion throughput (records/sec)

### High Availability
- Hive Metastore HA (multiple instances + ZooKeeper)
- MinIO distributed mode (4+ nodes for erasure coding)
- Spark cluster (multiple workers)

### Security
- RBAC (Dremio access controls)
- Encryption at rest (S3 server-side encryption)
- Encryption in transit (TLS for all services)
- Network segmentation (separate data/control planes)

### Monitoring
- Prometheus + Grafana
- Iceberg metadata metrics
- Query performance dashboards
- Data quality alerts

## Known Issues

### Hive Metastore PostgreSQL Authentication

**Issue:** Hive Metastore fails to connect to PostgreSQL with error:
```
The authentication type 10 is not supported
```

**Cause:** PostgreSQL scram-sha-256 authentication not compatible with Hive JDBC driver

**Workaround:** Use the **Quick Win Path** (Direct S3 access) instead of Hive catalog. See [WORKING-SETUP.md](WORKING-SETUP.md).

**Status:** Known issue, alternative architecture works perfectly.

---

## Troubleshooting

### Services won't start
```bash
# Check Docker resources
docker system df

# Check logs
docker compose logs <service_name>

# Restart specific service
docker compose restart <service_name>
```

### Can't connect to MinIO
```bash
# Test MinIO health
curl http://localhost:9000/minio/health/live

# Check buckets
docker exec zeek-demo-minio mc ls myminio
```

### Spark job fails
```bash
# Check Spark logs
docker logs zeek-demo-spark-master

# Verify data exists
ls -lh ~/zeek-iceberg-demo/data/

# Test Spark shell
docker exec -it zeek-demo-spark-master spark-shell
```

### Iceberg table not found
```bash
# Check Hive Metastore
docker exec -it zeek-demo-hive-metastore hive --service metatool -listFSRoot

# Verify S3 bucket
docker exec zeek-demo-minio mc ls myminio/iceberg-warehouse/
```

## Cleanup

```bash
# Stop all services
docker compose down

# Remove all data (WARNING: destructive)
docker compose down -v

# Remove Docker images
docker compose down --rmi all
```

## Next Steps

1. ✅ **Validate baseline demo** (Zeek → OCSF → Iceberg → Dremio)
2. 🔲 **Add Impala** (requires Iceberg-compatible Docker image)
3. 🔲 **Add more OCSF classes** (DNS 4003, HTTP 4002, SSH, etc.)
4. 🔲 **Performance benchmarking** (compare Reflection vs raw queries)
5. 🔲 **Scale testing** (millions of records)
6. 🔲 **Security hardening** (RBAC, encryption, audit logs)

## References

- **OCSF Schema**: https://schema.ocsf.io/
- **Apache Iceberg**: https://iceberg.apache.org/
- **Dremio Docs**: https://docs.dremio.com/
- **Zeek Logs**: https://docs.zeek.org/en/stable/log-formats.html
- **Production SQL Views**: `~/Zeek-to-OCSF-mapping/output-deliverables/sql-views/`

---

**Demo Status**: Ready for Testing 🚀
**Created**: 2025-11-26
**Owner**: Jeremy Wiley
**Purpose**: Cloudera migration POC (Hive/Impala → S3 + Iceberg + OCSF)
