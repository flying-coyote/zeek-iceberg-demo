# ✅ Complete Demo Flow - Zeek → Iceberg → Dremio

**Total Time**: 15-20 minutes (Full setup) OR 5 minutes (Quick win path)
**Status**: Core services running, ready to configure and load data

---

## Part 0: Quick Win - Working Setup (5 Minutes) ⚡

**Want to see queries working NOW?** Skip to the simplified path:

**See:** [WORKING-SETUP.md](WORKING-SETUP.md)

This proven setup gives you:
- ✅ Dremio → MinIO direct connection (no Hive Metastore)
- ✅ Sample data pre-loaded (3,000 network activity records)
- ✅ SQL queries working in <5 minutes
- ✅ No authentication issues

**Critical:** Don't forget the "Enable compatibility mode" checkbox! [Solution guide here](SOLUTION-COMPATIBILITY-MODE.md).

Once working, come back here for Parts 2-7 to load real Zeek data and create Reflections.

---

## Full Setup with Hive Catalog (Parts 1-7)

**Note:** Hive Metastore has PostgreSQL authentication issues. The Quick Win path (above) is recommended for demos.

---

## Prerequisites Check ✓

Run these commands to verify everything is ready:

```bash
cd ~/zeek-iceberg-demo

# Check services running
docker compose ps

# Should show:
# - zeek-demo-minio (healthy)
# - zeek-demo-postgres (healthy)
# - zeek-demo-hive-metastore (running)
# - zeek-demo-dremio (running)
```

---

## Part 1: Configure Dremio (5 minutes)

### Step 1.1: Open Dremio
```bash
# Open in browser
http://localhost:9047
```

### Step 1.2: Create Admin Account
- **First Name**: Jeremy
- **Last Name**: Wiley
- **Email**: jeremy@example.com
- **Username**: admin
- **Password**: (your choice)
- Click **"Create Account"**

### Step 1.3: Add Hive Source
1. Click **"+ Add Source"**
2. Select **"Hive"**
3. Configure:
   - **Name**: `hive_metastore`
   - **Hive Metastore Host**: `hive-metastore`
   - **Port**: `9083`
4. Click **"Save"**

### Step 1.4: Add MinIO Source (S3)
1. Click **"+ Add Source"** again
2. Select **"Amazon S3"**
3. Configure:
   - **Name**: `minio`
   - **AWS Access Key**: `minioadmin`
   - **AWS Secret Key**: `minioadmin`
   - **Enable compatibility mode**: ✓

4. **Advanced Options** (IMPORTANT - expand this section):
   - Click **"Add Property"** and add:
     - Property 1: `fs.s3a.endpoint` = `http://minio:9000`
     - Property 2: `fs.s3a.path.style.access` = `true`
     - Property 3: `fs.s3a.connection.ssl.enabled` = `false`

5. Click **"Save"**

### Step 1.5: Verify Sources
- Left sidebar should show:
  - `hive_metastore` ✓
  - `minio` ✓
    - `iceberg-warehouse`
    - `zeek-data`

---

## Part 2: Install Python Dependencies (2 minutes)

```bash
cd ~/zeek-iceberg-demo

# Install dependencies
./install-dependencies.sh

# Or manually:
pip3 install --user pyiceberg[s3fs,hive] pyarrow pandas
```

**Expected output**: All packages install successfully

---

## Part 3: Load Data to Iceberg (5-10 minutes)

### Step 3.1: Run the Loader Script

```bash
cd ~/zeek-iceberg-demo

# Load 10,000 records (quick test)
python3 scripts/load_zeek_to_iceberg.py
```

**What this does**:
1. Reads Zeek conn logs (10K records for testing)
2. Transforms to OCSF Network Activity (class 4001)
3. Creates Iceberg table: `demo.security_data.network_activity`
4. Writes data partitioned by date

