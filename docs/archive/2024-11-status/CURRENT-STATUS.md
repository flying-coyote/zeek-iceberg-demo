# Zeek → OCSF → Dremio Demo - Current Status

**Date**: November 27, 2025
**Status**: 🟡 Data Recovered - Ready for Dremio Configuration

---

## ✅ Completed Steps

### 1. Infrastructure Running
All Docker containers healthy and communicating:
```
✅ zeek-demo-minio      - S3-compatible storage
✅ zeek-demo-dremio     - Query acceleration engine
✅ zeek-demo-hive       - Metastore (not actively used)
✅ zeek-demo-postgres   - Hive metastore backend
```

### 2. OCSF Data Loaded to MinIO

**Location**: `s3://zeek-data/network-activity-ocsf/`
```
9.1 MB - year=2025/month=11/day=13/data.parquet
100,000 OCSF-compliant records
65 OCSF fields implemented
Partitioned by event_date
```

**OCSF Schema Compliance**:
- ✅ Class UID: 4001 (Network Activity)
- ✅ Category UID: 4 (Network Activity)
- ✅ 65 OCSF fields with correct semantics
- ✅ RFC3339 timestamps
- ✅ OCSF 1.0+ field naming conventions

**Data Quality**:
```
Protocol Distribution:
- TCP: 89,229 (89.2%)
- UDP: 9,017 (9.0%)
- ICMP: 1,754 (1.8%)

Top Activities:
- Traffic: 30,043 (30.0%)
- http: 24,859 (24.9%)
- ssl: 24,853 (24.9%)
- dns: 10,636 (10.6%)
- ssh: 3,943 (3.9%)
```

### 3. Networking Fixed
- ✅ All containers on `zeek-demo-net` network
- ✅ Dremio can communicate with MinIO
- ✅ No more `SdkClientException` errors

---

## ⏳ Remaining Steps (15 minutes)

### Step 1: Login to Dremio (1 minute)

**Access**: http://localhost:9047

**Credentials**:
- Username: `flying-coyote`
- Password: (your password)

**Expected**: Login successful, see Dremio home page

---

### Step 2: Add MinIO Source (3 minutes)

**Manual Configuration** (recommended for first time):

1. Click **"+ Add Source"** (top right)
2. Select **"Amazon S3"**
3. Configure:

**General**:
- **Name**: `minio`

**Authentication**:
- **AWS Access Key**: `minioadmin`
- **AWS Secret Key**: `minioadmin`

**Advanced Options** (EXPAND THIS!):
Click **"Add Property"** three times:

| Name | Value |
|------|-------|
| `fs.s3a.endpoint` | `http://minio:9000` |
| `fs.s3a.path.style.access` | `true` |
| `fs.s3a.connection.ssl.enabled` | `false` |

**Other Settings**:
- ✅ Enable compatibility mode
- ✅ Enable asynchronous access (optional)

4. Click **"Save"**

**Expected**: See `minio` in left sidebar with buckets:
- `iceberg-warehouse`
- `zeek-data`

**Reference**: `/home/jerem/zeek-iceberg-demo/DREMIO-SETUP-GUIDE.md` (Step 3)

---

### Step 3: Format OCSF Dataset (2 minutes)

1. In Dremio sidebar, navigate:
   - Click `minio`
   - Click `zeek-data`
   - You should see `network-activity-ocsf` folder

2. Hover over `network-activity-ocsf` → Click **⋯** menu → **"Format Folder"**

3. In the Format dialog:
   - **Format Type**: `Parquet`
   - **Partition Fields** (optional): `year`, `month`, `day`
   - Click **"Save"**

**Expected**: Dataset formatted, ready to query

**Verify with Query**:
```sql
SELECT * FROM minio."zeek-data"."network-activity-ocsf" LIMIT 10;
```

You should see 10 OCSF records with 65 fields.

---

### Step 4: Create Reflections (5-10 minutes)

Reflections provide 10-100x query acceleration. You have **three options**:

#### Option A: Manual Creation (Most Control)

Follow the detailed guide:
- **File**: `/home/jerem/zeek-iceberg-demo/DREMIO-REFLECTION-GUIDE.md`
- **Create**: 3 reflections (1 raw + 2 aggregations)
- **Time**: ~10 minutes

#### Option B: REST API Script (Fastest)

Run the automated script:
```bash
cd /home/jerem/zeek-iceberg-demo
.venv/bin/python3 scripts/setup_reflections_simple.py
```

**What it does**:
1. Authenticates to Dremio API (prompts for password)
2. Finds the OCSF dataset
3. Creates 3 reflections automatically:
   - **Raw Reflection**: 13 key OCSF fields for fast queries
   - **Security Aggregation**: By IP, protocol, activity
   - **Time-based Aggregation**: Hourly traffic patterns

**Time**: ~2 minutes

#### Option C: Playwright Automation (After Login)

