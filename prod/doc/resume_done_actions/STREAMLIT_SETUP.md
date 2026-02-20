# 🎯 Streamlit Integration Guide

## Overview

This document describes the Streamlit dashboard added to the CryptoBot project. The dashboard provides a user-friendly interface to visualize ML predictions for cryptocurrency market movements.

## 📋 What's Been Added

### 1. **Streamlit Application** (`app/streamlit_app.py`)
A comprehensive dashboard with the following features:

#### Features:
- **📊 Predictions Tab**: Get real-time predictions from all ML models
  - Random Forest classifier predictions
  - LSTM neural network predictions
  - ARIMA price predictions (BTC only)
  - SARIMAX predictions (BTC only)

- **📈 Metrics Tab**: View model performance metrics
  - Global metrics for all symbols
  - Per-symbol detailed metrics
  - Accuracy, Precision, Recall, F1 scores
  - Time series model metrics (ARIMA, SARIMAX)

- **📉 History Tab**: Compare predictions with actual values
  - Detailed prediction history
  - Accuracy rates over time
  - Export predictions to CSV

- **ℹ️ About Tab**: Information about the project
  - Model descriptions
  - Supported cryptocurrencies
  - Architecture overview

### 2. **Docker Configuration**
- **Dockerfile.streamlit**: Separate Docker image for Streamlit service
- **Updated docker-compose.yml**: Added Streamlit service with proper networking

### 3. **Dependencies**
Updated `requirements.txt` with:
- `streamlit==1.39.0` - Web framework
- `plotly==5.24.0` - Interactive visualizations
- `requests==2.31.0` - HTTP client for API calls

## 🚀 Getting Started

### Prerequisites
- Docker and Docker Compose
- Python 3.12+ (if running locally)

### Running with Docker Compose

1. **Build and start all services:**
```bash
cd cryptobot/prod
docker-compose up --build
```

2. **Access the applications:**
   - **Streamlit Dashboard**: http://localhost:8501
   - **FastAPI API**: http://localhost:8000
   - **API Docs**: http://localhost:8000/docs
   - **PostgreSQL**: localhost:5432

3. **Stop services:**
```bash
docker-compose down
```

### Running Locally (Development)

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Run the Streamlit app:**
```bash
streamlit run app/streamlit_app.py
```

By default, it will connect to `http://localhost:8000` for the API. You can change this in the sidebar.

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Docker Compose Network               │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  Streamlit   │  │   FastAPI    │  │  PostgreSQL  │  │
│  │   (Port      │  │   (Port      │  │   (Port      │  │
│  │    8501)     │  │    8000)     │  │    5432)     │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
│        │                  │                  │            │
│        └──────────────────┼──────────────────┘            │
│                 requests   │   database                    │
│                            │                              │
│                   ┌────────▼────────┐                     │
│                   │   ML Models     │                     │
│                   │ - Random Forest │                     │
│                   │ - LSTM          │                     │
│                   │ - ARIMA         │                     │
│                   │ - SARIMAX       │                     │
│                   └─────────────────┘                     │
│                                                           │
└─────────────────────────────────────────────────────────┘
```

## 📚 API Endpoints Used

The Streamlit app integrates with these FastAPI endpoints:

### Health & Info
- `GET /health` - Check API status
- `GET /symbols` - Get available symbols

### Predictions
- `POST /predict` - Get predictions for a symbol

### Metrics
- `GET /metrics` - Get global metrics
- `GET /metrics/{symbol}` - Get metrics for specific symbol

### Evaluation
- `POST /evaluate` - Compare predictions with actual values

## 🎨 UI Components

### Sidebar
- Navigation between different sections
- API URL configuration
- Symbol selection
- Refresh controls

### Main Dashboard
- **Metrics Cards**: Display key metrics and predictions
- **Charts**: Interactive visualizations using Plotly
- **Tables**: Detailed data views with export options
- **Status Indicators**: Real-time health checks

## 🔧 Configuration

### API URL
The default API URL is set to `http://app:8000` (Docker internal network).
For local development, change it to `http://localhost:8000` via the sidebar.

### Streamlit Config
The Streamlit configuration is set in `Dockerfile.streamlit` and includes:
- Headless mode (no browser auto-launch)
- Port: 8501
- XSRF protection disabled (for local requests)

## 📊 Example Usage

1. **Get a Prediction:**
   - Navigate to "Predictions" tab
   - Select a cryptocurrency (BTCUSDT or ETHUSDT)
   - Click "Get Prediction"
   - View results from all 4 models

2. **Check Model Metrics:**
   - Navigate to "Metrics" tab
   - View global performance or select specific symbol
   - Compare different models' accuracy

3. **Export Prediction History:**
   - Navigate to "History" tab
   - Select symbol and number of samples
   - Click "Load History"
   - Download CSV file

## 🐛 Troubleshooting

### Streamlit not connecting to API
- Check if FastAPI service is running: `docker logs cryptobot_prod_app_1`
- Verify API health at http://localhost:8000/health
- Check network configuration in docker-compose.yml

### Models not loading
- Ensure ML models are in `app/models/` directory
- Check logs: `docker logs cryptobot_prod_app_1`
- Verify database connection

### Port conflicts
- Streamlit: 8501
- FastAPI: 8000
- PostgreSQL: 5432

Modify in `docker-compose.yml` if needed.

## 📈 Extending the Dashboard

### Adding New Charts
Streamlit examples:
```python
import plotly.express as px

# Create a chart
fig = px.line(data, x='timestamp', y='close')
st.plotly_chart(fig, use_container_width=True)
```

### Adding New Tabs
```python
tab1, tab2, tab3 = st.tabs(["Tab 1", "Tab 2", "Tab 3"])

with tab1:
    st.write("Content for tab 1")

with tab2:
    st.write("Content for tab 2")
```

### Caching API Calls
```python
@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_data():
    return requests.get(...).json()
```

## 📝 File Structure

```
cryptobot/prod/
├── Dockerfile                  # FastAPI container
├── Dockerfile.streamlit       # Streamlit container (NEW)
├── docker-compose.yml         # Docker Compose config (UPDATED)
├── requirements.txt           # Python dependencies (UPDATED)
├── app/
│   ├── streamlit_app.py      # Main Streamlit app (NEW)
│   ├── main.py               # FastAPI application
│   ├── evaluation.py         # Model evaluation
│   ├── models/               # ML models
│   └── data/                 # Data files
├── database/
│   └── init/                 # Database initialization
└── scripts/                  # Training scripts
```

## 🚦 Next Steps

1. **Test the dashboard**: Access http://localhost:8501 after starting services
2. **Monitor logs**: Use `docker-compose logs -f streamlit` to debug
3. **Customize**: Modify `streamlit_app.py` to add more features
4. **Deploy**: Configure for production deployment

## 📞 Support

For issues or questions:
- Check Streamlit documentation: https://docs.streamlit.io
- Check FastAPI documentation: https://fastapi.tiangolo.com
- Review error logs in Docker container logs

---

**Last Updated**: 2026-01-18