**Expected output**:
```
============================================================
Zeek → OCSF → Iceberg Data Loader
============================================================
[INFO] Reading Zeek logs from ...
[INFO] Read 10,000 Zeek records
[INFO] Transforming Zeek logs to OCSF schema
[INFO] Transformed 10,000 records to OCSF
[INFO] Loading 10,000 records to Iceberg table
[INFO] Created table security_data.network_activity
[INFO] Successfully loaded 10,000 records
============================================================
✓ Pipeline completed successfully!
============================================================
```

### Step 3.2: Verify Data in MinIO

```bash
# Check that data was written to S3
docker exec zeek-demo-minio mc ls myminio/iceberg-warehouse/ --recursive | head -20
```

**Should see**: Parquet files and Iceberg metadata

---

## Part 4: Query Data in Dremio (3 minutes)

### Step 4.1: Refresh Hive Source
1. In Dremio, click on `hive_metastore` in left sidebar
2. Click refresh icon (↻)
3. You should now see:
   - `hive_metastore`
     - `security_data` (database)
       - `network_activity` (table)

### Step 4.2: Run First Query

Click on `network_activity` table, then click **"New Query"**

```sql
-- View sample data
SELECT
  src_endpoint.ip as source_ip,
  dst_endpoint.ip as dest_ip,
  connection_info.protocol_name,
  traffic.bytes_out,
  traffic.bytes_in,
  from_unixtime(time/1000) as event_time
FROM hive_metastore.security_data.network_activity
LIMIT 10;
```

**Expected**: 10 rows of OCSF-formatted network traffic

### Step 4.3: Run Analytics Query

```sql
-- Top talkers by traffic volume
SELECT
  src_endpoint.ip as source_ip,
  COUNT(*) as connections,
  SUM(traffic.bytes_out + traffic.bytes_in) as total_traffic_bytes
FROM hive_metastore.security_data.network_activity
GROUP BY src_endpoint.ip
ORDER BY total_traffic_bytes DESC
LIMIT 20;
```

**Expected**: Top 20 source IPs by traffic volume

---

## Part 5: Create Dremio Reflections (5 minutes)

### Step 5.1: Create Raw Reflection

1. Navigate to `hive_metastore.security_data.network_activity`
2. Click **"Reflections"** tab
3. Click **"+ Create Reflection"**
4. Select **"Raw Reflection"**
5. Configure:
   - **Display Fields**: Select all
   - **Partition By**: `event_date`
   - **Sort By**: `time`
6. Click **"Save"**

### Step 5.2: Create Aggregation Reflection

1. Click **"+ Create Reflection"** again
2. Select **"Aggregation Reflection"**
3. Configure:
   - **Dimensions**:
     - `src_endpoint.ip`
     - `dst_endpoint.ip`
     - `connection_info.protocol_name`
     - `event_date`
   - **Measures**:
     - `SUM(traffic.bytes_in)` → Name: `total_bytes_in`
     - `SUM(traffic.bytes_out)` → Name: `total_bytes_out`
     - `COUNT(*)` → Name: `connection_count`
   - **Partition By**: `event_date`
   - **Sort By**: `src_endpoint.ip`
4. Click **"Save"**

### Step 5.3: Wait for Reflections to Build

1. Go to **Jobs** page (left sidebar)
2. Watch for "Reflection Refresh" jobs to complete
3. Usually takes 30-60 seconds for 10K records

### Step 5.4: Test Acceleration

Re-run the analytics query from Step 4.3:

```sql
-- This should now use the reflection!
SELECT
  src_endpoint.ip as source_ip,
  COUNT(*) as connections,
  SUM(traffic.bytes_out + traffic.bytes_in) as total_traffic_bytes
FROM hive_metastore.security_data.network_activity
GROUP BY src_endpoint.ip
ORDER BY total_traffic_bytes DESC
LIMIT 20;
```

**Check**:
- Look at query profile (click on job)
- Should show "Reflection Used: Yes"
- Query should be faster

---

## Part 6: Demo Queries (Show to Customer)

