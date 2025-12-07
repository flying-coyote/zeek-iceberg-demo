# Dremio Playwright Diagnostic Report

**Date**: 2025-12-06
**Tool**: Playwright with Chromium
**Target**: http://localhost:9047

---

## Executive Summary

Dremio web UI is **NOT rendering** due to a JavaScript error. The page loads but shows a blank screen with the message "You need to enable JavaScript to run this app" even though JavaScript is enabled.

### Root Cause

**JavaScript Error**: `Invalid language tag: en-US@posix`

This error prevents React from mounting and rendering the Dremio UI.

---

## Detailed Findings

### 1. Page Loading Status

- **URL**: http://localhost:9047/
- **HTTP Status**: 200 OK
- **Page Title**: "Dremio"
- **HTML Size**: 820,007 bytes
- **Body Text**: Only 61 characters ("You need to enable JavaScript to run this app")
- **React Root**: `#root` div exists but has **0 inner HTML** (React not rendering)

### 2. Resource Loading

All static resources load successfully:

```
✅ /static/js/runtime.cf15651f.js - 200 OK
✅ /static/js/vendor.387accd6.js - 200 OK
✅ /static/js/app.306a0043.js - 200 OK
✅ /static/css/vendor.6dd3e03a.css - 200 OK
✅ /static/css/app.91796d5e.css - 200 OK
✅ /static/js/jsPlumb-2.1.4-min.js - 200 OK
✅ /static/js/4197.91752383.chunk.js - 200 OK
✅ /static/js/2779.a9671a7a.chunk.js - 200 OK
✅ /static/js/SQLParsingWorker.worker.5e78ed3f.worker.js - 200 OK
✅ /static/js/9655.e03c235e.chunk.js - 200 OK
```

### 3. JavaScript Errors

**Critical Error**:
```
Invalid language tag: en-US@posix
```

This error occurs during JavaScript initialization and prevents React from rendering the application.

**Non-Critical Errors** (external services, safe to ignore):
- Failed to load Google Tag Manager (GTM-5D8RST) - ERR_NAME_NOT_RESOLVED
- Failed to load Sentry error tracking - 404/403

### 4. Backend Status

Dremio backend is **working correctly**:
- Container: `zeek-demo-dremio` is running
- MinIO connection: **WORKING** (successfully listing buckets: `iceberg-warehouse`, `zeek-data`)
- API endpoints: Responding with 200 OK
- Locale in container: `en_US.UTF-8` (correct)

### 5. Login Status

**Cannot test login** because the UI doesn't render. The page never shows the login form due to the JavaScript error.

---

## Visual Evidence

### Screenshot Analysis

1. **Initial Load** (`01_initial_load.png`): Blank white page
2. **After Wait** (`05_dashboard.png`): Still blank white page
3. **Deep Diagnostic** (`20251206_202405_deep_diagnostic.png`): Completely blank

All screenshots show an empty page with no UI elements rendered.

---

## Technical Analysis

### What's Happening

1. Browser navigates to http://localhost:9047
2. HTML loads successfully (820KB)
3. All JavaScript bundles load successfully
4. JavaScript begins initialization
5. **FAILS** at locale initialization with "Invalid language tag: en-US@posix"
6. React initialization aborts
7. Page remains at fallback state: "You need to enable JavaScript to run this app"

### Why It's Failing

The error "Invalid language tag: en-US@posix" suggests that:

1. Dremio's JavaScript is trying to initialize with locale `en-US@posix`
2. This is **not a valid BCP 47 language tag** (should be `en-US` without the `@posix` suffix)
3. JavaScript's `Intl` API rejects this tag
4. The error is thrown before React can mount

### Where the Locale Comes From

The locale `en-US@posix` is likely coming from:
- Browser's navigator.language
- Or Chromium/Playwright's default locale setting
- Or being synthesized from system environment variables

---

## What's NOT the Problem

- ❌ **NOT** a network issue (all resources load successfully)
- ❌ **NOT** a Dremio backend issue (server is working fine)
- ❌ **NOT** a Docker/container issue (Dremio container runs correctly)
- ❌ **NOT** a MinIO connection issue (connection verified working)
- ❌ **NOT** missing JavaScript files (all bundles load)
- ❌ **NOT** a credential issue (can't even get to login page)

---

## Solutions

### Option 1: Set Browser Locale Explicitly (RECOMMENDED)

Modify Playwright script to set a valid locale:

```python
async with async_playwright() as p:
    browser = await p.chromium.launch(headless=False)
    context = await browser.new_context(
        locale='en-US',  # Use standard locale
        viewport={'width': 1920, 'height': 1080}
    )
    page = await context.new_page()
```

### Option 2: Use Real Browser Instead of Playwright

Open Dremio in a regular browser (Chrome, Firefox, Edge):
```bash
# On your Windows host (not WSL)
start http://localhost:9047
```

Real browsers handle locale correctly and won't have this issue.

### Option 3: Patch Chromium Launch Args

Force Chromium to use en-US locale:

```python
browser = await p.chromium.launch(
    headless=False,
    args=['--lang=en-US']
)
```

### Option 4: Update Dremio (if bug in Dremio)

If this is a Dremio bug (improper locale handling), update to latest version or report bug to Dremio.

---

## Next Steps

### Immediate Actions

1. **Test with explicit locale** (Option 1 above)
2. **Verify fix** by checking if login page renders
3. **Continue testing** if fix works

### If Fix Works

4. Navigate to minio source
5. Check for zeek-data bucket
6. Verify network-activity-ocsf dataset
7. Run test query: `SELECT COUNT(*) FROM minio."zeek-data"."network-activity-ocsf"`

---

## Diagnostic Files Generated

All files in `/home/jerem/zeek-iceberg-demo/screenshots/`:

```
20251206_202118_01_initial_load.png       - First page load
20251206_202118_02_login_page.png         - Login attempt
20251206_202118_03_login_filled.png       - Credentials filled
20251206_202122_04_after_login.png        - After login click
20251206_202124_05_dashboard.png          - Dashboard check
20251206_202124_06_minio_not_found.png    - MinIO not found
20251206_202324_dremio_state.png          - Page state check
20251206_202405_deep_diagnostic.png       - Deep diagnostic
dremio_page.html                           - Full HTML source
dremio_diagnostic.json                     - Full diagnostic data
```

---

## Conclusion

**The "hanging" is not actually hanging** - it's a **JavaScript initialization failure** due to an invalid locale tag. The page loads immediately but fails to render the UI due to this locale error.

**Fix**: Configure Playwright to use a standard locale (`en-US` instead of `en-US@posix`) and the UI should render correctly.

**Estimated time to fix**: 2 minutes (update script with locale setting)
