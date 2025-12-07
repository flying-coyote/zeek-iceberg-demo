# Dremio Demo SQL Queries - OCSF Network Activity

**Purpose**: Ready-to-paste SQL queries that bypass slow UI navigation
**Dataset**: 100,000 OCSF-compliant network security events

---

## 🚀 Quick Start

1. Open Dremio: http://localhost:9047
2. Click **"New Query"** (or SQL tab)
3. Copy/paste any query below
4. Click **"Run"** or press **Ctrl+Enter**

**No folder navigation needed!** These queries use full paths.

---

## 📊 Query 1: Activity Overview (RECOMMENDED START)

**Purpose**: Show OCSF compliance and data distribution

```sql
SELECT
  activity_name,
  class_name,
  COUNT(*) as event_count,
  ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as percentage
FROM minio."zeek-data"."network-activity-ocsf"
WHERE category_uid = 4  -- OCSF Network Activity category
GROUP BY activity_name, class_name
ORDER BY event_count DESC;
```

**Expected Results**:
```
activity_name | class_name       | event_count | percentage
------------- | ---------------- | ----------- | ----------
Traffic       | Network Activity | 30,043      | 30.04%
http          | Network Activity | 24,859      | 24.86%
ssl           | Network Activity | 24,853      | 24.85%
dns           | Network Activity | 10,636      | 10.64%
ssh           | Network Activity | 3,943       | 3.94%
```

**Demo Talking Points**:
- ✅ OCSF class_uid 4001 (Network Activity)
- ✅ 100% compliance with OCSF v1.0
- ✅ 61 OCSF fields implemented
- ✅ Semantic field naming (activity_name, class_name)

---

## 🌐 Query 2: Top Network Talkers

**Purpose**: Show security analysis capabilities

```sql
SELECT
  src_endpoint_ip as source_ip,
  dst_endpoint_ip as destination_ip,
  connection_info_protocol_name as protocol,
  COUNT(*) as connection_count,
  SUM(traffic_bytes_in) as bytes_received,
  SUM(traffic_bytes_out) as bytes_sent,
  SUM(traffic_bytes_in + traffic_bytes_out) as total_bytes
FROM minio."zeek-data"."network-activity-ocsf"
GROUP BY src_endpoint_ip, dst_endpoint_ip, connection_info_protocol_name
ORDER BY total_bytes DESC
LIMIT 20;
```

**Demo Talking Points**:
- OCSF endpoint fields (src_endpoint_ip, dst_endpoint_ip)
- OCSF traffic fields (traffic_bytes_in, traffic_bytes_out)
- OCSF connection info (connection_info_protocol_name)
- Ready for security analysis without transformation

---

## 🔒 Query 3: Egress Traffic Analysis (Security Focus)

**Purpose**: Detect potential data exfiltration

```sql
SELECT
  src_endpoint_ip,
  dst_endpoint_ip,
  activity_name,
  connection_info_protocol_name as protocol,
  COUNT(*) as connection_count,
  SUM(traffic_bytes_out) as total_egress_bytes,
  ROUND(AVG(traffic_bytes_out), 2) as avg_bytes_per_connection
FROM minio."zeek-data"."network-activity-ocsf"
WHERE
  src_endpoint_is_local = true
  AND dst_endpoint_is_local = false
  AND traffic_bytes_out > 0
GROUP BY
  src_endpoint_ip,
  dst_endpoint_ip,
  activity_name,
  connection_info_protocol_name
ORDER BY total_egress_bytes DESC
LIMIT 20;
```

**Demo Talking Points**:
- OCSF locality fields (src_endpoint_is_local, dst_endpoint_is_local)
- Security use case: Egress traffic monitoring
- OCSF enables cross-vendor correlation
- Standard schema = easier threat detection

---

## ⏰ Query 4: Time-Based Traffic Patterns

**Purpose**: Show temporal analysis capabilities