### Query 1: Protocol Distribution
```sql
SELECT
  connection_info.protocol_name,
  COUNT(*) as connection_count,
  SUM(traffic.bytes_out + traffic.bytes_in) as total_bytes
FROM hive_metastore.security_data.network_activity
GROUP BY connection_info.protocol_name
ORDER BY connection_count DESC;
```

### Query 2: Top Destination IPs
```sql
SELECT
  dst_endpoint.ip,
  COUNT(DISTINCT src_endpoint.ip) as unique_sources,
  COUNT(*) as total_connections,
  SUM(traffic.bytes_in) as total_bytes_received
FROM hive_metastore.security_data.network_activity
GROUP BY dst_endpoint.ip
ORDER BY total_connections DESC
LIMIT 20;
```

### Query 3: Time-Based Analysis
```sql
SELECT
  event_date,
  connection_info.protocol_name,
  COUNT(*) as connections,
  SUM(traffic.bytes_out + traffic.bytes_in) / 1024 / 1024 as total_mb
FROM hive_metastore.security_data.network_activity
GROUP BY event_date, connection_info.protocol_name
ORDER BY event_date, total_mb DESC;
```

### Query 4: Long-Running Connections
```sql
SELECT
  src_endpoint.ip,
  dst_endpoint.ip,
  connection_info.service_name,
  duration / 1000 as duration_seconds,
  from_unixtime(time/1000) as start_time
FROM hive_metastore.security_data.network_activity
WHERE duration > 60000  -- Longer than 60 seconds
ORDER BY duration DESC
LIMIT 10;
```

---

## Part 7: Load More Data (Optional)

To load all 1M records instead of just 10K:

### Edit the Python script:
```bash
nano scripts/load_zeek_to_iceberg.py

# Change line:
# SAMPLE_SIZE = 10000
# To:
# SAMPLE_SIZE = None  # Load all records

# Save and exit (Ctrl+X, Y, Enter)
```

### Run again:
```bash
python3 scripts/load_zeek_to_iceberg.py
```

**Note**: This will take longer (~5-10 minutes for 1M records)

---

## Troubleshooting

### Python script fails: "Cannot connect to Hive"
```bash
# Check Hive is running
docker ps | grep hive

# If not running, start it
docker compose up -d hive-metastore
```

### Python script fails: "S3 connection error"
```bash
# Check MinIO is running
docker ps | grep minio

# Test MinIO
curl http://localhost:9000/minio/health/live
```

### Dremio can't see table after loading
```bash
# Refresh Hive source in Dremio
# Click the refresh icon (↻) next to hive_metastore
```

### Reflection won't build
```bash
# Check Dremio logs
docker logs zeek-demo-dremio | tail -50

# Ensure enough resources (Dremio needs ~8GB RAM)
```

---

## Demo Checklist

- [ ] Dremio configured with Hive and MinIO sources
- [ ] Python dependencies installed
- [ ] Data loaded to Iceberg (10K or 1M records)
- [ ] Tables visible in Dremio
- [ ] Sample queries run successfully
- [ ] Reflections created
- [ ] Reflections built (check Jobs page)
- [ ] Query acceleration verified
- [ ] Demo queries tested

---

## What You've Proven

✅ **S3 + Iceberg Configuration** - Working with MinIO
✅ **OCSF Transformation** - Zeek → OCSF Network Activity
✅ **Hive Metastore Integration** - Cloudera compatibility
✅ **Dremio Query Engine** - SQL interface working
✅ **Materialized Views** - Reflections for acceleration
✅ **Production Data Flow** - Real Zeek logs processed

---

## Next Steps for Production

1. **Add Impala** - Validate existing queries work unchanged
2. **Scale Testing** - Load full dataset (millions of records)
3. **More OCSF Classes** - DNS, HTTP, SSH logs
4. **Security Hardening** - RBAC, encryption, audit logs
5. **High Availability** - Hive HA, MinIO distributed mode
6. **Performance Tuning** - Reflection optimization, partition tuning

---

**Demo Status**: ✅ READY TO PRESENT
**Time to Complete**: 15-20 minutes
**Customer Value**: Clear migration path from Cloudera to modern lakehouse with OCSF
