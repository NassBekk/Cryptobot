import pandas as pd
import joblib
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.callbacks import EarlyStopping
from tensorflow.keras.regularizers import l2
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.statespace.sarimax import SARIMAX
from utils import normalize_features
import os
import numpy as np
from sklearn.metrics import mean_squared_error, classification_report, mean_absolute_error
from imblearn.over_sampling import SMOTE
from sklearn.utils.class_weight import compute_class_weight

def train_models():
    # Charger les données nettoyées
    df = pd.read_csv("data/processed/cleaned_crypto_data.csv")
    scaler = joblib.load("data/processed/scaler.pkl")

    # Séparation des features et de la cible
    features = df.drop(columns=['target', 'symbol', 'timestamp'])
    target = df['target']

    # Division en ensembles d'entraînement et de test
    X_train, X_test, y_train, y_test = train_test_split(features, target, test_size=0.2, random_state=42, shuffle=False)

    # Rééchantillonnage avec SMOTE
    smote = SMOTE(random_state=42)
    X_train_res, y_train_res = smote.fit_resample(X_train, y_train)

    # Calcul des poids des classes
    class_weights = compute_class_weight('balanced', classes=np.unique(y_train), y=y_train)
    class_weight_dict = {0: class_weights[0], 1: class_weights[1]}

    # Créer le dossier models s'il n'existe pas
    os.makedirs("models", exist_ok=True)

    # Entraînement du modèle Random Forest
    print("Entraînement du modèle Random Forest...")
    model_rf = RandomForestClassifier(n_estimators=100, random_state=42, class_weight='balanced')
    model_rf.fit(X_train_res, y_train_res)
    joblib.dump(model_rf, "models/random_forest_model.pkl")

    # Entraînement du modèle LSTM
    print("Entraînement du modèle LSTM...")
    X_train_lstm = X_train_res.values.reshape((X_train_res.shape[0], 1, X_train_res.shape[1]))
    X_test_lstm = X_test.values.reshape((X_test.shape[0], 1, X_test.shape[1]))

    model_lstm = Sequential([
        LSTM(64, return_sequences=True, input_shape=(1, X_train_res.shape[1]), kernel_regularizer=l2(0.01)),
        Dropout(0.3),
        LSTM(32, kernel_regularizer=l2(0.01)),
        Dropout(0.3),
        Dense(1, activation='sigmoid')
    ])
    model_lstm.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
    model_lstm.fit(X_train_lstm, y_train_res, epochs=50, batch_size=32, validation_split=0.2,
                   callbacks=[EarlyStopping(patience=5)], class_weight=class_weight_dict)
    model_lstm.save("models/lstm_model.keras")

    # Préparation des données pour ARIMA/SARIMAX (BTCUSDT)
    btc_data = df[df['symbol'] == 'BTCUSDT'][['timestamp', 'close']].copy()
    btc_data = btc_data.set_index('timestamp').asfreq('D').ffill().bfill()

    # Vérifier la taille des données
    if len(btc_data) < 100:
        print("Pas assez de données pour entraîner ARIMA/SARIMAX. Au moins 100 points sont nécessaires.")
        return

    # Vérifier les valeurs NaN dans les données
    if btc_data.isnull().values.any():
        print("Les données contiennent des valeurs NaN. Nettoyage supplémentaire nécessaire.")
        btc_data = btc_data.dropna()

    # Diviser les données en entraînement et test
    train_size = int(len(btc_data) * 0.8)
    train_ts, test_ts = btc_data.iloc[:train_size], btc_data.iloc[train_size:]

    # Entraînement du modèle ARIMA avec des paramètres simples
    print("Entraînement du modèle ARIMA...")
    try:
        model_arima = ARIMA(train_ts, order=(1, 1, 1))
        model_arima_fit = model_arima.fit()
        joblib.dump(model_arima_fit, "models/arima_model.pkl")
        print("Modèle ARIMA entraîné et sauvegardé.")
    except Exception as e:
        print(f"Erreur lors de l'entraînement d'ARIMA: {e}")

    # Entraînement du modèle SARIMAX avec des paramètres simples
    print("Entraînement du modèle SARIMAX...")
    try:
        model_sarimax = SARIMAX(train_ts, order=(1, 1, 1), seasonal_order=(1, 1, 1, 7))
        model_sarimax_fit = model_sarimax.fit(disp=False)
        joblib.dump(model_sarimax_fit, "models/sarimax_model.pkl")
        print("Modèle SARIMAX entraîné et sauvegardé.")
    except Exception as e:
        print(f"Erreur lors de l'entraînement de SARIMAX: {e}")

    print("Tous les modèles sont entraînés et sauvegardés.")

if __name__ == "__main__":
    train_models()
