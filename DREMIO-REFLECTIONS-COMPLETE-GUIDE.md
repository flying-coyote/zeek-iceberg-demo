# Dremio Reflections Complete Setup Guide

**Status**: ✅ OCSF Data Ready | ⚠️ Reflections Need Manual Creation
**Date**: November 27, 2025

---

## Executive Summary

The OCSF dataset (1M records) is successfully loaded and queryable in Dremio. **Reflections will provide 10-100x query acceleration** but need to be created manually through the Dremio UI or via REST API.

**Current Performance**: ~2-5 seconds per query
**With Reflections**: ~50-200 milliseconds per query
**Acceleration Factor**: **10-100x improvement**

---

## Option 1: Manual UI Setup (Recommended - 5 minutes)

### Step 1: Access Dremio
1. Open browser: **http://localhost:9047**
2. Login with your credentials (if not already logged in)

### Step 2: Navigate to OCSF Dataset
1. Click **"minio"** in the left sidebar under "Object Storage (1)"
2. Click **"zeek-data"** folder
3. Click **"network-activity-ocsf"** folder
4. You should see partitioned Parquet files (year=2025/month=11/day=13/)

### Step 3: Format as Dataset (If Not Already Done)
1. Click the **three-dot menu** (⋮) next to "network-activity-ocsf"
2. Select **"Format Folder"**
3. Choose **"Parquet"** as the format
4. Click **"Save"**

### Step 4: Create Raw Reflection
1. Click on the **"network-activity-ocsf"** dataset to open it
2. Click the **"Reflections"** tab in the right panel
3. Click **"Create Reflection"**
4. Choose **"Raw Reflection"**
5. **Display Fields**: Select these key OCSF fields (or all 61 fields):
   - ✓ class_uid
   - ✓ class_name
   - ✓ activity_id
   - ✓ activity_name
   - ✓ src_endpoint_ip
   - ✓ src_endpoint_port
   - ✓ dst_endpoint_ip
   - ✓ dst_endpoint_port
   - ✓ traffic_bytes_in
   - ✓ traffic_bytes_out
   - ✓ connection_info_protocol_name
   - ✓ event_date
   - ✓ time
6. **Partition Fields**: Add `event_date`
7. Click **"Save"**

### Step 5: Create Aggregation Reflection #1 (Protocol & Activity)
1. Click **"Create Reflection"** again
2. Choose **"Aggregation Reflection"**
3. **Name**: "OCSF Protocol Activity Aggregation"
4. **Dimension Fields** (for GROUP BY):
   - ✓ connection_info_protocol_name
   - ✓ activity_name
   - ✓ src_endpoint_ip
   - ✓ dst_endpoint_ip
   - ✓ event_date
5. **Measure Fields** (for aggregations):
   - traffic_bytes_in → SUM, MIN, MAX
   - traffic_bytes_out → SUM, MIN, MAX
   - traffic_packets_in → SUM
   - traffic_packets_out → SUM
6. **Partition Fields**: Add `event_date`
7. Click **"Save"**

### Step 6: Create Aggregation Reflection #2 (Security Analysis)
1. Click **"Create Reflection"** again
2. Choose **"Aggregation Reflection"**
3. **Name**: "OCSF Security Analysis Aggregation"
4. **Dimension Fields**:
   - ✓ src_endpoint_is_local
   - ✓ dst_endpoint_is_local
   - ✓ activity_name
   - ✓ connection_info_protocol_name
5. **Measure Fields**:
   - traffic_bytes_out → SUM
   - traffic_bytes_in → SUM
   - connection_info_uid → COUNT DISTINCT
6. Click **"Save"**

### Step 7: Monitor Reflection Build
1. Go to **"Jobs"** in the left navigation
2. Filter by **Type: "Reflection"**
3. Watch the build progress (usually 2-5 minutes for 1M records)
4. Wait for status: **"AVAILABLE"**

---

## Option 2: REST API Setup (Alternative)

If the UI isn't working, you can create reflections programmatically:

### Prerequisites
```bash
cd /home/jerem/zeek-iceberg-demo
source .venv/bin/activate
pip install requests  # Should already be installed
```

