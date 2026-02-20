#V.3.0 du script, je veux tester de l'asynchrone pour permettre au script de tourner plus vite.
#je pousse la date de recuperation a 2016, pour avoir plsu de cycle crypto. Il y a eu des optimisations a cause la limitation d'appel vers binance

import aiohttp
import asyncio
import pandas as pd
from datetime import datetime, timedelta
import time

async def fetch(session, url, max_retries=3, delay=1):
    """Fonction asynchrone pour récupérer les données depuis une URL avec gestion des erreurs 429."""
    for i in range(max_retries):
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 429:
                    wait_time = (2 ** i) * delay  # Délai exponentiel
                    print(f"Erreur 429 pour {url}. Réessai dans {wait_time} secondes...")
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
    """Récupère les statistiques 24h pour une paire."""
    url = f"https://api.binance.com/api/v3/ticker/24hr?symbol={symbol}"
    return await fetch(session, url)

async def get_order_book(session, symbol):
    """Récupère le carnet d'ordres (order book) pour une paire."""
    url = f"https://api.binance.com/api/v3/depth?symbol={symbol}&limit=5"
    return await fetch(session, url)

async def get_metrics_for_timestamp_async(session, symbol, date_str):
    """Récupère les métriques supplémentaires pour un timestamp donné de manière asynchrone."""
    stats_task = get_24h_stats(session, symbol)
    order_book_task = get_order_book(session, symbol)

    stats, order_book = await asyncio.gather(stats_task, order_book_task)

    if not stats or not order_book:
        return None

    volume_24h = float(stats['volume'])
    num_trades_24h = int(stats['count'])
    best_bid = float(order_book['bids'][0][0])
    best_ask = float(order_book['asks'][0][0])
    bid_ask_spread = best_ask - best_bid

    return {
        'bid_ask_spread': bid_ask_spread,
        'volume_24h': volume_24h,
        'num_trades_24h': num_trades_24h
    }

async def get_historical_data_with_metrics_async(session, symbol, interval, start_str, end_str):
    """Récupère les données historiques + métriques supplémentaires de manière asynchrone."""
    start_time = int(datetime.strptime(start_str, "%Y-%m-%d").timestamp() * 1000)
    end_time = int(datetime.strptime(end_str, "%Y-%m-%d").timestamp() * 1000) if end_str else int(datetime.now().timestamp() * 1000)

    print(f"Récupération des données pour {symbol} de {datetime.fromtimestamp(start_time/1000)} à {datetime.fromtimestamp(end_time/1000)}")

    all_data = []
    while start_time < end_time:
        current_end_time = min(start_time + 30 * 24 * 60 * 60 * 1000, end_time)
        klines = await get_klines(session, symbol, interval, start_time, current_end_time)

        if not klines:
            print(f"Aucune donnée pour {symbol} entre {datetime.fromtimestamp(start_time/1000)} et {datetime.fromtimestamp(current_end_time/1000)}.")
            break

        # Récupérer les métriques pour chaque bougie
        tasks = []
        for candle in klines:
            candle_time = datetime.fromtimestamp(candle[0]/1000).strftime('%Y-%m-%d')
            tasks.append(get_metrics_for_timestamp_async(session, symbol, candle_time))

        metrics_list = await asyncio.gather(*tasks)

        for candle, metrics in zip(klines, metrics_list):
            if metrics:
                candle.extend([metrics['bid_ask_spread'], metrics['volume_24h'], metrics['num_trades_24h']])

        all_data.extend(klines)
        print(f"Reçu {len(klines)} bougies pour {symbol}.")
        start_time = klines[-1][0] + 1
        await asyncio.sleep(2)  # Délai plus long pour éviter les erreurs 429

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

async def main():
    """Fonction principale pour récupérer les données de manière asynchrone."""
    symbols = ['BTCUSDT', 'ETHUSDT']  
    interval = '1d'
    start_date = '2020-01-01'
    end_date = '2025-11-01'  

    async with aiohttp.ClientSession() as session:
        tasks = []
        for symbol in symbols:
            print(f"Récupération des données pour {symbol}...")
            task = get_historical_data_with_metrics_async(session, symbol, interval, start_date, end_date)
            tasks.append(task)

        results = await asyncio.gather(*tasks)

    historical_data = pd.DataFrame()
    for df in results:
        if not df.empty:
            historical_data = pd.concat([historical_data, df])

    if not historical_data.empty:
        historical_data.to_csv('binance_historical_data_with_metrics_async.csv', index=False)
        print("Données sauvegardées dans 'binance_historical_data_with_metrics_async.csv'.")
    else:
        print("Aucune donnée n'a été récupérée.")

# Exécuter le script asynchrone
asyncio.run(main())
