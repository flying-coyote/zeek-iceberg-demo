# Start Here - Setup Reflections with Username

**Updated scripts now support both username and password!**

---

## Quick Start

### Step 1: Set Your Credentials

```bash
# If your username is "admin" (default)
export DREMIO_USERNAME="admin"
export DREMIO_PASSWORD="your_password"

# OR if you have a different username
export DREMIO_USERNAME="your_actual_username"
export DREMIO_PASSWORD="your_password"
```

### Step 2: Test Authentication

```bash
bash scripts/test_dremio_login.sh
```

**You should see**:
```
========================================================================
Dremio Authentication Diagnostic
========================================================================

✓ DREMIO_USERNAME: admin
✓ DREMIO_PASSWORD is set (length: X characters)

Checking Dremio connectivity...
✓ Dremio is accessible at http://localhost:9047

Testing authentication with username: admin
✅ Authentication SUCCESSFUL!

Token received (first 20 chars): ...
```

### Step 3: Run Reflection Setup

```bash
bash setup-reflections-simple.sh
```

**You should see**:
```
========================================================================
Dremio Reflection Setup - Simple Version
========================================================================

✓ Username: admin
✓ Password is set (X characters)

Checking Dremio...
✓ Dremio is running

Testing Dremio connectivity...
✓ Dremio is accessible

Testing authentication with username: admin
✓ Authentication successful

...

✅ SUCCESS!
```

---

## If Authentication Fails

### Error: "Invalid username or password"

**Fix**: Verify your credentials work in the browser first

1. Open http://localhost:9047
2. Try logging in manually
3. If it works, use the EXACT same credentials:

```bash
export DREMIO_USERNAME="the_exact_username_you_used"
export DREMIO_PASSWORD="the_exact_password_you_used"
bash scripts/test_dremio_login.sh
```

---

## Common Username Scenarios

### Scenario 1: Username is "admin"

```bash
export DREMIO_USERNAME="admin"
export DREMIO_PASSWORD="yourpass123"
bash setup-reflections-simple.sh
```

### Scenario 2: Username is an email

```bash
export DREMIO_USERNAME="john.doe@company.com"
export DREMIO_PASSWORD="yourpass123"
bash setup-reflections-simple.sh
```

### Scenario 3: Custom username

```bash
export DREMIO_USERNAME="myusername"
export DREMIO_PASSWORD="yourpass123"
bash setup-reflections-simple.sh
```

---

## All-In-One Command

```bash
# Set both and run in one command
DREMIO_USERNAME="admin" \
DREMIO_PASSWORD="your_password" \
bash setup-reflections-simple.sh
```

---

## What Gets Created

The script will create **4 reflections**:
1. **Raw Reflection** - Accelerates SELECT * queries
2. **Protocol Activity Aggregation** - Speeds up protocol analysis
3. **Security Analysis Aggregation** - Optimizes security queries
4. **Time-based Aggregation** - Accelerates time-series analysis

**Build time**: 2-5 minutes after creation

---

## After Setup Completes

### Check Reflection Status

```bash
# Make sure credentials are still set
export DREMIO_USERNAME="admin"
export DREMIO_PASSWORD="your_password"

# Check status
source venv/bin/activate
python3 scripts/check_reflections_auto.py
```

### Test Query Performance

1. Open http://localhost:9047
2. Run this query:

```sql
SELECT activity_name, COUNT(*) as events
FROM minio."zeek-data"."network-activity-ocsf"
GROUP BY activity_name
ORDER BY events DESC;
```

**Expected**: 100-300ms (was 2-4 seconds before reflections)

3. Click **"Profile"** tab
4. Look for green **"Reflection"** node ✅

---

## Quick Troubleshooting

### Username/password not persisting

```bash
# Check if they're set
echo "Username: $DREMIO_USERNAME"
echo "Password length: ${#DREMIO_PASSWORD}"

# If empty, set them again
export DREMIO_USERNAME="admin"
export DREMIO_PASSWORD="your_password"
```

### Password has special characters

```bash
# Use single quotes
export DREMIO_PASSWORD='my"pass$word!'
```

### Not sure what your username is?

1. Open http://localhost:9047
2. Look at the username field when you log in
3. Use that exact username in the export

---

## Files Reference

- **START-HERE-WITH-USERNAME.md** (this file) - Quick start
- **SETUP-WITH-USERNAME.md** - Detailed username/password guide
- **FIX-REFLECTION-ERRORS.md** - Troubleshooting guide
- **TRY-AGAIN.md** - Restart instructions

---

**Try it now!**

```bash
export DREMIO_USERNAME="admin"
export DREMIO_PASSWORD="your_password"
bash scripts/test_dremio_login.sh
```

If the test passes, run:

```bash
bash setup-reflections-simple.sh
```

You'll have reflections deployed in 5 minutes! 🚀
