#V.3.0 pour etre adapter a la version asynchrone du script historique où nosu avons retire des colonnes

import requests
import pandas as pd
from datetime import datetime, timedelta
import time
from sqlalchemy import create_engine

def fetch(url, max_retries=3, delay=2):
    """Fonction pour récupérer les données avec gestion des erreurs 429/418."""
    for i in range(max_retries):
        try:
            response = requests.get(url)
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:
                wait_time = (2 ** i) * delay
                print(f"Erreur 429 pour {url}. Réessai dans {wait_time} secondes...")
                time.sleep(wait_time)
            elif response.status_code == 418:
                wait_time = 60  # Attendre 1 minute en cas de ban
                print(f"Erreur 418 (IP bannie) pour {url}. Attente de {wait_time} secondes...")
                time.sleep(wait_time)
            else:
                print(f"Erreur {response.status_code} pour {url}: {response.text}")
                return None
        except Exception as e:
            print(f"Erreur lors de la requête {url}: {e}")
            wait_time = (2 ** i) * delay
            time.sleep(wait_time)
    return None

def get_metrics_for_timestamp(symbol, date_str):
    """Récupère les métriques supplémentaires pour un timestamp donné."""
    # Statistiques 24h
    stats_url = f"https://api.binance.com/api/v3/ticker/24hr?symbol={symbol}"
    stats = fetch(stats_url)
    if not stats:
        return None

    volume_24h = float(stats['volume'])
    num_trades_24h = int(stats['count'])

    # Order Book (spread bid-ask)
    order_book_url = f"https://api.binance.com/api/v3/depth?symbol={symbol}&limit=5"
    order_book = fetch(order_book_url)
    if not order_book:
        return None

    best_bid = float(order_book['bids'][0][0])
    best_ask = float(order_book['asks'][0][0])
    bid_ask_spread = best_ask - best_bid

    return {
        'bid_ask_spread': bid_ask_spread,
        'volume_24h': volume_24h,
        'num_trades_24h': num_trades_24h
    }

def get_daily_data_with_metrics(symbol, interval, start_str, end_str=None):
    """Récupère les données quotidiennes + métriques supplémentaires depuis Binance."""
    base_url = "https://api.binance.com/api/v3/klines"
    all_data = []
    start_time = int(datetime.strptime(start_str, "%Y-%m-%d").timestamp() * 1000)
    end_time = int(datetime.strptime(end_str, "%Y-%m-%d").timestamp() * 1000) if end_str else int(datetime.now().timestamp() * 1000)

    print(f"Récupération des données pour {symbol} de {datetime.fromtimestamp(start_time/1000)} à {datetime.fromtimestamp(end_time/1000)}")

    while start_time < end_time:
        current_end_time = min(start_time + 30 * 24 * 60 * 60 * 1000, end_time)
        url = f"{base_url}?symbol={symbol}&interval={interval}&startTime={start_time}&endTime={current_end_time}&limit=1000"
        data = fetch(url)

        if not data:
            print(f"Aucune donnée pour {symbol} entre {datetime.fromtimestamp(start_time/1000)} et {datetime.fromtimestamp(current_end_time/1000)}.")
            break

        for candle in data:
            candle_time = datetime.fromtimestamp(candle[0]/1000).strftime('%Y-%m-%d')
            metrics = get_metrics_for_timestamp(symbol, candle_time)
            if metrics:
                candle.extend([metrics['bid_ask_spread'], metrics['volume_24h'], metrics['num_trades_24h']])
            else:
                # Si les métriques ne sont pas disponibles, utiliser des valeurs par défaut
                candle.extend([None, None, None])

        all_data.extend(data)
        print(f"Reçu {len(data)} bougies pour {symbol}.")
        start_time = data[-1][0] + 1
        time.sleep(2)  # Délai de 2 secondes entre les requêtes

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

def update_daily_data_with_metrics(symbols, interval, db_url, timestamp_column='timestamp'):
    """Met à jour les données quotidiennes + métriques dans PostgreSQL."""
    engine = create_engine(db_url)

    for symbol in symbols:
        print(f"Mise à jour des données pour {symbol}...")

        # Récupérer la dernière date dans la base
        query = f"SELECT MAX(\"{timestamp_column}\") FROM binance_historical_data_with_metrics WHERE symbol = '{symbol}';"
        try:
            result = pd.read_sql(query, engine)
            last_date = result.iloc[0, 0]

            if pd.isna(last_date):
                start_date = '2021-01-01'  # Date par défaut si la table est vide
            else:
                if isinstance(last_date, str):
                    last_date = datetime.strptime(last_date.split()[0], '%Y-%m-%d')
                else:
                    last_date = last_date.date()
                start_date = (last_date + timedelta(days=1)).strftime('%Y-%m-%d')
        except Exception as e:
            print(f"Erreur lors de la lecture de la dernière date pour {symbol}: {e}")
            continue

        end_date = datetime.now().strftime('%Y-%m-%d')
        print(f"Récupération des nouvelles données pour {symbol} depuis {start_date}...")

        # Récupérer les nouvelles données
        new_data = get_daily_data_with_metrics(symbol, interval, start_date, end_date)
        if not new_data.empty:
            try:
                new_data.to_sql('binance_historical_data_with_metrics', engine, if_exists='append', index=False)
                print(f"Mise à jour terminée pour {symbol}. {len(new_data)} nouvelles bougies ajoutées.")
            except Exception as e:
                print(f"Erreur lors de l'import des données pour {symbol}: {e}")
        else:
            print(f"Aucune nouvelle donnée pour {symbol}.")

# Configuration
symbols = ['BTCUSDT', 'ETHUSDT']  # Réduire le nombre de paires pour éviter les bans
interval = '1d'  # Intervalle des bougies
db_url = "postgresql://nassim:datascientest@localhost:5432/crypto"  # URL de votre base PostgreSQL
timestamp_column = 'timestamp'  # Nom de la colonne de timestamp dans votre table

# Exécuter la mise à jour
update_daily_data_with_metrics(symbols, interval, db_url, timestamp_column)
