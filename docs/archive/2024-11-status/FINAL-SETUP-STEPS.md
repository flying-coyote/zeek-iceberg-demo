# Final Dremio Setup Steps - Manual Guide

**Date**: November 27, 2025
**Status**: 🟢 OCSF Data Loaded - 2 Quick Steps Remaining

---

## Current State Summary

### ✅ Completed (You're 90% Done!)

1. **Infrastructure Running**: All Docker containers healthy
2. **OCSF Data Loaded**: 100,000 records in MinIO `s3://zeek-data/network-activity-ocsf/`
3. **MinIO Source Configured**: Dremio can see the `minio` source with both buckets
4. **You're Logged In**: Dremio session active at http://localhost:9047

### ⏳ Remaining (10 Minutes Total)

1. **Format OCSF Dataset** (2 minutes)
2. **Create Reflections** (3 minutes setup + 5 minutes build time)

---

## Step 1: Format the OCSF Dataset (2 minutes)

### Navigate to Dataset
1. In Dremio left sidebar, expand **"Object Storage (1)"**
2. Click **"minio"**
3. Click **"zeek-data"** folder
4. You should see **"network-activity-ocsf"** folder

### Format as Parquet
1. Hover over **"network-activity-ocsf"** folder
2. Click the **⋯ (three dots)** menu icon
3. Select **"Format Folder"**

4. In the Format dialog:
   - **Format Type**: Select **"Parquet"**
   - **Partition Fields** (optional but recommended):
     - Add `year`
     - Add `month`
     - Add `day`
   - Click **"Save"**

### Verify Formatting Worked
1. After saving, you should see **"network-activity-ocsf"** appear as a dataset (folder icon changes to table icon)
2. Click on it to open
3. You should see the OCSF schema with 65 fields
4. Run a test query:
   ```sql
   SELECT * FROM minio."zeek-data"."network-activity-ocsf" LIMIT 10;
   ```
5. Should return 10 OCSF records instantly

**Expected Result**: Query returns 10 rows with OCSF fields like `class_uid`, `src_endpoint_ip`, `dst_endpoint_ip`, `traffic_bytes_in`, etc.

---

## Step 2: Create Reflections (8 minutes total)

Reflections provide 10-100x query acceleration. Create 3 reflections:

### Reflection 1: Raw Reflection (Fast Field Access)

1. While viewing the `network-activity-ocsf` dataset, click the **"Reflections"** tab at the top
2. Click **"New Reflection"**
3. Select **"Raw Reflections"**

**Configure Raw Reflection**:
- **Name**: `OCSF Raw Reflection`
- **Display Fields** (select these 13 fields from the list):
  - `class_uid`
  - `class_name`
  - `activity_id`
  - `activity_name`
  - `src_endpoint_ip`
  - `src_endpoint_port`
  - `dst_endpoint_ip`
  - `dst_endpoint_port`
  - `traffic_bytes_in`
  - `traffic_bytes_out`
  - `connection_info_protocol_name`
  - `event_date`
  - `time`

- **Partition Fields**:
  - Add `event_date`

- **Sort Fields**: (leave empty for now)

4. Click **"Save"**

---

### Reflection 2: Protocol Activity Aggregation

1. Click **"New Reflection"** again
2. Select **"Aggregation Reflections"**

**Configure Aggregation**:
- **Name**: `OCSF Protocol Activity Aggregation`

- **Dimensions** (group by these fields):
  - `connection_info_protocol_name`
  - `activity_name`
  - `src_endpoint_ip`
  - `dst_endpoint_ip`

- **Measures** (aggregate these fields):
  - `traffic_bytes_in`:
    - Check: SUM, MIN, MAX
  - `traffic_bytes_out`:
    - Check: SUM, MIN, MAX

3. Click **"Save"**

---

### Reflection 3: Security Analysis Aggregation

1. Click **"New Reflection"** again
2. Select **"Aggregation Reflections"**

