# Trino Integration - Deferred for Later

**Status**: ⏸️ **DEFERRED** - Complete after Dremio demo
**Priority**: Medium (Nice-to-have alternative query engine)
**Estimated Time**: 30-45 minutes

---

## Reason for Deferral

Trino requires additional memory resources and should be tested **after** the Dremio demo is complete. This allows us to:
1. ✅ Focus on getting Dremio demo perfect first
2. ✅ Shut down unnecessary services to free up resources
3. ✅ Give Trino full memory allocation for optimal performance
4. ✅ Compare Trino vs Dremio side-by-side on same queries

---

## Current Status

### ✅ What's Complete
- Docker Compose configuration created (`docker-compose.trino.yml`)
- Trino configuration files created:
  - `config/trino/config.properties` (memory optimized)
  - `config/trino/jvm.config` (JVM settings)
  - `config/trino/catalog/hive.properties` (Hive Metastore connector)
  - `config/trino/catalog/minio.properties` (Direct S3 access)
- Memory settings tuned for container environment

### ⚠️ What Needs Work
- Final memory tuning (encountered heap size conflicts)
- Container startup validation
- OCSF table creation
- Query performance benchmarking

---

## When to Resume Trino Work

### Prerequisites
1. ✅ Dremio demo complete and validated
2. ✅ Dremio reflections created and tested
3. ✅ Performance benchmarks collected from Dremio
4. ✅ Ready to shut down Dremio temporarily

### Resource Management Strategy

**Before Starting Trino**:
```bash
# Stop Dremio to free up memory (8GB+)
docker stop zeek-demo-dremio

# Optional: Stop Spark if not needed
docker stop zeek-demo-spark-master zeek-demo-spark-worker

# Verify available memory
free -h
```

**Start Trino with Full Resources**:
```bash
cd /home/jerem/zeek-iceberg-demo
docker-compose -f docker-compose.yml -f docker-compose.trino.yml up -d trino
```

---

## Trino Setup Tasks (When Ready)

### 1. Fix Memory Configuration (10 min)
**Issue**: Current config has heap size conflicts
**Solution**: Adjust `config/trino/config.properties`:
```properties
# Current (causing issues)
query.max-memory=2GB
query.max-memory-per-node=2GB

# Try lower values first
query.max-memory=1.5GB
query.max-memory-per-node=1.5GB
```

And `config/trino/jvm.config`:
```
# Increase heap size to 4G
-Xmx4G
```

### 2. Verify Trino Startup (5 min)
```bash
# Check Trino is running
docker ps | grep trino

# Check logs for errors
docker logs zeek-demo-trino

# Test Trino UI
curl http://localhost:8080/ui/

# Test Trino CLI
docker exec -it zeek-demo-trino trino --server localhost:8080 --catalog hive
```

### 3. Create OCSF Tables in Trino (15 min)
```sql
-- Connect to Trino CLI
docker exec -it zeek-demo-trino trino --server localhost:8080 --catalog hive

-- Create external table pointing to OCSF data
CREATE SCHEMA IF NOT EXISTS hive.ocsf_security;

CREATE TABLE IF NOT EXISTS hive.ocsf_security.network_activity (
  -- Core OCSF fields
  activity_id INTEGER,
  activity_name VARCHAR,
  category_name VARCHAR,
  category_uid INTEGER,
  class_name VARCHAR,
  class_uid INTEGER,

  -- Source endpoint
  src_endpoint_ip VARCHAR,
  src_endpoint_port INTEGER,
  src_endpoint_is_local BOOLEAN,

  -- Destination endpoint
  dst_endpoint_ip VARCHAR,
  dst_endpoint_port INTEGER,
  dst_endpoint_is_local BOOLEAN,

  -- Connection info
  connection_info_protocol_name VARCHAR,
  connection_info_protocol_num INTEGER,
  connection_info_uid VARCHAR,

  -- Traffic metrics
  traffic_bytes_in BIGINT,
  traffic_bytes_out BIGINT,
  traffic_packets_in BIGINT,
  traffic_packets_out BIGINT,

  -- Time fields
  time BIGINT,
  event_date VARCHAR
)
WITH (
  external_location = 's3a://zeek-data/network-activity-ocsf/',
  format = 'PARQUET'
);

-- Verify table
SELECT COUNT(*) FROM hive.ocsf_security.network_activity;

-- Sample query
SELECT * FROM hive.ocsf_security.network_activity LIMIT 10;
```

### 4. Run Performance Benchmarks (15 min)
Run the same queries used for Dremio and compare:

