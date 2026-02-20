#V2.0, recupere les donnees du nouveau CSV.
from sqlalchemy import create_engine
import pandas as pd

# Charger le CSV
df = pd.read_csv('binance_historical_data_secure.csv')

# Connexion à PostgreSQL
engine = create_engine('postgresql://nassim:datascientest@localhost:5432/crypto')
df.to_sql('binance_historical_data_with_metrics', engine, if_exists='replace', index=False)
print("Données importées dans PostgreSQL.")
