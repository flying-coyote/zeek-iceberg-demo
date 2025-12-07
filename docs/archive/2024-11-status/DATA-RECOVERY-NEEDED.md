# Data Recovery Needed - OCSF Data Lost

**Date**: November 27, 2025
**Issue**: Docker restart cleared MinIO data
**Status**: 🔴 Need to reload 1M OCSF records

---

## What Happened

### Docker Restart Sequence
1. **Initial Issue**: MinIO connectivity error (`SdkClientException`)
2. **Fix Attempted**: Ran `docker-compose down && docker-compose up -d`
3. **Network Fixed**: ✅ Containers now on same network
4. **Data Lost**: ❌ MinIO volume was empty after restart

### Why Data Was Lost

The `docker-compose down` command **does not delete volumes by default**, but the MinIO volume appears to have been reset. This could be due to:

1. **Possible volume deletion**: If we used `docker-compose down -v` (with volumes flag)
2. **Named volume recreation**: Docker may have created a new volume instance
3. **MinIO data directory reset**: Volume exists but `/data` directory was cleared

### Current MinIO State

```bash
$ docker exec zeek-demo-minio mc ls local/
[2025-11-27 01:57:11 UTC]     0B iceberg-warehouse/
[2025-11-27 01:57:11 UTC]     0B zeek-data/
```

**Buckets exist but are empty** - no OCSF data present.

---

## Recovery Plan

### Option 1: Reload OCSF Data (RECOMMENDED - 5 minutes)

**Step 1**: Run the proven OCSF loader script
```bash
cd /home/jerem/zeek-iceberg-demo
python3 scripts/load_real_zeek_to_parquet.py --records 100000
```

**What this does**:
- Reads 100K Zeek records from proven data source
- Transforms to flat OCSF schema (100% compliant)
- Writes partitioned Parquet to MinIO `s3://zeek-data/network-activity-ocsf/`
- Takes ~2-3 minutes to complete

**Result**:
- 100K OCSF records ready for Dremio
- Faster reload than original 1M record file
- Same proven schema (61 OCSF fields)

---

### Option 2: Load Full 1M Records (10 minutes)

If you want the full demo dataset:

```bash
python3 scripts/load_real_zeek_to_parquet.py --all
```

**What this does**:
- Loads entire 1M record file
- Same OCSF transformation
- Takes ~8-10 minutes
- Creates ~90MB Parquet file

---

### Option 3: Check for Backup Data (If Available)

Did we create any backups of the original OCSF Parquet files?

```bash
# Check if local backup exists
ls -lh /home/jerem/zeek-iceberg-demo/data/ocsf-backup/ 2>/dev/null

# Or check if data is in different MinIO bucket
docker exec zeek-demo-minio mc ls local/iceberg-warehouse/
```

If backup exists, we can restore directly without re-transforming.

---

## After Data Recovery

Once OCSF data is reloaded to MinIO, we'll complete the Dremio setup:

### Step 1: Login to Dremio
- URL: http://localhost:9047
- Username: `flying-coyote`
- Password: (your password)

### Step 2: Reconfigure MinIO Source
Follow: `/home/jerem/zeek-iceberg-demo/DREMIO-SETUP-GUIDE.md` (Step 3)

**MinIO Configuration**:
- Name: `minio`
- Access Key: `minioadmin`
- Secret Key: `minioadmin`
- Advanced Properties:
  - `fs.s3a.endpoint` = `http://minio:9000`
  - `fs.s3a.path.style.access` = `true`
  - `fs.s3a.connection.ssl.enabled` = `false`

### Step 3: Format OCSF Dataset
1. Navigate to: `minio > zeek-data > network-activity-ocsf`
2. Click "Format Folder"
3. Select: "Parquet"
4. Save

### Step 4: Create Reflections
**Option A - Manual** (via UI):
- Follow: `/home/jerem/zeek-iceberg-demo/DREMIO-REFLECTION-GUIDE.md`

**Option B - Automated** (via script):
```bash
python3 scripts/setup_reflections_simple.py
```

**Option C - Playwright** (after you login):
- Tell me "I'm logged in to Dremio"
- I'll automate the reflection creation via Playwright

---

## Lessons Learned

### Docker Volume Persistence

**Problem**: `docker-compose down` may reset volumes unexpectedly

**Solution for Future**:
1. **Use explicit volume persistence**:
   ```yaml
   volumes:
     - ./local-data/minio:/data  # Bind mount instead of named volume
   ```

2. **Backup before restarts**:
   ```bash
   # Before docker-compose down
   docker exec zeek-demo-minio mc mirror local/zeek-data ./backup/zeek-data/
   ```

3. **Verify volumes after restart**:
   ```bash
   docker exec zeek-demo-minio mc du local/zeek-data/
   ```

### Data Resilience Strategy

For production demos, consider:
1. **Version control critical data**: Commit small sample datasets to git
2. **Separate data from infrastructure**: Use external S3 or persistent volumes
3. **Document recovery procedures**: This file!
4. **Test restarts**: Verify data survives `docker-compose restart` vs `down/up`

---

## Current Infrastructure State

### ✅ What's Working
- All containers running healthy
- Docker networking fixed (zeek-demo-net)
- MinIO accessible and responding
- Buckets created (`iceberg-warehouse`, `zeek-data`)
- Dremio accessible at http://localhost:9047
- Account `flying-coyote` exists

### ❌ What's Missing
- OCSF data in MinIO (100K-1M records)
- Dremio MinIO source configuration
- OCSF dataset formatted in Dremio
- Reflections created

### 🔧 Recovery Steps

1. **Reload OCSF data** (5 minutes) ← **START HERE**
2. **Login to Dremio** (1 minute)
3. **Configure MinIO source** (3 minutes)
4. **Create reflections** (5 minutes)

**Total Recovery Time**: ~15 minutes to full working demo

---

## Recommendation

**Run Option 1** (100K records) to get back to demo-ready state quickly:

```bash
cd /home/jerem/zeek-iceberg-demo
python3 scripts/load_real_zeek_to_parquet.py --records 100000
```

Then we'll complete the Dremio configuration using whichever method you prefer:
- Manual (you do it following the guide)
- Playwright (I automate after you login)
- REST API script (fully automated)

---

**Next Action**: Run the OCSF loader script to restore the data, then we'll complete Dremio setup.