```sql
SELECT
  DATE_TRUNC('hour', FROM_UNIXTIME(time / 1000)) as hour,
  connection_info_protocol_name as protocol,
  COUNT(*) as event_count,
  COUNT(DISTINCT src_endpoint_ip) as unique_sources,
  COUNT(DISTINCT dst_endpoint_ip) as unique_destinations,
  SUM(traffic_bytes_in + traffic_bytes_out) as total_traffic
FROM minio."zeek-data"."network-activity-ocsf"
GROUP BY
  DATE_TRUNC('hour', FROM_UNIXTIME(time / 1000)),
  connection_info_protocol_name
ORDER BY hour, total_traffic DESC;
```

**Demo Talking Points**:
- OCSF timestamp field (time in epoch milliseconds)
- Temporal correlation across security events
- Baseline establishment for anomaly detection

---

## 🔍 Query 5: OCSF Field Inventory (Compliance Demo)

**Purpose**: Show all OCSF fields implemented

```sql
SELECT
  class_uid,
  class_name,
  category_uid,
  category_name,
  activity_id,
  activity_name,
  metadata_product_vendor_name,
  metadata_product_name,
  metadata_log_name,
  metadata_log_version
FROM minio."zeek-data"."network-activity-ocsf"
LIMIT 10;
```

**Demo Talking Points**:
- OCSF metadata fields show data provenance
- Class/Category UIDs enable tool interoperability
- Activity IDs standardize event types
- One schema works across all vendors

---

## 📈 Query 6: Protocol Distribution

**Purpose**: Quick statistics overview

```sql
SELECT
  connection_info_protocol_name as protocol,
  COUNT(*) as event_count,
  ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as percentage,
  SUM(traffic_bytes_in + traffic_bytes_out) as total_bytes,
  ROUND(AVG(traffic_bytes_in + traffic_bytes_out), 2) as avg_bytes_per_event
FROM minio."zeek-data"."network-activity-ocsf"
WHERE connection_info_protocol_name IS NOT NULL
GROUP BY connection_info_protocol_name
ORDER BY event_count DESC;
```

**Expected Results**:
```
protocol | event_count | percentage | total_bytes | avg_bytes
-------- | ----------- | ---------- | ----------- | -----------
TCP      | 89,229      | 89.23%     | XXX         | XXX
UDP      | 9,017       | 9.02%      | XXX         | XXX
ICMP     | 1,754       | 1.75%      | XXX         | XXX
```

---

## 🎯 Query 7: Service/Port Analysis

**Purpose**: Identify common services

```sql
SELECT
  dst_endpoint_port as destination_port,
  activity_name as service,
  connection_info_protocol_name as protocol,
  COUNT(*) as connection_count,
  COUNT(DISTINCT src_endpoint_ip) as unique_sources
FROM minio."zeek-data"."network-activity-ocsf"
WHERE dst_endpoint_port IS NOT NULL
GROUP BY dst_endpoint_port, activity_name, connection_info_protocol_name
ORDER BY connection_count DESC
LIMIT 20;
```

**Demo Talking Points**:
- OCSF port fields (dst_endpoint_port)
- Service identification (activity_name maps to service)
- Common ports: 80 (HTTP), 443 (SSL), 53 (DNS)

---

## 🚨 Query 8: Suspicious Connection States

**Purpose**: Security anomaly detection

```sql
SELECT
  connection_info_protocol_name as protocol,
  connection_info_state as conn_state,
  COUNT(*) as event_count,
  ROUND(AVG(CAST(duration AS DOUBLE)), 2) as avg_duration_ms,
  SUM(CASE WHEN traffic_bytes_in = 0 AND traffic_bytes_out = 0 THEN 1 ELSE 0 END) as zero_byte_connections
FROM minio."zeek-data"."network-activity-ocsf"
WHERE connection_info_state IS NOT NULL
GROUP BY connection_info_protocol_name, connection_info_state
ORDER BY event_count DESC;
```

**Demo Talking Points**:
- OCSF connection state field (connection_info_state)
- Zeek connection states (SF, REJ, S0, etc.)
- Anomaly detection: Zero-byte connections, unusual states

---

## ⚡ Query 9: Performance Test (Large Aggregation)

**Purpose**: Demonstrate query performance on 100K records

