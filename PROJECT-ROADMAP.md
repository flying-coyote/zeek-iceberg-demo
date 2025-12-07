# UltraCore OCSF Project - Strategic Roadmap

**Last Updated**: November 30, 2025
**Project Status**: Option 6 documented, data recovery needed
**Test Plan v1.0 Deadline**: 2-3 weeks

---

## Current State Assessment

### ✅ Completed
- Option 6 documentation (22K words, production-ready)
- OCSF transformation logic (conn protocol, 61 fields, 100% compliance)
- Performance validation (1M records, <1s queries)
- Infrastructure setup (MinIO + Dremio working)
- Comprehensive viability assessment

### ⚠️ Degraded
- **Data lost in MinIO** (buckets exist but empty)
- Dremio reflections not deployed
- MinIO source may need reconfiguration in Dremio

### ❌ Not Started
- dns, ssl, smtp protocol transformations (75% of Test Plan coverage)
- Option 5 implementation (Nessie + Iceberg)
- Production hardening (monitoring, RBAC, encryption)

---

## Immediate Actions (Next 24 Hours)

### Priority 1: Restore Demo Capability (15 minutes)

**Objective**: Get Option 6 back to working demo state

**Steps**:
1. **Reload OCSF data** (5 minutes)
   ```bash
   cd /home/jerem/zeek-iceberg-demo
   source .venv/bin/activate
   python scripts/load_real_zeek_to_ocsf.py --records 100000 --validate
   ```
   Expected output: 100K records in `s3://zeek-data/network-activity-ocsf/`

2. **Verify data loaded** (1 minute)
   ```bash
   docker exec zeek-demo-minio mc ls local/zeek-data/network-activity-ocsf/ --recursive
   ```
   Expected: Parquet files in year=/month=/day= partitions

3. **Configure Dremio MinIO source** (5 minutes)
   - Login: http://localhost:9047
   - Add S3 source: `minio`
   - Critical: Enable "compatibility mode"
   - Add properties:
     - `fs.s3a.endpoint` = `http://minio:9000`
     - `fs.s3a.path.style.access` = `true`
     - `fs.s3a.connection.ssl.enabled` = `false`

4. **Format dataset and test query** (4 minutes)
   - Format folder: `minio > zeek-data > network-activity-ocsf`
   - Run test query:
     ```sql
     SELECT COUNT(*) FROM minio."zeek-data"."network-activity-ocsf";
     ```
   - Expected: 100,000 records

**Deliverable**: Working demo for Option 6
**Blocker Resolution**: Unblocks all downstream tasks

---

### Priority 2: Deploy Dremio Reflections (10 minutes)

**Objective**: Enable query acceleration (10-100x speedup)

**Option A - Automated** (Recommended):
```bash
python scripts/create_dremio_reflections.py
# Enter Dremio credentials when prompted
```

**Option B - Manual**:
- Follow: `DREMIO-REFLECTIONS-COMPLETE-GUIDE.md`
- Create 3 reflections:
  1. Raw reflection (key fields)
  2. Security aggregation (IP + protocol + activity)
  3. Time-based aggregation (hourly patterns)

**Validation**:
- Check Jobs page for "Build Reflection" status
- Wait for COMPLETED (2-5 minutes for 100K records)
- Re-run test query, verify "Accelerated" indicator

**Deliverable**: 10-100x faster queries
**Value**: Demonstrates production-ready performance

---

### Priority 3: Data Persistence Fix (30 minutes)

**Objective**: Prevent data loss on Docker restarts

**Option A - Bind Mounts** (Recommended):

Edit `docker-compose.yml`:
```yaml
services:
  minio:
    volumes:
      - ./minio-data:/data  # Bind mount instead of named volume
```

**Option B - Backup Script**:

Create `scripts/backup_minio.sh`:
```bash
#!/bin/bash
# Backup MinIO data before restarts
BACKUP_DIR="./backups/$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP_DIR"
docker exec zeek-demo-minio mc mirror local/zeek-data "$BACKUP_DIR/zeek-data"
echo "Backup complete: $BACKUP_DIR"
```

