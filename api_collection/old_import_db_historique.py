#V.1.0 du script, basé sur les Klines uniquement
from sqlalchemy import create_engine
import pandas as pd

# Charger le CSV
df = pd.read_csv('binance_historical_data.csv')

# Connexion à PostgreSQL
engine = create_engine('postgresql://nassim:datascientest@localhost:5432/crypto')
df.to_sql('binance_historical_data', engine, if_exists='replace', index=False)
print("Données importées dans PostgreSQL.")