```sql
-- Query 1: Top Talkers
SELECT
  src_endpoint_ip,
  dst_endpoint_ip,
  connection_info_protocol_name,
  SUM(traffic_bytes_in + traffic_bytes_out) as total_bytes,
  COUNT(*) as connection_count
FROM hive.ocsf_security.network_activity
WHERE class_uid = 4001
GROUP BY src_endpoint_ip, dst_endpoint_ip, connection_info_protocol_name
ORDER BY total_bytes DESC
LIMIT 20;

-- Query 2: Protocol Distribution
SELECT
  connection_info_protocol_name,
  COUNT(*) as event_count,
  SUM(traffic_bytes_in + traffic_bytes_out) as total_bytes
FROM hive.ocsf_security.network_activity
GROUP BY connection_info_protocol_name
ORDER BY event_count DESC;

-- Query 3: Security Analysis
SELECT
  activity_name,
  src_endpoint_is_local,
  dst_endpoint_is_local,
  COUNT(*) as events,
  SUM(traffic_bytes_out) as egress_bytes
FROM hive.ocsf_security.network_activity
WHERE
  class_uid = 4001
  AND src_endpoint_is_local = true
  AND dst_endpoint_is_local = false
GROUP BY activity_name, src_endpoint_is_local, dst_endpoint_is_local
ORDER BY egress_bytes DESC;
```

---

## Comparison Criteria: Trino vs Dremio

### Performance Metrics to Collect
| Metric | Dremio | Trino | Winner |
|--------|--------|-------|--------|
| Simple SELECT query | ? | ? | TBD |
| Aggregation query | ? | ? | TBD |
| JOIN query | ? | ? | TBD |
| Memory usage | ? | ? | TBD |
| Startup time | ? | ? | TBD |
| Ease of use | ? | ? | TBD |

### Feature Comparison
| Feature | Dremio | Trino |
|---------|--------|-------|
| Reflections/Caching | ✅ Yes | ❌ No |
| S3 Direct Access | ✅ Yes | ✅ Yes |
| Hive Metastore | ✅ Yes | ✅ Yes |
| SQL Compliance | ANSI SQL | ANSI SQL |
| Web UI | ✅ Excellent | ✅ Good |
| JDBC/ODBC | ✅ Yes | ✅ Yes |
| Cloud Native | ✅ Yes | ✅ Yes |

### Use Case Fit
**Dremio Best For**:
- Interactive analytics with caching
- Self-service BI
- Query acceleration needed
- Non-technical users

**Trino Best For**:
- Ad-hoc queries without caching
- Federated queries across sources
- Cost-conscious deployments
- Technical analysts comfortable with SQL

---

## Expected Outcome

After testing Trino, we should be able to answer:

1. **Does Trino work with our OCSF data?** (Yes/No)
2. **How does Trino performance compare to Dremio?** (Faster/Slower/Same)
3. **Should we recommend Trino as alternative?** (Yes/No/Depends)
4. **What are the trade-offs?** (Memory, speed, ease of use)

---

## Decision Framework

**Choose Dremio if**:
- Need query acceleration (reflections)
- Want excellent UI/UX
- Prefer caching for repeated queries
- Self-service analytics is priority

**Choose Trino if**:
- Need federated queries across many sources
- Want lower resource usage
- Don't need caching/reflections
- Prefer pure open-source (no commercial entity)

**Choose Both if**:
- Want flexibility for different use cases
- Have resources to run both
- Different teams prefer different tools

---

## Files Already Created

1. ✅ `docker-compose.trino.yml` - Trino service definition
2. ✅ `config/trino/config.properties` - Coordinator config
3. ✅ `config/trino/jvm.config` - JVM settings
4. ✅ `config/trino/catalog/hive.properties` - Hive connector
5. ✅ `config/trino/catalog/minio.properties` - S3 connector

---

## Quick Start (When Ready)

```bash
# 1. Stop Dremio to free resources
docker stop zeek-demo-dremio

# 2. Start Trino
cd /home/jerem/zeek-iceberg-demo
docker-compose -f docker-compose.yml -f docker-compose.trino.yml up -d trino

# 3. Wait for startup
sleep 30

# 4. Check logs
docker logs zeek-demo-trino

# 5. Access Trino UI
# Browser: http://localhost:8080

# 6. Connect with CLI
docker exec -it zeek-demo-trino trino --server localhost:8080 --catalog hive

# 7. Create OCSF tables (SQL above)

# 8. Run benchmarks

# 9. Document results

# 10. Decide: Dremio vs Trino vs Both
```

---

## Reminder

**Don't forget to restart Dremio when done testing Trino**:
```bash
docker start zeek-demo-dremio
```

---

**Status**: Ready to resume when Dremio demo is complete
**Estimated Completion**: 30-45 minutes total
**Risk Level**: Low (all config files ready)

---

*Deferred on November 27, 2025 - Focus on Dremio demo first* ⏸️