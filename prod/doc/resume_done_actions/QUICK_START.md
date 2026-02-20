# 🚀 Quick Start Guide - CryptoBot

## What Was Fixed

Your models weren't being created because:
- ❌ Training scripts never ran (Docker only started the API)
- ❌ `/data` and `/models` directories didn't exist
- ❌ No database population mechanism on startup

**Now fixed!** ✅

---

## Start the Application

```bash
cd /home/nassbuntu/projet/AVR25-CDE-OPA-1/cryptobot/prod
docker-compose up --build
```

**Wait for**: All models trained → "Starting FastAPI Application" message

---

## What Happens Automatically

1. ✅ Database starts
2. ✅ Waits for PostgreSQL (up to 30 sec)
3. ✅ Cleans data from database
4. ✅ Trains all models (RF, LSTM, ARIMA, SARIMAX)
5. ✅ Creates `/models` directory with trained models
6. ✅ Starts FastAPI server on port 8000

---

## Test It Works

```bash
# Health check
curl http://localhost:8000/health

# Get supported symbols
curl http://localhost:8000/symbols

# Make a prediction
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"symbol": "BTCUSDT"}'
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "Models not loading" | Check logs: `docker-compose logs app` |
| "PostgreSQL error" | Ensure db container is running: `docker-compose ps` |
| "No data error" | Verify data in database with init scripts |
| "Port 8000 in use" | Change port in `docker-compose.yml` |

---

## Key Files Modified

- `scripts/00_init_and_train.py` ← NEW training orchestrator
- `entrypoint.sh` ← NEW Docker startup script
- `Dockerfile` ← Updated with directories & entrypoint
- `docker-compose.yml` ← Updated with volume persistence
- `app/main.py` ← Updated with graceful error handling

---

## Verify Models Exist

```bash
docker exec cryptobot_app_1 ls -la /app/models/
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

## For Detailed Docs

See: `SETUP_AND_FIX.md` in the prod directory
