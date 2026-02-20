from fastapi.testclient import TestClient
from app.main import app
import pytest

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "service": "cryptobot-api"}

def test_get_symbols():
    response = client.get("/symbols")
    assert response.status_code == 200
    data = response.json()
    assert "symbols" in data
    assert "BTCUSDT" in data["symbols"]
    assert "ETHUSDT" in data["symbols"]

def test_predict_invalid_symbol():
    payload = {
        "symbol": "INVALID",
        "timestamp": None
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 400
    assert "non supporté" in response.json()["detail"]
