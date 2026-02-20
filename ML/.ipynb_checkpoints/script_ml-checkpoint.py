import pandas as pd
from sqlalchemy import create_engine
from datetime import datetime


# Etape 1: recuperation de nos donnees depuis postgres, au jour meme
# Connexion à la base de données
db_url = "postgresql://nassim:datascientest@localhost:5432/crypto"
engine = create_engine(db_url)

# Requête pour récupérer les données BTCUSDT et ETHUSDT
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

# Chargement des données dans un DataFrame
df = pd.read_sql(query, engine)

# Affichage des premières lignes
print("Aperçu des données brutes :")
print(df.head())
print("\nTypes de données :")
print(df.dtypes)


#Etape 2: Nettoyag des donnees
#2.1 Suppression des doublons
df = df.drop_duplicates(subset=['symbol', 'timestamp'], keep='last')
print(f"\nNombre de lignes après suppression des doublons : {len(df)}")

#2.2 Gestion des valeurs manquantes
# Vérification des valeurs manquantes
print("\nValeurs manquantes par colonne :")
print(df.isnull().sum())

# et Suppression des lignes avec des valeurs manquantes
df = df.dropna()
print(f"\nNombre de lignes après suppression des valeurs manquantes : {len(df)}")

#2.3 Conversion des types de donnees
# Conversion des colonnes numériques
numeric_cols = ['open', 'high', 'low', 'close', 'volume', 'Quote asset volume', 'Number of trades',
                'bid_ask_spread', 'volume_24h', 'num_trades_24h']
df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors='coerce')

# Conversion de la colonne timestamp en datetime
df['timestamp'] = pd.to_datetime(df['timestamp'])


#Etape 3: creatioon de nouvelles varialbles, pour une vrai analyses des donnees
#Je ne suis pas un expert sur les marches, donc j'ai regardé pour avoir de l'aide, grace a deux LLM differents
#3.1 Calcul des rendements quotidiens
df['daily_return'] = df.groupby('symbol')['close'].pct_change()

#3.2 Moyennes mobiles sur 7 et 30 jours
df['ma_7'] = df.groupby('symbol')['close'].rolling(window=7).mean().reset_index(level=0, drop=True)
df['ma_30'] = df.groupby('symbol')['close'].rolling(window=30).mean().reset_index(level=0, drop=True)

#3.3 Volatilité sur 7 jours
df['volatility'] = df.groupby('symbol')['daily_return'].rolling(window=7).std().reset_index(level=0, drop=True)

#3.4 Calcul du RSI (Relative Strength Index)
def calculate_rsi(series, window=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

df['rsi'] = df.groupby('symbol')['close'].apply(calculate_rsi).reset_index(level=0, drop=True)


#3.5 Calcul des ratio Volume/Prix
df['volume_to_price_ratio'] = df['volume'] / df['close']


#Etape 4: Gestion des Outliers
# Suppression des valeurs aberrantes pour le prix de clôture
df = df[(df['close'] > 0) & (df['close'] < df.groupby('symbol')['close'].transform(lambda x: x.quantile(0.99)))]

# Suppression des valeurs aberrantes pour le volume
df = df[df['volume'] < df.groupby('symbol')['volume'].transform(lambda x: x.quantile(0.99))]

#Etape 5: Normalisation des donnees
from sklearn.preprocessing import MinMaxScaler

# Sélection des colonnes à normaliser
cols_to_normalize = ['open', 'high', 'low', 'close', 'volume', 'Quote asset volume', 'Number of trades',
                     'bid_ask_spread', 'volume_24h', 'num_trades_24h', 'ma_7', 'ma_30', 'volatility', 'rsi', 'volume_to_price_ratio']

# Normalisation des données entre 0 et 1
scaler = MinMaxScaler()
df[cols_to_normalize] = scaler.fit_transform(df[cols_to_normalize])


#Etape 6: Separation de nos donnees pour le ML
#3.1 definition de notre target
# Prédire le rendement du lendemain (1 si hausse, 0 si baisse)
df['target'] = (df.groupby('symbol')['daily_return'].shift(-1) > 0).astype(int)
df = df.dropna(subset=['target'])


#3.2 Separation des variables explicatives et cible
# Sélection des variables explicatives
feats = df.drop(columns=['target', 'symbol', 'timestamp'])

# Sélection de la cible
target = df['target']


#3.3 Separation des ejeux de donnees
from sklearn.model_selection import train_test_split

# Division des données(on fera un 80/20)
X_train, X_test, y_train, y_test = train_test_split(feats, target, test_size=0.2, random_state=42, shuffle=False)

