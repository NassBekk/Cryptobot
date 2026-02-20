import pandas as pd
from sqlalchemy import create_engine
from sklearn.preprocessing import MinMaxScaler
import os

def calculate_rsi(series, window=14):
    """Calcule le RSI (Relative Strength Index)."""
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def load_data_from_db():
    """Charge les données depuis PostgreSQL."""
    db_url = "postgresql://nassim:datascientest@db:5432/crypto"
    engine = create_engine(db_url)
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
        ORDER BY symbol, timestamp
    """
    return pd.read_sql(query, engine)

def prepare_features(df):
    """Prépare les features pour les modèles."""
    df['daily_return'] = df.groupby('symbol')['close'].pct_change()
    df['ma_7'] = df.groupby('symbol')['close'].rolling(window=7).mean().reset_index(level=0, drop=True)
    df['ma_30'] = df.groupby('symbol')['close'].rolling(window=30).mean().reset_index(level=0, drop=True)
    df['volatility'] = df.groupby('symbol')['daily_return'].rolling(window=7).std().reset_index(level=0, drop=True)
    df['rsi'] = df.groupby('symbol')['close'].apply(calculate_rsi).reset_index(level=0, drop=True)
    df['volume_to_price_ratio'] = df['volume'] / df['close']
    return df.dropna()

def normalize_features(df, scaler=None, fit=True):
    """Normalise les features."""
    cols_to_normalize = ['open', 'high', 'low', 'close', 'volume', 'Quote asset volume', 'Number of trades',
                         'bid_ask_spread', 'volume_24h', 'num_trades_24h', 'ma_7', 'ma_30', 'volatility', 'rsi', 'volume_to_price_ratio']
    if fit:
        scaler = MinMaxScaler()
        df[cols_to_normalize] = scaler.fit_transform(df[cols_to_normalize])
    else:
        df[cols_to_normalize] = scaler.transform(df[cols_to_normalize])
    
    # NEW: Store close column bounds for inverse transform
    close_index = cols_to_normalize.index('close')
    scaler.close_min = scaler.data_min_[close_index]
    scaler.close_max = scaler.data_max_[close_index]
    
    return df, scaler
