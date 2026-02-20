# Cryptobot - Système de Prédiction Cryptomonnaies

Ce projet implémente un système complet de collecte de données et de prédiction pour les cryptomonnaies utilisant plusieurs modèles de machine learning et de séries temporelles.

## 📋 Table des Matières

- [Architecture du Projet](#architecture-du-projet)
- [Prérequis](#prérequis)
- [Guide de Démarrage Rapide](#guide-de-démarrage-rapide)
- [Workflow Complet](#workflow-complet)
- [Documentation Détaillée](#documentation-détaillée)

---

## 🏗️ Architecture du Projet

Le projet est structuré en deux modules principaux :

```
cryptobot/
│
├── api_collection/              # MODULE 1: Collecte des données Binance
│   ├── recuperation_historique.py      # Récupération initiale des données historiques
│   ├── import_db_historique.py         # Import des données dans PostgreSQL
│   ├── mise_a_jour_quotidienne.py      # Mise à jour quotidienne des données
│   └── *.csv                           # Fichiers de données générés
│
├── prod/                        # MODULE 2: ML & API de Prédiction
│   ├── app/                            # Application FastAPI
│   │   ├── main.py                     # Point d'entrée de l'API
│   │   ├── models/                     # Modèles ML déployés
│   │   └── data/                       # Données pour l'API
│   │
│   ├── scripts/                        # Scripts de traitement ML
│   │   ├── utils.py                    # Fonctions utilitaires
│   │   ├── 01_data_cleaning.py         # Nettoyage des données
│   │   ├── 02_train_models.py          # Entraînement des modèles
│   │   └── 03_make_predictions.py      # Génération des prédictions
│   │
│   ├── data/                           # Données ML
│   │   ├── processed/                  # Données nettoyées
│   │   └── predictions/                # Prédictions générées
│   │
│   ├── models/                         # Modèles entraînés
│   │   ├── random_forest_model.pkl
│   │   ├── lstm_model.keras
│   │   ├── arima_model.pkl
│   │   └── sarimax_model.pkl
│   │
│   ├── docker-compose.yml              # Orchestration conteneurs
│   ├── Dockerfile                      # Configuration conteneur API
│   └── requirements.txt                # Dépendances Python
│
└── README.md                    # Ce fichier
```

---

## 🔧 Prérequis

- **Python** 3.12+
- **PostgreSQL** (ou Docker pour utiliser PostgreSQL en conteneur)
- **Docker & Docker Compose** (recommandé pour le déploiement)
- **Connexion Internet** (pour les appels API Binance)

### Dépendances Python Principales

```
pandas==2.0.3
numpy==1.24.3
scikit-learn==1.3.0
tensorflow==2.12.0
statsmodels==0.14.0
fastapi==0.109.1
uvicorn==0.27.0
sqlalchemy==2.0.19
psycopg2-binary==2.9.6
aiohttp==3.8.4
requests==2.31.0
```

---

## 🚀 Guide de Démarrage Rapide

### Installation Complète en 5 Étapes

#### Étape 1 : Préparer l'Environnement

```bash
# Cloner le projet (si applicable)
cd /home/nassbuntu/projet/AVR25-CDE-OPA-1/cryptobot

# Créer un environnement virtuel
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# ou : venv\Scripts\activate  # Windows

# Installer les dépendances
pip install -r prod/requirements.txt
pip install aiohttp requests  # Pour api_collection
```

#### Étape 2 : Démarrer la Base de Données PostgreSQL

**Option A : Avec Docker (recommandé)**
```bash
cd prod/
docker-compose up -d db
```

**Option B : PostgreSQL local**
```bash
# Créer la base de données
psql -U postgres -c "CREATE DATABASE crypto;"
psql -U postgres -c "CREATE USER nassim WITH PASSWORD 'datascientest';"
psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE crypto TO nassim;"
```

#### Étape 3 : Collecter les Données Historiques (OBLIGATOIRE)

```bash
cd api_collection/

# 1. Récupérer les données historiques depuis Binance (2020-2025)
python recuperation_historique.py
# ⏱️ Durée: ~10-15 minutes
# 📁 Génère: binance_historical_data_secure.csv

# 2. Importer les données dans PostgreSQL
python import_db_historique.py
# ✅ Crée la table: binance_historical_data_with_metrics
```

**Configuration des symboles et dates :**
Vous pouvez modifier dans [recuperation_historique.py](api_collection/recuperation_historique.py) :
```python
symbols = ['BTCUSDT', 'ETHUSDT']  # Ajouter d'autres paires
start_date = '2020-01-01'
end_date = '2025-11-01'
```

#### Étape 4 : Entraîner les Modèles ML

```bash
cd ../prod/scripts/

# 1. Nettoyer les données
python 01_data_cleaning.py
# 📁 Génère: ../data/processed/cleaned_crypto_data.csv

# 2. Entraîner les modèles
python 02_train_models.py
# ⏱️ Durée: ~5-10 minutes
# 📁 Génère: ../models/*.pkl et ../models/*.keras

# 3. (Optionnel) Générer des prédictions initiales
python 03_make_predictions.py
# 📁 Génère: ../data/predictions/latest_predictions.csv
```

#### Étape 5 : Lancer l'API de Prédiction

```bash
cd ../
docker-compose up --build
```

L'API sera disponible sur : **http://localhost:8000**

---

## 📊 Workflow Complet

### Phase 1 : Collecte des Données (api_collection/)

#### 1.1 Récupération Initiale

Le script [recuperation_historique.py](api_collection/recuperation_historique.py) utilise l'API publique de Binance de manière asynchrone pour :

- **Récupérer les bougies (klines)** : Prix OHLCV (Open, High, Low, Close, Volume)
- **Récupérer les métriques 24h** : Volume 24h, nombre de trades
- **Récupérer le carnet d'ordres** : Bid-Ask Spread

**Caractéristiques :**
- ✅ Gestion des erreurs 429 (rate limit) et 418 (ban IP)
- ✅ Retry automatique avec backoff exponentiel
- ✅ Délais entre requêtes (2 secondes) pour éviter les bans
- ✅ Asynchrone (aiohttp) pour des performances optimales

**Colonnes générées :**
```
timestamp, open, high, low, close, volume, symbol,
bid_ask_spread, volume_24h, num_trades_24h
```

#### 1.2 Import dans PostgreSQL

Le script [import_db_historique.py](api_collection/import_db_historique.py) :
- Charge le CSV généré
- Crée/remplace la table `binance_historical_data_with_metrics`
- Utilise SQLAlchemy pour la connexion

#### 1.3 Mise à Jour Quotidienne

Le script [mise_a_jour_quotidienne.py](api_collection/mise_a_jour_quotidienne.py) permet de :
- Détecter automatiquement la dernière date dans la base
- Récupérer uniquement les nouvelles données
- Ajouter les nouvelles bougies à la table existante

**À exécuter quotidiennement (optionnel, via cron) :**
```bash
0 1 * * * cd /path/to/api_collection && python mise_a_jour_quotidienne.py
```

---

### Phase 2 : Machine Learning & Prédictions (prod/)

#### 2.1 Architecture des Modèles

Le système utilise 4 modèles complémentaires :

| Modèle | Type | Usage | Symboles |
|--------|------|-------|----------|
| **Random Forest** | Classification | Prédiction hausse/baisse | BTCUSDT, ETHUSDT |
| **LSTM** | Régression (Deep Learning) | Prédiction de prix | BTCUSDT, ETHUSDT |
| **ARIMA** | Séries temporelles | Prédiction de tendance | BTCUSDT uniquement |
| **SARIMAX** | Séries temporelles + saisonnalité | Prédiction avancée | BTCUSDT uniquement |

#### 2.2 Pipeline de Traitement

**Script 1 : [01_data_cleaning.py](prod/scripts/01_data_cleaning.py)**
- Charge les données depuis PostgreSQL
- Nettoie les valeurs manquantes
- Génère des features (moyennes mobiles, RSI, etc.)
- Sauvegarde : `data/processed/cleaned_crypto_data.csv`

**Script 2 : [02_train_models.py](prod/scripts/02_train_models.py)**
- Entraîne les 4 modèles sur les données nettoyées
- Évalue les performances (accuracy, MAE, RMSE)
- Sauvegarde les modèles dans `models/`

**Script 3 : [03_make_predictions.py](prod/scripts/03_make_predictions.py)**
- Charge les modèles entraînés
- Génère des prédictions pour les symboles
- Sauvegarde : `data/predictions/latest_predictions.csv`

#### 2.3 API FastAPI

L'API expose les prédictions via plusieurs endpoints :

**Endpoints disponibles :**

```bash
# Santé de l'API
GET /health

# Liste des symboles supportés
GET /symbols
# Réponse: ["BTCUSDT", "ETHUSDT"]

# Métriques de performance globales
GET /metrics

# Métriques par symbole
GET /metrics/{symbol}

# Prédictions
POST /predict
Content-Type: application/json
{"symbol": "BTCUSDT"}
```

**Exemple de réponse de prédiction :**
```json
{
  "symbol": "BTCUSDT",
  "timestamp": "2026-01-28T12:00:00",
  "predictions": {
    "random_forest": 1,          // 1 = hausse, 0 = baisse
    "lstm": 1,
    "arima": 45000.5,            // Prix prédit
    "sarimax": 45100.2
  }
}
```

---

## 🗄️ Base de Données

### Configuration PostgreSQL

**Connexion par défaut :**
```
Host: localhost
Port: 5432
Database: crypto
User: nassim
Password: datascientest
```

**Table principale :**
```sql
binance_historical_data_with_metrics
```

**Schéma :**
```sql
CREATE TABLE binance_historical_data_with_metrics (
    timestamp DATE,
    symbol VARCHAR(20),
    open FLOAT,
    high FLOAT,
    low FLOAT,
    close FLOAT,
    volume FLOAT,
    bid_ask_spread FLOAT,
    volume_24h FLOAT,
    num_trades_24h INTEGER,
    -- autres colonnes...
);
```

---

## 🐳 Services Docker

Le fichier [docker-compose.yml](prod/docker-compose.yml) orchestre 3 services :

| Service | Port | Description |
|---------|------|-------------|
| **db** | 5432 | PostgreSQL 13 |
| **app** | 8000 | API FastAPI |
| **pgadmin** | 5050 | Interface d'administration PostgreSQL |

**Accès PgAdmin :**
- URL : http://localhost:5050
- Email : `nassim@crypto.com`
- Password : `bitcoin`

---

## 📚 Documentation Détaillée

Pour plus de détails, consultez les fichiers suivants dans [prod/](prod/) :

- **[API_USAGE.md](prod/API_USAGE.md)** : Guide complet d'utilisation de l'API
- **[ARCHITECTURE.md](prod/ARCHITECTURE.md)** : Architecture technique détaillée
- **[ARIMA_SARIMAX_GUIDE.md](prod/ARIMA_SARIMAX_GUIDE.md)** : Guide des modèles de séries temporelles
- **[DEV_REFERENCE.md](prod/DEV_REFERENCE.md)** : Référence pour développeurs
- **[QUICK_START.md](prod/QUICK_START.md)** : Démarrage rapide
- **[DEBUG_CHECKLIST.md](prod/DEBUG_CHECKLIST.md)** : Guide de débogage

---

## 🔄 Maintenance et Mise à Jour

### Mise à Jour Quotidienne Automatique

Pour automatiser la collecte de nouvelles données :

```bash
# Créer un cron job
crontab -e

# Ajouter (exécution à 1h du matin)
0 1 * * * cd /home/nassbuntu/projet/AVR25-CDE-OPA-1/cryptobot/api_collection && /home/nassbuntu/nass_env/bin/python mise_a_jour_quotidienne.py >> /tmp/cryptobot_update.log 2>&1
```

### Réentraînement des Modèles

Il est recommandé de réentraîner les modèles régulièrement (hebdomadairement ou mensuellement) :

```bash
cd prod/scripts/
python 01_data_cleaning.py
python 02_train_models.py

# Redémarrer l'API pour charger les nouveaux modèles
cd ..
docker-compose restart app
```

---

## ⚠️ Limitations et Bonnes Pratiques

### Limitations de l'API Binance

- **Rate Limit** : 1200 requêtes par minute (Weight)
- **Ban IP (418)** : Peut survenir en cas d'abus
- **Délais recommandés** : 2 secondes entre requêtes

### Bonnes Pratiques

1. **Ne pas récupérer les données historiques trop souvent** : Utiliser le script de mise à jour quotidienne
2. **Limiter le nombre de symboles** : Commencer avec BTCUSDT et ETHUSDT
3. **Surveiller les logs** : Vérifier les erreurs 429/418 dans les logs
4. **Sauvegardes régulières** : Exporter la base PostgreSQL régulièrement

```bash
# Backup PostgreSQL
docker exec -t cryptobot-db pg_dump -U nassim crypto > backup_$(date +%Y%m%d).sql

# Restore
docker exec -i cryptobot-db psql -U nassim crypto < backup_20260128.sql
```

---

## 🐛 Troubleshooting

### Problème 1 : Erreur 429 ou 418 de Binance

**Solution :**
- Augmenter les délais dans les scripts (actuellement 2 secondes)
- Réduire le nombre de symboles récupérés
- Attendre quelques heures avant de réessayer

### Problème 2 : Base de données vide après import

**Vérification :**
```bash
docker exec -it cryptobot-db psql -U nassim -d crypto -c "SELECT COUNT(*) FROM binance_historical_data_with_metrics;"
```

**Solution :**
- Vérifier que le CSV a été généré correctement
- Re-exécuter `import_db_historique.py`

### Problème 3 : Modèles non trouvés par l'API

**Solution :**
```bash
# Vérifier la présence des modèles
ls -la prod/models/
ls -la prod/app/models/

# Copier les modèles si nécessaire
cp prod/models/* prod/app/models/

# Redémarrer l'API
docker-compose restart app
```

### Problème 4 : Erreur de connexion PostgreSQL

**Solution :**
```bash
# Vérifier que le service est démarré
docker-compose ps

# Vérifier les logs
docker-compose logs db

# Redémarrer le service
docker-compose restart db
```

---

## 👥 Contribution

Projet développé dans le cadre du projet **AVR25-CDE-OPA-1**.

### Structure de Développement

```bash
# Branche principale
main

# Créer une branche de feature
git checkout -b feature/nouvelle-fonctionnalite

# Tester avant commit
pytest tests/

# Commit
git commit -m "feat: description"

# Push
git push origin feature/nouvelle-fonctionnalite
```

---

## 📄 Licence

Ce projet est développé dans un cadre éducatif.

---

## 📞 Support

Pour toute question ou problème :
1. Consulter la documentation dans [prod/](prod/)
2. Vérifier le [DEBUG_CHECKLIST.md](prod/DEBUG_CHECKLIST.md)
3. Consulter les logs : `docker-compose logs -f`

---

**Dernière mise à jour :** 28 janvier 2026
