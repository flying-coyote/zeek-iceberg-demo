# Check if Reflections Are Set Up

Reflections require authentication to check via API. Here's how to verify:

---

## Method 1: Check via Dremio UI (Easiest)

1. Open **http://localhost:9047**
2. Login with your credentials
3. Navigate to: **minio** → **zeek-data** → **network-activity-ocsf**
4. Click on the dataset name
5. Click **"Reflections"** tab (at the top)

### What You Should See:

**If Reflections ARE set up:**
- You'll see 1-4 reflections listed
- Each should show:
  - Green checkmark icon (✓)
  - Status: "AVAILABLE" or "Can Accelerate"
  - Type: "RAW" or "AGGREGATION"

**If Reflections are NOT set up:**
- Empty list or "No reflections" message
- Button: "Create Reflection"

---

## Method 2: Check via API (with password)

```bash
# Set your password
export DREMIO_PASSWORD="your_password"

# Run the check script
source venv/bin/activate
python3 scripts/check_reflections_auto.py
```

This will authenticate and show you:
- Number of reflections
- Each reflection's name and status
- Whether they're AVAILABLE or still REFRESHING

---

## Method 3: Test Query Performance

Run this query in Dremio SQL editor:

```sql
SELECT
  activity_name,
  COUNT(*) as events
FROM minio."zeek-data"."network-activity-ocsf"
GROUP BY activity_name
ORDER BY events DESC;
```

### Performance Indicators:

**If reflections ARE working:**
- Query completes in: **100-300ms**
- Click "Profile" tab → See green "Reflection" node

**If reflections are NOT set up:**
- Query takes: **2-4 seconds**
- No reflection nodes in query profile

---

## Quick Answer

**To definitively check right now:**

1. Open: http://localhost:9047
2. Navigate to: minio > zeek-data > network-activity-ocsf
3. Click: "Reflections" tab

**Empty list** = Reflections NOT set up
**Shows reflections** = Reflections ARE set up

---

## If Reflections Are NOT Set Up

Run this one command:

```bash
export DREMIO_PASSWORD="your_password"
source venv/bin/activate
python3 scripts/create_reflections_auto.py
```

Wait 2-5 minutes for reflections to build.

---

## I Can't Check Without Your Credentials

Since the Dremio API requires authentication, I cannot programmatically check the reflection status without your password.

**You'll need to check manually using Method 1 above** (Dremio UI - takes 30 seconds).

Please check and let me know:
- Are reflections showing in the Reflections tab?
- If yes, how many and what status?
- If no, would you like me to help you deploy them?
