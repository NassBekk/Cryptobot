# 🔧 Setup & Troubleshooting Guide

## Problem Summary

Your models weren't being created in Docker because:

1. **No training pipeline execution**: The Docker container only ran the FastAPI server. The training scripts were never executed.
2. **Missing directories**: `/data` and `/models` directories didn't exist.
3. **Missing data source**: The training pipeline requires data in PostgreSQL, which wasn't populated on startup.

## Solution Implemented

### ✅ What Was Fixed

1. **Created `00_init_and_train.py`**: Orchestrates the complete training pipeline
   - Checks PostgreSQL availability (retries up to 30 seconds)
   - Runs data cleaning (`01_data_cleaning.py`)
   - Runs model training (`02_train_models.py`)
   - Reports success/failure of each step

2. **Created `entrypoint.sh`**: Docker startup script
   - Waits for PostgreSQL to be ready
   - Executes the initialization/training pipeline
   - Starts the FastAPI server
   - Provides clear status messages

3. **Updated `Dockerfile`**
   - Creates required directories (`/app/models`, `/app/data/processed`, `/app/data/predictions`)
   - Uses entrypoint script for proper initialization
   - Makes the script executable

4. **Updated `docker-compose.yml`**
   - Added volume mounts for `/models` and `/data` directories for persistence
   - Added `restart: unless-stopped` for auto-restart on crash
   - Ensures models/data survive container restarts

5. **Improved `app/main.py` startup**
   - Graceful error handling if models don't exist yet
   - Better logging of model loading status
   - Won't crash if training hasn't completed
   - Provides clear warnings about missing models

---

## How to Run

### Option 1: Docker (Recommended)

```bash
# Navigate to the project directory
cd /home/nassbuntu/projet/AVR25-CDE-OPA-1/cryptobot/prod

# Build and start the containers
docker-compose up --build

# The output will show:
# 1. Database initialization
# 2. Data cleaning progress
# 3. Model training progress (Random Forest, LSTM, ARIMA, SARIMAX)
# 4. API server startup
```

**Expected timeline**: ~3-10 minutes depending on data size and hardware

### Option 2: Local Development

```bash
# Ensure PostgreSQL is running
# Configure DATABASE_URL environment variable

# Run the training pipeline manually
cd /home/nassbuntu/projet/AVR25-CDE-OPA-1/cryptobot/prod/scripts
python 00_init_and_train.py

# Then start the API in another terminal
cd /home/nassbuntu/projet/AVR25-CDE-OPA-1/cryptobot/prod
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## Verification Checklist

After startup, verify:

✅ **Check Docker logs**:
```bash
docker-compose logs app
```

✅ **API Health Check**:
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{"status": "healthy", "service": "cryptobot-api"}
```

✅ **Check Available Symbols**:
```bash
curl http://localhost:8000/symbols
```

Expected response:
```json
{
  "symbols": ["BTCUSDT", "ETHUSDT"],
  "description": "Symboles de cryptomonnaies supportés pour les prédictions"
}
```

✅ **Verify Models Exist**:
```bash
# Inside or outside container
ls -la ./models/
```

Should show:
```
random_forest_model.pkl
lstm_model.keras
arima_model_BTCUSDT.pkl
arima_model_ETHUSDT.pkl
sarimax_model_BTCUSDT.pkl
sarimax_model_ETHUSDT.pkl
```

---

## Troubleshooting

### ❌ "PostgreSQL not available after 30 seconds"
- **Cause**: Database container didn't start
- **Fix**: 
  ```bash
  docker-compose ps  # Check if db container is running
  docker-compose logs db  # Check database logs
  ```

### ❌ "No such file or directory: cleaned_crypto_data.csv"
- **Cause**: Data cleaning failed (no data in database)
- **Fix**: 
  - Ensure data exists in PostgreSQL table `binance_historical_data_with_metrics`
  - Check database initialization scripts in `database/init/`

### ❌ "Models not loading in app"
- **Cause**: Training pipeline didn't complete or models are in wrong location
- **Fix**: 
  ```bash
  docker-compose logs app | grep -E "ARIMA|Random|LSTM|SARIMAX"
  ```

### ❌ "API won't start"
- **Cause**: Models are missing and old code doesn't handle gracefully
- **Fix**: Updated code now handles missing models, but restart should help:
  ```bash
  docker-compose restart app
  ```

---

## Key Files Modified

- ✅ `/scripts/00_init_and_train.py` (NEW)
- ✅ `/entrypoint.sh` (NEW)
- ✅ `/Dockerfile` (UPDATED)
- ✅ `/docker-compose.yml` (UPDATED)
- ✅ `/app/main.py` (UPDATED - startup logic)

---

## Next Steps

1. **Populate PostgreSQL with data**:
   - If using Binance API, run the data collection scripts
   - Check `/database/init/` for any SQL initialization files

2. **Monitor training progress**:
   ```bash
   docker-compose logs -f app
   ```

3. **Test predictions once ready**:
   ```bash
   curl -X POST http://localhost:8000/predict \
     -H "Content-Type: application/json" \
     -d '{"symbol": "BTCUSDT"}'
   ```

---

## Files Structure After Fix

```
prod/
├── entrypoint.sh           ← Entry point script for Docker
├── Dockerfile              ← Updated with proper initialization
├── docker-compose.yml      ← Updated with volume persistence
├── app/
│   ├── main.py            ← Updated with graceful error handling
│   ├── models/            ← Will be created automatically
│   └── data/processed/    ← Will be created automatically
├── scripts/
│   ├── 00_init_and_train.py  ← Training orchestrator (NEW)
│   ├── 01_data_cleaning.py   ← Data cleaning
│   ├── 02_train_models.py    ← Model training
│   └── utils.py
├── models/                ← Will be created automatically
├── data/
│   ├── processed/         ← Will be created automatically
│   └── predictions/       ← Will be created automatically
└── requirements.txt
```

---

## Performance Notes

- **Data Cleaning**: Usually < 1 minute
- **Random Forest Training**: 1-2 minutes
- **LSTM Training**: 2-5 minutes (depends on epochs and data size)
- **ARIMA/SARIMAX Training**: 1-3 minutes per symbol
- **Total First Run**: 5-15 minutes

---

## Support

If you still encounter issues:
1. Check the detailed logs: `docker-compose logs app`
2. Verify PostgreSQL is working: `docker-compose exec db psql -U nassim -d crypto -c "SELECT COUNT(*) FROM binance_historical_data_with_metrics;"`
3. Check data exists: Ensure at least 50+ rows per symbol in the database
