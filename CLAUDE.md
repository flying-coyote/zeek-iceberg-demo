# CLAUDE.md - Zeek OCSF Dremio Demo Project

> **For AI Assistants**: This file contains everything you need to understand and work on this project effectively.

## Project Overview

**Name**: Zeek → OCSF → Dremio Demo Lab
**Purpose**: Production-ready demonstration of a modern security data lake using OCSF standardization
**Status**: 95% complete, demo-ready, awaiting reflection deployment
**Owner**: jerem
**Stack**: Docker Compose, Python, MinIO (S3), Dremio, Apache Parquet, OCSF v1.1

### What This Project Does

Demonstrates a complete security data pipeline:
1. **Ingest**: Zeek network logs (conn.log format)
2. **Transform**: Convert to OCSF v1.1 Network Activity (class 4001)
3. **Store**: Parquet format in MinIO (S3-compatible storage)
4. **Query**: Dremio SQL engine with reflection-based acceleration
5. **Analyze**: Security analytics with 10-100x query speedup

### Why This Project Exists

- **Standardization**: Show OCSF (Linux Foundation standard) in practice
- **Performance**: Demonstrate Dremio reflections (materialized views)
- **Modern Stack**: Object storage + query engine architecture
- **Security Focus**: Real-world network traffic analysis

### Key Metrics

- **Data**: 1M OCSF-compliant network activity records
- **Size**: 89.6MB compressed Parquet (75% compression ratio)
- **Fields**: 65 OCSF fields per record
- **Performance**: 30K records/sec transformation speed
- **Query Speedup**: 10-100x with reflections (target)

---

## Architecture

### Components

```
┌─────────────┐
│   Zeek      │ Network traffic → conn.log
└──────┬──────┘
       │
       v
┌─────────────┐
│   Python    │ Transform to OCSF v1.1
└──────┬──────┘
       │
       v
┌─────────────┐
│   MinIO     │ S3-compatible object storage
│  (Port 9001)│ Buckets: zeek-data, iceberg-warehouse
└──────┬──────┘
       │
       v
┌─────────────┐
│   Dremio    │ SQL query engine + reflections
│  (Port 9047)│ Credentials: admin / <your_password>
└─────────────┘
```

### Docker Services

| Service | Port | Purpose | Status Check |
|---------|------|---------|-------------|
| MinIO | 9000 (API), 9001 (UI) | S3 storage | http://localhost:9001 |
| Dremio | 9047 | Query engine | http://localhost:9047 |
| PostgreSQL | 5432 | Hive metastore backend | Internal only |
| Hive Metastore | 9083 | Iceberg catalog | Internal only |
| Spark Master | 8080 | Processing engine | http://localhost:8080 |
| Spark Worker | - | Spark executor | Managed by master |
| Jupyter | 8888 | Notebooks (optional) | http://localhost:8888 |

### Data Flow

```
data/sample_zeek_conn.log (100K records)
  ↓ [scripts/load_real_zeek_to_ocsf.py]
  ↓
MinIO: s3://zeek-data/network-activity-ocsf/*.parquet
  ↓
Dremio: minio."zeek-data"."network-activity-ocsf"
  ↓ [Reflections accelerate queries]
  ↓
SQL queries (10-100x faster)
```

### OCSF Schema

**Class**: Network Activity (4001)
**Category**: Network Activity (4)
**Version**: OCSF v1.1

**Key Fields**:
- `class_uid`, `class_name`, `category_name`, `activity_name`
- `src_endpoint_ip`, `dst_endpoint_ip`, `src_endpoint_port`, `dst_endpoint_port`
- `connection_info_protocol_name`, `connection_info_uid`
- `traffic_bytes_in`, `traffic_bytes_out`, `traffic_packets_in`, `traffic_packets_out`
- `time`, `event_date` (for partitioning)

---

## Quick Start (5 Minutes)

### Prerequisites
- Docker and Docker Compose installed
- 8GB RAM available
- Ports 9000, 9001, 9047 available

### Start Infrastructure

