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
    os.makedirs("data/processed", exist_ok=True)
    df.to_csv("data/processed/cleaned_crypto_data.csv", index=False)
    joblib.dump(scaler, "data/processed/scaler.pkl")
    print("Données nettoyées sauvegardées.")

if __name__ == "__main__":
    clean_data()
