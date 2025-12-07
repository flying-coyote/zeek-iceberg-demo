# Deploy Reflections NOW - One Command

**Your demo is ready. This one step will add 10-100x query acceleration.**

---

## Quick Deploy (5 minutes)

### Step 1: Set Password & Run

```bash
# Replace "your_password" with your actual Dremio password
export DREMIO_PASSWORD="your_password"

# Activate environment
source venv/bin/activate

# Deploy reflections
python3 scripts/create_reflections_auto.py
```

### Step 2: Wait for Build (2-5 minutes)

The script will:
- ✅ Authenticate with Dremio
- ✅ Find your OCSF dataset
- ✅ Create 4 reflections automatically
- ✅ Monitor build progress
- ✅ Report when complete

**Expected output**:
```
======================================================================
Dremio Reflection Auto-Setup
======================================================================

Authenticating with Dremio...
✓ Successfully authenticated
...
Creating reflections...
Creating raw reflection: OCSF Raw Reflection
  ✓ Created: OCSF Raw Reflection
...
Waiting for reflections to build...
  ⏳ OCSF Raw Reflection: REFRESHING
  ...
  ✓ OCSF Raw Reflection: AVAILABLE
✓ All 4 reflections available! (took 143s)

======================================================================
✓ Setup complete!
======================================================================
```

### Step 3: Test Performance

Open Dremio (http://localhost:9047) and run:

```sql
SELECT
  activity_name,
  COUNT(*) as events
FROM minio."zeek-data"."network-activity-ocsf"
GROUP BY activity_name
ORDER BY events DESC;
```

**Before reflections**: 2-4 seconds
**After reflections**: 100-300ms ⚡

**Verify reflection usage**:
1. Run query
2. Click "Profile" tab (top right)
3. Look for green "Reflection" node
4. ✅ = Reflection was used!

---

## Troubleshooting

### "Authentication failed"
**Check password**:
```bash
echo $DREMIO_PASSWORD
# Should show your password
```

**If empty, set it again**:
```bash
export DREMIO_PASSWORD="your_password"
```

### "Could not find dataset"
**Format the folder first**:
1. Open Dremio UI
2. Right-click folder: `minio > zeek-data > network-activity-ocsf`
3. Select "Format Folder"
4. Choose "Parquet"
5. Save
6. Re-run script

### Script hangs or times out
**Check Dremio is running**:
```bash
docker ps | grep dremio
# Should show zeek-demo-dremio running
```

**Restart Dremio if needed**:
```bash
docker restart zeek-demo-dremio
# Wait 30 seconds, then retry script
```

---

## Alternative: Manual Setup

If automation fails, see: **REFLECTION-SETUP-INSTRUCTIONS.md**

Manual setup takes 5-10 minutes via Dremio UI.

---

## After Deployment

**Your demo will show**:
- ✅ 1M OCSF records
- ✅ Sub-second query times
- ✅ 10-100x acceleration
- ✅ Professional polish

**Next**: Open **START-DEMO-NOW.md** to present!

---

**One command. 5 minutes. 10-100x faster queries. Let's go! 🚀**
