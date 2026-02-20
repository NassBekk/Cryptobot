# 🏗️ System Architecture & Data Flow

## Before (Broken) ❌

```
docker-compose up
         ↓
    ┌─────────────────────┐
    │   Build Docker      │
    │   Image             │
    └──────────┬──────────┘
               ↓
    ┌─────────────────────┐
    │   Start Container   │
    └──────────┬──────────┘
               ↓
    ┌─────────────────────┐
    │   Run Uvicorn API   │ ← ONLY THIS RUNS!
    │   (immediately)     │
    └──────────┬──────────┘
               ↓
    ┌─────────────────────┐
    │   API tries to      │
    │   load models...    │
    └──────────┬──────────┘
               ↓
    ┌─────────────────────┐
    │ ❌ CRASH!           │
    │ Models don't exist! │
    │ Training never ran! │
    └─────────────────────┘
```

---

## After (Fixed) ✅

```
docker-compose up
         ↓
    ┌─────────────────────────────┐
    │   Build Docker Image        │
    │   - Create /models          │
    │   - Create /data            │
    │   - Copy entrypoint.sh      │
    └──────────┬──────────────────┘
               ↓
    ┌─────────────────────────────┐
    │   Start Container           │
    │   Run entrypoint.sh ← NEW!  │
    └──────────┬──────────────────┘
               ↓
    ┌─────────────────────────────┐
    │   Wait for PostgreSQL       │
    │   (max 30 seconds)          │
    └──────────┬──────────────────┘
               ↓
    ┌─────────────────────────────┐
    │   Run Training Pipeline     │ ← NEW!
    │   00_init_and_train.py      │
    └──────────┬──────────────────┘
               ├─────────────────────┐
               ↓                     ↓
    ┌──────────────────┐  ┌─────────────────┐
    │ 01_Data Cleaning │  │ Load DB data    │
    │                  │→→| Apply features  │
    │ Output:          │  | Normalize       │
    │ cleaned_data.csv │  | Save scaler     │
    └──────────────────┘  └─────────────────┘
               ↓
    ┌──────────────────────────────┐
    │ 02_Train_Models ← NEW!       │
    │                              │
    │ Trains:                      │
    │ ✅ Random Forest             │
    │ ✅ LSTM                      │
    │ ✅ ARIMA (2 symbols)         │
    │ ✅ SARIMAX (2 symbols)       │
    │                              │
    │ Saves to /models/            │
    └──────────┬───────────────────┘
               ↓
    ┌──────────────────────────────┐
    │ ✅ All Models Created!       │
    │                              │
    │ Files exist:                 │
    │ - random_forest_model.pkl    │
    │ - lstm_model.keras           │
    │ - arima_model_BTCUSDT.pkl    │
    │ - arima_model_ETHUSDT.pkl    │
    │ - sarimax_model_BTCUSDT.pkl  │
    │ - sarimax_model_ETHUSDT.pkl  │
    └──────────┬───────────────────┘
               ↓
    ┌──────────────────────────────┐
    │   Run Uvicorn API            │
    │                              │
    │   FastAPI loads models       │
    │   from /models/ ✅           │
    └──────────┬───────────────────┘
               ↓
    ┌──────────────────────────────┐
    │ 🚀 API Ready!                │
    │                              │
    │ Endpoints:                   │
    │ /health                      │
    │ /symbols                     │
    │ /predict                     │
    │ /evaluate                    │
    │ /metrics                     │
    └──────────────────────────────┘
```

---

## Data Flow During Prediction

