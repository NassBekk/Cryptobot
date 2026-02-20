#V.1.0 du script, basé sur les Klines uniquement

import requests
import pandas as pd
from datetime import datetime, timedelta
import time

def get_historical_data(symbol, interval, start_str, end_str):
    base_url = "https://api.binance.com/api/v3/klines"
    all_data = []

    # Convertir les dates en timestamps (en millisecondes)
    start_time = int(datetime.strptime(start_str, "%Y-%m-%d").timestamp() * 1000)
    end_time = int(datetime.strptime(end_str, "%Y-%m-%d").timestamp() * 1000)

    print(f"Récupération des données pour {symbol} de {datetime.fromtimestamp(start_time/1000)} à {datetime.fromtimestamp(end_time/1000)}")

    while start_time < end_time:
        # Calculer la fin de la période actuelle (max 30 jours)
        current_end_time = min(start_time + 30 * 24 * 60 * 60 * 1000, end_time)

        # Construire l'URL avec les timestamps
        url = f"{base_url}?symbol={symbol}&interval={interval}&startTime={start_time}&endTime={current_end_time}&limit=1000"
        print(f"Requête : {url}")

        response = requests.get(url)

        if response.status_code != 200:
            print(f"Erreur {response.status_code} pour {symbol} : {response.text}")
            break

        data = response.json()

        if not data:
            print(f"Aucune donnée retournée pour {symbol} entre {datetime.fromtimestamp(start_time/1000)} et {datetime.fromtimestamp(current_end_time/1000)}.")
            break

        all_data.extend(data)
        print(f"Reçu {len(data)} bougies pour {symbol}.")

        # Mettre à jour start_time pour la prochaine itération
        start_time = data[-1][0] + 1  # +1 pour éviter les doublons

        if start_time >= end_time:
            print(f"Date de fin atteinte pour {symbol}.")
            break

        time.sleep(0.1)  # Respecter le rate limit de Binance

    if not all_data:
        print(f"Aucune donnée disponible pour {symbol}.")
        return pd.DataFrame()

    df = pd.DataFrame(all_data, columns=[
        'Open time', 'Open', 'High', 'Low', 'Close', 'Volume',
        'Close time', 'Quote asset volume', 'Number of trades',
        'Taker buy base', 'Taker buy quote', 'Ignore'
    ])
    df['symbol'] = symbol
    df['Open time'] = pd.to_datetime(df['Open time'], unit='ms')
    return df

# Exemple d'utilisation
symbols = ['BTCUSDT', 'ETHUSDT', 'BTCEUR', 'ETHEUR']  
interval = '1d'
start_date = '2021-01-01'
end_date = '2025-10-06'  

historical_data = pd.DataFrame()
for symbol in symbols:
    print(f"Récupération de {symbol}...")
    df = get_historical_data(symbol, interval, start_date, end_date)
    if not df.empty:
        historical_data = pd.concat([historical_data, df])

if not historical_data.empty:
    historical_data = historical_data[['symbol', 'Open time', 'Open', 'High', 'Low', 'Close', 'Volume']]
    historical_data.columns = ['symbol', 'timestamp', 'open', 'high', 'low', 'close', 'volume']
    historical_data.to_csv('binance_historical_data.csv', index=False)
    print("Données sauvegardées dans 'binance_historical_data.csv'.")
else:
    print("Aucune donnée n'a été récupérée.")
