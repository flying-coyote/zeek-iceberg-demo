# Try Setting Up Reflections Again

I've created improved scripts with better error handling to help you succeed.

---

## Option 1: Simple One-Step Script (Recommended)

This script checks everything step-by-step and gives clear error messages:

```bash
# Set your password
export DREMIO_PASSWORD="your_password"

# Run the simple setup script
bash setup-reflections-simple.sh
```

**What it does**:
- ✓ Checks if password is set
- ✓ Checks if Dremio is running
- ✓ Tests authentication
- ✓ Installs dependencies if needed
- ✓ Runs the reflection setup
- ✓ Shows clear success/error messages

**If it fails**, it will tell you exactly what's wrong and how to fix it.

---

## Option 2: Diagnostic First (If you got errors before)

Run the diagnostic to see what went wrong:

```bash
# Set your password
export DREMIO_PASSWORD="your_password"

# Run diagnostic
bash scripts/test_dremio_login.sh
```

**This tells you**:
- Is the password set correctly?
- Can we connect to Dremio?
- Does authentication work?

**Once diagnostic passes**, run:
```bash
bash setup-reflections-simple.sh
```

---

## Option 3: Manual Setup (If scripts keep failing)

Sometimes the UI is the most reliable:

1. Open **http://localhost:9047**
2. Login with your credentials
3. Navigate: **minio** → **zeek-data** → **network-activity-ocsf**
4. Click on the dataset name
5. Click **"Reflections"** tab
6. Click **"Create Reflection"**
7. Select **"Raw Reflection"**
8. Configuration:
   - Display Fields: Click "Select All"
   - Leave other fields default
9. Click **"Save"**

**Done!** Even one raw reflection gives you 5-10x speedup.

---

## Common Issues and Fixes

### Issue 1: Password not persisting

```bash
# Check if password is still set:
echo $DREMIO_PASSWORD

# If it's empty, set it again:
export DREMIO_PASSWORD="your_password"

# Verify:
echo "Password length: ${#DREMIO_PASSWORD}"
```

**Note**: `export` only works in the current terminal. If you opened a new terminal, set it again.

---

### Issue 2: Password has special characters

If your password has quotes, dollar signs, or other special characters:

```bash
# Use single quotes for passwords with special chars:
export DREMIO_PASSWORD='my"pass$word'

# OR escape special characters:
export DREMIO_PASSWORD="my\"pass\$word"

# OR set it interactively (password won't be visible):
read -s -p "Enter Dremio password: " DREMIO_PASSWORD
export DREMIO_PASSWORD
echo ""  # New line after password entry
```

---

### Issue 3: "Authentication failed"

**Verify your password works**:
1. Open http://localhost:9047 in browser
2. Try logging in with username `admin` and your password
3. If it works in browser but not in script, your password might have special characters (see Issue 2)
4. If it doesn't work in browser, you need to reset your Dremio password

---

### Issue 4: Module not found errors

```bash
# Make sure you're in venv:
source venv/bin/activate

# Install dependencies:
pip install requests --quiet

# Verify:
python3 -c "import requests; print('OK')"
```

---

## What Errors Did You Get?

To help you better, please run this and share the output:

```bash
export DREMIO_PASSWORD="your_password"
bash scripts/test_dremio_login.sh
```

This will show me exactly what's failing, and I can give you a specific fix.

---

## Quick Decision Tree

**Did you get "Authentication failed"?**
→ See: FIX-REFLECTION-ERRORS.md → "Common Error 1"

**Did you get "Module not found"?**
→ See: FIX-REFLECTION-ERRORS.md → "Common Error 4"

**Did you get "Cannot connect"?**
→ Check if Dremio is running: `docker ps | grep dremio`

**Something else?**
→ Run the diagnostic: `bash scripts/test_dremio_login.sh`

---

## Files Created to Help You

1. **TRY-AGAIN.md** (this file) - Quick restart guide
2. **setup-reflections-simple.sh** - All-in-one setup with error handling
3. **scripts/test_dremio_login.sh** - Diagnostic script
4. **FIX-REFLECTION-ERRORS.md** - Detailed troubleshooting

---

## Quick Commands

```bash
# Method 1: Simple one-step (recommended)
export DREMIO_PASSWORD="your_password"
bash setup-reflections-simple.sh

# Method 2: Diagnostic first
export DREMIO_PASSWORD="your_password"
bash scripts/test_dremio_login.sh
# If that passes, then:
bash setup-reflections-simple.sh

# Method 3: Original Python script
export DREMIO_PASSWORD="your_password"
source venv/bin/activate
python3 scripts/create_reflections_auto.py
```

---

## Expected Timeline

- **Setup**: 30 seconds to run script
- **Build time**: 2-5 minutes for reflections to complete
- **Total**: ~5 minutes to deployed reflections

---

**Let's get those reflections working! Try the simple script above and let me know what happens.** 👍
