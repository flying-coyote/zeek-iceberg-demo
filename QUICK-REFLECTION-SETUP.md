# Quick Dremio Reflection Setup (5 minutes)

## Prerequisites
- Dremio running at http://localhost:9047
- You're logged in to Dremio
- Dataset `minio > zeek-data > network-activity-ocsf` is visible

## Option 1: Automated via Python Script (Recommended)

Run this command and enter your Dremio password when prompted:

```bash
python3 scripts/create_dremio_reflections.py
```

The script will:
1. Connect to Dremio API
2. Find your OCSF dataset
3. Create 4 reflections (1 raw + 3 aggregation)
4. Wait for them to build (2-5 minutes)
5. Report success

**If script fails**: Use Manual UI method below

---

## Option 2: Manual UI Setup (5 minutes)

### Step 1: Navigate to Dataset
1. Open http://localhost:9047
2. Click: **minio** → **zeek-data** → **network-activity-ocsf**
3. Click on the dataset name (should show preview of data)

### Step 2: Create Raw Reflection
1. Click **"Reflections"** tab (top of page)
2. Click **"Create Reflection"** button
3. Select **"Raw Reflection"**
4. Configuration:
   - **Name**: OCSF Raw Reflection
   - **Display Fields**: Select first 50 fields (or click "Select All")
   - **Partition Fields**: Click "+ Add Field" → Select `event_date`
   - **Distribution**: Leave empty
5. Click **"Save"**

### Step 3: Create Aggregation Reflection #1
1. Click **"Create Reflection"** again
2. Select **"Aggregation Reflection"**
3. Configuration:
   - **Name**: Protocol Activity Aggregation
   - **Dimensions** (click "+ Add Dimension"):
     - `connection_info_protocol_name`
     - `activity_name`
     - `src_endpoint_ip`
     - `dst_endpoint_ip`
   - **Measures** (click "+ Add Measure"):
     - `traffic_bytes_in` → Check: SUM, MIN, MAX
     - `traffic_bytes_out` → Check: SUM, MIN, MAX
     - `traffic_packets_in` → Check: SUM
     - `traffic_packets_out` → Check: SUM
   - **Partition**: `event_date`
4. Click **"Save"**

### Step 4: Create Aggregation Reflection #2
1. Click **"Create Reflection"** again
2. Select **"Aggregation Reflection"**
3. Configuration:
   - **Name**: Security Analysis Aggregation
   - **Dimensions**:
     - `src_endpoint_is_local`
     - `dst_endpoint_is_local`
     - `activity_name`
     - `connection_info_protocol_name`
   - **Measures**:
     - `traffic_bytes_out` → SUM
     - `traffic_bytes_in` → SUM
     - Use COUNT measure (should be available by default)
4. Click **"Save"**

### Step 5: Monitor Build Progress
1. Click **"Jobs"** in left sidebar
2. Filter by: **Type = "Reflection Refresh"**
3. Watch status change from "RUNNING" → "COMPLETED"
4. Typical build time: 1-3 minutes for 100K records

### Step 6: Verify Reflections are Active
1. Go back to your dataset
2. Click **"Reflections"** tab
3. All reflections should show:
   - Status: **Green checkmark** (Available)
   - Availability: **"Can Accelerate"**

---

## Testing Reflection Acceleration

Run this query before and after reflections are built:

```sql
SELECT
  activity_name,
  COUNT(*) as event_count,
  SUM(traffic_bytes_in + traffic_bytes_out) as total_traffic
FROM minio."zeek-data"."network-activity-ocsf"
GROUP BY activity_name
ORDER BY event_count DESC;
```

**Expected Results**:
- **Before reflections**: 500-1000ms
- **After reflections**: 50-150ms
- **Speedup**: 5-20x faster

To confirm reflection was used:
1. Run the query
2. Click **"Profile"** tab (top right of results)
3. Look for green "Reflection" node in query plan

---

## Quick Verification

Run this one-liner to check if reflections accelerate:

```sql
-- Should be VERY fast after reflections build
SELECT COUNT(*) FROM minio."zeek-data"."network-activity-ocsf";
```

**Before**: ~200-500ms
**After**: ~10-50ms

---

## Troubleshooting

### "Cannot create reflection - dataset not found"
- Make sure you've formatted the folder as Parquet
- In Dremio, right-click the folder → "Format Folder" → Select "Parquet"
- Then retry reflection creation

### Reflections stuck in "REFRESHING" status
- This is normal for first build
- Wait 5 minutes
- If still stuck after 10 minutes, disable and re-enable the reflection

### Query doesn't use reflection
- Check query profile to see why
- Common reasons:
  - Reflection still building
  - Query uses fields not in reflection
  - Query pattern doesn't match reflection dimensions

---

## What Gets Accelerated

These query patterns will be accelerated:

✅ **Activity breakdown** (Aggregation #1)
```sql
SELECT activity_name, COUNT(*)
FROM minio."zeek-data"."network-activity-ocsf"
GROUP BY activity_name;
```

✅ **Protocol analysis** (Aggregation #1)
```sql
SELECT connection_info_protocol_name, SUM(traffic_bytes_in)
FROM minio."zeek-data"."network-activity-ocsf"
GROUP BY connection_info_protocol_name;
```

✅ **Security analysis** (Aggregation #2)
```sql
SELECT src_endpoint_is_local, dst_endpoint_is_local, COUNT(*)
FROM minio."zeek-data"."network-activity-ocsf"
GROUP BY src_endpoint_is_local, dst_endpoint_is_local;
```

✅ **SELECT * queries** (Raw Reflection)
```sql
SELECT *
FROM minio."zeek-data"."network-activity-ocsf"
LIMIT 1000;
```

---

## For Demo Presentation

When showing reflections in demo:

1. **Show reflection tab**: "These 4 reflections pre-compute common query patterns"
2. **Run accelerated query**: "Notice this completes in 50ms"
3. **Show profile**: "Green checkmark shows reflection was used"
4. **Explain benefit**: "10-100x faster, automatic query rewriting, no code changes"

**Key talking point**: "Reflections provide sub-second query performance on 100K records. With 1M records, the speedup becomes even more dramatic - queries that take 10-30 seconds drop to 200-500 milliseconds."
