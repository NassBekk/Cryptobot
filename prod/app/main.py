from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
import joblib
import tensorflow as tf
from sqlalchemy import create_engine, text
import os
from datetime import datetime
from typing import Optional, List
import numpy as np
import sys

# Ajouter le répertoire parent au path pour les imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Import du module evaluation
from app.evaluation import (
    load_test_data,
    prepare_features_for_evaluation,
    evaluate_classification_models,
    evaluate_time_series_models,
    get_predictions_comparison
)

app = FastAPI(
    title ="CryptoBot Prediction API",
    description="API pour prédire les mouvements des prix des cryptomonnaies en utilisant plusieurs modèles de machine learning et de séries temporelles.",
    version="1.0.0",
    openapi_tags=[
        {"name": "Prediction", "description": "Endpoints pour les prédictions de prix"},
        {"name": "Metrics", "description": "Endpoints pour les métriques de performance des modèles"},
        {"name": "Checks", "description": "Verification de l'état de santé de l'API"}
    ]
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Symboles autorisés
ALLOWED_SYMBOLS = ["BTCUSDT", "ETHUSDT"]

# Modèle pour les requêtes de prédiction
class PredictionRequest(BaseModel):
    symbol: str
    timestamp: Optional[str] = None

# Endpoint pour lister les symboles supportés
@app.get("/symbols", tags=["Checks"])
async def get_symbols():
    """Retourne la liste des symboles supportés par l'API."""
    return {
        "symbols": ALLOWED_SYMBOLS,
        "description": "Symboles de cryptomonnaies supportés pour les prédictions"
    }

# Endpoint de santé
@app.get("/health", tags=["Checks"])
async def health_check():
    """Endpoint de vérification de santé de l'API."""
    return {"status": "healthy", "service": "cryptobot-api"}

# Initialize global variables
model_rf = None
model_lstm = None
model_arima_dict = {}
model_sarimax_dict = {}
scaler = None

# Charger les modèles au démarrage
@app.on_event("startup")
async def load_models():
    global model_rf, model_lstm, model_arima_dict, model_sarimax_dict, scaler
    
    print("\n" + "="*60)
    print("📊 Loading Models at Startup")
    print("="*60)
    
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    models_dir = os.path.join(base_dir, "models")
    app_models_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models")
    app_data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "processed")
    
    # Créer les répertoires s'ils n'existent pas
    os.makedirs(models_dir, exist_ok=True)
    os.makedirs(app_models_dir, exist_ok=True)
    os.makedirs(app_data_dir, exist_ok=True)
    
    # Try to load Random Forest model
    rf_path = os.path.join(app_models_dir, "random_forest_model.pkl")
    if not os.path.exists(rf_path):
        rf_path = os.path.join(models_dir, "random_forest_model.pkl")
    
    if os.path.exists(rf_path):
        try:
            model_rf = joblib.load(rf_path)
            print(f"✅ Random Forest model loaded from {rf_path}")
        except Exception as e:
            print(f"❌ Failed to load Random Forest model: {e}")
            model_rf = None
    else:
        print(f"⚠️ Random Forest model not found at {rf_path}")
        model_rf = None
    
    # Try to load LSTM model
    lstm_path = os.path.join(app_models_dir, "lstm_model.keras")
    if not os.path.exists(lstm_path):
        lstm_path = os.path.join(models_dir, "lstm_model.keras")
    
    if os.path.exists(lstm_path):
        try:
            model_lstm = tf.keras.models.load_model(lstm_path)
            print(f"✅ LSTM model loaded from {lstm_path}")
        except Exception as e:
            print(f"❌ Failed to load LSTM model: {e}")
            model_lstm = None
    else:
        print(f"⚠️ LSTM model not found at {lstm_path}")
        model_lstm = None
    
    # Try to load Scaler
    scaler_path = os.path.join(app_data_dir, "scaler.pkl")
    if not os.path.exists(scaler_path):
        scaler_path = os.path.join(base_dir, "data", "processed", "scaler.pkl")
    
    if os.path.exists(scaler_path):
        try:
            scaler = joblib.load(scaler_path)
            print(f"✅ Scaler loaded from {scaler_path}")
            
            scaler_info_path = os.path.join(app_data_dir, "scaler_info.pkl")
            if not os.path.exists(scaler_info_path):
                scaler_info_path = os.path.join(base_dir, "data", "processed", "scaler_info.pkl")
            
            if os.path.exists(scaler_info_path):
                scaler_info = joblib.load(scaler_info_path)
                scaler.close_min = scaler_info['close_min']
                scaler.close_max = scaler_info['close_max']
            else:
                close_index = 3
                scaler.close_min = scaler.data_min_[close_index]
                scaler.close_max = scaler.data_max_[close_index]
        except Exception as e:
            print(f"❌ Failed to load Scaler: {e}")
            scaler = None
    else:
        print(f"⚠️ Scaler not found at {scaler_path}")
        scaler = None
    
    # Load symbol-specific models
    model_arima_dict = {}
    model_sarimax_dict = {}
    
    for symbol in ALLOWED_SYMBOLS:
        # Try ARIMA
        arima_path = os.path.join(app_models_dir, f"arima_model_{symbol}.pkl")
        if not os.path.exists(arima_path):
            arima_path = os.path.join(models_dir, f"arima_model_{symbol}.pkl")
        
        if os.path.exists(arima_path):
            try:
                model_arima_dict[symbol] = joblib.load(arima_path)
                print(f"✅ ARIMA model for {symbol} loaded")
            except Exception as e:
                print(f"❌ Failed to load ARIMA model for {symbol}: {e}")
                model_arima_dict[symbol] = None
        else:
            print(f"⚠️ ARIMA model not found for {symbol}")
            model_arima_dict[symbol] = None
        
        # Try SARIMAX
        sarimax_path = os.path.join(app_models_dir, f"sarimax_model_{symbol}.pkl")
        if not os.path.exists(sarimax_path):
            sarimax_path = os.path.join(models_dir, f"sarimax_model_{symbol}.pkl")
        
        if os.path.exists(sarimax_path):
            try:
                model_sarimax_dict[symbol] = joblib.load(sarimax_path)
                print(f"✅ SARIMAX model for {symbol} loaded")
            except Exception as e:
                print(f"❌ Failed to load SARIMAX model for {symbol}: {e}")
                model_sarimax_dict[symbol] = None
        else:
            print(f"⚠️ SARIMAX model not found for {symbol}")
            model_sarimax_dict[symbol] = None
    
    print("="*60 + "\n")

