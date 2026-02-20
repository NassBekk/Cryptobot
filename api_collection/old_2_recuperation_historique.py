#V.2.0 du script, nous ajoutons, en plsu des données des klines, Volume de quote et  nombre de trades
# afin d'avoir plus de variables explicatives, sur lesquels voir l'influence possible sur le ML

import requests
import pandas as pd
from datetime import datetime, timedelta
import time

def get_historical_data_with_metrics(symbol, interval, start_str, end_str=None):
    """Récupère les données historiques + métriques supplémentaires depuis Binance."""
    base_url = "https://api.binance.com/api/v3/klines"
    all_data = []
    start_time = int(datetime.strptime(start_str, "%Y-%m-%d").timestamp() * 1000)
    end_time = int(datetime.strptime(end_str, "%Y-%m-%d").timestamp() * 1000) if end_str else int(datetime.now().timestamp() * 1000)

    print(f"Récupération des données pour {symbol} de {datetime.fromtimestamp(start_time/1000)} à {datetime.fromtimestamp(end_time/1000)}")

    while start_time < end_time:
        current_end_time = min(start_time + 30 * 24 * 60 * 60 * 1000, end_time)
        url = f"{base_url}?symbol={symbol}&interval={interval}&startTime={start_time}&endTime={current_end_time}&limit=1000"
        response = requests.get(url)

        if response.status_code != 200:
            print(f"Erreur {response.status_code} pour {symbol}: {response.text}")
            break

        data = response.json()
        if not data:
            print(f"Aucune donnée pour {symbol} entre {datetime.fromtimestamp(start_time/1000)} et {datetime.fromtimestamp(current_end_time/1000)}.")
            break

        for candle in data:
            candle_time = datetime.fromtimestamp(candle[0]/1000).strftime('%Y-%m-%d')
            # Récupérer les métriques supplémentaires pour ce timestamp
            metrics = get_metrics_for_timestamp(symbol, candle_time)
            candle.extend([metrics['bid_ask_spread'], metrics['volume_24h'], metrics['num_trades_24h']])

        all_data.extend(data)
        print(f"Reçu {len(data)} bougies pour {symbol}.")
        start_time = data[-1][0] + 1
        time.sleep(0.1)  # Respecter le rate limit

    if not all_data:
        return pd.DataFrame()

    df = pd.DataFrame(all_data, columns=[
        'timestamp', 'open', 'high', 'low', 'close', 'volume',
        'Close time', 'Quote asset volume', 'Number of trades',
        'Taker buy base', 'Taker buy quote', 'Ignore',
        'bid_ask_spread', 'volume_24h', 'num_trades_24h'
    ])
    df['symbol'] = symbol
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms').dt.date
    return df

def get_metrics_for_timestamp(symbol, date_str):
    """Récupère les métriques supplémentaires pour un timestamp donné."""
    # Statistiques 24h
    stats_url = f"https://api.binance.com/api/v3/ticker/24hr?symbol={symbol}"
    stats = requests.get(stats_url).json()
    volume_24h = float(stats['volume'])
    num_trades_24h = int(stats['count'])

    # Order Book (spread bid-ask)
    order_book_url = f"https://api.binance.com/api/v3/depth?symbol={symbol}&limit=5"
    order_book = requests.get(order_book_url).json()
    best_bid = float(order_book['bids'][0][0])
    best_ask = float(order_book['asks'][0][0])
    bid_ask_spread = best_ask - best_bid

    return {
        'bid_ask_spread': bid_ask_spread,
        'volume_24h': volume_24h,
        'num_trades_24h': num_trades_24h
    }

#Recuperation de nos donnees
symbols = ['BTCUSDT', 'ETHUSDT', 'BTCEUR', 'ETHEUR']  
interval = '1d'
start_date = '2016-01-01'
end_date = '2025-10-06'  

historical_data = pd.DataFrame()
for symbol in symbols:
    print(f"Récupération des données pour {symbol}...")
    df = get_historical_data_with_metrics(symbol, interval, start_date, end_date)
    if not df.empty:
        historical_data = pd.concat([historical_data, df])

if not historical_data.empty:
    historical_data.to_csv('binance_historical_data_with_metrics.csv', index=False)
    print("Données sauvegardées dans 'binance_historical_data_with_metrics.csv'.")
else:
    print("Aucune donnée n'a été récupérée.")