**Validation**:
```bash
# Test restart
docker-compose restart minio
docker exec zeek-demo-minio mc ls local/zeek-data/network-activity-ocsf/
# Expected: Data still present
```

**Deliverable**: Resilient data storage
**Risk Mitigation**: Prevents future data loss incidents

---

## Short-Term Goals (1-2 Weeks)

### Goal 1: Complete Protocol Coverage for Test Plan v1.0

**Objective**: Implement dns, ssl, smtp transformations (reach 100% Test Plan coverage)

**Task 1.1: DNS Protocol Transformation** (12-16 hours)

**Complexity**: HIGH (parallel vectors: queries, answers)

**Implementation**:
1. Create `scripts/transform_zeek_dns_to_ocsf.py`
2. Map to OCSF DNS Activity (class_uid: 4003)
3. Handle parallel vectors:
   - `dns.query__hostname` (double underscore delimiter)
   - `dns.query__type`
   - `dns.answer__ip` (array → flattened)
4. Validation: 13 OCSF compliance checks
5. Test with 100K DNS records

**Key Fields**:
```python
class_uid: 4003  # DNS Activity
query.hostname: Z (Zeek query field)
query.type: qtype_name
answer.rcode: rcode_name
answer.ip: answers (array handling required)
```

**Deliverable**: `dns-ocsf-transformation-results.md` with validation

**Estimated Effort**:
- Script development: 6 hours
- Testing & debugging: 4 hours
- Documentation: 2 hours
- **Total: 12 hours**

---

**Task 1.2: SSL/TLS Protocol Transformation** (10-14 hours)

**Complexity**: MEDIUM (certificate chains, multiple fields)

**Implementation**:
1. Create `scripts/transform_zeek_ssl_to_ocsf.py`
2. Map to OCSF TLS Activity (no specific class, use Network Activity with enrichment)
3. Key mappings:
   - `certificate.subject`: server_name (SNI)
   - `certificate.issuer`: issuer from cert
   - `tls.version`: version field
   - `tls.cipher_suite`: cipher
4. Handle certificate validation fields

**Key Fields**:
```python
class_uid: 4001  # Network Activity (TLS enriched)
activity_name: "TLS"
tls_version: version
tls_cipher: cipher
certificate_subject: subject
certificate_issuer: issuer
```

**Deliverable**: `ssl-ocsf-transformation-results.md`

**Estimated Effort**:
- Script development: 5 hours
- Certificate handling: 3 hours
- Testing: 2 hours
- Documentation: 2 hours
- **Total: 12 hours**

---

**Task 1.3: SMTP Protocol Transformation** (10-14 hours)

**Complexity**: MEDIUM (email recipients array, multiple fields)

**Implementation**:
1. Create `scripts/transform_zeek_smtp_to_ocsf.py`
2. Map to OCSF Email Activity (class_uid: 4009)
3. Handle recipient arrays (parallel vectors)
4. Email metadata: subject, from, to, cc

**Key Fields**:
```python
class_uid: 4009  # Email Activity
activity_name: "Email"
email_from: mailfrom
email_to: rcptto (array → flattened)
email_subject: subject
email_size: total_bytes
```

**Deliverable**: `smtp-ocsf-transformation-results.md`

**Estimated Effort**:
- Script development: 5 hours
- Array handling: 3 hours
- Testing: 2 hours
- Documentation: 2 hours
- **Total: 12 hours**

---

**Task 1.4: Multi-Protocol Integration Testing** (4-6 hours)

**Objective**: Validate all 4 protocols working together

**Implementation**:
1. Load mixed dataset (conn + dns + ssl + smtp)
2. Query across protocols:
   ```sql
   SELECT
     class_name,
     activity_name,
     COUNT(*) as events
   FROM minio."zeek-data"."all-ocsf-protocols"
   GROUP BY class_name, activity_name;
   ```