```bash
# From project root
docker compose up -d

# Verify all services healthy (wait 60s)
docker ps

# Expected: 7 containers running
```

### Access UIs

- **MinIO Console**: http://localhost:9001 (minioadmin / minioadmin)
- **Dremio UI**: http://localhost:9047 (admin / <your_password>)
- **Spark UI**: http://localhost:8080

### Load Data

```bash
# Activate Python environment
source venv/bin/activate

# Load 1M OCSF records (already done if data exists)
python3 scripts/load_real_zeek_to_ocsf.py
```

### Configure Dremio (CRITICAL STEP)

```bash
# Set credentials
export DREMIO_USERNAME="admin"
export DREMIO_PASSWORD="your_password"

# Setup MinIO source (MUST enable compatibility mode!)
python3 scripts/setup_dremio_minio_source.py
```

**Manual alternative**: See `SETUP-MINIO-SOURCE-NOW.md`

### Deploy Reflections

```bash
# After MinIO source is configured
bash run-reflection-setup.sh
```

### Test Queries

```sql
-- In Dremio SQL editor
SELECT COUNT(*) FROM minio."zeek-data"."network-activity-ocsf";
-- Should return: 1,000,000
```

---

## Key Files and Directories

### Critical Files (Must Understand)

| File | Purpose | Read First? |
|------|---------|------------|
| `CLAUDE.md` | This file - AI assistant guide | ✅ YES |
| `README.md` | Human-readable project overview | ✅ YES |
| `PROJECT-STATUS-CURRENT.md` | Living status document | ✅ YES |
| `docker-compose.yml` | Infrastructure definition | If touching services |
| `PROJECT-AUDIT-REPORT.md` | Best practices audit results | For improvements |

### Documentation Structure

```
/
├── CLAUDE.md                     # ← You are here
├── README.md                     # GitHub entry point
├── PROJECT-STATUS-CURRENT.md    # Current state
├── PROJECT-AUDIT-REPORT.md      # Best practices audit
├── FIX-MINIO-CONNECTION.md      # MinIO troubleshooting
├── DEMO-CHEAT-SHEET.md          # Quick demo reference
├── START-DEMO-NOW.md            # Demo presentation guide
└── docs/archive/                # Historical documentation
```

### Scripts Directory

```
scripts/
├── load_real_zeek_to_ocsf.py              # ★ Data loader (1M records)
├── transform_zeek_to_ocsf_flat.py         # Zeek → OCSF transformer
├── setup_dremio_minio_source.py           # MinIO source setup (Playwright)
├── create_reflections_playwright_auto.py  # Reflection deployment (Playwright)
├── test_dremio_login.py                   # Auth diagnostic
├── test_query_performance.py              # Query benchmark
└── check_reflections.py                   # Reflection status check
```

### Data Directories (Bind Mounts)

```
minio-data/
  └── zeek-data/
      └── network-activity-ocsf/
          ├── year=2024/month=12/day=08/*.parquet  # Partitioned data
          └── ...

dremio-data/            # Dremio metadata and reflections
postgres-data/          # Hive metastore database
```

### Configuration

```
config/
  ├── hive-site.xml     # Hive metastore config
  └── dremio/           # Dremio config (if needed)

.claude/
  ├── settings.local.json   # Claude Code permissions
  └── commands/             # Custom slash commands (empty currently)
```

---

## Common Workflows

### 1. Starting the Demo

```bash
# Start infrastructure
docker compose up -d

# Wait 60 seconds for services to initialize
sleep 60

# Verify services
docker ps | grep zeek-demo

# Set credentials
export DREMIO_USERNAME="admin"
export DREMIO_PASSWORD="your_password"

# Check if MinIO source is configured in Dremio
# If not: python3 scripts/setup_dremio_minio_source.py

# Check if reflections exist
source venv/bin/activate
python3 scripts/check_reflections.py

# If reflections don't exist: bash run-reflection-setup.sh
```

### 2. Loading New Data

