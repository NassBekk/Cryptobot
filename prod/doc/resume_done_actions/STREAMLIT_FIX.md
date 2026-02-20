# 🔧 Streamlit Fix - January 20, 2026

## Problem

Streamlit container was showing as "unhealthy" (`Up (unhealthy)`) even though it was running and accessible.

## Root Cause

The health check in `Dockerfile.streamlit` was using the `curl` command to check `http://localhost:8501/_stcore/health`, but `curl` was not installed in the Docker image.

**Original Dockerfile.streamlit:**
```dockerfile
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health
```

This health check would always fail because `curl` doesn't exist in the container, causing Docker to mark the container as unhealthy.

## Solution

Updated the Dockerfile to:
1. **Install curl** as part of the dependencies
2. **Add proper health check parameters** (interval, timeout, start-period, retries)

**Updated Dockerfile.streamlit:**
```dockerfile
# Install curl along with other dependencies
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/* && \
    pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Health check with proper timing
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl --fail http://localhost:8501/_stcore/health || exit 1
```

## Changes Made

**File Modified**: `/Dockerfile.streamlit`

- ✅ Added `curl` installation to apt-get command
- ✅ Added health check parameters for robustness
- ✅ Maintained all existing functionality

## Verification

After the fix:

```bash
docker-compose ps
```

Shows:
```
prod_streamlit_1   streamlit run app/streamli ...   Up (healthy)   0.0.0.0:8501->8501/tcp
```

✅ Health check now **passes successfully**

## Testing

```bash
# Test Streamlit is accessible
curl http://localhost:8501
# Response: HTTP 200 OK

# Check all services
docker-compose ps
# All containers: Up (healthy) or Up
```

## Impact

- ✅ Streamlit dashboard now fully operational
- ✅ Health checks passing
- ✅ No changes to functionality
- ✅ Container auto-restarts work properly now

## How to Use

The fix is already applied. Just access Streamlit at:
```
http://localhost:8501
```

## Future Prevention

This issue occurred because:
1. The Dockerfile referenced a tool (`curl`) that wasn't available
2. The health check wasn't properly configured

**Best Practice**: Always ensure any tool referenced in health checks is installed in the Docker image.
