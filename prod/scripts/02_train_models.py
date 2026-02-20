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
    # Définir les chemins
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    processed_dir = os.path.join(project_root, "data", "processed")
    models_dir = os.path.join(project_root, "models")
    
    # Charger les données nettoyées
    df = pd.read_csv(os.path.join(processed_dir, "cleaned_crypto_data.csv"))
    scaler = joblib.load(os.path.join(processed_dir, "scaler.pkl"))

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
    os.makedirs(models_dir, exist_ok=True)

    # Entraînement du modèle Random Forest
    print("Entraînement du modèle Random Forest...")
    model_rf = RandomForestClassifier(n_estimators=100, random_state=42, class_weight='balanced')
    model_rf.fit(X_train_res, y_train_res)
    joblib.dump(model_rf, os.path.join(models_dir, "random_forest_model.pkl"))

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
    model_lstm.save(os.path.join(models_dir, "lstm_model.keras"))

    # Préparation des données pour ARIMA/SARIMAX pour chaque symbole
    print("\n=== Entraînement des modèles de séries temporelles ===")

    symbols_to_train = ['BTCUSDT', 'ETHUSDT']

    for symbol in symbols_to_train:
        print(f"\n--- Traitement de {symbol} ---")
        symbol_data = df[df['symbol'] == symbol][['timestamp', 'close']].copy()
        symbol_data['timestamp'] = pd.to_datetime(symbol_data['timestamp'])
        symbol_data = symbol_data.sort_values('timestamp')
        symbol_data = symbol_data.set_index('timestamp')
        
        # Extraire la série (pandas Series)
        ts_data = symbol_data['close']

        # Vérifier la taille des données
        print(f"Nombre de points de données {symbol}: {len(ts_data)}")
        if len(ts_data) < 50:
            print(f"⚠️ Pas assez de données pour {symbol}. Au moins 50 points sont nécessaires.")
            continue

        # Vérifier les valeurs NaN dans les données
        initial_nans = ts_data.isnull().sum()
        if initial_nans > 0:
            print(f"⚠️ {initial_nans} valeurs NaN détectées. Interpolation...")
            ts_data = ts_data.interpolate(method='linear')

        print(f"✓ Données {symbol}: min={ts_data.min():.2f}, max={ts_data.max():.2f}, moyenne={ts_data.mean():.2f}")

        # Diviser les données en entraînement et test
        train_size = int(len(ts_data) * 0.8)
        train_ts = ts_data.iloc[:train_size]
        test_ts = ts_data.iloc[train_size:]
        
        print(f"✓ Taille training: {len(train_ts)}, Taille test: {len(test_ts)}")

        # Entraînement du modèle ARIMA
        print(f"\n📊 Entraînement du modèle ARIMA(1,1,2) pour {symbol}...")
        try:
            model_arima = ARIMA(train_ts, order=(1, 1, 2))
            model_arima_fit = model_arima.fit()
            
            # Faire une prédiction de test
            forecast_arima = model_arima_fit.forecast(steps=len(test_ts))
            mae_arima = mean_absolute_error(test_ts, forecast_arima[:len(test_ts)])
            
            # Sauvegarder le modèle avec le symbole dans le nom
            arima_filename = f"arima_model_{symbol}.pkl"
            joblib.dump(model_arima_fit, os.path.join(models_dir, arima_filename))
            print(f"✓ Modèle ARIMA(1,1,2) pour {symbol} entraîné et sauvegardé.")
            print(f"  MAE sur test set: {mae_arima:.4f}")
            
        except Exception as e:
            print(f"❌ Erreur lors de l'entraînement d'ARIMA pour {symbol}: {e}")
            import traceback
            traceback.print_exc()

        # Entraînement du modèle SARIMAX
        print(f"\n📈 Entraînement du modèle SARIMAX(1,1,1)x(1,1,1,7) pour {symbol}...")
        try:
            model_sarimax = SARIMAX(
                train_ts, 
                order=(1, 1, 1),
                seasonal_order=(1, 1, 1, 7)
            )
            model_sarimax_fit = model_sarimax.fit(disp=False, maxiter=200)
            
            # Faire une prédiction de test
            forecast_sarimax = model_sarimax_fit.forecast(steps=len(test_ts))
            mae_sarimax = mean_absolute_error(test_ts, forecast_sarimax[:len(test_ts)])
            
            # Sauvegarder le modèle avec le symbole dans le nom
            sarimax_filename = f"sarimax_model_{symbol}.pkl"
            joblib.dump(model_sarimax_fit, os.path.join(models_dir, sarimax_filename))
            print(f"✓ Modèle SARIMAX(1,1,1)x(1,1,1,7) pour {symbol} entraîné et sauvegardé.")
            print(f"  MAE sur test set: {mae_sarimax:.4f}")
            
        except Exception as e:
            print(f"❌ Erreur lors de l'entraînement de SARIMAX pour {symbol}: {e}")
            import traceback
            traceback.print_exc()

    print("\nTous les modèles sont entraînés et sauvegardés.")

if __name__ == "__main__":
    train_models()