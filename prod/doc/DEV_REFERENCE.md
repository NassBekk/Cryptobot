# 👨‍💻 Developer Reference Card

Quick lookup for common operations.

---

## 🚀 Start/Stop Commands

```bash
# Start everything
docker-compose up --build

# Start in background
docker-compose up -d --build

# View logs
docker-compose logs -f app

# Stop everything
docker-compose down

# Restart a specific service
docker-compose restart app
docker-compose restart db

# Rebuild just the app container
docker-compose up --build app
```

---

## 🧪 Testing

### API Health
```bash
curl http://localhost:8000/health
```

### Get Symbols
```bash
curl http://localhost:8000/symbols
```

### Make Prediction
```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"symbol": "BTCUSDT"}'
```

### Get Metrics
```bash
curl http://localhost:8000/metrics
curl http://localhost:8000/metrics/BTCUSDT
```

---

## 🗄️ Database Commands

### Connect to Database
```bash
docker-compose exec db psql -U nassim -d crypto
```

### Common Queries
```sql
-- Check table exists
\dt

-- Count records
SELECT COUNT(*) FROM binance_historical_data_with_metrics;

-- Check specific symbol
SELECT COUNT(*) FROM binance_historical_data_with_metrics 
WHERE symbol = 'BTCUSDT';

-- List all symbols
SELECT DISTINCT symbol FROM binance_historical_data_with_metrics;

-- Recent data
SELECT * FROM binance_historical_data_with_metrics 
ORDER BY timestamp DESC LIMIT 10;
```

### Exit psql
```sql
\q
```

---

## 📂 File Operations

### Inside Container

```bash
# Enter container
docker-compose exec app bash

# List models
ls -la /app/models/

# List processed data
ls -la /app/data/processed/

# View training log (if exists)
cat /app/data/training.log

# Check available disk space
df -h
```

### From Host

```bash
# Copy file from container
docker cp <container_name>:/app/models/random_forest_model.pkl ./

# Copy file to container
docker cp ./random_forest_model.pkl <container_name>:/app/models/

# Check volumes
docker volume ls

# Inspect volume
docker inspect <volume_name>
```

---

## 🔍 Debugging

### View Full Logs
```bash
# Last 100 lines
docker-compose logs app | tail -100

# With timestamps
docker-compose logs -t app

# Real-time
docker-compose logs -f app

# Filter by keyword
docker-compose logs app | grep "ERROR\|WARNING\|Model"
```

### Check Container Status
```bash
# List all containers
docker-compose ps

# Inspect container
docker inspect <container_name>

# View resource usage
docker stats

# Check container events
docker events --filter container=<container_name>
```

### Manual Training Run
```bash
# Enter container
docker-compose exec app bash

# Run data cleaning
cd scripts && python 01_data_cleaning.py

# Run model training
python 02_train_models.py

# Run predictions
python 03_make_predictions.py
```

---

## 📊 Monitoring

### Check Memory/CPU Usage
```bash
docker stats
```

### Track Training Progress
```bash
# Monitor in real-time
watch -n 1 "docker exec <app_container> ls -lh /app/models/"

# Check data processing
docker-compose exec app wc -l /app/data/processed/cleaned_crypto_data.csv
```

### Database Size
```bash
docker-compose exec db psql -U nassim -d crypto \
  -c "SELECT pg_size_pretty(pg_database_size('crypto'))"
```

---

## 🛠️ Common Fixes

### Clear Everything (Fresh Start)
```bash
docker-compose down
docker system prune -a
docker volume prune
docker-compose up --build
```

### Force Retraining
```bash
# Remove trained models
docker-compose exec app rm -rf /app/models/*

# Remove processed data
docker-compose exec app rm -rf /app/data/processed/*

# Restart app
docker-compose restart app
```

### Fix Port Already in Use
```bash
# Find process using port 8000
lsof -i :8000

# Kill it
kill -9 <PID>

# Or change port in docker-compose.yml
# "8080:8000" instead of "8000:8000"
```

### Free Disk Space
```bash
# Remove unused Docker images
docker image prune -a

# Remove unused volumes
docker volume prune

# Remove unused networks
docker network prune
```

---

## 🔧 Configuration Changes

### Change API Port
**File**: `docker-compose.yml`
```yaml
# Line 7, change from:
ports:
  - "8000:8000"

# To:
ports:
  - "8080:8000"
```

### Change Database Credentials
**Files**: `docker-compose.yml`, `scripts/utils.py`
```bash
# Update in docker-compose.yml environment variables
# Update in utils.py in load_data_from_db() function
```

### Change Training Parameters
**File**: `scripts/02_train_models.py`
```python
# Random Forest
model_rf = RandomForestClassifier(
    n_estimators=200,  # Change this
    random_state=42
)

# LSTM
model_lstm.fit(
    X_train_lstm, y_train_res,
    epochs=100,  # Change this
    batch_size=32
)
```