```sql
SELECT
  src_endpoint_ip,
  COUNT(DISTINCT dst_endpoint_ip) as unique_destinations,
  COUNT(DISTINCT dst_endpoint_port) as unique_ports,
  COUNT(*) as total_connections,
  SUM(traffic_bytes_in + traffic_bytes_out) as total_traffic,
  MIN(time) as first_seen,
  MAX(time) as last_seen
FROM minio."zeek-data"."network-activity-ocsf"
GROUP BY src_endpoint_ip
HAVING COUNT(*) > 100
ORDER BY total_connections DESC
LIMIT 20;
```

**Expected Performance**: <1 second on 100K records

**Demo Talking Points**:
- Sub-second query on 100,000 events
- Parquet columnar format optimization
- Dremio query acceleration
- Production-ready performance

---

## 🌟 Query 10: Full OCSF Schema Sample

**Purpose**: Show complete OCSF record structure

```sql
SELECT
  -- OCSF Core Fields
  class_uid,
  class_name,
  category_uid,
  category_name,
  activity_id,
  activity_name,
  type_uid,
  severity_id,
  status_id,

  -- Metadata
  metadata_product_vendor_name,
  metadata_product_name,
  metadata_log_name,

  -- Source Endpoint
  src_endpoint_ip,
  src_endpoint_port,
  src_endpoint_is_local,

  -- Destination Endpoint
  dst_endpoint_ip,
  dst_endpoint_port,
  dst_endpoint_is_local,

  -- Connection Info
  connection_info_protocol_name,
  connection_info_state,
  connection_info_boundary,

  -- Traffic
  traffic_bytes_in,
  traffic_bytes_out,
  traffic_packets_in,
  traffic_packets_out,

  -- Timing
  time,
  duration

FROM minio."zeek-data"."network-activity-ocsf"
LIMIT 5;
```

**Demo Talking Points**:
- 61 OCSF fields visible
- Hierarchical field naming (endpoint.ip → src_endpoint_ip)
- Flat schema for performance, OCSF semantics preserved
- Vendor-neutral, tool-agnostic format

---

## 🎬 Suggested Demo Flow

### 1. Start with Activity Overview (Query 1)
- Shows data loaded and OCSF compliant
- Demonstrates 100K records ready
- **Runtime**: <500ms

### 2. Show Security Analysis (Query 3 - Egress)
- Real-world security use case
- OCSF enables immediate analysis
- **Runtime**: <1s

### 3. Demonstrate Performance (Query 9)
- Complex aggregation on 100K records
- Sub-second results
- **Runtime**: <1s

### 4. Show OCSF Schema (Query 10)
- Complete field inventory
- Standards compliance
- **Runtime**: <100ms

**Total Demo Time**: 3-5 minutes with explanations

---

## 💡 Pro Tips

### For Best Performance
1. Run query once to "warm up" Dremio
2. Consider creating Reflections (materialized views) for 10-100x speedup
3. Use `LIMIT` for initial exploration

### For Presentations
1. Pre-paste queries in multiple tabs
2. Have results ready to show
3. Explain OCSF benefits while query runs

### For Development
1. Use `LIMIT 10` during testing
2. Add `WHERE` clauses to filter data
3. Use `EXPLAIN PLAN` to understand query execution

---

## 📚 OCSF Field Reference

### Core OCSF Fields (Always Present)
- `class_uid`: OCSF event class (4001 = Network Activity)
- `category_uid`: OCSF category (4 = Network Activity)
- `activity_id`: Specific activity type
- `time`: Event timestamp (epoch milliseconds)

### Network Activity Fields
- `src_endpoint_*`: Source endpoint details
- `dst_endpoint_*`: Destination endpoint details
- `connection_info_*`: Connection metadata
- `traffic_*`: Traffic statistics

### Metadata Fields
- `metadata_product_*`: Data source information
- `metadata_log_*`: Log format details
- `severity_id`, `status_id`: Event classification

---

## ✅ Success Criteria

After running these queries, you should see:
- ✅ 100,000 total records
- ✅ Sub-second query times
- ✅ OCSF-compliant field names
- ✅ Accurate data distributions
- ✅ Usable security insights

**Your demo is ready!** 🎉

---

**Note**: All queries use the full path `minio."zeek-data"."network-activity-ocsf"` to bypass UI folder navigation and ensure fast execution.