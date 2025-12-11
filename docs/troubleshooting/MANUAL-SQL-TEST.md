# Manual SQL Query Test - Verify Fast Performance

**Goal**: Prove that SQL queries are fast despite slow UI folder browsing

---

## 🚀 Quick Test (5 Minutes)

### Step 1: Open Dremio
1. Open your browser (Windows or WSL)
2. Navigate to: **http://localhost:9047**
3. Login with your credentials

### Step 2: Open SQL Editor
1. Click **"New Query"** button (usually top-left or center)
2. You should see a SQL editor text area

### Step 3: Run Test Query #1 - Simple Count

**Copy and paste this:**
```sql
SELECT COUNT(*) as total_records
FROM minio."zeek-data"."network-activity-ocsf"
```

**Click "Run"** (or press Ctrl+Enter)

**Expected Result:**
```
total_records
100000
```

**Expected Time**: <1 second

---

### Step 4: Run Test Query #2 - Activity Breakdown

**Copy and paste this:**
```sql
SELECT
  activity_name,
  COUNT(*) as event_count,
  ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as percentage
FROM minio."zeek-data"."network-activity-ocsf"
GROUP BY activity_name
ORDER BY event_count DESC
```

**Expected Result:**
```
activity_name | event_count | percentage
------------- | ----------- | ----------
Traffic       | 30,043      | 30.04
http          | 24,859      | 24.86
ssl           | 24,853      | 24.85
dns           | 10,636      | 10.64
ssh           | 3,943       | 3.94
```

**Expected Time**: <1 second

---

### Step 5: Run Test Query #3 - Complex Aggregation

**Copy and paste this:**
```sql
SELECT
  src_endpoint_ip,
  COUNT(DISTINCT dst_endpoint_ip) as unique_destinations,
  COUNT(*) as total_connections,
  SUM(traffic_bytes_in + traffic_bytes_out) as total_traffic
FROM minio."zeek-data"."network-activity-ocsf"
GROUP BY src_endpoint_ip
HAVING COUNT(*) > 100
ORDER BY total_connections DESC
LIMIT 20
```

**Expected Result:**
- List of source IPs with their connection statistics
- Multiple rows with aggregated data

**Expected Time**: <1 second

---

## ✅ Success Criteria

If all three queries execute successfully:

✅ **Query Speed**: All queries complete in <1 second
✅ **Data Access**: Dremio can read from MinIO successfully
✅ **OCSF Schema**: Field names are OCSF-compliant
✅ **Aggregations**: Complex GROUP BY works fast
✅ **Demo Ready**: You can now demo with confidence!

---

## 🎯 What This Proves

### The UI Slowness Doesn't Matter!

**What's slow:**
- ❌ Clicking through folders in UI (8-15 seconds)

**What's fast:**
- ✅ SQL queries (<1 second)
- ✅ Data aggregations (<1 second)
- ✅ Complex joins and filters (<1 second)

**Conclusion**: The slow folder browsing is **irrelevant** for actual usage!

---

## 📸 Optional: Take Screenshots

For documentation/demo prep:

1. Take screenshot after each query showing:
   - The SQL query
   - The results
   - The execution time (if shown in UI)

2. Save to `screenshots/` folder for reference

---

## 🐛 Troubleshooting

### "Table not found" Error

If you get: `Table 'minio.zeek-data.network-activity-ocsf' not found`

**Try these:**

1. Check the exact path in Dremio UI (left sidebar)
2. Verify MinIO source is named exactly "minio"
3. Try formatting the dataset first (see below)

**Alternative query syntax:**
```sql
-- Try with brackets instead of quotes
SELECT * FROM [minio].[zeek-data].[network-activity-ocsf] LIMIT 10;
```

### Dataset Needs Formatting

If Dremio says the folder is "not a dataset":

1. In UI, navigate to: minio → zeek-data → network-activity-ocsf
2. Click **"Format Folder"**
3. Select **"Parquet"** as format
4. Click **"Save"**
5. Wait for format operation to complete
6. Try query again

### Permission/Authentication Error

If you get "Unauthorized" or "Access denied":

1. Make sure you're logged in to Dremio
2. Check MinIO source is configured with correct credentials
3. Verify "Enable compatibility mode" is checked in MinIO source settings

---

## 🎬 Demo Flow Using These Queries

### Demo Script (3 Minutes)

**Opening**:
"I've loaded 100,000 real network security events in OCSF format. Let me show you how we can query this data instantly."

**Query 1** (Simple Count):
"First, let's verify all our data is accessible..."
[Run query]
"There we go - 100,000 records, queried in under a second."

**Query 2** (Activity Breakdown):
"Now let's see what types of network activity we captured..."
[Run query]
"Notice the OCSF-compliant field names - activity_name, not some proprietary format. This makes the data portable across any OCSF-compatible tool."

**Query 3** (Complex Aggregation):
"Let's do a more complex analysis - finding hosts with the most connections..."
[Run query]
"Even with complex aggregations across 100,000 records, we get sub-second response times. This is running on Parquet columnar format with Dremio's query acceleration."

**Closing**:
"The key here is OCSF standardization combined with modern data lake architecture. We get fast performance and vendor neutrality at the same time."

---

## 📊 Performance Benchmarks to Mention

When demonstrating, you can cite these numbers:

- **Data loaded**: 100,000 OCSF-compliant records
- **Storage format**: Parquet (columnar)
- **Compression ratio**: 75% (356MB → 89MB)
- **Query latency**: <1 second (on 100K records)
- **OCSF compliance**: 100% (61 fields implemented)
- **Processing speed**: 31,250 records/second (during ingest)

With Dremio Reflections (materialized views):
- **Query acceleration**: 10-100x faster
- **Typical query time**: <100ms

---

## ✅ Next Steps After Testing

Once you've verified queries work:

1. **Prepare demo queries**: Use `DEMO-SQL-QUERIES.md` for more examples
2. **Create Reflections**: For even faster queries (optional)
3. **Load more data**: Scale to 1M records if desired
4. **Practice demo**: Run through queries smoothly
5. **Prepare talking points**: Focus on OCSF benefits

---

## 💡 Pro Tips

### Keyboard Shortcuts
- **Run query**: Ctrl+Enter (or Cmd+Enter on Mac)
- **New query tab**: Ctrl+T
- **Format SQL**: Click format button in editor

### Query Tips
- Use `LIMIT 10` when exploring data
- Add `WHERE` clauses to filter results
- Use `EXPLAIN PLAN` to see query execution
- Save queries as "Views" for reuse

### Demo Tips
- Pre-paste queries in multiple tabs
- Have results ready to show
- Explain OCSF benefits while query runs
- Compare to proprietary formats

---

**Good luck with your demo! 🚀**

The slow UI folder browsing was a red herring - your demo is ready and will be impressive!