3. Create unified reflections
4. Performance benchmark all protocols

**Deliverable**: `multi-protocol-validation-report.md`

**Estimated Effort**: 6 hours

---

**Total Protocol Coverage Effort**: 42-50 hours (~1-1.5 weeks full-time)

**Milestone**: Test Plan v1.0 has 100% protocol coverage for Option 6

---

### Goal 2: Production Hardening (20-30 hours)

**Objective**: Make Option 6 production-ready beyond demo

**Task 2.1: Security Hardening** (8 hours)

**Implementation**:
1. **MinIO Security**:
   - Create dedicated service account (not minioadmin)
   - Enable TLS for S3 API
   - Implement bucket policies (read-only for Dremio)
   - Enable audit logging

2. **Dremio Security**:
   - Configure LDAP/SAML authentication
   - Implement RBAC (data source permissions)
   - Enable query auditing
   - TLS for web UI and JDBC/ODBC

3. **Network Security**:
   - Internal Docker network isolation
   - Expose only necessary ports
   - Add nginx reverse proxy (optional)

**Deliverable**: `SECURITY-HARDENING-GUIDE.md`

---

**Task 2.2: Monitoring & Alerting** (10 hours)

**Implementation**:
1. **Infrastructure Monitoring**:
   - Prometheus exporters for MinIO, Dremio
   - Grafana dashboards:
     - Storage usage (MinIO)
     - Query performance (Dremio)
     - Reflection build status
     - Error rates

2. **Application Monitoring**:
   - Transformation pipeline metrics
   - Data quality alerts (NULL checks, value ranges)
   - OCSF compliance monitoring

3. **Alerting**:
   - Storage capacity alerts (>80%)
   - Query performance degradation (>5s queries)
   - Reflection build failures
   - Data freshness (no new data in 24h)

**Deliverable**: `docker-compose.monitoring.yml` + dashboards

---

**Task 2.3: Automated Testing** (8 hours)

**Implementation**:
1. **Unit Tests**:
   - Transformation logic tests (pytest)
   - OCSF field mapping validation
   - Data type correctness

2. **Integration Tests**:
   - End-to-end pipeline test (Zeek → MinIO → Dremio)
   - Query correctness validation
   - Performance regression tests

3. **CI/CD Pipeline**:
   - GitHub Actions workflow
   - Automated test on PR
   - Docker image builds

**Deliverable**: `tests/` directory + `.github/workflows/ci.yml`

---

**Task 2.4: Documentation & Runbooks** (6 hours)

**Implementation**:
1. **Operational Runbooks**:
   - Deployment checklist
   - Troubleshooting guide (expanded)
   - Incident response procedures
   - Disaster recovery plan

2. **User Documentation**:
   - Query cookbook (common OCSF queries)
   - Field reference guide
   - Performance tuning guide

**Deliverable**: `docs/` directory with comprehensive guides

---

**Total Production Hardening Effort**: 32 hours (~1 week full-time)

**Milestone**: Option 6 ready for customer production deployment

---

## Medium-Term Goals (3-6 Weeks)

### Goal 3: Implement Option 5 (Nessie + Iceberg)

**Objective**: Complete the "missing" Option 5 for Test Plan

**Why**: Provides time-travel, versioning, multi-engine catalog

**Phase 3.1: Nessie Catalog Setup** (8-12 hours)

**Implementation**:
1. Add Nessie to `docker-compose.yml`:
   ```yaml
   nessie:
     image: projectnessie/nessie:latest
     ports:
       - "19120:19120"
     environment:
       QUARKUS_HTTP_PORT: 19120
   ```

2. Configure authentication (OAuth2 or basic auth)

3. Create initial branches:
   - `main` - production data
   - `dev` - development/testing
   - `staging` - pre-production

4. Test catalog operations via REST API

**Deliverable**: Working Nessie catalog server

**Validation**:
```bash
curl http://localhost:19120/api/v1/config
# Expected: Nessie configuration JSON
```

