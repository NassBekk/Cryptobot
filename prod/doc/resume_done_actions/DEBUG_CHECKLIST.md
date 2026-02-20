# 🔍 Debug Checklist

Use this when something doesn't work as expected.

## ✅ Pre-Flight Checks

- [ ] Docker is installed: `docker --version`
- [ ] Docker Compose is installed: `docker-compose --version`
- [ ] No containers already running on ports 8000, 5432, 8501
- [ ] You're in the correct directory: `/prod`

---

## 📊 Startup Verification

### Check 1: Containers Starting

```bash
docker-compose up --build
# Watch for these messages:
# - "db_1      | PostgreSQL started"
# - "app_1     | ⏳ Waiting for PostgreSQL"
# - "app_1     | ✅ PostgreSQL is ready!"
```

**Issue?** Database didn't start
```bash
docker-compose logs db
```

---

### Check 2: Data Pipeline Starting

Look for these messages in logs:
```
📌 Step 1: Data Cleaning
📌 Step 2: Model Training
```

**Issue?** Training didn't start
```bash
docker-compose logs app | grep -E "Training|Data|Cleaning"
```

---

### Check 3: Models Being Created

Look for success messages like:
```
✅ Random Forest model loaded
✅ LSTM model loaded  
✅ ARIMA model for BTCUSDT loaded
✅ SARIMAX model for BTCUSDT loaded
```

**Issue?** Models not found
```bash
# Wait 5-10 minutes on first run, then check:
docker exec <app_container_name> ls -la /app/models/
```

---

## 🛠️ Common Issues & Fixes

### Issue: "psycopg2 OperationalError"

**Cause**: PostgreSQL not ready

**Fix**:
```bash
# Check if DB is running
docker-compose ps

# If not running, restart:
docker-compose restart db

# Wait 10 seconds, then try again
docker-compose logs db | tail -20
```

---

### Issue: "No such file: cleaned_crypto_data.csv"

**Cause**: No data in the database

**Fix**:
```bash
# Check if binance_historical_data_with_metrics table exists:
docker-compose exec db psql -U nassim -d crypto -c "\dt"

# Check if table has data:
docker-compose exec db psql -U nassim -d crypto -c "SELECT COUNT(*) FROM binance_historical_data_with_metrics;"

# If count is 0, data needs to be populated
# Run your data collection script or import process
```

---

### Issue: "Scaler not found" or "Shape mismatch"

**Cause**: Inconsistent data features

**Fix**:
```bash
# Delete old cleaned data and retrain:
docker exec <app_name> rm -rf /app/data/processed/

# Restart container to re-train:
docker-compose restart app
```

---

### Issue: "Port 8000 already in use"

**Fix**:
```bash
# Option 1: Kill existing process
lsof -i :8000
kill -9 <PID>

# Option 2: Use different port in docker-compose.yml
# Change "8000:8000" to "8080:8000"
```

---

### Issue: Models load but predictions fail

**Cause**: Model incompatibility or data mismatch

**Fix**:
```bash
# Get detailed error:
docker-compose logs app | grep -A5 "ERROR\|Exception"

# Check model files exist:
docker exec <app_name> ls -lh /app/models/

# Verify data preprocessing matches training:
grep "normalize_features" /app/scripts/01_data_cleaning.py
grep "normalize_features" /app/scripts/02_train_models.py
```

---

## 📈 Performance Monitoring

### Check Training Progress

```bash
# Real-time logs
docker-compose logs -f app

# Filter for specific model training
docker-compose logs app | grep "Training\|Epoch\|accuracy"
```

### Estimated Timeline

```
0-30s:    PostgreSQL startup
30-60s:   Python environment initialization  
60-120s:  Data loading and cleaning
120-240s: Random Forest training
240-360s: LSTM training
360-480s: ARIMA training
480-540s: SARIMAX training
540-600s: API server startup
```

**Total**: ~5-15 minutes on first run (depends on data size)

---

## 🧪 Manual Testing

### Test Data Pipeline

```bash
# Enter the app container
docker-compose exec app bash

# Run data cleaning manually
cd scripts
python 01_data_cleaning.py

# Check output
ls -la ../data/processed/
```

### Test Model Training

```bash
# Inside container
python 02_train_models.py

# Check models created
ls -la ../models/
```

### Test API

```bash
# Health check
curl http://localhost:8000/health

# Symbols list
curl http://localhost:8000/symbols

# Test prediction
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"symbol": "BTCUSDT"}'
```

---

## 🗑️ Clean Start

If everything is broken, do a clean start:

```bash
# Stop all containers
docker-compose down

# Remove all data
docker system prune -a

# Remove volumes (⚠️ This deletes PostgreSQL data)
docker volume prune

# Start fresh
docker-compose up --build
```

---

## 📋 Information to Provide When Asking for Help

1. Output of `docker-compose ps`
2. Last 50 lines of `docker-compose logs app`
3. Output of checking models: `docker exec <app_name> ls -la /app/models/`
4. Database record count: 
   ```bash
   docker-compose exec db psql -U nassim -d crypto -c "SELECT COUNT(*) FROM binance_historical_data_with_metrics;"
   ```
5. Your OS and Docker versions

---

## 📞 Support Resources

- Check `SETUP_AND_FIX.md` for detailed setup info
- Check `QUICK_START.md` for quick reference
- Docker Compose docs: https://docs.docker.com/compose/
- FastAPI docs: https://fastapi.tiangolo.com/
