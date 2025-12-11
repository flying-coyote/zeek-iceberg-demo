# Fix MinIO S3 Connection Error

You're getting "could not connect to s3 source" - this is a common issue. Here's how to fix it.

---

## Quick Fix (Most Common Issue)

The problem is usually that **"Enable compatibility mode"** wasn't checked when adding the source.

### Fix Steps:

1. **Open Dremio**: http://localhost:9047
2. **Go to Sources** (left sidebar or /#/sources)
3. **Find your MinIO source** and click the **⋮** (three dots) or right-click
4. **Select "Edit"** or "Remove" it

### If Editing the Source:

1. Make sure **"Enable compatibility mode"** is ✅ **CHECKED**
2. Verify credentials:
   - Access Key: `minioadmin`
   - Secret Key: `minioadmin`
3. Click **"Save"**

### If Removing and Re-adding:

1. **Remove** the old source
2. Click **"Add Source"**
3. Select **"Amazon S3"**
4. Fill in:

```
Name: minio
AWS Access Key: minioadmin
AWS Secret Key: minioadmin

✅ Enable compatibility mode  <-- CRITICAL! Must be checked!

Optional (if fields are visible):
- Root Path: leave empty or /
- Encrypt Connection: No/Disabled
```

5. Click **"Save"**

---

## Alternative: Add Connection Properties

If "Enable compatibility mode" isn't visible or doesn't work, add these manually:

### In Dremio Source Configuration:

Look for **"Connection Properties"** or **"Advanced Options"** section.

Add these properties:

```
fs.s3a.endpoint = minio:9000
fs.s3a.path.style.access = true
fs.s3a.connection.ssl.enabled = false
```

---

## Verify MinIO is Accessible

Before configuring Dremio, verify MinIO is running:

```bash
# Check MinIO container
docker ps | grep minio

# Should show: zeek-demo-minio running

# Check MinIO is responding
curl http://localhost:9000
# Should return XML error (that's OK - means it's responding)

# Check from inside Dremio's network
docker exec zeek-demo-dremio curl http://minio:9000
# Should return XML (means Dremio can reach MinIO)
```

If MinIO isn't accessible from Dremio container, restart the containers:

```bash
docker-compose restart
```

---

## Check Data Exists in MinIO

Verify the OCSF data is actually in MinIO:

```bash
# Check buckets exist
docker exec zeek-demo-minio ls /data
# Should show: iceberg-warehouse  zeek-data

# Check OCSF data exists
docker exec zeek-demo-minio ls /data/zeek-data/network-activity-ocsf/
# Should show: year=2025

# Check the parquet file
docker exec zeek-demo-minio find /data/zeek-data -name "*.parquet"
# Should show path to data.parquet file
```

If data is missing, reload it:

```bash
source venv/bin/activate
python3 scripts/load_real_zeek_to_ocsf.py --all
```

---

## Complete Configuration Reference

Here's the exact configuration that should work:

### Source Configuration in Dremio UI:

**Tab: General**
- Name: `minio`

**Tab: Authentication**
- AWS Access Key: `minioadmin`
- AWS Secret Key: `minioadmin`
- IAM Role: (leave empty)

**Tab: Advanced Options**
- ✅ **Enable compatibility mode** ← MUST BE CHECKED
- Root Path: (leave empty)
- Enable async: (default/leave unchecked)

**Tab: Connection Properties** (if visible)
Add these:
```
fs.s3a.endpoint: minio:9000
fs.s3a.path.style.access: true
fs.s3a.connection.ssl.enabled: false
```

**Tab: Reflection Refresh**
- (leave defaults)

---

## Test the Connection

After saving the source:

1. **Refresh** the sources page
2. **Click on "minio"** source
3. You should see:
   - `iceberg-warehouse` (bucket)
   - `zeek-data` (bucket)

4. **Click "zeek-data"**
5. You should see:
   - `network-activity-ocsf` (folder)

6. **Click "network-activity-ocsf"**
7. You should see:
   - `year=2025` (partition folder)

If you see this, the connection works! ✅

---

## Common Errors and Fixes

### Error: "Access Denied"
**Fix**: Wrong credentials
- Access Key: `minioadmin` (not `minio`)
- Secret Key: `minioadmin`

### Error: "Connection timeout"
**Fix**: MinIO not reachable from Dremio
```bash
docker-compose restart
# Wait 30 seconds
# Try adding source again
```

### Error: "Unsupported S3 operation"
**Fix**: Compatibility mode not enabled
- Edit source
- ✅ Check "Enable compatibility mode"
- Save

### Error: "Bucket not found"
**Fix**: Buckets don't exist in MinIO
```bash
# Check buckets
docker exec zeek-demo-minio mc ls myminio
# Should show: zeek-data, iceberg-warehouse

# If missing, recreate them
docker-compose up -d minio-init
```

---

## Step-by-Step Manual Setup (Copy-Paste)

1. Open: http://localhost:9047
2. Click: **Sources** (left sidebar)
3. Click: **Add Source** (top right, "+" button)
4. Click: **Amazon S3**
5. Fill in:
   - Name: `minio`
   - Access Key: `minioadmin`
   - Secret Key: `minioadmin`
6. **✅ Check "Enable compatibility mode"**
7. Click: **Save**
8. Wait 5 seconds
9. Click: **minio** in sources list
10. Should see buckets!

---

## If All Else Fails: Use REST API

You can add the source via REST API:

```bash
# Login to get token
TOKEN=$(curl -s -X POST http://localhost:9047/apiv2/login \
  -H "Content-Type: application/json" \
  -d '{"userName":"admin","password":"your_password"}' \
  | grep -o '"token":"[^"]*"' | cut -d'"' -f4)

# Add MinIO source
curl -X POST http://localhost:9047/api/v3/catalog \
  -H "Authorization: _dremio$TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "entityType": "source",
    "name": "minio",
    "type": "S3",
    "config": {
      "accessKey": "minioadmin",
      "accessSecret": "minioadmin",
      "secure": false,
      "enableAsync": true,
      "enableFileStatusCheck": true,
      "rootPath": "/",
      "defaultCtasFormat": "PARQUET",
      "propertyList": [
        {"name": "fs.s3a.path.style.access", "value": "true"},
        {"name": "fs.s3a.endpoint", "value": "minio:9000"},
        {"name": "fs.s3a.connection.ssl.enabled", "value": "false"}
      ]
    }
  }'
```

---

## Next Steps After Connection Works

Once you can see the MinIO source and browse to the data:

1. **Format the dataset** (if not done):
   - Right-click `network-activity-ocsf` folder
   - Select "Format Folder"
   - Choose "Parquet"
   - Save

2. **Run a test query**:
   ```sql
   SELECT COUNT(*) FROM minio."zeek-data"."network-activity-ocsf"
   ```
   Should return: 1,000,000

3. **Create reflections**:
   - Navigate to dataset
   - Click "Reflections" tab
   - Click "Create Reflection"
   - Select "Raw Reflection"
   - Save

---

**The #1 fix: Enable compatibility mode! Try that first.** ✅