---

**Phase 3.2: Iceberg Table Creation** (12-16 hours)

**Implementation**:
1. Modify `scripts/zeek_to_ocsf_iceberg.py`:
   - Change catalog from Hive to Nessie:
     ```python
     spark.sql.catalog.nessie.catalog-impl = org.apache.iceberg.nessie.NessieCatalog
     spark.sql.catalog.nessie.uri = http://nessie:19120/api/v1
     ```

2. Create OCSF tables for all protocols:
   - `nessie.ocsf.network_activity` (conn)
   - `nessie.ocsf.dns_activity` (dns)
   - `nessie.ocsf.tls_activity` (ssl)
   - `nessie.ocsf.email_activity` (smtp)

3. Load data to Iceberg tables

4. Test snapshots and time-travel:
   ```sql
   SELECT * FROM nessie.ocsf.network_activity
   VERSION AS OF 'snapshot-id-12345';
   ```

**Deliverable**: OCSF data in Iceberg format via Nessie

---

**Phase 3.3: Dremio-Nessie Integration** (8-12 hours)

**Implementation**:
1. Configure Dremio Nessie source:
   - Source type: Nessie
   - Nessie endpoint: `http://nessie:19120/api/v1`
   - Authentication: Configure credentials

2. Browse Nessie catalog in Dremio

3. Create reflections on Iceberg tables

4. Benchmark query performance (Iceberg vs. Parquet)

**Deliverable**: Dremio querying Iceberg via Nessie

---

**Phase 3.4: Option 5 Validation** (8-10 hours)

**Implementation**:
1. Run full OCSF compliance tests (all 4 protocols)
2. Performance benchmarks vs. Option 6
3. Test time-travel queries
4. Test schema evolution
5. Document advantages/disadvantages

**Deliverable**: `OPTION-5-VALIDATION-REPORT.md`

---

**Total Option 5 Implementation**: 36-50 hours (~1.5-2 weeks full-time)

**Milestone**: Test Plan v1.0 has both Option 5 AND Option 6 validated

---

### Goal 4: Advanced Features (20-30 hours)

**Task 4.1: Real-Time Streaming** (12-16 hours)

**Objective**: Ingest Zeek logs in real-time vs. batch

**Implementation**:
1. Kafka topic for Zeek logs
2. Spark Structured Streaming:
   ```python
   zeek_stream = spark.readStream.format("kafka") \
     .option("subscribe", "zeek-logs") \
     .load()

   ocsf_stream = transform_zeek_to_ocsf(zeek_stream)

   ocsf_stream.writeStream \
     .format("iceberg") \
     .outputMode("append") \
     .option("path", "s3://zeek-data/network-activity-ocsf") \
     .start()
   ```

3. Micro-batch processing (10-second windows)
4. Exactly-once semantics

**Deliverable**: Real-time OCSF transformation pipeline

---

**Task 4.2: Data Quality Framework** (8-12 hours)

**Objective**: Automated data quality validation

**Implementation**:
1. Great Expectations integration:
   - Schema validation (column types, names)
   - Value range checks (ports 0-65535)
   - Completeness checks (NULL percentages)
   - Referential integrity (IP format validation)

2. Automated quality reports
3. Quality score dashboard
4. Alerts on quality degradation

**Deliverable**: `scripts/data_quality_checks.py` + dashboard

---

**Task 4.3: Multi-Tenancy** (8-10 hours)

**Objective**: Support multiple customers/environments

**Implementation**:
1. Partition by customer_id
2. Dremio access controls per customer
3. Reflection strategy per customer
4. Cost allocation by customer

**Deliverable**: Multi-tenant architecture guide

---

## Long-Term Vision (3-6 Months)

### Vision 1: OCSF Data Lake Platform

**Objective**: Full-featured security data lake

