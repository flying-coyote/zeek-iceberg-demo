# Working Setup - MinIO + Dremio (Verified November 26, 2025)

**Status**: ✅ Fully operational and tested
**Architecture**: Simplified lakehouse (no Hive Metastore required)
**Query Performance**: <1s for 3,000 records

---

## What Works

This is the **proven, working configuration** for querying Parquet data in MinIO using Dremio.

```
Sample Data (Parquet) → MinIO (S3-compatible storage) → Dremio (SQL query engine)
```

**Advantages over Hive Metastore approach:**
- No PostgreSQL authentication issues
- Simpler architecture
- Dremio's native S3 connector
- Direct folder → dataset conversion
- Faster setup (5 minutes vs 20 minutes)

---

## Prerequisites

1. **Docker services running:**
   ```bash
   cd ~/zeek-iceberg-demo
   docker compose up -d minio postgres dremio
   ```

2. **Sample data loaded:**
   ```bash
   source .venv/bin/activate
   python3 scripts/create_sample_parquet.py
   ```
   Creates 3,000 records in `s3://zeek-data/network-activity/`

---

## Dremio Configuration (The Critical Steps)

### Step 1: Access Dremio

```bash
# Open in browser
http://localhost:9047
```

If first time, create admin account.

### Step 2: Add MinIO as Amazon S3 Source

1. Click **"Add Source"** → Select **"Amazon S3"**

2. **General Tab:**
   - Name: `minio`
   - Authentication: **No Authentication**
   - Encrypt connection: **Unchecked** (disabled)
   - Public Buckets: `zeek-data`

3. **Advanced Options Tab:**

   **🔴 CRITICAL: Enable compatibility mode checkbox**

   This checkbox is **REQUIRED** for MinIO and other S3-compatible storage systems.

   ✅ Check **"Enable compatibility mode"**

4. **Advanced Options → Connection Properties:**

   Add these four properties:

   | Property Name | Value | Purpose |
   |---------------|-------|---------|
   | `fs.s3a.endpoint` | `minio:9000` | MinIO endpoint (NO `http://` prefix!) |
   | `fs.s3a.path.style.access` | `true` | Use path-style bucket URLs |
   | `fs.s3a.connection.ssl.enabled` | `false` | Disable SSL for local development |
   | `fs.s3a.endpoint.region` | `us-east-1` | Explicit region specification |

5. Click **"Save"**

---

## Why "Enable Compatibility Mode" is Critical

**Without this checkbox:**
```
RuntimeException: Error while trying to get region of zeek-data:
java.lang.NullPointerException: region must not be null.
```

**With this checkbox enabled:**
- Dremio disables AWS-specific region auto-detection
- S3 API calls work with MinIO's implementation
- Queries execute successfully

**Source:** [Dremio Official Documentation](https://docs.dremio.com/cloud/sonar/data-sources/amazon-s3/configuring-s3-compatible-storage/)

---

## Data Setup

### Step 3: Browse to Data

1. In Dremio left sidebar, expand **"minio"**
2. Navigate to **"zeek-data"** → **"network-activity"**
3. You should see partition folders: `year=2025/month=11/day=*/`

### Step 4: Format as Dataset (Optional but Recommended)

1. Click on **"network-activity"** folder
2. Click **"Format Folder"** button
3. Select **"Parquet"** format
4. Click **"Save"**

Dremio will auto-detect the schema and create a queryable dataset.

---

## Query Testing

### Test Query 1: Basic Select

```sql
SELECT * FROM minio."zeek-data"."network-activity" LIMIT 10;
```

**Expected Result:**
- 10 rows returned in <1s
- Columns: timestamp, src_ip, dst_ip, src_port, dst_port, protocol, bytes_sent, bytes_received, packets, duration, event_date, year, month, day

### Test Query 2: Protocol Distribution

```sql
SELECT
  protocol,
  COUNT(*) as connection_count,
  SUM(bytes_sent + bytes_received) as total_bytes
FROM minio."zeek-data"."network-activity"
GROUP BY protocol
ORDER BY connection_count DESC;
```

### Test Query 3: Top Talkers

```sql
SELECT
  src_ip,
  COUNT(*) as connections,
  SUM(bytes_sent) as total_bytes_sent,
  SUM(bytes_received) as total_bytes_received
FROM minio."zeek-data"."network-activity"
GROUP BY src_ip
ORDER BY total_bytes_sent DESC
LIMIT 20;
```

### Test Query 4: Port Analysis

```sql
SELECT
  dst_port,
  protocol,
  COUNT(*) as connections,
  AVG(duration) as avg_duration_ms
FROM minio."zeek-data"."network-activity"
GROUP BY dst_port, protocol
ORDER BY connections DESC
LIMIT 20;
```

---

## Docker Networking Notes

**Important:** Both Dremio and MinIO run in the same Docker network (`demo-network`), so:

✅ **Use container hostname:** `minio:9000`
❌ **Don't use localhost:** `localhost:9000` (won't work from Dremio container)
❌ **Don't add protocol:** `http://minio:9000` (Dremio adds `http://` automatically)