**Prerequisites**: You must be logged into Dremio first

**Steps**:
1. Login to Dremio manually
2. Tell me: "I'm logged in to Dremio"
3. I'll use Playwright to automate reflection creation

**Pros**: Watch the automation work in real-time
**Cons**: Requires manual login first (security limitation)

---

### Step 5: Verify Reflections Built (3 minutes)

1. In Dremio, click **"Jobs"** (top navigation)
2. Look for "Build Reflection" jobs
3. Wait for all to show **"COMPLETED"** status

**Expected time**: 2-5 minutes for 100K records

**Troubleshooting**: If reflections fail to build, check:
- Dataset is formatted correctly
- Reflection fields exist in dataset schema
- Sufficient memory (Dremio has 8GB configured)

---

### Step 6: Test Query Performance (2 minutes)

Run a query to verify reflection acceleration:

```sql
-- Before reflections: ~500ms
-- After reflections: ~50ms (10x faster)

SELECT
  activity_name,
  class_name,
  COUNT(*) as events,
  SUM(traffic_bytes_in + traffic_bytes_out) as total_bytes
FROM minio."zeek-data"."network-activity-ocsf"
WHERE category_uid = 4
GROUP BY activity_name, class_name
ORDER BY total_bytes DESC;
```

**Expected**:
- Query completes in <100ms
- Results show traffic breakdown by activity
- Dremio UI indicates "Accelerated" (reflection used)

---

## 🎯 What Success Looks Like

After completing all 6 steps:

1. ✅ Dremio connected to MinIO
2. ✅ OCSF dataset formatted and queryable
3. ✅ 3 reflections created and built
4. ✅ Queries running 10-100x faster
5. ✅ Demo-ready OCSF data lake

**Demo Capabilities**:
- Query 100K OCSF records in milliseconds
- OCSF-compliant field names and semantics
- Production-grade Parquet optimization
- Reflection-accelerated analytics
- Partitioned storage for scalability

---

## 📊 Sample OCSF Queries for Demo

### Network Activity Overview
```sql
SELECT
  activity_name,
  class_name,
  COUNT(*) as events,
  SUM(traffic_bytes_in + traffic_bytes_out) as total_bytes
FROM minio."zeek-data"."network-activity-ocsf"
WHERE category_uid = 4
GROUP BY activity_name, class_name
ORDER BY total_bytes DESC;
```

### Top Talkers by Protocol
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

### Security Analysis - Egress Traffic
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

### Time-based Analysis
```sql
SELECT
  DATE_TRUNC('hour', FROM_UNIXTIME(time / 1000)) as hour,
  COUNT(*) as events,
  COUNT(DISTINCT src_endpoint_ip) as unique_sources,
  COUNT(DISTINCT dst_endpoint_ip) as unique_destinations
FROM minio."zeek-data"."network-activity-ocsf"
GROUP BY DATE_TRUNC('hour', FROM_UNIXTIME(time / 1000))
ORDER BY hour;
```

---

## 🔧 Troubleshooting

### "Cannot see minio source in Dremio"
- Verify MinIO container is healthy: `docker ps | grep minio`
- Check network connectivity: `docker network inspect zeek-demo-net`
- Restart Dremio: `docker restart zeek-demo-dremio`

### "Dataset not found"
- Verify data exists: `docker exec zeek-demo-minio mc ls local/zeek-data/network-activity-ocsf/`
- Refresh Dremio catalog: Click refresh icon in sidebar
- Re-add MinIO source with correct properties

### "Reflection build failed"
- Check Jobs page for error message
- Verify dataset schema matches reflection fields
- Ensure sufficient memory (8GB configured)
- Try creating simpler reflection first (fewer fields)

---

## 📁 Key Files Reference

| File | Purpose |
|------|---------|
| `DREMIO-SETUP-GUIDE.md` | Step-by-step Dremio configuration |
| `DREMIO-REFLECTION-GUIDE.md` | Detailed reflection creation guide |
| `scripts/setup_reflections_simple.py` | Automated reflection script |
| `scripts/load_real_zeek_to_ocsf.py` | OCSF data loader (already run) |
| `CURRENT-STATUS.md` | This file - current status |

---

## 🚀 Next Action

**Pick one approach for Step 2-6**:

### Recommended: Manual Configuration First Time
1. Login to Dremio
2. Add MinIO source manually (3 min)
3. Format OCSF dataset (2 min)
4. Run reflection script OR create manually (5-10 min)
5. Test queries (2 min)

**Total time**: ~15 minutes to fully working demo

### Alternative: Fully Automated
1. Login to Dremio
2. Tell me "I'm logged in"
3. I'll attempt Playwright automation for the rest

**Pros**: Faster if it works
**Cons**: Less learning, harder to troubleshoot if issues

---

**Your Choice**: Tell me which approach you prefer, or just start with the manual setup and let me know when you need help!
