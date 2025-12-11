# Fix Reflection Setup Errors

Let's diagnose and fix the errors step by step.

---

## Step 1: Run the Diagnostic Script

This will tell us exactly what's wrong:

```bash
# Make sure password is set
export DREMIO_PASSWORD="your_actual_password"

# Run diagnostic
bash scripts/test_dremio_login.sh
```

**This script checks**:
- ✓ Is DREMIO_PASSWORD set?
- ✓ Is Dremio accessible?
- ✓ Does authentication work?

**Possible outcomes**:

### ✅ If you see "Authentication SUCCESSFUL!"
Good! Your credentials work. Skip to **Step 2**.

### ❌ If you see "Authentication FAILED"
The diagnostic will show the exact error. Common issues:

---

## Common Error 1: "Invalid username or password"

**Cause**: Wrong password or account doesn't exist

**Fix**:
1. Open http://localhost:9047 in browser
2. Try logging in manually with username: `admin` and your password
3. **If login fails in browser**: You need to reset/create your Dremio account
4. **If login works in browser**: Your password has special characters that need escaping

**For special characters in password**:
```bash
# If password has quotes, escape them:
export DREMIO_PASSWORD='my"password'  # Use single quotes

# If password has $, escape it:
export DREMIO_PASSWORD="my\$password"  # Use backslash

# Simplest - set it interactively:
read -s DREMIO_PASSWORD
export DREMIO_PASSWORD
# Then type your password (won't be visible)
```

---

## Common Error 2: "DREMIO_PASSWORD is not set"

**Cause**: Environment variable didn't persist

**Fix**:
```bash
# Check if it's set:
echo $DREMIO_PASSWORD

# If empty, set it again:
export DREMIO_PASSWORD="your_password"

# Verify it's set:
echo $DREMIO_PASSWORD
```

**Note**: `export` only works in the current terminal session. If you opened a new terminal, you need to set it again.

---

## Common Error 3: "Cannot connect to Dremio"

**Cause**: Dremio container not running

**Fix**:
```bash
# Check if Dremio is running
docker ps | grep dremio

# If not running, start it:
docker-compose up -d dremio

# Wait 30 seconds for startup:
sleep 30

# Try again:
bash scripts/test_dremio_login.sh
```

---

## Common Error 4: Python module errors

**Error**: `ModuleNotFoundError: No module named 'requests'`

**Fix**:
```bash
# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install requests --quiet

# Verify installation
python3 -c "import requests; print('requests OK')"
```

---

## Step 2: Run the Reflection Setup (After Diagnostic Passes)

Once the diagnostic shows "Authentication SUCCESSFUL!", run:

```bash
# Make sure you're in venv
source venv/bin/activate

# Make sure password is still set
echo $DREMIO_PASSWORD

# Run the reflection setup
python3 scripts/create_reflections_auto.py
```

---

## Step 3: What to Expect

**Successful output looks like**:
```
======================================================================
Dremio Reflection Auto-Setup
======================================================================

Authenticating with Dremio...
✓ Successfully authenticated
Looking up dataset: minio > zeek-data > network-activity-ocsf
  Found: minio (id: ...)
  Found: zeek-data (id: ...)
  Found: network-activity-ocsf (id: ...)
✓ Dataset ID: ...

Creating reflections...

Creating raw reflection: OCSF Raw Reflection
  ✓ Created: OCSF Raw Reflection
...
```

**If you get an error**, capture the exact error message and I can help troubleshoot.

---

## Step 4: If Script Fails - Manual Fallback

If the script continues to fail, you can create reflections manually:

### Manual Setup (5 minutes):

1. Open http://localhost:9047
2. Navigate: **minio** → **zeek-data** → **network-activity-ocsf**
3. Click the dataset name
4. Click **"Reflections"** tab
5. Click **"Create Reflection"**
6. Select **"Raw Reflection"**
7. Click **"Save"**

That's it! Even one raw reflection will give you 5-10x speedup.

---

## Troubleshooting Specific Errors

### Error: "Could not find dataset"

**Cause**: Dataset not formatted in Dremio

**Fix**:
1. Open Dremio UI
2. Navigate to: minio > zeek-data > network-activity-ocsf
3. Right-click the folder
4. Select **"Format Folder"**
5. Choose **"Parquet"**
6. Click **"Save"**
7. Re-run script

---

### Error: "Timeout waiting for reflections"

**Not actually an error** - reflections are still building in background.

**Fix**: Just wait. Check status:
1. Open Dremio UI
2. Go to dataset Reflections tab
3. Watch status change from REFRESHING → AVAILABLE (2-5 min)

---

## Quick Debug Commands

```bash
# Check password is set
echo "Password length: ${#DREMIO_PASSWORD}"

# Check Dremio is running
docker ps | grep dremio

# Check Dremio logs
docker logs zeek-demo-dremio --tail 50

# Test Dremio API directly
curl http://localhost:9047/apiv2/login \
  -H "Content-Type: application/json" \
  -d "{\"userName\":\"admin\",\"password\":\"$DREMIO_PASSWORD\"}"

# Check Python dependencies
source venv/bin/activate
pip list | grep requests
```

---

## Still Having Issues?

Run this and share the output:

```bash
bash scripts/test_dremio_login.sh 2>&1 | tee diagnostic.log
cat diagnostic.log
```

This will show me exactly what's failing.

---

## Alternative: Use Dremio UI (Always Works)

If all else fails, the UI method is 100% reliable:

1. Open http://localhost:9047
2. Login
3. Go to: minio > zeek-data > network-activity-ocsf
4. Click "Reflections" tab
5. Click "Create Reflection"
6. Select "Raw Reflection"
7. Click "Save"

Takes 2 minutes, zero errors. 👍
