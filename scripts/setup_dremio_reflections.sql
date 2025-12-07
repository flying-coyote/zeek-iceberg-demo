-- Dremio Reflections Setup for OCSF Data
-- Run these queries in Dremio SQL Editor after logging in
-- Access Dremio at: http://localhost:9047

-- ============================================
-- Step 1: Verify OCSF Dataset is Available
-- ============================================

-- Check if the dataset exists
SELECT COUNT(*) as record_count
FROM minio."zeek-data"."network-activity-ocsf"
LIMIT 1;

-- Verify OCSF fields are present
SELECT
  class_uid,
  class_name,
  activity_name,
  src_endpoint_ip,
  dst_endpoint_ip,
  traffic_bytes_in,
  traffic_bytes_out,
  connection_info_protocol_name
FROM minio."zeek-data"."network-activity-ocsf"
LIMIT 5;

-- ============================================
-- Step 2: Create Raw Reflection
-- ============================================

-- Raw reflections accelerate SELECT * queries
-- This is done through the Dremio UI:
-- 1. Navigate to: minio > zeek-data > network-activity-ocsf
-- 2. Click on the dataset
-- 3. Click "Reflections" tab
-- 4. Click "Create Raw Reflection"
-- 5. Select all fields (or top 50 most important)
-- 6. Add partition field: event_date
-- 7. Enable the reflection

-- ============================================
-- Step 3: Test Query Performance (Before Reflections)
-- ============================================

-- Query 1: Top Talkers (note the execution time)
SELECT
  src_endpoint_ip,
  dst_endpoint_ip,
  connection_info_protocol_name,
  SUM(traffic_bytes_in + traffic_bytes_out) as total_bytes,
  COUNT(*) as connection_count
FROM minio."zeek-data"."network-activity-ocsf"
WHERE class_uid = 4001
GROUP BY src_endpoint_ip, dst_endpoint_ip, connection_info_protocol_name
ORDER BY total_bytes DESC
LIMIT 20;

-- Query 2: Protocol Distribution (note the execution time)
SELECT
  connection_info_protocol_name,
  COUNT(*) as event_count,
  SUM(traffic_bytes_in + traffic_bytes_out) as total_bytes,
  AVG(traffic_bytes_in + traffic_bytes_out) as avg_bytes
FROM minio."zeek-data"."network-activity-ocsf"
GROUP BY connection_info_protocol_name
ORDER BY event_count DESC;

-- Query 3: Activity Analysis (note the execution time)
SELECT
  activity_name,
  class_name,
  COUNT(*) as events,
  SUM(traffic_bytes_in) as total_bytes_in,
  SUM(traffic_bytes_out) as total_bytes_out,
  COUNT(DISTINCT src_endpoint_ip) as unique_sources,
  COUNT(DISTINCT dst_endpoint_ip) as unique_destinations
FROM minio."zeek-data"."network-activity-ocsf"
WHERE category_uid = 4
GROUP BY activity_name, class_name
ORDER BY events DESC;

-- Query 4: Security Analysis - Egress Traffic
SELECT
  activity_name,
  src_endpoint_is_local,
  dst_endpoint_is_local,
  COUNT(*) as events,
  SUM(traffic_bytes_out) as egress_bytes,
  AVG(traffic_bytes_out) as avg_egress_bytes
FROM minio."zeek-data"."network-activity-ocsf"
WHERE
  class_uid = 4001
  AND src_endpoint_is_local = true
  AND dst_endpoint_is_local = false
GROUP BY activity_name, src_endpoint_is_local, dst_endpoint_is_local
ORDER BY egress_bytes DESC;

-- Query 5: Time-based Analysis (if time field exists)
SELECT
  DATE_TRUNC('hour', FROM_UNIXTIME(time / 1000)) as hour,
  COUNT(*) as events,
  COUNT(DISTINCT src_endpoint_ip) as unique_sources,
  COUNT(DISTINCT dst_endpoint_ip) as unique_destinations,
  SUM(traffic_bytes_in + traffic_bytes_out) as total_traffic
FROM minio."zeek-data"."network-activity-ocsf"
GROUP BY DATE_TRUNC('hour', FROM_UNIXTIME(time / 1000))
ORDER BY hour;

-- ============================================
-- Step 4: Create Aggregation Reflections
-- ============================================

-- Through the Dremio UI, create these aggregation reflections:

-- Reflection 1: Protocol & Activity Aggregation
-- Dimensions: connection_info_protocol_name, activity_name, src_endpoint_ip, dst_endpoint_ip
-- Measures: SUM(traffic_bytes_in), SUM(traffic_bytes_out), COUNT(*)
-- Partition: event_date

-- Reflection 2: Security Analysis Aggregation
-- Dimensions: src_endpoint_is_local, dst_endpoint_is_local, activity_name
-- Measures: SUM(traffic_bytes_out), SUM(traffic_bytes_in), COUNT(*)

-- Reflection 3: Time-based Aggregation
-- Dimensions: event_date, class_name, category_name
-- Measures: COUNT(*), COUNT(DISTINCT src_endpoint_ip), COUNT(DISTINCT dst_endpoint_ip)

-- ============================================
-- Step 5: Monitor Reflection Status
-- ============================================

-- Check reflection build status in Dremio UI:
-- 1. Go to: Jobs (left sidebar)
-- 2. Filter by: Type = "Reflection"
-- 3. Monitor progress

-- Once reflections are built (usually 2-5 minutes for 1M records),
-- re-run the queries above and compare execution times.

-- Expected improvements:
-- - Raw queries: 50-80% faster
-- - Aggregation queries: 90-95% faster
-- - Complex joins: 70-90% faster

-- ============================================
-- Step 6: View Query Plans
-- ============================================

-- After reflections are built, view query plan to confirm reflection usage:
-- 1. Run any query
-- 2. Click "Query Profile" tab
-- 3. Look for "Reflection" nodes in the plan
-- 4. Green checkmark = reflection used

-- ============================================
-- Notes for Demo
-- ============================================

-- Key talking points:
-- 1. "Reflections provide 10-100x query acceleration"
-- 2. "Automatic query rewriting - no code changes needed"
-- 3. "Smart refresh policies maintain data freshness"
-- 4. "Cost-based optimizer chooses best reflection automatically"

-- Performance metrics to highlight:
-- - Before reflections: ~2-5 seconds per query
-- - After reflections: ~50-200 milliseconds per query
-- - Acceleration factor: 10-100x improvement