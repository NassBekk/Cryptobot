import pandas as pd
from utils import load_data_from_db, prepare_features, normalize_features
import joblib
import os

def clean_data():
    # Charger les données
    df = load_data_from_db()

    # Nettoyage et préparation
    df = df.drop_duplicates(subset=['symbol', 'timestamp'], keep='last')
    df = df.dropna()
    df = prepare_features(df)

    # Normalisation
    df, scaler = normalize_features(df)

    # Définir la cible (1=hausse, 0=baisse)
    df['target'] = (df.groupby('symbol')['daily_return'].shift(-1) > 0).astype(int)
    df = df.dropna(subset=['target'])

    # Sauvegarder les données nettoyées et le scaler
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    processed_dir = os.path.join(project_root, "data", "processed")
    os.makedirs(processed_dir, exist_ok=True)
    df.to_csv(os.path.join(processed_dir, "cleaned_crypto_data.csv"), index=False)
    joblib.dump(scaler, os.path.join(processed_dir, "scaler.pkl"))
    # Sauvegarder aussi les informations du scaler pour l'inverse transform
    scaler_info = {
        'close_min': scaler.close_min,
        'close_max': scaler.close_max
    }
    joblib.dump(scaler_info, os.path.join(processed_dir, "scaler_info.pkl"))
    print("Données nettoyées sauvegardées.")

if __name__ == "__main__":
    clean_data()
