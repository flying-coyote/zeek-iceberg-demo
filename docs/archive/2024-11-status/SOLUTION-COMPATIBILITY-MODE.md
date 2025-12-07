# Solution: Enable Compatibility Mode for MinIO

## Problem Identified

**Error**: `RuntimeException: Error while trying to get region of zeek-data: java.lang.NullPointerException: region must not be null.`

**Root Cause**: Missing "Enable compatibility mode" checkbox in Dremio configuration.

## Solution from Official Dremio Documentation

Source: https://docs.dremio.com/cloud/sonar/data-sources/amazon-s3/configuring-s3-compatible-storage/

### Required Configuration for MinIO (S3-Compatible Storage)

When configuring MinIO as an Amazon S3 source in Dremio, you **MUST** enable compatibility mode:

#### Step-by-Step Configuration

1. **General Tab**:
   - Name: `minio`
   - Authentication: `AWS Access Key` (if using credentials) OR `No Authentication` (for public buckets)
   - Encrypt connection: **Unchecked**
   - Public Buckets: `zeek-data` (if using No Authentication)

2. **Advanced Options Tab**:

   **✅ CRITICAL: Check "Enable compatibility mode"**

   This checkbox is **essential** for S3-compatible storage like MinIO!

3. **Advanced Options Tab - Connection Properties**:

   Add these properties:

   | Property Name | Value | Notes |
   |---------------|-------|-------|
   | `fs.s3a.path.style.access` | `true` | **Required** - Use path-style URLs |
   | `fs.s3a.endpoint` | `minio:9000` | **Required** - NO `http://` prefix! |
   | `fs.s3a.connection.ssl.enabled` | `false` | Optional - Disable SSL for local |
   | `fs.s3a.endpoint.region` | `us-east-1` | Optional - Set region explicitly |

### What "Enable Compatibility Mode" Does

According to Dremio documentation:
- Enables support for non-AWS S3-compatible storage systems
- Adjusts S3 API calls to work with MinIO, Ceph, StorageGRID, etc.
- Disables AWS-specific region auto-detection
- Allows connection to S3-compatible endpoints

### Why We Missed This

**Previous attempts**:
- ❌ We configured all connection properties correctly
- ❌ We set the endpoint without `http://` prefix
- ❌ We added path-style access
- ❌ We even added region property
- **BUT** we never enabled the "Enable compatibility mode" checkbox!

This checkbox is easy to miss because:
1. It's in Advanced Options, but NOT in Connection Properties
2. It's separate from the properties list
3. The UI doesn't warn you if it's not enabled
4. The error message doesn't mention compatibility mode

## Docker Networking Consideration

**Important**: In our Docker Compose setup, both Dremio and MinIO are in the same network (`demo-network`), so:
- ✅ Use `minio:9000` (container hostname)
- ❌ Don't use `localhost:9000` (won't work across containers)
- ❌ Don't use `http://minio:9000` (no protocol prefix!)

## Next Steps

1. **Delete current MinIO source** (to start fresh)
2. **Recreate with compatibility mode enabled**:
   - Enable compatibility mode checkbox ✓
   - Add `fs.s3a.path.style.access = true`
   - Add `fs.s3a.endpoint = minio:9000`
   - Add `fs.s3a.connection.ssl.enabled = false`
3. **Test query**:
   ```sql
   SELECT * FROM minio."zeek-data"."network-activity" LIMIT 10;
   ```

## Expected Result

With compatibility mode enabled, Dremio should:
- ✅ Connect to MinIO without region errors
- ✅ Browse bucket structure
- ✅ Execute queries successfully
- ✅ Return 10 rows of network activity data

## References

- [Dremio: Configuring S3-Compatible Storage](https://docs.dremio.com/cloud/sonar/data-sources/amazon-s3/configuring-s3-compatible-storage/)
- [Dremio Community: Connecting to MinIO with Docker](https://community.dremio.com/t/connecting-dremio-to-s3-compatible-store-minio-with-docker/11592)
- [Dremio: Distributed Storage Configuration](https://docs.dremio.com/current/get-started/cluster-deployments/customizing-configuration/dremio-conf/dist-store-config/)

## Confidence Level

**High** - This is documented in official Dremio documentation specifically for MinIO and S3-compatible storage. Multiple community forum posts confirm this checkbox is required for non-AWS S3 storage systems.