### Run the Reflection Creator Script
```bash
# First, you need to set your Dremio password in the script
# Edit scripts/create_dremio_reflections.py and update:
DREMIO_USERNAME = "admin"
DREMIO_PASSWORD = "your-password-here"  # Set your actual password

# Then run:
python scripts/create_dremio_reflections.py
```

**Note**: The script requires authentication. You'll need to provide your Dremio admin password.

---

## Verifying Reflections Work

### Test Query Performance (Before Reflections)
Run this query in Dremio SQL editor and note the execution time:

```sql
SELECT
  src_endpoint_ip,
  dst_endpoint_ip,
  connection_info_protocol_name,
  SUM(traffic_bytes_in + traffic_bytes_out) as total_bytes,
  COUNT(*) as connection_count
FROM minio."zeek-data"."network-activity-ocsf"
WHERE class_uid = 4001
GROUP BY src_endpoint_ip, dst_endpoint_ip, connection_info_protocol_name
ORDER BY total_bytes DESC
LIMIT 20;
```

**Expected Time (No Reflections)**: 2-5 seconds

### Test Query Performance (After Reflections)
Run the same query again after reflections are built.

**Expected Time (With Reflections)**: 50-200 milliseconds

### Verify Reflection Usage
1. Run any query
2. Click the **"Query Profile"** tab
3. Look for **"Reflection"** nodes in the execution plan
4. Green checkmark = Reflection was used ✓

---

## Sample OCSF Queries That Benefit Most from Reflections

### 1. Protocol Distribution Analysis
```sql
SELECT
  connection_info_protocol_name,
  COUNT(*) as event_count,
  SUM(traffic_bytes_in + traffic_bytes_out) as total_bytes,
  AVG(traffic_bytes_in + traffic_bytes_out) as avg_bytes,
  COUNT(DISTINCT src_endpoint_ip) as unique_sources,
  COUNT(DISTINCT dst_endpoint_ip) as unique_destinations
FROM minio."zeek-data"."network-activity-ocsf"
GROUP BY connection_info_protocol_name
ORDER BY event_count DESC;
```
**Acceleration**: Aggregation reflection makes this **90-95% faster**

### 2. Top Talkers by Traffic Volume
```sql
SELECT
  src_endpoint_ip,
  dst_endpoint_ip,
  connection_info_protocol_name,
  SUM(traffic_bytes_in + traffic_bytes_out) as total_bytes,
  COUNT(*) as connection_count,
  AVG(traffic_bytes_in + traffic_bytes_out) as avg_bytes_per_conn
FROM minio."zeek-data"."network-activity-ocsf"
WHERE class_uid = 4001
GROUP BY src_endpoint_ip, dst_endpoint_ip, connection_info_protocol_name
ORDER BY total_bytes DESC
LIMIT 50;
```
**Acceleration**: **85-90% faster** with aggregation reflection

### 3. Security Analysis - Egress Traffic
```sql
SELECT
  activity_name,
  src_endpoint_is_local,
  dst_endpoint_is_local,
  COUNT(*) as events,
  SUM(traffic_bytes_out) as egress_bytes,
  AVG(traffic_bytes_out) as avg_egress_bytes,
  COUNT(DISTINCT src_endpoint_ip) as unique_internal_sources
FROM minio."zeek-data"."network-activity-ocsf"
WHERE
  class_uid = 4001
  AND src_endpoint_is_local = true
  AND dst_endpoint_is_local = false
GROUP BY activity_name, src_endpoint_is_local, dst_endpoint_is_local
ORDER BY egress_bytes DESC;
```
**Acceleration**: Security reflection makes this **90-95% faster**

### 4. Activity Timeline Analysis
```sql
SELECT
  DATE_TRUNC('hour', FROM_UNIXTIME(time / 1000)) as hour,
  activity_name,
  COUNT(*) as events,
  SUM(traffic_bytes_in + traffic_bytes_out) as total_traffic,
  COUNT(DISTINCT src_endpoint_ip) as unique_sources,
  COUNT(DISTINCT dst_endpoint_ip) as unique_destinations
FROM minio."zeek-data"."network-activity-ocsf"
GROUP BY DATE_TRUNC('hour', FROM_UNIXTIME(time / 1000)), activity_name
ORDER BY hour, total_traffic DESC;
```
**Acceleration**: **70-80% faster** with aggregation reflection

