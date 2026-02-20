#V.3.1 du script, je viens d'etre bani de Binance car trop de requete, on ameliore pour permettre de recuperer ca


import aiohttp
import asyncio
import pandas as pd
from datetime import datetime, timedelta
import time

async def fetch(session, url, max_retries=3, delay=2):
    """Fonction asynchrone pour récupérer les données avec gestion des erreurs 429/418."""
    for i in range(max_retries):
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 429:
                    wait_time = (2 ** i) * delay
                    print(f"Erreur 429 pour {url}. Réessai dans {wait_time} secondes...")
                    await asyncio.sleep(wait_time)
                elif response.status == 418:
                    wait_time = 60  # Attendre 1 minute en cas de ban
                    print(f"Erreur 418 (IP bannie) pour {url}. Attente de {wait_time} secondes...")
                    await asyncio.sleep(wait_time)
                else:
                    print(f"Erreur {response.status} pour {url}")
                    return None
        except Exception as e:
            print(f"Erreur lors de la requête {url}: {e}")
            wait_time = (2 ** i) * delay
            await asyncio.sleep(wait_time)
    return None

async def get_klines(session, symbol, interval, start_time, end_time):
    """Récupère les bougies (klines) pour une paire et une période donnée."""
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&startTime={start_time}&endTime={end_time}&limit=1000"
    return await fetch(session, url)

async def get_24h_stats(session, symbol):
    """Récupère les statistiques 24h pour une paire (une fois par jour)."""
    url = f"https://api.binance.com/api/v3/ticker/24hr?symbol={symbol}"
    return await fetch(session, url)

async def get_order_book(session, symbol):
    """Récupère le carnet d'ordres (une fois par jour)."""
    url = f"https://api.binance.com/api/v3/depth?symbol={symbol}&limit=5"
    return await fetch(session, url)

async def get_historical_data_async(symbol, interval, start_str, end_str):
    """Récupère les données historiques de manière asynchrone et sécurisée."""
    start_time = int(datetime.strptime(start_str, "%Y-%m-%d").timestamp() * 1000)
    end_time = int(datetime.strptime(end_str, "%Y-%m-%d").timestamp() * 1000) if end_str else int(datetime.now().timestamp() * 1000)

    print(f"Récupération des données pour {symbol} de {datetime.fromtimestamp(start_time/1000)} à {datetime.fromtimestamp(end_time/1000)}")

    all_data = []
    async with aiohttp.ClientSession() as session:
        while start_time < end_time:
            current_end_time = min(start_time + 30 * 24 * 60 * 60 * 1000, end_time)
            klines = await get_klines(session, symbol, interval, start_time, current_end_time)

            if not klines:
                print(f"Aucune donnée pour {symbol} entre {datetime.fromtimestamp(start_time/1000)} et {datetime.fromtimestamp(current_end_time/1000)}.")
                break

            all_data.extend(klines)
            print(f"Reçu {len(klines)} bougies pour {symbol}.")
            start_time = klines[-1][0] + 1
            await asyncio.sleep(2)  # Délai de 2 secondes entre les requêtes

    if not all_data:
        return pd.DataFrame()

    df = pd.DataFrame(all_data, columns=[
        'timestamp', 'open', 'high', 'low', 'close', 'volume',
        'Close time', 'Quote asset volume', 'Number of trades',
        'Taker buy base', 'Taker buy quote', 'Ignore'
    ])
    df['symbol'] = symbol
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms').dt.date

    # Récupérer les métriques 24h et order book UNE SEULE FOIS par jour
    unique_dates = df['timestamp'].unique()
    metrics_data = []
    async with aiohttp.ClientSession() as session:
        for date in unique_dates:
            date_str = date.strftime('%Y-%m-%d')
            stats = await get_24h_stats(session, symbol)
            order_book = await get_order_book(session, symbol)
            await asyncio.sleep(2)  # Délai entre les requêtes de métriques

            if stats and order_book:
                volume_24h = float(stats['volume'])
                num_trades_24h = int(stats['count'])
                best_bid = float(order_book['bids'][0][0])
                best_ask = float(order_book['asks'][0][0])
                bid_ask_spread = best_ask - best_bid

                metrics_data.append({
                    'timestamp': date,
                    'bid_ask_spread': bid_ask_spread,
                    'volume_24h': volume_24h,
                    'num_trades_24h': num_trades_24h
                })

    metrics_df = pd.DataFrame(metrics_data)
    df = df.merge(metrics_df, on='timestamp', how='left')
    return df

async def main():
    """Fonction principale pour récupérer les données de manière sécurisée."""
    symbols = ['BTCUSDT', 'ETHUSDT'] 
    interval = '1d'
    start_date = '2020-01-01'
    end_date = '2025-11-01'  

    async with aiohttp.ClientSession() as session:
        tasks = []
        for symbol in symbols:
            print(f"Récupération des données pour {symbol}...")
            task = get_historical_data_async(symbol, interval, start_date, end_date)
            tasks.append(task)

        results = await asyncio.gather(*tasks)

    historical_data = pd.DataFrame()
    for df in results:
        if not df.empty:
            historical_data = pd.concat([historical_data, df])

    if not historical_data.empty:
        historical_data.to_csv('binance_historical_data_secure.csv', index=False)
        print("Données sauvegardées dans 'binance_historical_data_secure.csv'.")
    else:
        print("Aucune donnée n'a été récupérée.")

# Exécuter le script
asyncio.run(main())
