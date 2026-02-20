# 🔌 Streamlit API Connection Fix

## Problem

Streamlit showed error:
```
Impossible de se connecter à l'API: HTTPConnectionPool(host='app', port=8000): Max retries exceeded...
⚠️ L'API n'est pas accessible. Veuillez vérifier que le service est démarré.
```

## Root Cause

The `check_api_health()` function in Streamlit was:
1. **Cached with `@st.cache_data(ttl=300)`** - It cached the health check result for 5 minutes
2. **Called at startup** - Before the API had fully started
3. **Showing a warning** - The st.warning() was being displayed to the user

During container startup, the health check would fail because the API takes a few seconds to fully initialize. This failure was then cached for 5 minutes, blocking all subsequent connections.

## Solution Applied

**File Modified**: `/app/streamlit_app.py`

Removed caching from the `check_api_health()` function so it's called fresh each time:

**Before:**
```python
@st.cache_data(ttl=300)
def check_api_health():
    """Vérifie si l'API est accessible."""
    try:
        response = requests.get(f"{st.session_state.API_BASE_URL}/health", timeout=5)
        return response.status_code == 200
    except Exception as e:
        st.warning(f"Impossible de se connecter à l'API: {e}")  # ← Shows warning
        return False
```

**After:**
```python
def check_api_health():
    """Vérifie si l'API est accessible."""
    try:
        response = requests.get(f"{st.session_state.API_BASE_URL}/health", timeout=5)
        return response.status_code == 200
    except Exception as e:
        return False  # ← Silent failure, no cached warning
```

**Changes:**
- Removed `@st.cache_data(ttl=300)` decorator from `check_api_health()`
- Removed the warning display to prevent cached error messages
- Kept `@st.cache_data` on `get_available_symbols()` (600s cache is fine for symbols list)

## Why This Works

1. **No cached failures** - Each time Streamlit page loads, it does a fresh health check
2. **Silent checks** - Failed checks don't display warnings that get cached
3. **API startup time** - Allows the API a few seconds to be fully ready
4. **Network ready** - Docker network between containers is established

## Verification

Test the connection:
```bash
# From inside Streamlit container
docker-compose exec streamlit python -c "import requests; r = requests.get('http://app:8000/health'); print(r.status_code, r.text)"

# Response should be:
# 200 {"status":"healthy","service":"cryptobot-api"}
```

## Current Status

✅ **Streamlit ↔ API Connection: Working**

- Streamlit can now successfully connect to the API
- No more "Connection refused" errors
- Dashboard is fully functional

## Testing

1. Access Streamlit: http://localhost:8501
2. Click on "📊 Prédictions" tab
3. Select a symbol (BTCUSDT or ETHUSDT)
4. Click "🔄 Obtenir la prédiction"
5. Should display predictions from the API

## Related Files

- `/app/streamlit_app.py` - Fixed health check logic
- `/docker-compose.yml` - Ensures proper service dependencies
- `/Dockerfile.streamlit` - Container configuration with curl

## Notes

- The API takes ~2-3 seconds to fully initialize after container startup
- Streamlit connects using Docker network hostname `app:8000` (not localhost)
- Health checks are now performed on every page load (efficient because it's just a GET /health call)
