# Deploy Reflections NOW - Auth is Working!

Great! Authentication works. Here's what to do next.

---

## Step 1: Deploy Reflections (30 seconds to start)

Since your auth is working, run the reflection setup:

```bash
# Make sure credentials are still set in your terminal
export DREMIO_USERNAME="admin"
export DREMIO_PASSWORD="your_password"

# Activate virtual environment
source venv/bin/activate

# Run the reflection setup script
python3 scripts/create_reflections_auto.py
```

---

## What You'll See

**The script will**:
1. Authenticate with Dremio ✓ (you already tested this works)
2. Find your OCSF dataset
3. Create 4 reflections:
   - Raw Reflection
   - Protocol Activity Aggregation
   - Security Analysis Aggregation
   - Time-based Aggregation
4. Monitor build progress
5. Report when complete

**Expected output**:
```
======================================================================
Dremio Reflection Auto-Setup
======================================================================

Authenticating with Dremio...
✓ Successfully authenticated

Looking up dataset: minio > zeek-data > network-activity-ocsf
  Found: minio (id: ...)
  Found: zeek-data (id: ...)
  Found: network-activity-ocsf (id: ...)
✓ Dataset ID: ...

Creating reflections...

Creating raw reflection: OCSF Raw Reflection
  ✓ Created: OCSF Raw Reflection
Creating aggregation reflection: Protocol Activity Aggregation
  ✓ Created: Protocol Activity Aggregation
Creating aggregation reflection: Security Analysis Aggregation
  ✓ Created: Security Analysis Aggregation
Creating aggregation reflection: Time-based Aggregation
  ✓ Created: Time-based Aggregation

======================================================================
Reflections created successfully!
======================================================================

Waiting for reflections to build...
(This typically takes 2-5 minutes for 1M records)
  ⏳ OCSF Raw Reflection: REFRESHING
  ⏳ Protocol Activity Aggregation: REFRESHING
  ⏳ Security Analysis Aggregation: REFRESHING
  ⏳ Time-based Aggregation: REFRESHING
  ...
  (wait a few minutes)
  ...
  ✓ OCSF Raw Reflection: AVAILABLE
  ✓ Protocol Activity Aggregation: AVAILABLE
  ✓ Security Analysis Aggregation: AVAILABLE
  ✓ Time-based Aggregation: AVAILABLE
✓ All 4 reflections available! (took 143s)

======================================================================
✓ Setup complete!
======================================================================
```

---

## Step 2: Wait for Build (2-5 minutes)

The script will monitor the build progress automatically. You'll see status updates every 10 seconds.

**While you wait**, the reflections are:
- Pre-computing aggregations
- Building optimized data structures
- Creating acceleration indexes

---

## Step 3: Test Performance (After Build Completes)

Once the script shows all reflections are AVAILABLE:

1. **Open Dremio**: http://localhost:9047
2. **Run this test query**:

```sql
SELECT
  activity_name,
  COUNT(*) as events,
  SUM(traffic_bytes_in + traffic_bytes_out) as total_traffic
FROM minio."zeek-data"."network-activity-ocsf"
GROUP BY activity_name
ORDER BY events DESC;
```

3. **Check performance**:
   - **Before reflections**: 2-4 seconds
   - **With reflections**: 100-300ms ⚡ (10-15x faster!)

4. **Verify reflection usage**:
   - Click **"Profile"** tab (top right)
   - Look for green **"Reflection"** node in query plan
   - ✅ = Reflection was used!

---

## Alternative: All-in-One Command

If you want to do it in one line:

```bash
export DREMIO_USERNAME="admin" && \
export DREMIO_PASSWORD="your_password" && \
source venv/bin/activate && \
python3 scripts/create_reflections_auto.py
```

---

## If Something Goes Wrong

### Error: "Could not find dataset"

**Fix**:
1. Open Dremio UI: http://localhost:9047
2. Navigate to: minio > zeek-data > network-activity-ocsf
3. Right-click the folder
4. Select **"Format Folder"**
5. Choose **"Parquet"**
6. Click **"Save"**
7. Re-run the script

### Error: "Authentication failed"

Your credentials might have changed. Re-run the test:

```bash
export DREMIO_USERNAME="admin"
export DREMIO_PASSWORD="your_password"
bash scripts/test_dremio_login.sh
```

If that passes, try the reflection setup again.

---

## After Reflections Are Built

### Check Status Anytime

```bash
export DREMIO_USERNAME="admin"
export DREMIO_PASSWORD="your_password"
source venv/bin/activate
python3 scripts/check_reflections_auto.py
```

### Start Your Demo!

Open **START-DEMO-NOW.md** for the 15-minute demo flow.

With reflections, your queries will be **10-100x faster** - perfect for impressing stakeholders!

---

## Quick Command Reference

```bash
# Deploy reflections (run this now!)
export DREMIO_USERNAME="admin"
export DREMIO_PASSWORD="your_password"
source venv/bin/activate
python3 scripts/create_reflections_auto.py

# Check status later
python3 scripts/check_reflections_auto.py

# Test query in Dremio UI
SELECT activity_name, COUNT(*) FROM minio."zeek-data"."network-activity-ocsf" GROUP BY activity_name;
```

---

**You're ready! Run the deployment command above and watch the reflections get created!** 🚀
