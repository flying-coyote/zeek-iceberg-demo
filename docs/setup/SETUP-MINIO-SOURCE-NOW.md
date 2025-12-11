# Setup MinIO Source in Dremio - Do This First!

Before creating reflections, we need to configure the MinIO source in Dremio.

---

## Option 1: Automated (Playwright)

Run this script to automatically configure MinIO:

```bash
export DREMIO_USERNAME="admin"
export DREMIO_PASSWORD="your_password"
source venv/bin/activate
python3 scripts/setup_dremio_minio_source.py
```

The browser will open and attempt to:
1. Navigate to Sources page
2. Click "Add Source"
3. Select "Amazon S3"
4. Fill in MinIO configuration
5. Save the source

**If automation fails**, the browser stays open for you to complete manually.

---

## Option 2: Manual Setup (5 minutes - Most Reliable)

### Step 1: Open Dremio
1. Go to http://localhost:9047
2. Log in with your credentials

### Step 2: Add MinIO Source
1. Click **"Sources"** in left sidebar (or go to /#/sources)
2. Click **"Add Source"** button (top right, or "+" button)
3. Select **"Amazon S3"**

### Step 3: Configure MinIO
Fill in these values:

**General:**
- **Name**: `minio`

**Connection:**
- **Enable compatibility mode**: ✅ **CHECK THIS BOX** (very important!)
- **AWS Access Key**: `minioadmin`
- **AWS Secret Key**: `minioadmin`

**Advanced Options** (click to expand if needed):
- **Connection Properties**: Add these if the UI allows:
  - `fs.s3a.endpoint` = `http://minio:9000`
  - `fs.s3a.path.style.access` = `true`
  - OR just ensure "Enable compatibility mode" is checked

### Step 4: Save
1. Click **"Save"** button
2. Wait for source to connect (should take 2-5 seconds)

### Step 5: Verify
1. You should see **"minio"** in your sources list
2. Click on **minio** to expand it
3. You should see buckets: **zeek-data**, **iceberg-warehouse**
4. Click **zeek-data** → should see **network-activity-ocsf** folder

---

## Step 6: Format the Dataset (If Needed)

If the dataset isn't already formatted:

1. Navigate to: **minio** → **zeek-data** → **network-activity-ocsf**
2. Right-click the **network-activity-ocsf** folder
3. Select **"Format Folder"**
4. Choose **"Parquet"**
5. Click **"Save"**

---

## Troubleshooting

### "Connection failed" or "Access Denied"
**Issue**: MinIO credentials wrong or compatibility mode not enabled

**Fix**:
1. Make sure you checked **"Enable compatibility mode"**
2. Verify credentials:
   - Access Key: `minioadmin`
   - Secret Key: `minioadmin`
3. If Dremio shows advanced options, add:
   - Endpoint: `http://minio:9000`

### "Source already exists"
**Great!** You're all set. Skip to verifying the dataset.

### Can't see "zeek-data" bucket
**Check**:
1. MinIO is running: `docker ps | grep minio`
2. Buckets exist: `docker exec zeek-demo-minio ls /data`
3. Should show: `iceberg-warehouse`, `zeek-data`

### Can't see "network-activity-ocsf" folder
**Check data is loaded**:
```bash
docker exec zeek-demo-minio ls /data/zeek-data/network-activity-ocsf/
# Should show: year=2025
```

If not, reload data:
```bash
source venv/bin/activate
python3 scripts/load_real_zeek_to_ocsf.py --all
```

---

## After MinIO Source is Configured

Once you see the MinIO source and can navigate to the dataset:

### Format the dataset as Parquet (if not done):
1. Navigate to: minio > zeek-data > network-activity-ocsf
2. Right-click folder
3. "Format Folder" → "Parquet" → Save

### Then create reflections:
```bash
bash run-reflection-setup.sh
```

OR manually in UI:
1. Click on the dataset
2. Go to "Reflections" tab
3. Click "Create Reflection"
4. Select "Raw Reflection"
5. Click "Save"

---

## Quick Manual Setup Commands

**To check if source exists**:
- Go to http://localhost:9047/#/sources
- Look for "minio" in the list

**To add source manually**:
- Click "Add Source"
- Select "Amazon S3"
- Name: `minio`
- ✅ Enable compatibility mode
- Access Key: `minioadmin`
- Secret Key: `minioadmin`
- Save

**To verify dataset**:
- Navigate: minio > zeek-data > network-activity-ocsf
- Should show data preview
- If not, format folder as Parquet

---

## What This Enables

Once MinIO source is configured:
- ✅ Dremio can see your OCSF data
- ✅ You can query it with SQL
- ✅ You can create reflections
- ✅ You can run the demo!

---

**Run Option 1 (automated) or Option 2 (manual) now, then proceed with reflection setup!** 🚀