```
User Request
      ↓
  POST /predict
      ↓
┌─────────────────────────────────┐
│  FastAPI Predict Endpoint       │
│  (app/main.py)                  │
└──────────┬──────────────────────┘
           ↓
    Check models loaded ✅
           ↓
┌─────────────────────────────────┐
│  Query PostgreSQL               │
│  Get last 100 rows for symbol   │
└──────────┬──────────────────────┘
           ↓
┌─────────────────────────────────┐
│  Data Preprocessing             │
│  - Calculate indicators         │
│  - Moving averages              │
│  - RSI                          │
│  - Volatility                   │
│  - Normalize features           │
└──────────┬──────────────────────┘
           ↓
    ┌──────────────────┬──────────────┬──────────────┐
    ↓                  ↓              ↓              ↓
┌────────┐  ┌─────────────┐  ┌──────────┐  ┌───────────┐
│  RF    │  │    LSTM     │  │  ARIMA   │  │ SARIMAX   │
│Predict │  │  Predict    │  │Predict   │  │ Predict   │
└────┬───┘  └──────┬──────┘  └────┬─────┘  └─────┬─────┘
     ↓             ↓              ↓              ↓
     └─────────────┼──────────────┼──────────────┘
                   ↓
        ┌──────────────────────┐
        │ Aggregate Results    │
        │ - RF prediction      │
        │ - LSTM prediction    │
        │ - ARIMA prediction   │
        │ - SARIMAX prediction │
        │ - Average/consensus  │
        └──────────┬───────────┘
                   ↓
        ┌──────────────────────┐
        │ Return JSON Response │
        │ {"symbol": "..."}    │
        │  "predictions": {...}│
        └──────────────────────┘
                   ↓
        User receives prediction
```

---

## File Organization

```
prod/ (root)
│
├── 🐳 Docker Configuration
│   ├── Dockerfile                 ← Updated: Creates dirs, uses entrypoint
│   ├── docker-compose.yml         ← Updated: Adds volume persistence
│   └── entrypoint.sh             ← NEW: Orchestrates startup
│
├── 📚 Documentation
│   ├── QUICK_START.md            ← Quick reference
│   ├── SETUP_AND_FIX.md          ← Comprehensive setup guide
│   ├── DEBUG_CHECKLIST.md        ← Troubleshooting
│   ├── CHANGES_SUMMARY.md        ← This document summary
│   └── ARCHITECTURE.md           ← This file
│
├── 📊 scripts/ (Training Pipeline)
│   ├── 00_init_and_train.py      ← NEW: Main orchestrator
│   ├── 01_data_cleaning.py       ← Data preparation
│   ├── 02_train_models.py        ← Model training
│   ├── 03_make_predictions.py    ← Standalone predictions
│   └── utils.py                  ← Shared utilities
│
├── 🎯 app/ (FastAPI Application)
│   ├── main.py                   ← Updated: Better error handling
│   ├── evaluation.py
│   ├── __init__.py
│   ├── models/                   ← Trained models (created at runtime)
│   └── data/processed/           ← Processed data (created at runtime)
│
├── 🏛️ database/
│   └── init/                     ← SQL initialization scripts
│
├── 🎨 models/                    ← Model storage (created at runtime)
│   ├── random_forest_model.pkl
│   ├── lstm_model.keras
│   ├── arima_model_BTCUSDT.pkl
│   ├── arima_model_ETHUSDT.pkl
│   ├── sarimax_model_BTCUSDT.pkl
│   └── sarimax_model_ETHUSDT.pkl
│
├── 📁 data/                      ← Data storage (created at runtime)
│   ├── processed/
│   │   ├── cleaned_crypto_data.csv
│   │   ├── scaler.pkl
│   │   └── scaler_info.pkl
│   └── predictions/
│       └── latest_predictions.csv
│
└── 📦 requirements.txt           ← Python dependencies
```

---

## Component Interaction

