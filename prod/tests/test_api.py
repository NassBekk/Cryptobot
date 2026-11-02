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


class _EmptyFrame:
    empty = True


def _block_database(monkeypatch):
    """Replace engine creation and queries so tests never open PostgreSQL."""
    monkeypatch.setattr("app.main.create_engine", lambda url: object())


def _require_models(monkeypatch):
    monkeypatch.setattr("app.main.model_rf", object())
    monkeypatch.setattr("app.main.model_lstm", object())
    monkeypatch.setattr("app.main.scaler", object())


def test_predict_missing_model_returns_503(monkeypatch):
    monkeypatch.setattr("app.main.model_rf", None)

    def fail_if_called(*args, **kwargs):
        raise AssertionError("database should not be queried when models are unavailable")

    _block_database(monkeypatch)
    monkeypatch.setattr("app.main.pd.read_sql", fail_if_called)

    response = client.post("/predict", json={"symbol": "BTCUSDT"})
    assert response.status_code == 503


def test_predict_empty_data_returns_404(monkeypatch):
    _require_models(monkeypatch)
    _block_database(monkeypatch)
    monkeypatch.setattr("app.main.pd.read_sql", lambda *args, **kwargs: _EmptyFrame())

    response = client.post("/predict", json={"symbol": "BTCUSDT"})
    detail = response.json()["detail"]
    assert response.status_code == 404
    assert "Aucune donnée" in detail
    assert "BTCUSDT" in detail
    assert "Erreur lors de la prédiction" not in detail


def test_predict_internal_error_hides_details(monkeypatch):
    _require_models(monkeypatch)
    _block_database(monkeypatch)

    def fail_query(*args, **kwargs):
        raise RuntimeError("postgresql://user:secret-password@db/crypto")

    monkeypatch.setattr("app.main.pd.read_sql", fail_query)

    response = client.post("/predict", json={"symbol": "ETHUSDT"})
    assert response.status_code == 500
    assert response.json()["detail"] == "Erreur lors de la prédiction"
    assert "secret-password" not in response.text