```bash
# Activate environment
source venv/bin/activate

# Load data (creates partitioned Parquet in MinIO)
python3 scripts/load_real_zeek_to_ocsf.py

# Refresh dataset in Dremio (metadata sync)
# Via UI: Navigate to dataset → Format folder → Save
```

### 3. Creating/Managing Reflections

```bash
# Set credentials first
export DREMIO_USERNAME="admin"
export DREMIO_PASSWORD="your_password"

# Automated (Playwright)
python3 scripts/create_reflections_playwright_auto.py

# Manual
# 1. Open http://localhost:9047
# 2. Navigate to: minio > zeek-data > network-activity-ocsf
# 3. Click "Reflections" tab
# 4. Create Raw + Aggregation reflections
# 5. Wait 2-5 minutes for build
```

### 4. Troubleshooting Dremio Connection

```bash
# Verify MinIO is running
docker ps | grep minio

# Verify Dremio can reach MinIO
docker exec zeek-demo-dremio curl http://minio:9000

# Verify data exists
docker exec zeek-demo-minio ls -lh /data/zeek-data/network-activity-ocsf/

# Check MinIO source in Dremio
# UI: Sources → minio → Settings → MUST have "Enable compatibility mode" checked!

# See detailed guide
cat FIX-MINIO-CONNECTION.md
```

### 5. Giving a Demo

```bash
# Follow the presentation script
cat START-DEMO-NOW.md

# Quick reference
cat DEMO-CHEAT-SHEET.md

# SQL queries to copy-paste
cat DEMO-SQL-QUERIES.md
```

### 6. Stopping/Restarting

```bash
# Stop all services
docker compose down

# Restart (preserves data in bind mounts)
docker compose up -d

# Clean restart (WARNING: deletes all data)
docker compose down -v
rm -rf minio-data/ dremio-data/ postgres-data/
docker compose up -d
```

---

## Conventions and Standards

### Git Commit Messages

Format: `<emoji> <description>`

Examples:
```
✅ Load 100K real Zeek conn logs to MinIO via Parquet
🏗️ Add demo infrastructure - Docker + Python scripts
📚 Consolidate docs - working MinIO + Dremio setup documented
🔧 Fix Dremio MinIO integration - enable compatibility mode
⚡ Increase Playwright login timeout to 20 seconds
```

**Always include attribution**:
```
<commit message>

Generated with [Claude Code](https://claude.ai/code)
via [Happy](https://happy.engineering)

Co-Authored-By: Claude <noreply@anthropic.com>
Co-Authored-By: Happy <yesreply@happy.engineering>
```

### Python Code Style

- **Logging**: Use `logging` module, not `print()`
- **Docstrings**: Required for complex functions
- **Error Handling**: Try/except with informative messages
- **Environment Variables**: Use `os.getenv()` with defaults
- **Credentials**: NEVER hardcode, always from env vars
- **Type Hints**: Use where helpful (function signatures)

Example:
```python
import os
import logging

logger = logging.getLogger(__name__)

DREMIO_USERNAME = os.getenv("DREMIO_USERNAME", "admin")
DREMIO_PASSWORD = os.getenv("DREMIO_PASSWORD", "")

def setup_source(name: str) -> bool:
    """Setup data source in Dremio

    Args:
        name: Source name to create

    Returns:
        True if successful, False otherwise
    """
    try:
        # Implementation
        logger.info(f"✓ Created source: {name}")
        return True
    except Exception as e:
        logger.error(f"Failed to create source: {e}")
        return False
```

### Documentation Style

