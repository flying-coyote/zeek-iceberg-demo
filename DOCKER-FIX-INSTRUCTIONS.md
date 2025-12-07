# Docker/WSL Integration Fix Instructions

## Current Status
✅ Docker Desktop is installed on Windows (v28.5.1)
✅ Docker socket exists at `/var/run/docker.sock`
❌ WSL integration is NOT enabled
❌ Docker commands not working in WSL

---

## Solution: Enable Docker Desktop WSL Integration

### Step-by-Step Instructions (2 minutes)

1. **Switch to Windows** (Alt+Tab or click Windows taskbar)

2. **Find Docker Desktop icon** in system tray (bottom-right corner, whale icon)
   - If not visible, click the up arrow to show hidden icons
   - If not running, start Docker Desktop from Start Menu

3. **Open Docker Desktop Settings**
   - Right-click the Docker whale icon → "Settings"
   - OR: Open Docker Desktop window → Click gear icon (top-right)

4. **Navigate to WSL Integration**
   - In left sidebar: Click "Resources"
   - Then click "WSL Integration"

5. **Enable WSL Integration**
   - Toggle ON: "Enable integration with my default WSL distro"
   - Find your distro in the list (likely "Ubuntu" or similar)
   - Toggle it ON (should turn blue/enabled)

   Your settings should look like:
   ```
   ☑ Enable integration with my default WSL distro

   Enable integration with additional distros:
   Ubuntu                    [Toggle: ON]
   ```

6. **Apply Changes**
   - Click "Apply & Restart" button
   - Wait for Docker Desktop to restart (~ 30-60 seconds)
   - The whale icon should stop animating when ready

7. **Return to WSL Terminal** and test:
   ```bash
   docker version
   ```

---

## Expected Result After Fix

When properly configured, you should see:
```
Client:
 Version:           26.0.0 (or similar)
 API version:       1.45
 OS/Arch:           linux/amd64

Server: Docker Desktop
 Engine:
  Version:          26.0.0
  API version:      1.45
```

Both Client AND Server sections should appear.

---

## If Docker Desktop Settings Won't Open

Try these alternatives:

1. **Restart Docker Desktop**:
   - Right-click whale icon → "Quit Docker Desktop"
   - Start Docker Desktop again from Start Menu
   - Try settings again

2. **Check Docker Desktop is fully started**:
   - Whale icon should be steady (not animated)
   - Hover over icon should show "Docker Desktop is running"

3. **Windows Restart** (last resort):
   - Save all work
   - Restart Windows
   - Docker Desktop should auto-start
   - Try settings again

---

## Alternative: Command Line Fix

If UI is not accessible, try PowerShell (as Administrator):
```powershell
# In Windows PowerShell (not WSL)
docker version
wsl --list --verbose
```

Make sure your WSL distro shows as "Running" and is version 2.

---

## Verification in WSL

Once WSL integration is enabled, verify with:
```bash
# Should work without any "not found" errors
docker version
docker ps
docker-compose version

# Should show Docker info
docker info | grep "Server Version"
```

---

## Still Having Issues?

Common problems and solutions:

**"The command 'docker' could not be found"**
- WSL integration not enabled yet
- Docker Desktop not fully restarted
- Try: Close WSL terminal, wait 10 seconds, open new terminal

**"Cannot connect to Docker daemon"**
- Docker Desktop not running
- Start Docker Desktop on Windows first

**"Permission denied on /var/run/docker.sock"**
- Run: `sudo usermod -aG docker $USER`
- Then: `newgrp docker`

---

## Next Steps After Fix

Once Docker is working:
```bash
cd /home/jerem/zeek-iceberg-demo

# Start infrastructure
docker-compose up -d

# Verify containers
docker-compose ps

# Load demo data
source .venv/bin/activate
python scripts/load_real_zeek_to_ocsf.py --records 100000
```

---

**Time Required**: 2-3 minutes
**Difficulty**: Easy (just toggle settings)
**Success Rate**: 95% (works unless Docker Desktop has issues)