**Configure Aggregation**:
- **Name**: `OCSF Security Analysis Aggregation`

- **Dimensions**:
  - `src_endpoint_is_local`
  - `dst_endpoint_is_local`
  - `activity_name`
  - `connection_info_protocol_name`

- **Measures**:
  - `traffic_bytes_in`:
    - Check: SUM
  - `traffic_bytes_out`:
    - Check: SUM

3. Click **"Save"**

---

## Step 3: Monitor Reflection Build (5 minutes)

### Watch Build Progress
1. Click **"Jobs"** in the top navigation (or left sidebar)
2. Filter by **Job Type: "Reflection"** or **"Build Reflection"**
3. You should see 3 reflection build jobs in progress

**Expected Timeline** (for 100K records):
- **Raw Reflection**: 1-2 minutes
- **Aggregation 1**: 2-3 minutes
- **Aggregation 2**: 1-2 minutes

**Total**: 4-7 minutes for all reflections to complete

### Verify Success
All 3 jobs should show status: **"COMPLETED"**

If any fail:
- Click on the failed job to see error details
- Common issues:
  - Field doesn't exist in schema (typo in field name)
  - Insufficient memory (Dremio configured with 8GB, should be OK)
  - Dataset not formatted correctly (go back to Step 1)

---

## Step 4: Test Query Performance (2 minutes)

### Baseline Query (Without Reflections)
Before reflections, this query would take ~500ms on 100K records.

### Accelerated Query (With Reflections)
Run this query to test reflection acceleration:

```sql
SELECT
  activity_name,
  class_name,
  COUNT(*) as events,
  SUM(traffic_bytes_in + traffic_bytes_out) as total_bytes,
  COUNT(DISTINCT src_endpoint_ip) as unique_sources
FROM minio."zeek-data"."network-activity-ocsf"
WHERE category_uid = 4
GROUP BY activity_name, class_name
ORDER BY total_bytes DESC;
```

**Expected Results**:
- **Query Time**: <100ms (was ~500ms before)
- **Acceleration**: 5-10x faster
- **Dremio UI**: Shows "Accelerated" indicator (green lightning bolt)
- **Data**: Breakdown of traffic by activity type

### More Test Queries

**Top Talkers** (uses Protocol Activity reflection):
```sql
SELECT
  src_endpoint_ip,
  dst_endpoint_ip,
  connection_info_protocol_name,
  SUM(traffic_bytes_in + traffic_bytes_out) as total_bytes,
  COUNT(*) as connections
FROM minio."zeek-data"."network-activity-ocsf"
WHERE class_uid = 4001
GROUP BY src_endpoint_ip, dst_endpoint_ip, connection_info_protocol_name
ORDER BY total_bytes DESC
LIMIT 20;
```

**Security Analysis** (uses Security Analysis reflection):
```sql
SELECT
  activity_name,
  src_endpoint_is_local,
  dst_endpoint_is_local,
  COUNT(*) as events,
  SUM(traffic_bytes_out) as egress_bytes
FROM minio."zeek-data"."network-activity-ocsf"
WHERE
  class_uid = 4001
  AND src_endpoint_is_local = true
  AND dst_endpoint_is_local = false
GROUP BY activity_name, src_endpoint_is_local, dst_endpoint_is_local
ORDER BY egress_bytes DESC;
```

---

## Success Criteria

After completing all steps, you should have:

### ✅ Infrastructure
- Dremio connected to MinIO
- OCSF dataset formatted and queryable
- 3 reflections: AVAILABLE status

### ✅ Performance
- Queries running in <100ms (was ~500ms)
- "Accelerated" indicator showing in query results
- 5-100x speedup depending on query type

### ✅ Demo-Ready
- 100,000 OCSF-compliant records
- Production-grade Parquet optimization
- Reflection-accelerated analytics
- Real Zeek network traffic data
- OCSF 1.0+ field naming conventions

---

## Troubleshooting