- **Headers**: Use ATX-style (`# H1`, `## H2`)
- **Code Blocks**: Always specify language (```bash, ```python, ```sql)
- **Emojis**: Use sparingly for visual markers (✅ ❌ ⚠️ 🔴 🟡 🟢)
- **Status Updates**: Keep PROJECT-STATUS-CURRENT.md updated
- **Archive Old Docs**: Move outdated docs to `docs/archive/`

### Naming Conventions

- **Scripts**: `verb_object.py` (e.g., `load_real_zeek_to_ocsf.py`)
- **Docs**: `TOPIC-DESCRIPTION.md` (e.g., `FIX-MINIO-CONNECTION.md`)
- **Docker Services**: `zeek-demo-<service>` (e.g., `zeek-demo-minio`)
- **Buckets**: Lowercase with hyphens (e.g., `zeek-data`)

---

## Troubleshooting

### Problem: Dremio shows "Could not connect to S3 source"

**Solution**: Enable compatibility mode in MinIO source configuration

```bash
# Via UI:
1. Go to http://localhost:9047
2. Sources → minio → Settings (gear icon)
3. Advanced Options → ✅ Enable compatibility mode
4. Save

# See detailed guide:
cat FIX-MINIO-CONNECTION.md
```

### Problem: Playwright scripts timeout during login

**Solution**: Scripts now handle manual login gracefully

```bash
# If script times out but you logged in manually:
# → Script detects successful login and continues

# Increase timeout if needed (already set to 20s):
# Edit scripts/create_reflections_playwright_auto.py
# Line 64: timeout=20000
```

### Problem: Environment variables not set

**Solution**: Set credentials in same terminal session

```bash
# Set variables
export DREMIO_USERNAME="admin"
export DREMIO_PASSWORD="your_password"

# Verify
echo $DREMIO_USERNAME
echo $DREMIO_PASSWORD

# Test authentication
bash scripts/test_dremio_login.sh
```

### Problem: Services not starting

**Solution**: Check Docker resources and port conflicts

```bash
# Check Docker is running
docker ps

# Check port availability
lsof -i :9000  # MinIO
lsof -i :9047  # Dremio

# View service logs
docker compose logs dremio
docker compose logs minio

# Restart services
docker compose restart
```

### Problem: Reflections not accelerating queries

**Solution**: Verify reflections are built and enabled

```bash
# Check reflection status
python3 scripts/check_reflections.py

# Via UI:
# Jobs → Filter by "Reflection" → Should show "COMPLETED"

# Force refresh
# Dataset → Reflections → Click refresh icon
```

### Problem: Data not visible in Dremio

**Solution**: Format folder as Parquet dataset

```bash
# Via UI:
1. Navigate to: minio > zeek-data > network-activity-ocsf
2. Click "Format Folder"
3. Select "Parquet"
4. Click "Save"

# Verify query works:
SELECT COUNT(*) FROM minio."zeek-data"."network-activity-ocsf";
```

---

## Current Status (As of 2025-12-09)

### ✅ Completed

- [x] Docker infrastructure (7 services)
- [x] Data loader (1M OCSF records)
- [x] OCSF transformation (65 fields)
- [x] Parquet partitioning (year/month/day)
- [x] MinIO data storage
- [x] Dremio setup and configuration
- [x] Playwright automation scripts
- [x] Comprehensive documentation
- [x] Demo materials (queries, presentation guide)
- [x] Project audit against best practices

### 🟡 In Progress

- [ ] MinIO source configuration in Dremio (user action required)
  - **Blocker**: User must enable "compatibility mode" in UI
  - **Guide**: See `FIX-MINIO-CONNECTION.md`

- [ ] Reflection deployment (blocked by MinIO source)
  - **Script Ready**: `run-reflection-setup.sh`
  - **Will take**: 2-5 minutes after source is configured

### ⚪ Planned (From Audit)

- [ ] Create requirements.txt (5 min)
- [ ] Remove venv from git (10 min)
- [ ] Consolidate documentation (30 min)
- [ ] Add automated testing (1 hr)

### Known Issues

1. **MinIO source requires compatibility mode** - Path-style S3 access needed
2. **venv committed to git** - Should be in .gitignore (2M+ insertions)
3. **40+ markdown files in root** - Needs organization into docs/ structure
4. **No requirements.txt** - Manual dependency installation currently

---

## Performance Benchmarks

### Data Loader Performance

- **Speed**: 30,000 records/sec
- **Time to load 1M records**: ~33 seconds
- **Compression ratio**: 75% (from ~360MB to 89.6MB)
- **Partitioning**: By event_date (year/month/day)

### Expected Query Performance

| Query Type | Before Reflections | After Reflections | Speedup |
|-----------|-------------------|------------------|---------|
| SELECT * (10K rows) | 2-3 sec | 100-200 ms | 10-15x |
| Aggregation (GROUP BY) | 5-8 sec | 50-100 ms | 50-100x |
| Complex JOIN | 10-15 sec | 500-1000 ms | 10-20x |

### Reflection Build Time

- **1M records**: 2-5 minutes
- **Raw reflection**: ~1-2 minutes
- **Aggregation reflections (3x)**: ~3-4 minutes total

---

## Decision Log

### Why OCSF?

- Linux Foundation standard for security data
- Vendor-neutral schema
- Growing adoption in enterprise security
- Well-documented (65+ fields for network activity)

### Why Dremio?

- Reflections provide automatic query acceleration
- No code changes needed (transparent to users)
- SQL-standard interface
- Self-service data access

### Why MinIO?

- S3-compatible (industry standard API)
- Self-hosted (no cloud dependency)
- Lightweight and fast
- Perfect for demos and development

### Why Parquet?

- Columnar format (efficient for analytics)
- Excellent compression (75% in our case)
- Native support in Dremio, Spark, Pandas
- Partitioning support for query pruning

### Why Playwright?

- Reliable browser automation
- Async/await support
- Good error handling
- Works with Dremio UI

---

## For Next Session

### If Starting Fresh Session

1. Read this file (CLAUDE.md)
2. Check PROJECT-STATUS-CURRENT.md
3. Verify infrastructure: `docker ps`
4. Set environment variables if needed

### If Continuing Work

**Immediate priority**: Wait for user to fix MinIO source connection

**Once source is fixed**:
1. Deploy reflections: `bash run-reflection-setup.sh`
2. Test query performance
3. Practice demo presentation

**Audit recommendations** (if approved):
1. Create requirements.txt
2. Update README.md
3. Remove venv from git
4. Consolidate documentation

### Questions to Ask User

- "Did you enable compatibility mode in the MinIO source?" (blocking issue)
- "Would you like me to implement the audit recommendations?"
- "Should I create requirements.txt and clean up the project structure?"

---

## Resources

### External Documentation

- OCSF Schema: https://schema.ocsf.io/
- Dremio Docs: https://docs.dremio.com/
- MinIO Docs: https://min.io/docs/
- Parquet Format: https://parquet.apache.org/

### Internal Guides

- Demo Presentation: `START-DEMO-NOW.md`
- SQL Queries: `DEMO-SQL-QUERIES.md`
- Quick Reference: `DEMO-CHEAT-SHEET.md`
- MinIO Setup: `SETUP-MINIO-SOURCE-NOW.md`
- Connection Issues: `FIX-MINIO-CONNECTION.md`

### Useful Commands

```bash
# View all Docker logs
docker compose logs -f

# Check Dremio logs specifically
docker compose logs -f dremio

# Execute command in container
docker exec -it zeek-demo-dremio bash

# View MinIO bucket contents
docker exec zeek-demo-minio ls -lh /data/zeek-data/

# Test Dremio API
curl -X POST http://localhost:9047/apiv2/login \
  -H "Content-Type: application/json" \
  -d '{"userName":"admin","password":"your_password"}'
```

---

## Success Criteria

### Demo is Ready When:

- [x] Infrastructure running (7 services healthy)
- [x] Data loaded (1M OCSF records in MinIO)
- [ ] MinIO source configured in Dremio (with compatibility mode)
- [ ] Reflections created and built
- [x] Demo queries prepared
- [x] Presentation guide ready

### Project is Complete When:

- [ ] All demo success criteria met
- [ ] Query performance verified (10-100x speedup)
- [ ] Documentation consolidated
- [ ] requirements.txt created
- [ ] venv removed from git
- [ ] CLAUDE.md exists (✅ this file!)

---

**Last Updated**: 2025-12-09
**Status**: CLAUDE.md created as part of audit Phase 1 implementation
**Next**: Create requirements.txt, update README.md