# Endpoint pour obtenir les prédictions
@app.post("/predict", tags=["Prediction"])
async def predict(request: PredictionRequest):
    """Fait une prédiction sur l'une des pairs autorisées (BTCUSDT, ETHUSDT)"""
    # Valider le symbole
    if request.symbol.upper() not in ALLOWED_SYMBOLS:
        raise HTTPException(
            status_code=400, 
            detail=f"Symbole '{request.symbol}' non supporté. Symboles autorisés: {', '.join(ALLOWED_SYMBOLS)}"
        )
    
    # Check if models are loaded
    if model_rf is None or model_lstm is None or scaler is None:
        raise HTTPException(
            status_code=503,
            detail="⚠️ Models are still loading or training. Please wait a moment and try again. Check /health endpoint for status."
        )
    
    # Normaliser le symbole (majuscules)
    symbol = request.symbol.upper()
    
    try:
        # Connexion à la base de données
        db_url = os.getenv("DATABASE_URL", "postgresql://nassim:datascientest@db:5432/crypto")
        engine = create_engine(db_url)

        # Récupérer les dernières données (utilisation de paramètres pour éviter SQL injection)
        query = """
            SELECT * FROM (
                SELECT
                    symbol,
                    timestamp,
                    open,
                    high,
                    low,
                    close,
                    volume,
                    "Quote asset volume",
                    "Number of trades",
                    bid_ask_spread,
                    volume_24h,
                    num_trades_24h
                FROM binance_historical_data_with_metrics
                WHERE symbol = :symbol
                ORDER BY timestamp DESC
                LIMIT 100
            ) AS recent_data
            ORDER BY timestamp ASC  -- Re-order chronologically for feature calculation
            """
        new_df = pd.read_sql(text(query), engine, params={"symbol": symbol})
        
        # Vérifier que des données ont été trouvées
        if new_df.empty:
            raise HTTPException(
                status_code=404,
                detail=f"Aucune donnée trouvée pour le symbole '{symbol}' dans la base de données"
            )

        # Préparation des données
        new_df['daily_return'] = new_df['close'].pct_change()
        new_df['ma_7'] = new_df['close'].rolling(window=7).mean()
        new_df['ma_30'] = new_df['close'].rolling(window=30).mean()
        new_df['volatility'] = new_df['daily_return'].rolling(window=7).std()
        new_df['rsi'] = calculate_rsi(new_df['close'])
        new_df['volume_to_price_ratio'] = new_df['volume'] / new_df['close']

        # Normalisation
        cols_to_normalize = ['open', 'high', 'low', 'close', 'volume', 'Quote asset volume', 'Number of trades',
                            'bid_ask_spread', 'volume_24h', 'num_trades_24h', 'ma_7', 'ma_30', 'volatility', 'rsi', 'volume_to_price_ratio']
        new_df[cols_to_normalize] = scaler.transform(new_df[cols_to_normalize])

        # Sélection des features
        new_features = new_df.drop(columns=['symbol', 'timestamp'])

        # Prédictions avec Random Forest et LSTM
        rf_prediction = model_rf.predict(new_features.iloc[[-1]])
        lstm_features = new_features.iloc[[-1]].values.reshape((1, 1, new_features.shape[1]))
        lstm_prediction = (model_lstm.predict(lstm_features) > 0.5).astype(int)

        # Préparation des données pour ARIMA/SARIMAX
        arima_prediction = None
        sarimax_prediction = None
        arima_error = None
        sarimax_error = None
        
        try:
            # Obtenir les dernières données de série temporelle pour la prédiction
            ts_query = """
                SELECT timestamp, close
                FROM binance_historical_data_with_metrics
                WHERE symbol = :symbol
                ORDER BY timestamp DESC
                LIMIT 100
            """
            ts_df = pd.read_sql(text(ts_query), engine, params={"symbol": symbol})
                
            if len(ts_df) > 0:
                # Préparer la série temporelle
                ts_df['timestamp'] = pd.to_datetime(ts_df['timestamp'])
                ts_df = ts_df.sort_values('timestamp')
                ts_series = ts_df.set_index('timestamp')['close']
                    
                # Prédiction ARIMA
                model_arima = model_arima_dict.get(symbol)
                if model_arima is not None:
                    try:
                        arima_forecast = model_arima.get_forecast(steps=1)
                        arima_prediction = arima_forecast.predicted_mean.values[0]

                        # Inverse transform ARIMA prediction
                        if arima_prediction is not None:
                            close_range = scaler.close_max - scaler.close_min
                            arima_prediction = arima_prediction * close_range + scaler.close_min

                        print(f"✓ Prédiction ARIMA {symbol}: {arima_prediction:.2f}")
                    except Exception as e:
                        arima_error = f"Erreur prédiction ARIMA: {str(e)}"
                        print(f"❌ {arima_error}")
                else:
                    arima_error = f"Modèle ARIMA pour {symbol} non chargé"
                    print(f"⚠️ {arima_error}")

                # Prédiction SARIMAX
                model_sarimax = model_sarimax_dict.get(symbol)
                if model_sarimax is not None:
                    try:
                        sarimax_forecast = model_sarimax.get_forecast(steps=1)
                        sarimax_prediction = sarimax_forecast.predicted_mean.values[0]
                            
                        # Inverse transform SARIMAX prediction
                        if sarimax_prediction is not None:
                            close_range = scaler.close_max - scaler.close_min
                            sarimax_prediction = sarimax_prediction * close_range + scaler.close_min
                        print(f"✓ Prédiction SARIMAX {symbol}: {sarimax_prediction:.2f}")
                    except Exception as e:
                        sarimax_error = f"Erreur prédiction SARIMAX: {str(e)}"
                        print(f"❌ {sarimax_error}")
                else:
                    sarimax_error = f"Modèle SARIMAX pour {symbol} non chargé"
                    print(f"⚠️ {sarimax_error}")
                        
        except Exception as e:
            print(f"❌ Erreur lors de la préparation des données pour ARIMA/SARIMAX: {e}")
            arima_error = str(e)
            sarimax_error = str(e)


        # Retourner les prédictions
        return {
            "symbol": symbol,
            "timestamp": str(datetime.now()),
            "predictions": {
                "random_forest": int(rf_prediction[0]),
                "lstm": int(lstm_prediction[0][0]),
                "arima": float(arima_prediction) if arima_prediction is not None else None,
                "sarimax": float(sarimax_prediction) if sarimax_prediction is not None else None
            },
            "notes": {
                "arima_note": arima_error,
                "sarimax_note": sarimax_error
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la prédiction: {e}")

def calculate_rsi(series, window=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))


# Endpoint pour obtenir les métriques de performance globales
@app.get("/metrics", tags=["Metrics"])
async def get_metrics(limit: int = 1000):
    """
    Retourne les métriques de performance de tous les modèles sur les données de test.
    
    Args:
        limit: Nombre maximum d'échantillons à utiliser pour l'évaluation
    """
    try:
        db_url = os.getenv("DATABASE_URL", "postgresql://nassim:datascientest@db:5432/crypto")
        engine = create_engine(db_url)
        
        results = {}
        
        # Évaluer pour chaque symbole
        for symbol in ALLOWED_SYMBOLS:
            # Charger les données de test
            test_df = load_test_data(db_url, symbol=symbol, limit=limit)
            
            if test_df.empty:
                results[symbol] = {"error": "Aucune donnée disponible"}
                continue
            
            # Préparer les features
            try:
                X_test, y_test, df_features = prepare_features_for_evaluation(test_df, scaler)
                
                if len(X_test) == 0:
                    results[symbol] = {"error": "Pas assez de données après préparation"}
                    continue
                
                # Évaluer les modèles de classification
                classification_metrics = evaluate_classification_models(
                    model_rf, model_lstm, X_test, y_test
                )
                
                results[symbol] = {
                    "classification": classification_metrics,
                    "test_samples": len(X_test)
                }
                
                # Pour BTCUSDT, évaluer aussi les modèles de séries temporelles
                if symbol == "BTCUSDT":
                    try:
                        btc_data = df_features[df_features['symbol'] == 'BTCUSDT'][['timestamp', 'close']].copy()
                        btc_data = btc_data.set_index('timestamp').sort_index()
                        if len(btc_data) > 10:
                            # Utiliser les 20% derniers comme test
                            test_size = int(len(btc_data) * 0.2)
                            test_ts = btc_data.iloc[-test_size:]['close']
                            
                            ts_metrics = evaluate_time_series_models(model_arima, model_sarimax, test_ts)
                            results[symbol]["time_series"] = ts_metrics
                    except Exception as e:
                        results[symbol]["time_series"] = {"error": str(e)}
                        
            except Exception as e:
                results[symbol] = {"error": str(e)}
        
        return {
            "overall_metrics": results,
            "models_evaluated": ["random_forest", "lstm", "arima", "sarimax"],
            "test_limit": limit
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors du calcul des métriques: {e}")


# Endpoint pour obtenir les métriques pour un symbole spécifique
@app.get("/metrics/{symbol}", tags=["Metrics"])
async def get_metrics_by_symbol(symbol: str, limit: int = 1000):
    """
    Retourne les métriques de performance pour un symbole spécifique.
    
    Args:
        symbol: Symbole à évaluer (BTCUSDT ou ETHUSDT)
        limit: Nombre maximum d'échantillons à utiliser
    """
    symbol = symbol.upper()
    
    if symbol not in ALLOWED_SYMBOLS:
        raise HTTPException(
            status_code=400,
            detail=f"Symbole '{symbol}' non supporté. Symboles autorisés: {', '.join(ALLOWED_SYMBOLS)}"
        )
    
    try:
        db_url = os.getenv("DATABASE_URL", "postgresql://nassim:datascientest@db:5432/crypto")
        engine = create_engine(db_url)
        
        # Charger les données de test
        test_df = load_test_data(db_url, symbol=symbol, limit=limit)
        
        if test_df.empty:
            raise HTTPException(
                status_code=404,
                detail=f"Aucune donnée disponible pour le symbole '{symbol}'"
            )
        
        # Préparer les features
        X_test, y_test, df_features = prepare_features_for_evaluation(test_df, scaler)
        
        if len(X_test) == 0:
            raise HTTPException(
                status_code=400,
                detail="Pas assez de données après préparation des features"
            )
        
        # Évaluer les modèles de classification
        classification_metrics = evaluate_classification_models(
            model_rf, model_lstm, X_test, y_test
        )
        
        result = {
            "symbol": symbol,
            "classification": classification_metrics,
            "test_samples": len(X_test)
        }
        
        # Pour BTCUSDT, évaluer aussi les modèles de séries temporelles
        if symbol == "BTCUSDT":
            try:
                btc_data = df_features[df_features['symbol'] == 'BTCUSDT'][['timestamp', 'close']].copy()
                btc_data = btc_data.set_index('timestamp').sort_index()
                if len(btc_data) > 10:
                    test_size = int(len(btc_data) * 0.2)
                    test_ts = btc_data.iloc[-test_size:]['close']
                    ts_metrics = evaluate_time_series_models(model_arima, model_sarimax, test_ts)
                    result["time_series"] = ts_metrics
            except Exception as e:
                result["time_series"] = {"error": str(e)}
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors du calcul des métriques: {e}")


# Modèle pour les requêtes d'évaluation
class EvaluateRequest(BaseModel):
    symbol: str
    limit: Optional[int] = 500


# Endpoint pour comparer les prédictions aux valeurs réelles
# Dans l'endpoint /evaluate de votre main.py
@app.post("/evaluate", tags=["Metrics"])
async def evaluate_predictions(request: EvaluateRequest):
    """
    Compare les prédictions des modèles aux valeurs réelles sur un jeu de test.
    """
    symbol = request.symbol.upper()
    # ✅ AJOUT: Garantir un minimum de données pour les rolling windows
    limit = max(request.limit, 150)  # Minimum 150 pour avoir assez après dropna
    
    if symbol not in ALLOWED_SYMBOLS:
        raise HTTPException(
            status_code=400,
            detail=f"Symbole '{symbol}' non supporté. Symboles autorisés: {', '.join(ALLOWED_SYMBOLS)}"
        )
    
    try:
        db_url = os.getenv("DATABASE_URL", "postgresql://nassim:datascientest@db:5432/crypto")
        engine = create_engine(db_url)
        
        # Charger les données de test
        test_df = load_test_data(db_url, symbol=symbol, limit=request.limit)
        
        if test_df.empty:
            raise HTTPException(
                status_code=404,
                detail=f"Aucune donnée disponible pour le symbole '{symbol}'"
            )
        
        # ✅ CORRECTION: Sauvegarder les VRAIS prix AVANT toute normalisation
        original_close_prices = test_df['close'].copy()
        original_timestamps = test_df['timestamp'].copy()
        
        # Préparer les features (cette étape normalise les données)
        X_test, y_test, df_features = prepare_features_for_evaluation(test_df, scaler)
        
        if len(X_test) == 0:
            raise HTTPException(
                status_code=400,
                detail="Pas assez de données après préparation des features"
            )
        
        # Obtenir les timestamps et symboles
        timestamps = df_features['timestamp'].values if 'timestamp' in df_features.columns else None
        symbols = df_features['symbol'].values if 'symbol' in df_features.columns else None
        
        # ✅ CORRECTION: Aligner les prix originaux avec les données après dropna
        # df_features a moins de lignes que test_df à cause du dropna
        # On doit retrouver les indices correspondants
        if 'timestamp' in df_features.columns:
            # Utiliser les timestamps pour aligner
            aligned_prices = []
            for ts in df_features['timestamp']:
                idx = original_timestamps[original_timestamps == ts].index
                if len(idx) > 0:
                    aligned_prices.append(original_close_prices.iloc[idx[0]])
                else:
                    aligned_prices.append(np.nan)
            actual_prices = np.array(aligned_prices)
        else:
            # Fallback: prendre les dernières valeurs
            actual_prices = original_close_prices.iloc[-len(df_features):].values
        # ✅ AJOUT: Logs de débogage
        print(f"\n🔍 DEBUG /evaluate endpoint:")
        print(f"   original_close_prices shape: {original_close_prices.shape}")
        print(f"   original_close_prices min/max: {original_close_prices.min():.2f} / {original_close_prices.max():.2f}")
        print(f"   df_features shape: {df_features.shape}")
        print(f"   actual_prices shape: {actual_prices.shape}")
        print(f"   actual_prices min/max: {np.nanmin(actual_prices):.2f} / {np.nanmax(actual_prices):.2f}")
        print(f"   Premiers prix: {actual_prices[:5]}")


        # Générer les comparaisons avec les VRAIS prix
        comparison_df = get_predictions_comparison(
            model_rf, model_lstm, X_test, y_test, timestamps, symbols, actual_prices
        )

        # ✅ VÉRIFIER que actual_price contient bien les vrais prix
        if 'actual_price' in comparison_df.columns:
            print(f"✓ Prix réels dans comparison_df: min={comparison_df['actual_price'].min():.2f}, max={comparison_df['actual_price'].max():.2f}")
        
        # Convertir en format JSON
        comparison_dict = comparison_df.to_dict(orient='records')
        
        # Calculer des statistiques résumées
        accuracy_rf = (comparison_df['correct_rf'].sum() / len(comparison_df))
        accuracy_lstm = (comparison_df['correct_lstm'].sum() / len(comparison_df))
        
        return {
            "symbol": symbol,
            "total_samples": len(comparison_df),
            "summary": {
                "random_forest_accuracy": float(accuracy_rf),
                "lstm_accuracy": float(accuracy_lstm)
            },
            "comparisons": comparison_dict[:100]  # Limiter à 100 pour la réponse
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'évaluation: {e}")