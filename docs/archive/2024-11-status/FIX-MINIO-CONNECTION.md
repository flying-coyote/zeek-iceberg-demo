# Fix MinIO Connection Error in Dremio

**Error**: `Unable to execute HTTP request: http: Name or service not known`

**Root Cause**: MinIO source is missing the S3 endpoint configuration that tells Dremio how to connect to the MinIO container.

---

## Quick Fix (5 minutes)

### Step 1: Edit MinIO Source

1. In Dremio, click on **"minio"** in the left sidebar (under Object Storage)
2. Click the **gear/settings icon** (⚙️) at the top right
3. Select **"Edit Source"**

### Step 2: Add Required Advanced Properties

Scroll down to **"Advanced Options"** section and click to expand it.

You need to add **3 critical properties**. For each property:
1. Click **"Add Property"**
2. Enter the Name and Value exactly as shown below

**Property 1:**
- **Name**: `fs.s3a.endpoint`
- **Value**: `http://minio:9000`

**Property 2:**
- **Name**: `fs.s3a.path.style.access`
- **Value**: `true`

**Property 3:**
- **Name**: `fs.s3a.connection.ssl.enabled`
- **Value**: `false`

### Step 3: Verify Other Settings

While you're in the Edit Source dialog, verify:

**General Settings:**
- **Name**: `minio` (don't change)

**Authentication:**
- **Access Key**: `minioadmin`
- **Secret Key**: `minioadmin`

**Connection Settings:**
- ✅ **Enable compatibility mode** (check this box)

### Step 4: Save and Test

1. Click **"Save"** at the bottom
2. Dremio will test the connection
3. You should see a success message

### Step 5: Refresh and Verify

1. After saving, click on **"minio"** in the sidebar again
2. You should now see the two buckets:
   - `iceberg-warehouse`
   - `zeek-data`
3. Click into **`zeek-data`**
4. You should see the folders:
   - `network-activity` (old test data)
   - `network-activity-ocsf` (✅ **this is what we need**)
   - `network-activity-real` (100K records without OCSF schema)

---

## Why This Happens

When Dremio containers restart, the MinIO source configuration can lose the advanced properties. These properties are **essential** because:

1. **`fs.s3a.endpoint`**: Tells Dremio the MinIO container is at `http://minio:9000` (not AWS S3)
2. **`fs.s3a.path.style.access`**: Uses path-style URLs (`http://minio:9000/bucket/key`) instead of virtual-hosted style
3. **`fs.s3a.connection.ssl.enabled`**: Disables SSL since we're using plain HTTP in the demo

Without these, Dremio tries to connect to AWS S3 instead of your local MinIO container.

---

## Verification Commands (Optional)

If you want to verify MinIO is accessible from Dremio's perspective:

```bash
# Check if Dremio can resolve 'minio' hostname
docker exec zeek-demo-dremio ping -c 1 minio

# Check if MinIO is responding on port 9000
docker exec zeek-demo-dremio curl -I http://minio:9000/minio/health/live
```

Both should succeed if networking is correct.

---

## After Fixing Connection

Once the MinIO connection is working, you can proceed with:

### 1. Format the OCSF Dataset (2 minutes)
- Navigate to: `minio > zeek-data > network-activity-ocsf`
- Click the **⋯** menu → **"Format Folder"**
- Select **"Parquet"**
- Click **"Save"**

### 2. Create Reflections (8 minutes)
Follow the guide in `FINAL-SETUP-STEPS.md`

---

## If You Still Get Errors

### Error: "Access Denied"
- Check Access Key and Secret Key are both `minioadmin`

### Error: "Connection Refused"
- Verify MinIO container is running: `docker ps | grep minio`
- Restart if needed: `docker restart zeek-demo-minio`

### Error: "Bucket does not exist"
- Check data exists in MinIO:
  ```bash
  docker exec zeek-demo-minio mc ls local/zeek-data/network-activity-ocsf/
  ```
- Should show the 9.1MB Parquet file

### Folders Still Don't Load in UI
- Click the **refresh icon** next to the minio source
- Wait 10 seconds
- Refresh your browser page

---

## Quick Reference: MinIO Advanced Properties

Copy-paste these if needed:

```
Name: fs.s3a.endpoint
Value: http://minio:9000

Name: fs.s3a.path.style.access
Value: true

Name: fs.s3a.connection.ssl.enabled
Value: false
```

---

**Next**: After fixing the connection, you should be able to see and format the `network-activity-ocsf` folder!