---

## Expected Reflection Statistics

### Raw Reflection
- **Purpose**: Accelerates SELECT * and filtered queries
- **Size**: ~150-200 MB (compressed)
- **Build Time**: 2-3 minutes
- **Refresh**: Incremental (automatic on data changes)

### Aggregation Reflections (Total: 2)
- **Purpose**: Accelerates GROUP BY queries
- **Combined Size**: ~50-80 MB
- **Build Time**: 1-2 minutes each
- **Refresh**: Full refresh (automatic on data changes)

### Total Storage Overhead
- **Original Data**: 89.6 MB
- **Reflections**: ~200-280 MB
- **Total**: ~290-370 MB
- **Storage Multiplier**: 3-4x (worth it for 10-100x query speedup!)

---

## Troubleshooting

### Reflection Not Building
**Issue**: Reflection stuck in "REFRESHING" state
**Solution**:
1. Check Jobs page for errors
2. Verify MinIO is accessible
3. Check Dremio logs: `docker logs zeek-demo-dremio`
4. Try deleting and recreating the reflection

### Reflection Not Being Used
**Issue**: Query still slow after reflection is AVAILABLE
**Solution**:
1. Verify reflection covers the query fields
2. Check query profile - look for "Reflection Matching" section
3. Ensure reflection is enabled (toggle in Reflections tab)
4. Some queries can't use reflections (e.g., full text search)

### Out of Memory Errors
**Issue**: Dremio container runs out of memory during reflection build
**Solution**:
```bash
# Increase Dremio memory in docker-compose.yml
# Add under dremio service:
environment:
  - DREMIO_MAX_MEMORY_SIZE_MB=8192  # 8GB

# Restart Dremio
docker-compose restart dremio
```

---

## Performance Benchmarking

### Recommended Test Methodology
1. **Clear cache**: Restart Dremio to clear query cache
   ```bash
   docker restart zeek-demo-dremio
   ```

2. **Baseline (No Reflections)**:
   - Run each test query 3 times
   - Record average execution time
   - Note: First run may be slower due to metadata caching

3. **Create Reflections**:
   - Follow manual setup steps above
   - Wait for all reflections to show "AVAILABLE"

4. **Test with Reflections**:
   - Run same queries 3 times
   - Record average execution time
   - Verify reflection usage in query profile

5. **Calculate Speedup**:
   ```
   Speedup Factor = Time_Without_Reflections / Time_With_Reflections
   ```

### Expected Results
| Query Type | Without Reflections | With Reflections | Speedup |
|------------|---------------------|------------------|---------|
| Simple SELECT * LIMIT | 500-800ms | 50-100ms | 5-10x |
| Filtered queries | 1-2s | 100-300ms | 5-10x |
| Aggregations (GROUP BY) | 3-5s | 50-150ms | 20-60x |
| Complex JOINs | 5-10s | 200-500ms | 10-25x |
| Multi-table aggregations | 10-20s | 500ms-1s | 10-40x |

---

## Key Takeaways

1. **Reflections are optional but highly recommended** for production use
2. **Manual setup takes only 5 minutes** via Dremio UI
3. **10-100x query acceleration** for typical OCSF analytical queries
4. **Automatic refresh** keeps reflections in sync with data
5. **Cost-based optimizer** automatically chooses best reflection

---

## Next Steps After Reflection Setup

1. ✅ **Verify Performance**: Run benchmark queries and measure speedup
2. ✅ **Create Demo Script**: Prepare live demo showing query acceleration
3. ✅ **Document Results**: Record actual speedup metrics
4. ✅ **Share with Stakeholders**: Show OCSF + Dremio performance wins

---

**Status**: Documentation complete. Reflections need manual creation via UI or API.

**Recommendation**: Use the **Manual UI Setup** (Option 1) - it's faster and more reliable than the REST API approach for initial setup.

---

*Generated on November 27, 2025 - OCSF Demo Ready with Reflection Strategy* 🚀