---

## Troubleshooting

### Issue: "region must not be null" error

**Solution:** You forgot to check the "Enable compatibility mode" checkbox in Advanced Options.

1. Go to minio source settings
2. Advanced Options tab
3. ✅ Check "Enable compatibility mode"
4. Save

### Issue: Bucket browse timeout

**Solution:** Add the `fs.s3a.endpoint.region` property:
- Property: `fs.s3a.endpoint.region`
- Value: `us-east-1`

### Issue: Query returns no data

**Check these:**
1. Is sample data actually loaded?
   ```bash
   docker exec zeek-demo-minio mc ls myminio/zeek-data/network-activity/ --recursive
   ```

2. Did you format the folder in Dremio?
   - Navigate to network-activity folder
   - Click "Format Folder"
   - Select Parquet

---

## Next Steps

### 1. Create Dremio Reflections (Query Acceleration)

Reflections are Dremio's materialized views that dramatically accelerate queries.

**Create Aggregation Reflection:**
1. Navigate to `minio."zeek-data"."network-activity"`
2. Click **"Reflections"** tab
3. Click **"Create Reflection"** → **"Aggregation"**
4. Configure:
   - **Dimensions:** src_ip, dst_ip, protocol, dst_port
   - **Measures:** SUM(bytes_sent), SUM(bytes_received), COUNT(*)
   - **Partition By:** event_date
5. Save and wait for build (~30 seconds for 3K records)

**Test acceleration:**
```sql
-- Re-run the top talkers query
-- Check query profile to verify reflection was used
SELECT
  src_ip,
  COUNT(*) as connections,
  SUM(bytes_sent) as total_bytes_sent
FROM minio."zeek-data"."network-activity"
GROUP BY src_ip
ORDER BY total_bytes_sent DESC
LIMIT 20;
```

### 2. Load Real Zeek Data

Replace sample data with actual Zeek conn logs:

```bash
# If you have real Zeek data
source .venv/bin/activate
python3 scripts/load_real_zeek_data.py
```

### 3. Add More OCSF Event Classes

Extend to other security data types:
- DNS Activity (class 4003)
- HTTP Activity (class 4002)
- SSH Activity (class 4007)

---

## Sample Data Schema

The `create_sample_parquet.py` script generates this schema:

```
timestamp           TIMESTAMP
src_ip              STRING
dst_ip              STRING
src_port            INT64
dst_port            INT64
protocol            STRING (TCP, UDP, ICMP)
bytes_sent          INT64
bytes_received      INT64
packets             INT64
duration            FLOAT64 (milliseconds)
event_date          STRING (partition key)
```

**Partitioning:** Data partitioned by `year/month/day` for efficient querying.

---

## Comparison: Hive Metastore vs Direct S3

| Feature | Hive Metastore | Direct S3 (This Setup) |
|---------|----------------|------------------------|
| **Setup Complexity** | High (Hive + PostgreSQL) | Low (just MinIO + Dremio) |
| **Auth Issues** | Yes (PostgreSQL scram-sha-256) | None |
| **Query Performance** | Same | Same |
| **Iceberg Support** | Yes (with Hive catalog) | Yes (with Nessie or REST catalog) |
| **OCSF Support** | Yes | Yes |
| **Production Ready** | Yes (with fixes) | Yes |

**Recommendation:** Start with Direct S3 for demos and POCs. Add Hive Metastore only when you need:
- Multi-engine support (Spark + Dremio + Impala)
- Centralized metadata management
- Iceberg table versioning via Hive catalog

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     Zeek Network Logs                        │
│                    (conn.log, 357MB)                         │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              Transform to Parquet (Python)                   │
│           Optional: Map to OCSF Network Activity             │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              MinIO (S3-Compatible Storage)                   │
│                                                               │
│  Bucket: zeek-data                                           │
│  └── network-activity/                                       │
│      ├── year=2025/month=11/day=24/data.parquet             │
│      ├── year=2025/month=11/day=25/data.parquet             │
│      └── year=2025/month=11/day=26/data.parquet             │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   Dremio Query Engine                        │
│                                                               │
│  Features:                                                   │
│  • Direct S3 access (no Hive Metastore needed)              │
│  • SQL query interface                                       │
│  • Reflections for acceleration                             │
│  • JDBC/ODBC connectivity                                    │
└─────────────────────────────────────────────────────────────┘
```

---

## Files Reference

- **This guide:** `WORKING-SETUP.md`
- **Detailed solution:** `SOLUTION-COMPATIBILITY-MODE.md`
- **Sample data generator:** `scripts/create_sample_parquet.py`
- **Full architecture:** `README.md`
- **Troubleshooting history:** `VERIFICATION-RESULTS-SESSION2.md`

---

**Last Updated:** November 26, 2025
**Tested With:** Dremio Community Edition (Docker), MinIO RELEASE.2024-10-02T17-50-41Z
**Demo Status:** ✅ Production-ready for customer presentations
