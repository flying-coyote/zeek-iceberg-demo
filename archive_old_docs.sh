#!/bin/bash

# Script to archive old status documentation files
# Keeps only the essential documents and moves old ones to an archive folder

echo "Archiving old documentation files..."

# Create archive directory
mkdir -p docs/archive/2024-11-status

# List of files to archive (old status files from November)
FILES_TO_ARCHIVE=(
    "COMPLETE-DEMO-FLOW.md"
    "COMPLETE-DEMO-STATUS.md"
    "CURRENT-STATUS.md"
    "DATA-RECOVERY-NEEDED.md"
    "FINAL-DEMO-STATUS.md"
    "FINAL-SETUP-STEPS.md"
    "FIX-MINIO-CONNECTION.md"
    "OCSF-1M-RECORDS-RESULTS.md"
    "OCSF-DEMO-COMPLETE-STATUS.md"
    "PLAYWRIGHT-DREMIO-STATUS.md"
    "PLAYWRIGHT-REFLECTION-ATTEMPT-SUMMARY.md"
    "SESSION-SUMMARY.md"
    "START-HERE.md"
    "QUICK-START.md"
    "REAL-ZEEK-DATA-RESULTS.md"
    "1M-RECORDS-RESULTS.md"
    "TRINO-DEFERRED-TODO.md"
    "WORKING-SETUP.md"
    "SOLUTION-COMPATIBILITY-MODE.md"
)

# Move files to archive
for file in "${FILES_TO_ARCHIVE[@]}"; do
    if [ -f "$file" ]; then
        echo "Archiving: $file"
        mv "$file" docs/archive/2024-11-status/
    fi
done

echo ""
echo "Files archived to: docs/archive/2024-11-status/"
echo ""
echo "Remaining documentation files:"
ls -1 *.md

echo ""
echo "Archive complete!"
echo ""
echo "Essential documents preserved:"
echo "  - README.md (main project overview)"
echo "  - PROJECT-STATUS-2024-12.md (current status)"
echo "  - PROJECT-ROADMAP.md (future plans)"
echo "  - DREMIO-SETUP-GUIDE.md (Dremio configuration)"
echo "  - DREMIO-REFLECTIONS-COMPLETE-GUIDE.md (query optimization)"
echo "  - OCSF-IMPLEMENTATION-DECISION.md (design rationale)"
echo "  - TEST-PLAN-OPTION-6-DOCUMENTATION.md (implementation details)"