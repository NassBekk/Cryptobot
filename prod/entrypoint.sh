#!/bin/bash
# Docker entrypoint: Initialize database and train models before starting API

set -e

echo "=================================================="
echo "🚀 CryptoBot Application Initialization"
echo "=================================================="

SCRIPTS_DIR="/app/scripts"

# Wait for PostgreSQL
echo "⏳ Waiting for PostgreSQL..."
for i in {1..30}; do
    if python3 -c "from sqlalchemy import create_engine; engine = create_engine('postgresql://nassim:datascientest@db:5432/crypto'); engine.connect()" 2>/dev/null; then
        echo "✅ PostgreSQL is ready!"
        break
    fi
    echo "   Attempt $i/30..."
    sleep 1
done

# Run initialization and training
echo ""
echo "📊 Running data pipeline..."
python3 "$SCRIPTS_DIR/00_init_and_train.py"

TRAINING_RESULT=$?
if [ $TRAINING_RESULT -ne 0 ]; then
    echo "⚠️ Training pipeline encountered issues, but continuing..."
fi

# Check if models exist
if [ -f "/app/models/random_forest_model.pkl" ] && [ -f "/app/models/lstm_model.keras" ]; then
    echo "✅ Models are ready!"
else
    echo "⚠️ Warning: Some models were not created. The API may have limited functionality."
fi

echo ""
echo "=================================================="
echo "🎯 Starting FastAPI Application"
echo "=================================================="

# Start the API server
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