**Components**:
- Ingestion: Zeek, Suricata, Palo Alto, AWS CloudTrail, Azure Sentinel
- Storage: Multi-protocol OCSF in Iceberg
- Catalog: Nessie with branch-per-environment
- Query: Dremio, Spark, Trino, Athena
- Analytics: Jupyter, Superset, Tableau
- ML: Anomaly detection, threat hunting models

**Estimated Effort**: 400-600 hours

---

### Vision 2: OCSF Marketplace

**Objective**: Pre-built OCSF transformations

**Features**:
- Transformation library for 50+ data sources
- OCSF schema registry
- Field mapping documentation
- Compliance validators
- Performance benchmarks

**Business Model**: Open-source core + enterprise support

---

## Prioritization Framework

### Decision Matrix

**Use this to prioritize tasks**:

| Priority | Criteria | Current Tasks |
|----------|----------|---------------|
| **P0 - Immediate** | Blockers, demo broken | Restore data, configure Dremio |
| **P1 - High** | Test Plan v1.0 deadline | Protocol coverage (dns, ssl, smtp) |
| **P2 - Medium** | Production readiness | Security, monitoring, testing |
| **P3 - Low** | Nice-to-have | Option 5, streaming, multi-tenancy |
| **P4 - Future** | Long-term vision | Platform, marketplace |

### Effort vs. Impact

**Quick Wins** (High Impact, Low Effort):
1. ✅ Restore demo (15 min, unblocks everything)
2. ✅ Deploy reflections (10 min, 10-100x speedup)
3. ✅ Data persistence fix (30 min, prevents future issues)

**Strategic Investments** (High Impact, High Effort):
1. Protocol coverage (42-50 hours, completes Test Plan)
2. Production hardening (32 hours, enables customer deployments)
3. Option 5 implementation (36-50 hours, differentiation)

**Defer** (Low Impact or Very High Effort):
1. Real-time streaming (until batch proven)
2. Multi-tenancy (until multiple customers)
3. OCSF Marketplace (long-term vision)

---

## Recommended Action Plan

### This Week (40 hours)

**Monday** (8 hours):
- Morning: Restore demo (P0) - 15 min
- Morning: Deploy reflections (P0) - 10 min
- Morning: Data persistence fix (P0) - 30 min
- Rest of day: DNS protocol transformation - 6 hours

**Tuesday** (8 hours):
- DNS protocol testing & debugging - 6 hours
- DNS documentation - 2 hours

**Wednesday** (8 hours):
- SSL protocol transformation - 6 hours
- SSL testing - 2 hours

**Thursday** (8 hours):
- SSL documentation - 2 hours
- SMTP protocol transformation - 6 hours

**Friday** (8 hours):
- SMTP testing & documentation - 4 hours
- Multi-protocol integration testing - 4 hours

**Weekend Deliverables**:
- ✅ Demo restored and working
- ✅ Reflections deployed
- ✅ Data persistence fixed
- ✅ DNS, SSL, SMTP transformations complete
- ✅ Test Plan v1.0 has 100% protocol coverage for Option 6

---

### Next Week (40 hours)

**Focus**: Production hardening

**Monday-Tuesday** (16 hours):
- Security hardening (MinIO, Dremio, network)

**Wednesday-Thursday** (16 hours):
- Monitoring & alerting setup
- Grafana dashboards

**Friday** (8 hours):
- Automated testing framework
- Documentation & runbooks

**Deliverables**:
- ✅ Production-ready Option 6
- ✅ Security hardening complete
- ✅ Monitoring operational
- ✅ Automated tests passing

---

### Weeks 3-4 (80 hours)

**Focus**: Option 5 implementation (if desired)

**Week 3**:
- Nessie catalog setup (12 hours)
- Iceberg table creation (16 hours)
- Dremio-Nessie integration (12 hours)

**Week 4**:
- Option 5 validation (10 hours)
- Performance benchmarking (10 hours)
- Documentation (20 hours)
- Buffer for issues (18 hours)

**Deliverables**:
- ✅ Option 5 fully implemented and validated
- ✅ Test Plan v1.0 has BOTH Option 5 and Option 6

