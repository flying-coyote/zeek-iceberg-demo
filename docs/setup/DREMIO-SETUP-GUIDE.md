# Dremio Configuration Guide

**Access**: http://localhost:9047

---

## Step 1: Create Admin Account (First Visit)

1. **Open browser**: http://localhost:9047
2. **You'll see**: "Welcome to Dremio" page
3. **Fill in**:
   - First Name: Jeremy
   - Last Name: Wiley
   - Email: jeremy@example.com (any email works)
   - Username: admin
   - Password: (your choice - remember this!)
4. **Click**: "Create Account"

---

## Step 2: Add Hive Source (Iceberg Catalog)

### 2.1 Navigate to Sources
- Click **"+ Add Source"** button (top right)
- Or click **"Add a source"** from home page

### 2.2 Select Hive
- Scroll to find **"Hive"** in the source types
- Click **"Hive"**

### 2.3 Configure Hive Connection
**General Settings**:
- **Name**: `hive_metastore`
- **Hive Metastore Host**: `hive-metastore`
- **Port**: `9083`

**Advanced Options** (expand if needed):
- Leave defaults (Kerberos: None)

**Click**: "Save"

### 2.4 Verify Connection
- You should see `hive_metastore` appear in left sidebar
- Click on it to expand
- You might see empty (no tables yet) - that's expected!

---

## Step 3: Add MinIO Source (S3 Storage)

### 3.1 Add New Source
- Click **"+ Add Source"** again

### 3.2 Select Amazon S3
- Find **"Amazon S3"** in the list
- Click **"Amazon S3"**

### 3.3 Configure MinIO Connection

**General Settings**:
- **Name**: `minio`

**Authentication**:
- **AWS Access Key**: `minioadmin`
- **AWS Secret Key**: `minioadmin`

**Advanced Options** (EXPAND THIS - IMPORTANT!):

Scroll down and expand "Advanced Options"

Click **"Add Property"** twice and add these properties:

**Property 1**:
- Name: `fs.s3a.endpoint`
- Value: `http://minio:9000`

**Property 2**:
- Name: `fs.s3a.path.style.access`
- Value: `true`

**Property 3** (Optional but recommended):
- Name: `fs.s3a.connection.ssl.enabled`
- Value: `false`

**Other Settings**:
- **Enable compatibility mode**: ✓ (Check this box)
- **Root Path**: `/` (leave as is)
- **Enable asynchronous access**: ✓ (optional, improves performance)

**Click**: "Save"

### 3.4 Verify MinIO Connection
- You should see `minio` in left sidebar
- Click to expand
- You should see buckets:
  - `iceberg-warehouse`
  - `zeek-data`

---

## Step 4: Test the Setup

### 4.1 Check Hive Connection
```sql
-- In Dremio SQL editor, try:
SHOW SCHEMAS IN hive_metastore;
```

**Expected**: Should show any databases (might be empty if no tables created yet)

### 4.2 Check MinIO Connection
```sql
-- Check MinIO buckets
SHOW SCHEMAS IN minio;
```

**Expected**: Should show `iceberg-warehouse` and `zeek-data`

---

## Step 5: Create Test Table (Optional)

Once we load data with Python script, you can query it:

```sql
-- After data is loaded, this should work:
SELECT * FROM hive_metastore.security_data.network_activity LIMIT 10;
```

---

## Troubleshooting

### "Unable to connect to Hive Metastore"
- **Check**: Hive container is running
  ```bash
  docker ps | grep hive
  ```
- **Verify**: Hostname is `hive-metastore` (not localhost)

### "S3 bucket not accessible"
- **Check**: MinIO container is running
  ```bash
  docker ps | grep minio
  ```
- **Verify**: Advanced properties are set correctly
  - `fs.s3a.endpoint` = `http://minio:9000`
  - `fs.s3a.path.style.access` = `true`

### "Cannot see buckets in MinIO source"
- **Check**: Buckets exist
  ```bash
  docker exec zeek-demo-minio mc ls myminio
  ```
- **Refresh**: Click refresh icon in Dremio sidebar

---

## What's Next?

After configuring Dremio:
1. ✅ Hive source connected
2. ✅ MinIO (S3) source connected
3. 🔲 Load data with Python script (next step!)
4. 🔲 Create reflections for query acceleration
5. 🔲 Run demo queries

**Next**: Run the Python script to load Zeek → OCSF → Iceberg data!
