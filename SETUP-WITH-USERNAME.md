# Setup Reflections with Username and Password

The scripts need both username and password. Here's how to set them up properly.

---

## Quick Setup (Most Common)

If your username is **admin** (default):

```bash
# Only need to set password (username defaults to "admin")
export DREMIO_PASSWORD="your_password"

# Run setup
bash setup-reflections-simple.sh
```

---

## Setup with Custom Username

If your username is **NOT "admin"**:

```bash
# Set both username and password
export DREMIO_USERNAME="your_username"
export DREMIO_PASSWORD="your_password"

# Run setup
bash setup-reflections-simple.sh
```

---

## Verify Your Credentials First

Not sure what your username and password are? Test them:

```bash
# Set your credentials
export DREMIO_USERNAME="admin"  # or your actual username
export DREMIO_PASSWORD="your_password"

# Run diagnostic
bash scripts/test_dremio_login.sh
```

**If authentication succeeds**, you'll see:
```
✅ Authentication SUCCESSFUL!
```

**If it fails**, you'll see the error and can fix it.

---

## Complete Step-by-Step

### Step 1: Set Credentials

```bash
# Set username (if not "admin")
export DREMIO_USERNAME="your_username"

# Set password
export DREMIO_PASSWORD="your_password"

# Verify they're set
echo "Username: $DREMIO_USERNAME"
echo "Password length: ${#DREMIO_PASSWORD} characters"
```

### Step 2: Test Authentication

```bash
bash scripts/test_dremio_login.sh
```

**Expected output**:
```
========================================================================
Dremio Authentication Diagnostic
========================================================================

✓ DREMIO_PASSWORD is set (length: X characters)

Checking Dremio connectivity...
✓ Dremio is accessible at http://localhost:9047

Testing authentication...
✅ Authentication SUCCESSFUL!

Token received (first 20 chars): abcd1234...

You can now run:
  python3 scripts/create_reflections_auto.py
```

### Step 3: Run Reflection Setup

```bash
bash setup-reflections-simple.sh
```

OR

```bash
source venv/bin/activate
python3 scripts/create_reflections_auto.py
```

---

## Common Scenarios

### Scenario 1: Default Setup (username = admin)

```bash
export DREMIO_PASSWORD="mypassword123"
bash setup-reflections-simple.sh
```

### Scenario 2: Custom Username

```bash
export DREMIO_USERNAME="john.doe@company.com"
export DREMIO_PASSWORD="mypassword123"
bash setup-reflections-simple.sh
```

### Scenario 3: Password with Special Characters

```bash
# Use single quotes to avoid shell interpretation
export DREMIO_USERNAME="admin"
export DREMIO_PASSWORD='my"pass$word!'
bash setup-reflections-simple.sh
```

### Scenario 4: Set Interactively (password hidden)

```bash
# Set username
export DREMIO_USERNAME="admin"

# Set password interactively (won't be visible)
read -s -p "Enter Dremio password: " DREMIO_PASSWORD
export DREMIO_PASSWORD
echo ""  # New line

# Run setup
bash setup-reflections-simple.sh
```

---

## Troubleshooting

### "Invalid username or password"

**Check your credentials in Dremio UI first**:
1. Open http://localhost:9047
2. Try logging in manually
3. Use the EXACT same username and password in your exports

**Common issues**:
- Username is case-sensitive
- Email address usernames need quotes if they have special chars
- Password has special characters that need escaping

### "DREMIO_PASSWORD is not set"

**This means the export didn't work**:

```bash
# Check if it's set
echo $DREMIO_PASSWORD

# If empty, set it again
export DREMIO_PASSWORD="your_password"

# Verify
echo "Password is set: ${#DREMIO_PASSWORD} chars"
```

### Password disappeared after opening new terminal

**Export only lasts for current terminal session**:

Solution 1: Re-export in new terminal
```bash
export DREMIO_USERNAME="admin"
export DREMIO_PASSWORD="your_password"
```

Solution 2: Put them in a file (for convenience)
```bash
# Create credentials file (don't commit to git!)
cat > .dremio-credentials.sh <<EOF
export DREMIO_USERNAME="admin"
export DREMIO_PASSWORD="your_password"
EOF

# Source it whenever needed
source .dremio-credentials.sh
bash setup-reflections-simple.sh
```

---

## Quick Command Reference

```bash
# Set credentials
export DREMIO_USERNAME="admin"           # Your username
export DREMIO_PASSWORD="your_password"   # Your password

# Test authentication
bash scripts/test_dremio_login.sh

# Run setup (if auth test passes)
bash setup-reflections-simple.sh

# Check status later
python3 scripts/check_reflections_auto.py
```

---

## What Username Should I Use?

**To find out**:
1. Open http://localhost:9047
2. Look at what username you use to log in
3. Common usernames:
   - `admin` (default)
   - Your email address
   - A custom username you created

**If you've never logged into Dremio before**:
- You might need to create an account first
- Visit http://localhost:9047
- Follow the first-time setup wizard
- Then use those credentials in the scripts

---

## All-In-One Command

```bash
# Set both, then run - all in one go
DREMIO_USERNAME="admin" \
DREMIO_PASSWORD="your_password" \
bash setup-reflections-simple.sh
```

This sets the variables just for this one command.

---

**Now try again with both username and password set!** 👍