```
┌─────────────────────────────────────────────────────────────────┐
│                    Docker Container                             │
│                                                                 │
│  ┌────────────────────────────────────────────────────────┐   │
│  │              entrypoint.sh (NEW)                       │   │
│  │  - Waits for PostgreSQL                               │   │
│  │  - Runs 00_init_and_train.py                          │   │
│  │  - Starts uvicorn API                                 │   │
│  └────────────┬───────────────────────────────────────┬──┘   │
│               ↓                                       ↓        │
│  ┌────────────────────────┐    ┌────────────────────────────┐ │
│  │ Training Pipeline      │    │ FastAPI Application        │ │
│  │                        │    │                            │ │
│  │ 00_init_and_train.py   │    │ app/main.py                │ │
│  │ ├─ 01_data_cleaning    │    │ ├─ Load models             │ │
│  │ └─ 02_train_models     │    │ ├─ Define endpoints        │ │
│  │    ├─ RF               │    │ └─ Handle predictions      │ │
│  │    ├─ LSTM             │    │                            │ │
│  │    ├─ ARIMA            │    │ Exposed on :8000           │ │
│  │    └─ SARIMAX          │    │                            │ │
│  │                        │    │                            │ │
│  │ Saves to:             │    │ Loads from:               │
│  │ /models/              │    │ /models/                  │ │
│  │ /data/processed/      │    │ /data/processed/          │ │
│  └────────────┬───────────┘    └────────────────────────────┘ │
│               ↓                                                 │
│  ┌────────────────────────────────────────────────────────┐   │
│  │              PostgreSQL Database (External Container)  │   │
│  │  - Stores raw crypto data                             │   │
│  │  - Port: 5432                                         │   │
│  │  - User: nassim                                       │   │
│  └────────────────────────────────────────────────────────┘   │
│               ↑                                                 │
└───────────────┼─────────────────────────────────────────────────┘
                │
        ┌───────┴────────┐
        ↓                ↓
    Host System     External
    Volume Mounts   World
    - ./models/     (HTTP Port 8000)
    - ./data/       (Streamlit 8501)
    - ./scripts/
```

---

## Key Innovations

### 1. **Startup Orchestration** (entrypoint.sh)
```
Replaces:   Simple CMD that runs API immediately
With:       Orchestrated startup that trains first
Benefit:    Models always exist when API starts
```

### 2. **Training Pipeline** (00_init_and_train.py)
```
Replaces:   Manual execution of separate scripts
With:       Automatic orchestration with retries
Benefit:    Reliable, repeatable, automated setup
```

### 3. **Graceful Degradation** (main.py)
```
Replaces:   Hard crash if models missing
With:       Graceful handling with warnings
Benefit:    API stays up even during training
```

### 4. **Volume Persistence** (docker-compose.yml)
```
Replaces:   Data lost on container restart
With:       Persistent volumes for models/data
Benefit:    Models survive container lifecycle
```

---

## System Requirements

### Hardware
- CPU: 2+ cores
- RAM: 4GB minimum (8GB recommended)
- Disk: 5GB free space

### Software
- Docker: 20.10+
- Docker Compose: 1.29+
- Python: 3.12 (in container)

### Network
- Port 8000: FastAPI
- Port 5432: PostgreSQL
- Port 8501: Streamlit (optional)

---

## Performance Expectations

| Component | Startup Time | Notes |
|-----------|--------------|-------|
| PostgreSQL | 10-20s | Includes health checks |
| Data Cleaning | 30-120s | Depends on data size |
| Random Forest | 30-60s | 100 estimators |
| LSTM | 60-180s | 50 epochs, early stopping |
| ARIMA | 30-90s | Per symbol |
| SARIMAX | 60-120s | Per symbol |
| **Total** | **3-15 min** | First run varies |

---

## Security Considerations

### Current (Development)
- Database credentials in code
- No authentication on API
- No HTTPS

### For Production
- Use environment variables for credentials
- Add API authentication (OAuth2, JWT)
- Enable HTTPS/SSL
- Add rate limiting
- Add logging and monitoring
- Use secrets management (Docker secrets, K8s)

---

## Scaling Considerations

### Horizontal Scaling
- Use load balancer (nginx, HAProxy)
- Multiple API instances
- Shared PostgreSQL (RDS, managed database)
- Shared model storage (S3, NFS)

### Vertical Scaling
- Larger instances
- More CPU cores
- More RAM
- SSD storage for data

### Optimization
- Cache model predictions
- Batch predict requests
- Use GPU for LSTM
- Parallel training for different symbols
