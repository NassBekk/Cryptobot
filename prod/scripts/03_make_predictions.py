import pandas as pd
import joblib
import tensorflow as tf
from sqlalchemy import create_engine
from utils import prepare_features, normalize_features
import os
import numpy as np

def make_predictions():
    # Définir les chemins
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    processed_dir = os.path.join(project_root, "data", "processed")
    predictions_dir = os.path.join(project_root, "data", "predictions")
    models_dir = os.path.join(project_root, "models")

    # Connexion à la base de données
    db_url = "postgresql://nassim:datascientest@localhost:5432/crypto"
    engine = create_engine(db_url)

    # Récupérer les dernières données
    query = """
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
        WHERE symbol IN ('BTCUSDT', 'ETHUSDT')
        ORDER BY symbol, timestamp DESC
        LIMIT 100
    """
    new_df = pd.read_sql(query, engine)

    # Préparation des données
    new_df = prepare_features(new_df)
    scaler = joblib.load(os.path.join(processed_dir, "scaler.pkl"))
    new_df, _ = normalize_features(new_df, scaler=scaler, fit=False)

    # Sélection des features
    new_features = new_df.drop(columns=['symbol', 'timestamp'])

    # Charger les modèles
    model_rf = joblib.load(os.path.join(models_dir, "random_forest_model.pkl"))
    model_lstm = tf.keras.models.load_model(os.path.join(models_dir, "lstm_model.keras"))

    # Prédictions avec Random Forest et LSTM
    new_predictions_rf = model_rf.predict(new_features)
    new_features_lstm = new_features.values.reshape((new_features.shape[0], 1, new_features.shape[1]))
    new_predictions_lstm = (model_lstm.predict(new_features_lstm) > 0.5).astype(int)

    # Préparation des données pour ARIMA/SARIMAX (BTCUSDT)
    btc_data = new_df[new_df['symbol'] == 'BTCUSDT'][['timestamp', 'close']].copy()
    btc_data = btc_data.set_index('timestamp').asfreq('D').ffill().bfill()

    # Initialiser les colonnes de prédiction
    new_df['prediction_arima'] = np.nan
    new_df['prediction_sarimax'] = np.nan

    # Prédictions avec ARIMA
    try:
        model_arima = joblib.load(os.path.join(models_dir, "arima_model.pkl"))
        arima_predictions = model_arima.forecast(steps=len(btc_data))
        arima_predictions = pd.Series(arima_predictions, index=btc_data.index)
        new_df.loc[new_df['symbol'] == 'BTCUSDT', 'prediction_arima'] = arima_predictions.values
    except Exception as e:
        print(f"Erreur lors du chargement du modèle ARIMA: {e}")

    # Prédictions avec SARIMAX
    try:
        model_sarimax = joblib.load(os.path.join(models_dir, "sarimax_model.pkl"))
        sarimax_predictions = model_sarimax.forecast(steps=len(btc_data))
        sarimax_predictions = pd.Series(sarimax_predictions, index=btc_data.index)
        new_df.loc[new_df['symbol'] == 'BTCUSDT', 'prediction_sarimax'] = sarimax_predictions.values
    except Exception as e:
        print(f"Erreur lors du chargement du modèle SARIMAX: {e}")

    # Ajouter les prédictions au DataFrame
    new_df['prediction_rf'] = new_predictions_rf
    new_df['prediction_lstm'] = new_predictions_lstm.flatten()

    # Sauvegarder les prédictions
    os.makedirs(predictions_dir, exist_ok=True)
    new_df.to_csv(os.path.join(predictions_dir, "latest_predictions.csv"), index=False)
    print("Prédictions générées et sauvegardées.")

    # Afficher les dernières prédictions
    btc_predictions = new_df[new_df['symbol'] == 'BTCUSDT']
    print("\nDernières prédictions pour BTCUSDT:")
    print(btc_predictions[['timestamp', 'close', 'prediction_rf', 'prediction_lstm']].tail(10))

    # Visualisation des prédictions
    plot_predictions(btc_predictions, predictions_dir)

def plot_predictions(btc_predictions, predictions_dir):
    import matplotlib.pyplot as plt

    plt.figure(figsize=(15, 10))

    # Tracer le prix réel
    plt.plot(btc_predictions['timestamp'], btc_predictions['close'], label='Prix Réel', color='blue', linewidth=2)

    # Tracer les prédictions des modèles de séries temporelles
    if 'prediction_arima' in btc_predictions.columns and not btc_predictions['prediction_arima'].isnull().all():
        plt.plot(btc_predictions['timestamp'], btc_predictions['prediction_arima'], label='ARIMA', color='red', linestyle='--')
    if 'prediction_sarimax' in btc_predictions.columns and not btc_predictions['prediction_sarimax'].isnull().all():
        plt.plot(btc_predictions['timestamp'], btc_predictions['prediction_sarimax'], label='SARIMAX', color='green', linestyle='--')

    # Tracer les prédictions de classification (Random Forest et LSTM)
    plt.scatter(btc_predictions['timestamp'], btc_predictions['close'] + 2000,
                c=btc_predictions['prediction_rf'], cmap='coolwarm', label='Random Forest', marker='o', s=100, edgecolors='black')
    plt.scatter(btc_predictions['timestamp'], btc_predictions['close'] + 4000,
                c=btc_predictions['prediction_lstm'], cmap='viridis', label='LSTM', marker='s', s=100, edgecolors='black')

    plt.title('Comparaison des Prédictions pour BTCUSDT')
    plt.xlabel('Date')
    plt.ylabel('Prix (USD)')
    plt.legend()
    plt.grid(True)
    plt.xticks(rotation=45)
    plt.tight_layout()
    os.makedirs(predictions_dir, exist_ok=True)
    plt.savefig(os.path.join(predictions_dir, "comparison_plot.png"))
    plt.show()

if __name__ == "__main__":
    make_predictions()
