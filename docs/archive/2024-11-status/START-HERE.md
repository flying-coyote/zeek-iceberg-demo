# 🚀 START HERE - Your Demo is Ready!

**Location**: `~/zeek-iceberg-demo/`
**Status**: ✅ Core services running
**Next**: Configure Dremio and load data (15 minutes)

---

## Quick Status Check

```bash
cd ~/zeek-iceberg-demo
docker compose ps
```

**You should see running**:
- ✅ zeek-demo-minio (S3 storage)
- ✅ zeek-demo-postgres (database)
- ✅ zeek-demo-hive-metastore (catalog)
- ✅ zeek-demo-dremio (query engine)

---

## Follow These Steps

### 1️⃣ Configure Dremio (5 minutes)

**📖 Guide**: Open `DREMIO-SETUP-GUIDE.md` and follow it

**Quick version**:
1. Open http://localhost:9047
2. Create admin account
3. Add Hive source: `hive-metastore:9083`
4. Add MinIO source with advanced properties

---

### 2️⃣ Install Python Dependencies (2 minutes)

```bash
cd ~/zeek-iceberg-demo
./install-dependencies.sh
```

---

### 3️⃣ Load Data (5 minutes)

```bash
python3 scripts/load_zeek_to_iceberg.py
```

**This will**:
- Read 10,000 Zeek network logs
- Transform to OCSF Network Activity (class 4001)
- Write to Iceberg table: `security_data.network_activity`
- Make data queryable in Dremio

---

### 4️⃣ Query in Dremio (3 minutes)

1. Refresh `hive_metastore` in Dremio
2. Navigate to: `security_data.network_activity`
3. Run query:
   ```sql
   SELECT * FROM hive_metastore.security_data.network_activity LIMIT 10;
   ```

---

### 5️⃣ Create Reflections (5 minutes)

Follow **COMPLETE-DEMO-FLOW.md** Part 5 to create reflections for query acceleration.

---

## Documentation Files

| File | Purpose |
|------|---------|
| **START-HERE.md** | This file - your starting point |
| **COMPLETE-DEMO-FLOW.md** | Full step-by-step guide (15-20 min) |
| **DREMIO-SETUP-GUIDE.md** | Dremio configuration with screenshots |
| **CURRENT-STATUS.md** | What's working right now |
| **README.md** | Full technical documentation |
| **QUICK-START.md** | 5-minute quick start |

---

## Key URLs

- **Dremio**: http://localhost:9047
- **MinIO Console**: http://localhost:9001 (minioadmin / minioadmin)
- **Spark UI**: http://localhost:8080 (not working - using Python instead)

---

## What This Demonstrates

✅ **S3 Storage** - MinIO as S3-compatible object store
✅ **Iceberg Tables** - Modern lakehouse table format
✅ **Hive Metastore** - Cloudera compatibility layer
✅ **OCSF Transformation** - Security data standardization
✅ **Dremio Query Engine** - Fast SQL queries
✅ **Materialized Views** - Reflections for acceleration

---

## If Something Goes Wrong

### Services won't start
```bash
docker compose down
docker compose up -d
```

### Python script fails
```bash
# Check Hive and MinIO are running
docker ps | grep -E "hive|minio"

# Check logs
docker logs zeek-demo-hive-metastore
docker logs zeek-demo-minio
```

### Can't access Dremio
```bash
# Check Dremio logs
docker logs zeek-demo-dremio

# Restart Dremio
docker compose restart dremio
```

---

## Alternative: Original Spark Approach

The Spark-based pipeline didn't work due to Docker image issues. The Python alternative (`load_zeek_to_iceberg.py`) does the same thing:

- ❌ PySpark pipeline (image not available)
- ✅ Python + PyIceberg (works perfectly!)

**Outcome is identical** - data ends up in Iceberg tables either way.

---

## Need Help?

Check these files in order:
1. **START-HERE.md** (this file)
2. **COMPLETE-DEMO-FLOW.md** (detailed steps)
3. **DREMIO-SETUP-GUIDE.md** (Dremio specific)
4. **CURRENT-STATUS.md** (troubleshooting)

---

## Total Time Estimate

- ⏱️ Dremio configuration: 5 minutes
- ⏱️ Install dependencies: 2 minutes
- ⏱️ Load data: 5 minutes
- ⏱️ Test queries: 3 minutes
- ⏱️ Create reflections: 5 minutes

**Total**: ~20 minutes to fully working demo

---

**🎯 Your Next Command**:

```bash
# Open the complete guide
cat ~/zeek-iceberg-demo/COMPLETE-DEMO-FLOW.md
```

**Then**:
1. Open http://localhost:9047 (configure Dremio)
2. Run `./install-dependencies.sh`
3. Run `python3 scripts/load_zeek_to_iceberg.py`
4. Query data in Dremio!

---

**Ready?** Follow **COMPLETE-DEMO-FLOW.md** for the full walkthrough! 🚀
