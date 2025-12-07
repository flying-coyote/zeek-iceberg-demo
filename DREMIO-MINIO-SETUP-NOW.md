# Dremio MinIO Configuration - Step by Step

**Time Required**: 5 minutes
**Current Status**: Dremio is running at http://localhost:9047

---

## Step 1: Open Dremio (30 seconds)

### Open your browser and navigate to:
# **http://localhost:9047**

You should see either:
- A **login page** (if you've set up before)
- A **"Create Admin Account"** page (first time)

---

## Step 2: Account Setup (1 minute)

### If First Time:
Fill in the admin account form:
- **First Name**: Your name (or "Admin")
- **Last Name**: Your name (or "User")
- **Email**: Any email (e.g., admin@example.com)
- **Username**: admin (or your choice)
- **Password**: Choose a password (remember it!)

Click **"Next"** or **"Create Account"**

### If Returning:
Login with your previously created credentials

---

## Step 3: Add MinIO Source (2 minutes)

Once logged in:

1. **Click "+ Add Source"** button (usually top-left or in main area)

2. **Select "Amazon S3"** from the list

3. **Fill in General Settings**:
   - **Name**: `minio` (exactly this, lowercase)
   - **Description**: (optional) "Local MinIO S3 Storage"

4. **Authentication**:
   - **AWS Access Key**: `minioadmin`
   - **AWS Secret Key**: `minioadmin`
   - **IAM Role**: Leave blank
   - **Assume Role**: Leave blank

5. **CRITICAL - Advanced Options**:
   - ✅ **Check "Enable compatibility mode"** (VERY IMPORTANT!)
   - Click **"Show advanced options"** or **"Advanced Options"**
   - Click **"Add property"** button THREE times
   - Add these three properties:

   | Property Name | Property Value |
   |--------------|----------------|
   | `fs.s3a.endpoint` | `http://minio:9000` |
   | `fs.s3a.path.style.access` | `true` |
   | `fs.s3a.connection.ssl.enabled` | `false` |

6. **Other Settings** (leave defaults):
   - Root Path: `/` or leave empty
   - Max Connections: 100 (or default)
   - Request Timeout: 60 (or default)

7. **Click "Save"**

### Success Indicators:
- You should see "minio" appear in the left sidebar
- No error messages
- Can expand "minio" to see buckets

### Common Errors and Fixes:
- **"Unable to connect"**: Check "Enable compatibility mode" is checked
- **"Access denied"**: Verify credentials are exactly `minioadmin`
- **"Connection refused"**: Ensure endpoint is `http://minio:9000` (not localhost)

---

## Step 4: Navigate to Dataset (1 minute)

1. In the left sidebar, click on **"minio"** to expand it
2. You should see two buckets:
   - `iceberg-warehouse` (ignore this)
   - `zeek-data` (this is our data)
3. Click **"zeek-data"** to expand
4. You should see **"network-activity-ocsf"** folder
5. Click on **"network-activity-ocsf"**

---

## Step 5: Format the Dataset (30 seconds)

When you click on "network-activity-ocsf", you'll see either:
- Raw folder contents (if not formatted)
- Data preview (if already formatted)

### If Not Formatted:
1. Look for **"Format Folder"** button or **"⋯"** menu → **"Format Folder"**
2. In the Format dialog:
   - **File Format**: Select **"Parquet"**
   - **Compression**: Should auto-detect as "snappy"
   - Click **"Save"**

### Success Indicators:
- You see a data preview with columns
- Can see field names like `activity_name`, `class_uid`, etc.
- Shows record count (should be 100,000)

---

## Step 6: Test Query (30 seconds)

Click **"New Query"** or use the SQL editor and paste:

```sql
SELECT
  activity_name,
  COUNT(*) as event_count,
  SUM(traffic_bytes_in + traffic_bytes_out) as total_bytes
FROM minio."zeek-data"."network-activity-ocsf"
GROUP BY activity_name
ORDER BY event_count DESC;
```

Click **"Run"** or press Ctrl+Enter

### Expected Results:
```
activity_name | event_count | total_bytes
-----------------------------------------
Traffic       | 30,043      | XX,XXX,XXX
http          | 24,859      | XX,XXX,XXX
ssl           | 24,853      | XX,XXX,XXX
dns           | 10,636      | X,XXX,XXX
ssh           | 3,943       | X,XXX,XXX
```

---

## ✅ Success Checklist

- [ ] Dremio account created/logged in
- [ ] MinIO source added with name "minio"
- [ ] Can see zeek-data bucket
- [ ] network-activity-ocsf formatted as Parquet
- [ ] Test query returns results
- [ ] Shows 100,000 total records

---

## 🚀 Next Steps

Once connected, you can:
1. Create Reflections for 10-100x query speedup
2. Build dashboards
3. Run complex OCSF queries
4. Load more data (1M+ records)

---

## Troubleshooting

### "Cannot connect to S3 source"
1. Verify Docker containers are running: `docker ps`
2. Check MinIO is accessible: `curl http://localhost:9000/minio/health/live`
3. Ensure "Enable compatibility mode" is checked
4. Verify endpoint is `http://minio:9000` not `http://localhost:9000`

### "No data visible"
1. Check data exists: `docker exec zeek-demo-minio mc ls local/zeek-data/network-activity-ocsf/`
2. Try refreshing: Click refresh icon in Dremio
3. Re-format the folder as Parquet

### "Query fails"
1. Check dataset is formatted
2. Verify table name is correct: `minio."zeek-data"."network-activity-ocsf"`
3. Check field names match (they're OCSF-compliant with underscores)

---

**Need Help?** Let me know where you get stuck and I can provide more specific guidance!