### "Cannot see network-activity-ocsf folder"
- **Verify data exists**: Run from terminal:
  ```bash
  docker exec zeek-demo-minio mc ls local/zeek-data/network-activity-ocsf/
  ```
  Should show: `9.1MiB STANDARD ...data.parquet`

- **Refresh Dremio catalog**:
  - Right-click on `zeek-data` folder
  - Select "Refresh Metadata"
  - Wait 10 seconds
  - Refresh browser page

### "Format Folder" fails
- **Check MinIO connection**:
  - Click "minio" source in sidebar
  - Click gear icon → "Edit Source"
  - Verify connection settings:
    - Access Key: `minioadmin`
    - Secret Key: `minioadmin`
    - Advanced Properties must include:
      - `fs.s3a.endpoint` = `http://minio:9000`
      - `fs.s3a.path.style.access` = `true`
      - `fs.s3a.connection.ssl.enabled` = `false`

### "Reflection build fails"
- **Check field names**: OCSF fields are case-sensitive
  - Use `traffic_bytes_in` not `Traffic_Bytes_In`
  - Use `src_endpoint_ip` not `src_ip`

- **Verify schema**: Run this query to see actual field names:
  ```sql
  SELECT * FROM minio."zeek-data"."network-activity-ocsf" LIMIT 1;
  ```

- **Check memory**: Dremio needs sufficient RAM
  ```bash
  docker stats zeek-demo-dremio
  ```
  Should show <8GB memory usage

### Query still slow after reflections
- **Wait for build to complete**: Jobs must show "COMPLETED" not "RUNNING"
- **Check acceleration indicator**: Query results should show green lightning bolt
- **Verify reflection matches query**: Reflection must include fields used in query
- **Clear and refresh**: Sometimes Dremio needs a refresh:
  ```sql
  ALTER TABLE minio."zeek-data"."network-activity-ocsf" REFRESH METADATA;
  ```

---

## Alternative: Automated Setup (If You Want)

If you'd prefer to automate reflection creation via script:

### Set Password Environment Variable
```bash
export DREMIO_PASSWORD="your-password-here"
```

### Run Reflection Script
```bash
cd /home/jerem/zeek-iceberg-demo
.venv/bin/python3 scripts/setup_reflections_simple.py
```

**Pros**: Faster, less clicking
**Cons**: Less understanding of what's happening

**However**, you still need to manually format the dataset first (Step 1) before running the script.

---

## What You've Accomplished

This demo shows a production-quality data pipeline:

1. **Real Zeek Data**: 100K actual network logs
2. **OCSF Transformation**: Industry-standard schema
3. **Parquet Optimization**: Columnar storage for analytics
4. **S3-Compatible Storage**: MinIO (production uses AWS S3)
5. **Query Acceleration**: Dremio reflections (10-100x speedup)
6. **SQL Analytics**: Standard SQL queries on security data

**This is a complete modern data stack for cybersecurity!**

---

## Next Steps After This

Once reflections are working:

1. **Scale to 1M records**: Run loader with `--all` flag
2. **Add more queries**: Explore OCSF fields
3. **Try Iceberg tables**: For better schema evolution
4. **Test Impala**: Alternative query engine (deferred earlier)
5. **Benchmark Trino**: Compare query performance (deferred earlier)

---

## Files for Reference

| File | Purpose |
|------|---------|
| `CURRENT-STATUS.md` | Current overall status |
| `DREMIO-SETUP-GUIDE.md` | Complete setup guide |
| `DREMIO-REFLECTION-GUIDE.md` | Detailed reflection docs |
| `FINAL-SETUP-STEPS.md` | This file - final manual steps |
| `scripts/setup_reflections_simple.py` | Automated reflection script |

---

**You're on the last 10 minutes of a complete OCSF data lake demo. Let's finish this!**

### Quick Checklist:
- [ ] Format dataset (2 min)
- [ ] Create 3 reflections (3 min)
- [ ] Wait for builds (5 min)
- [ ] Test queries (2 min)

**Total: ~12 minutes to completion!**