---

## 📈 Performance Tuning

### Speed Up Training
```python
# Reduce data (in scripts/utils.py)
df = df.head(10000)  # Use only first 10k rows

# Reduce LSTM epochs (in scripts/02_train_models.py)
epochs=10  # Instead of 50

# Reduce RF estimators (in scripts/02_train_models.py)
n_estimators=50  # Instead of 100
```

### Reduce Memory Usage
```bash
# Limit Docker memory
# In docker-compose.yml:
services:
  app:
    mem_limit: 2g  # 2GB limit
```

### Use GPU for LSTM
```bash
# Requires nvidia-docker
# Modify Dockerfile to use tensorflow GPU image

# Change in 02_train_models.py:
# GPU should be auto-detected if available
```

---

## 📝 Development Workflow

### Add a New Feature
```bash
# 1. Create feature branch (if using git)
git checkout -b feature/my-feature

# 2. Make changes locally or in container

# 3. Test changes
docker-compose restart app

# 4. View results
docker-compose logs app

# 5. Commit and push
```

### Update Dependencies
```bash
# 1. Edit requirements.txt
vim requirements.txt

# 2. Rebuild container
docker-compose build --no-cache app

# 3. Start and test
docker-compose up
```

### Add New Cryptocurrency
```python
# 1. Update in scripts/utils.py load_data_from_db():
WHERE symbol IN ('BTCUSDT', 'ETHUSDT', 'BNBUSDT')  # Add here

# 2. Update in app/main.py ALLOWED_SYMBOLS:
ALLOWED_SYMBOLS = ["BTCUSDT", "ETHUSDT", "BNBUSDT"]  # Add here

# 3. Retrain models
docker-compose restart app
```

---

## 🆘 Emergency Commands

### If Everything is Broken
```bash
# Ultimate reset
docker-compose down -v
rm -rf ./models ./data
docker system prune -a --volumes
docker-compose up --build
```

### View Container ID
```bash
docker-compose ps
# Use the Container ID from the output
```

### Direct Container Access
```bash
# As root
docker exec -u root <container_name> bash

# With specific user
docker exec -u appuser <container_name> bash
```

### Save Container State
```bash
# Commit container to image
docker commit <container_name> my-backup:latest

# Export image
docker save my-backup:latest > backup.tar

# Load image later
docker load < backup.tar
```

---

## 📚 Documentation Structure

| File | Purpose | Best For |
|------|---------|----------|
| QUICK_START.md | Get started fast | New users |
| SETUP_AND_FIX.md | Detailed setup | Troubleshooting |
| DEBUG_CHECKLIST.md | Step-by-step debugging | Fixing issues |
| ARCHITECTURE.md | System design | Understanding flow |
| CHANGES_SUMMARY.md | What changed | Understanding fixes |
| DEV_REFERENCE.md | This file! | Quick lookup |

---

## 🔗 Useful Links

- [Docker Docs](https://docs.docker.com/)
- [Docker Compose Docs](https://docs.docker.com/compose/)
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [PostgreSQL Docs](https://www.postgresql.org/docs/)
- [TensorFlow/Keras Docs](https://www.tensorflow.org/api_docs)
- [Scikit-learn Docs](https://scikit-learn.org/stable/documentation.html)

---

## 💡 Pro Tips

1. **Always check logs first**: 90% of issues are visible in logs
2. **Use `ps` before any restart**: Understand what you're restarting
3. **Backup before changing**: `docker commit` the current state
4. **Use `-v` for verbose output**: More debugging info
5. **Read error messages carefully**: They often tell you exactly what's wrong
6. **Test locally before Docker**: Easier to debug
7. **Keep requirements.txt updated**: Track your dependencies
8. **Document your changes**: Future you will thank you
9. **Use meaningful container names**: Makes things easier to find
10. **Automate repetitive tasks**: Scripts save time

---

## ⚡ Quick Shortcuts

```bash
# Alias for docker-compose (if using bash)
alias dc='docker-compose'

# View app logs quickly
alias logs='docker-compose logs -f app'

# Enter app container
alias app='docker-compose exec app bash'

# Enter db container
alias db='docker-compose exec db psql -U nassim -d crypto'

# Restart everything
alias restart='docker-compose restart'

# Full reset
alias reset='docker-compose down -v && docker system prune -a'
```

Add these to your `.bashrc` or `.zshrc` for faster development!

---

## 🎓 Learning Resources

- Understand Docker: https://docker101.readthedocs.io/
- FastAPI tutorial: https://fastapi.tiangolo.com/tutorial/
- PostgreSQL basics: https://www.postgresqltutorial.com/
- Machine Learning with scikit-learn: https://scikit-learn.org/stable/documentation.html
- Deep Learning with TensorFlow: https://www.tensorflow.org/tutorials

---

**Last updated**: January 20, 2026
**Version**: 1.0
**Status**: ✅ Ready for use
