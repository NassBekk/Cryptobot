# Cryptobot - Système de Prédiction Cryptomonnaies

Ce projet implémente un système de prédiction pour les cryptomonnaies utilisant plusieurs modèles de machine learning et de séries temporelles.

## Structure du Projet

```
prod/
│
├── app/                          # Application FastAPI (pour le déploiement)
│   ├── main.py                   # Point d'entrée de l'API
│   ├── models/                   # Modèles entraînés (chargés par FastAPI)
│   └── data/                     # Données utilisées par l'API
│
├── scripts/                      # Scripts autonomes pour le traitement des données
│   ├── utils.py                  # Fonctions utilitaires
│   ├── 01_data_cleaning.py      # Nettoyage des données
│   ├── 02_train_models.py       # Entraînement des modèles
│   └── 03_make_predictions.py   # Génération des prédictions
│
├── data/                         # Données brutes et traitées
│   ├── processed/                # Données nettoyées (ex: `cleaned_crypto_data.csv`)
│   └── predictions/              # Prédictions générées (ex: `latest_predictions.csv`)
│
├── models/                       # Modèles entraînés (Random Forest, LSTM, ARIMA, SARIMAX)
│   ├── random_forest_model.pkl
│   ├── lstm_model.keras
│   ├── arima_model.pkl
│   └── sarimax_model.pkl
│
├── Dockerfile                    # Configuration pour containeriser l'application
├── docker-compose.yml            # Orchestration des conteneurs (app + base de données)
├── requirements.txt              # Dépendances Python
└── README.md                     # Documentation du projet
```

## Prérequis

- Docker et Docker Compose
- Python 3.12+ (pour l'exécution locale des scripts)
- PostgreSQL (inclus dans docker-compose)

## Installation

1. **Cloner le repository** (si applicable)

2. **Construire et démarrer les conteneurs Docker** :
```bash
docker-compose up --build
```

3. **Exécuter les scripts de traitement** (dans l'ordre) :
```bash
# Depuis le répertoire prod/
cd scripts/

# 1. Nettoyer les données
python 01_data_cleaning.py

# 2. Entraîner les modèles
python 02_train_models.py

# 3. Générer des prédictions
python 03_make_predictions.py
```

## Architecture

### Base de données

- **PostgreSQL** : Stocke les données historiques de Binance
- **Table principale** : `binance_historical_data_with_metrics`
- **Port** : 5432
- **Credentials** :
  - User: `nassim`
  - Password: `datascientest`
  - Database: `crypto`

### Modèles de Machine Learning

1. **Random Forest Classifier** : Classification binaire (hausse/baisse)
2. **LSTM** : Réseau de neurones récurrent pour la prédiction de séries temporelles
3. **ARIMA** : Modèle de séries temporelles pour la prédiction de prix
4. **SARIMAX** : ARIMA avec composantes saisonnières

### API FastAPI

L'API expose plusieurs endpoints pour les prédictions :

- **URL** : `http://localhost:8000`
- **Symboles supportés** : `BTCUSDT`, `ETHUSDT`
- **Endpoints disponibles** :
  - `GET /health` : Vérification de santé
  - `GET /symbols` : Liste des symboles supportés
  - `GET /metrics` : Métriques de performance globales
  - `GET /metrics/{symbol}` : Métriques de performance par symbole
  - `POST /evaluate` : Comparaison prédictions vs valeurs réelles
  - `POST /predict` : Obtenir des prédictions pour un symbole

**Exemple de requête :**
```bash
curl -X POST "http://localhost:8000/predict" \
  -H "Content-Type: application/json" \
  -d '{"symbol": "BTCUSDT"}'
```

**Réponse pour BTCUSDT :**
```json
{
  "symbol": "BTCUSDT",
  "timestamp": "2024-01-10T12:00:00",
  "predictions": {
    "random_forest": 1,
    "lstm": 1,
    "arima": 45000.5,
    "sarimax": 45100.2
  }
}
```

**Réponse pour ETHUSDT :**
```json
{
  "symbol": "ETHUSDT",
  "timestamp": "2024-01-10T12:00:00",
  "predictions": {
    "random_forest": 1,
    "lstm": 0,
    "arima": null,
    "sarimax": null
  }
}
```

**Note :** Pour ETHUSDT, les modèles ARIMA/SARIMAX ne sont pas disponibles (entraînés uniquement sur BTCUSDT).

📖 **Documentation complète** : Voir [API_USAGE.md](API_USAGE.md) pour plus de détails et d'exemples.

## Services Docker

- **app** : Application FastAPI (port 8000)
- **db** : Base de données PostgreSQL (port 5432)
- **pgadmin** : Interface d'administration PostgreSQL (port 5050)
  - Email: `nassim@crypto.com`
  - Password: `bitcoin`

## Utilisation

### Entraînement des modèles

Les modèles doivent être entraînés avant d'utiliser l'API :

1. Assurez-vous que la base de données contient des données historiques
2. Exécutez les scripts dans l'ordre :
   - `01_data_cleaning.py` : Nettoie et prépare les données
   - `02_train_models.py` : Entraîne tous les modèles
3. Les modèles seront sauvegardés dans `models/` et copiés dans `app/models/` pour l'API

### Utilisation de l'API

Une fois les conteneurs démarrés et les modèles entraînés :

```bash
curl -X POST "http://localhost:8000/predict" \
  -H "Content-Type: application/json" \
  -d '{"symbol": "BTCUSDT"}'
```

### Génération de prédictions en lot

Pour générer des prédictions pour tous les symboles :

```bash
python scripts/03_make_predictions.py
```

Les prédictions seront sauvegardées dans `data/predictions/latest_predictions.csv`.

## Dépendances

Les dépendances principales sont listées dans `requirements.txt` :

- pandas==2.0.3
- numpy==1.24.3
- scikit-learn==1.3.0
- tensorflow==2.12.0
- statsmodels==0.14.0
- fastapi==0.109.1
- uvicorn==0.27.0
- sqlalchemy==2.0.19
- psycopg2-binary==2.9.6

## Notes

- Les scripts utilisent des chemins relatifs basés sur la structure du projet
- Les modèles doivent être présents dans `app/models/` pour que l'API fonctionne
- Le scaler est nécessaire pour la normalisation des données
- Les données de test doivent être disponibles dans la base de données PostgreSQL

## Troubleshooting

1. **Erreur de connexion à la base de données** :
   - Vérifiez que le service `db` est démarré : `docker-compose ps`
   - Vérifiez les credentials dans `docker-compose.yml`

2. **Modèles non trouvés** :
   - Assurez-vous d'avoir exécuté `02_train_models.py`
   - Vérifiez que les fichiers sont présents dans `models/` ou `app/models/`

3. **Erreurs de dépendances** :
   - Reconstruisez l'image Docker : `docker-compose build --no-cache`

## Auteur

Projet développé dans le cadre du projet AVR25-CDE-OPA-1.