---

## Success Metrics

### Technical Metrics

**Performance**:
- Transformation throughput: >30K records/second
- Query latency (1M records): <1 second
- Reflection speedup: 10-100x
- Storage compression: >70%

**Quality**:
- OCSF compliance: 100% (all 13 checks)
- Protocol coverage: 100% (conn, dns, ssl, smtp)
- Test coverage: >80%
- Data quality score: >95%

**Reliability**:
- Uptime: >99.9%
- Data loss incidents: 0
- Failed reflection builds: <5%
- Query success rate: >99%

### Business Metrics

**Test Plan v1.0**:
- Option 6 documented: ✅
- Protocol coverage: 100% target
- Validation complete: ✅
- Production-ready: Target by Week 2

**Customer Value**:
- Demo-to-production time: <1 week
- Setup time: <1 hour (Option 6)
- TCO vs. commercial SIEM: 80% lower
- Query performance vs. competitors: 10-100x faster

---

## Risk Management

### Risk Register

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **Data loss on restart** | HIGH (occurred) | HIGH | Bind mounts + backup script (P0) |
| **Protocol implementation complexity** | MEDIUM | HIGH | Start with DNS (hardest), learn patterns |
| **Test Plan deadline missed** | MEDIUM | HIGH | Focus on Option 6, defer Option 5 if needed |
| **Nessie integration issues** | MEDIUM | MEDIUM | Allocate buffer time, have Option 6 fallback |
| **Performance degradation at scale** | LOW | MEDIUM | Early benchmarking, reflection optimization |
| **OCSF spec changes** | LOW | LOW | Monitor OCSF releases, versioned schemas |

---

## Communication Plan

### Weekly Status Reports

**Template**:
```
Week of [DATE]

Completed:
- [Task 1] - X hours
- [Task 2] - Y hours

In Progress:
- [Task 3] - Z% complete

Blockers:
- [Issue 1] - Need [Resource/Decision]

Next Week:
- [Planned Task 1]
- [Planned Task 2]

Metrics:
- Protocol coverage: X%
- Test Plan readiness: Y%
- Production hardening: Z%
```

### Stakeholder Updates

**Cadence**: End of each phase

**Content**:
- Demo video (5 minutes)
- Performance benchmarks
- Protocol coverage status
- Risk updates
- Timeline adjustments

---

## Questions for Stakeholders

Before proceeding, clarify:

1. **Test Plan v1.0 Scope**:
   - Is Option 6 sufficient, or is Option 5 required?
   - Can we defer Option 5 to v1.1?
   - Is 100% protocol coverage (dns, ssl, smtp) mandatory for v1.0?

2. **Production Requirements**:
   - What security certifications needed? (SOC2, FedRAMP, etc.)
   - What scale? (Records/day, query concurrency)
   - What integrations? (SIEM, SOAR, BI tools)

3. **Resource Allocation**:
   - Full-time or part-time?
   - Timeline flexibility if issues arise?
   - Budget for commercial tools if needed?

4. **Success Criteria**:
   - What defines "production-ready"?
   - What performance SLAs?
   - What documentation requirements?

---

## Conclusion

**Immediate Focus**: Restore demo (15 min) → Enables all other work

**Short-Term Focus**: Protocol coverage (1-2 weeks) → Completes Test Plan v1.0

**Medium-Term Focus**: Option 5 implementation (3-4 weeks) → Differentiation

**Long-Term Vision**: OCSF data lake platform → Market leadership

**Recommended Start**: Execute Priority 1-3 immediate actions TODAY, then proceed with weekly plan based on stakeholder priorities.

---

**Next Step**: Which priority would you like to tackle first?

1. **Restore demo now** (15 min) - Unblocks everything
2. **Start DNS protocol** (after restore) - Highest complexity, learn first
3. **Review & adjust roadmap** - Align on priorities before execution
4. **Something else** - Your strategic priority
