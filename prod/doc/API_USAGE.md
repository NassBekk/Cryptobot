# Guide d'utilisation de l'API

## Endpoints disponibles

### 1. Health Check
```bash
GET /health
```

Vérifie l'état de l'API.

**Réponse :**
```json
{
  "status": "healthy",
  "service": "cryptobot-api"
}
```

### 2. Liste des symboles supportés
```bash
GET /symbols
```

Retourne la liste des symboles de cryptomonnaies supportés.

**Réponse :**
```json
{
  "symbols": ["BTCUSDT", "ETHUSDT"],
  "description": "Symboles de cryptomonnaies supportés pour les prédictions"
}
```

### 3. Métriques de performance (globales)
```bash
GET /metrics?limit=1000
```

Retourne les métriques de performance de tous les modèles pour tous les symboles.

**Paramètres :**
- `limit` (optionnel, défaut: 1000) : Nombre maximum d'échantillons à utiliser pour l'évaluation

**Réponse :**
```json
{
  "overall_metrics": {
    "BTCUSDT": {
      "classification": {
        "random_forest": {
          "accuracy": 0.75,
          "precision": 0.73,
          "recall": 0.78,
          "f1_score": 0.75,
          "confusion_matrix": [[45, 12], [8, 35]]
        },
        "lstm": {
          "accuracy": 0.72,
          "precision": 0.70,
          "recall": 0.75,
          "f1_score": 0.72,
          "confusion_matrix": [[42, 15], [10, 33]]
        }
      },
      "time_series": {
        "arima": {
          "mse": 1250000.5,
          "mae": 950.3,
          "rmse": 1118.0,
          "r2_score": 0.85
        },
        "sarimax": {
          "mse": 1150000.2,
          "mae": 920.1,
          "rmse": 1072.5,
          "r2_score": 0.87
        }
      },
      "test_samples": 100
    },
    "ETHUSDT": {
      "classification": {
        "random_forest": {
          "accuracy": 0.71,
          "precision": 0.69,
          "recall": 0.74,
          "f1_score": 0.71,
          "confusion_matrix": [[40, 14], [11, 35]]
        },
        "lstm": {
          "accuracy": 0.68,
          "precision": 0.66,
          "recall": 0.71,
          "f1_score": 0.68,
          "confusion_matrix": [[38, 16], [12, 34]]
        }
      },
      "test_samples": 95
    }
  },
  "models_evaluated": ["random_forest", "lstm", "arima", "sarimax"],
  "test_limit": 1000
}
```

### 4. Métriques de performance par symbole
```bash
GET /metrics/{symbol}?limit=1000
```

Retourne les métriques de performance pour un symbole spécifique.

**Paramètres :**
- `symbol` : Symbole à évaluer (`BTCUSDT` ou `ETHUSDT`)
- `limit` (optionnel, défaut: 1000) : Nombre maximum d'échantillons à utiliser

**Réponse :** (même format que dans `/metrics` mais pour un seul symbole)

### 5. Comparaison prédictions vs valeurs réelles
```bash
POST /evaluate
Content-Type: application/json

{
  "symbol": "BTCUSDT",
  "limit": 500
}
```

Compare les prédictions des modèles aux valeurs réelles sur un jeu de test.

**Paramètres :**
- `symbol` (requis) : Symbole à évaluer (`BTCUSDT` ou `ETHUSDT`)
- `limit` (optionnel, défaut: 500) : Nombre maximum d'échantillons à utiliser

**Réponse :**
```json
{
  "symbol": "BTCUSDT",
  "total_samples": 500,
  "summary": {
    "random_forest_accuracy": 0.75,
    "lstm_accuracy": 0.72
  },
  "comparisons": [
    {
      "timestamp": "2024-01-01T00:00:00",
      "actual": 1,
      "prediction_rf": 1,
      "prediction_lstm": 1,
      "correct_rf": true,
      "correct_lstm": true
    },
    ...
  ]
}
```

### 6. Prédictions
```bash
POST /predict
Content-Type: application/json

{
  "symbol": "BTCUSDT",
  "timestamp": "2024-01-01T00:00:00"  // Optionnel
}
```

**Paramètres :**
- `symbol` (requis) : Symbole de la paire de cryptomonnaie (`BTCUSDT` ou `ETHUSDT`)
- `timestamp` (optionnel) : Timestamp pour la prédiction

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

**Note :** Pour ETHUSDT, `arima` et `sarimax` sont `null` car ces modèles sont entraînés uniquement sur BTCUSDT.

**Codes d'erreur :**
- `400` : Symbole non supporté
- `404` : Aucune donnée trouvée pour le symbole
- `500` : Erreur serveur

## Exemples d'utilisation

### Avec curl

```bash
# Vérifier les symboles supportés
curl http://localhost:8000/symbols

# Obtenir les métriques globales
curl "http://localhost:8000/metrics?limit=1000"

# Obtenir les métriques pour BTCUSDT
curl "http://localhost:8000/metrics/BTCUSDT?limit=1000"

# Comparer prédictions vs valeurs réelles
curl -X POST "http://localhost:8000/evaluate" \
  -H "Content-Type: application/json" \
  -d '{"symbol": "BTCUSDT", "limit": 500}'

# Prédiction pour BTCUSDT
curl -X POST "http://localhost:8000/predict" \
  -H "Content-Type: application/json" \
  -d '{"symbol": "BTCUSDT"}'

# Prédiction pour ETHUSDT
curl -X POST "http://localhost:8000/predict" \
  -H "Content-Type: application/json" \
  -d '{"symbol": "ETHUSDT"}'
```

### Avec Python (requests)

```python
import requests

BASE_URL = "http://localhost:8000"

# Lister les symboles
response = requests.get(f"{BASE_URL}/symbols")
print(response.json())

# Obtenir les métriques globales
response = requests.get(f"{BASE_URL}/metrics", params={"limit": 1000})
metrics = response.json()
print(f"Accuracy RF BTCUSDT: {metrics['overall_metrics']['BTCUSDT']['classification']['random_forest']['accuracy']}")

# Obtenir les métriques pour un symbole
response = requests.get(f"{BASE_URL}/metrics/BTCUSDT", params={"limit": 1000})
print(response.json())

# Comparer prédictions vs valeurs réelles
response = requests.post(
    f"{BASE_URL}/evaluate",
    json={"symbol": "BTCUSDT", "limit": 500}
)
comparison = response.json()
print(f"Accuracy RF: {comparison['summary']['random_forest_accuracy']}")
print(f"Accuracy LSTM: {comparison['summary']['lstm_accuracy']}")

# Prédiction BTCUSDT
response = requests.post(
    f"{BASE_URL}/predict",
    json={"symbol": "BTCUSDT"}
)
print(response.json())

# Prédiction ETHUSDT
response = requests.post(
    f"{BASE_URL}/predict",
    json={"symbol": "ETHUSDT"}
)
print(response.json())
```

### Avec JavaScript (fetch)

```javascript
const BASE_URL = 'http://localhost:8000';

// Lister les symboles
fetch(`${BASE_URL}/symbols`)
  .then(res => res.json())
  .then(data => console.log(data));

// Prédiction BTCUSDT
fetch(`${BASE_URL}/predict`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ symbol: 'BTCUSDT' })
})
  .then(res => res.json())
  .then(data => console.log(data));
```

## Interprétation des résultats

### Prédictions

#### Modèles de classification (Random Forest, LSTM)
- `0` : Prédiction de baisse
- `1` : Prédiction de hausse

#### Modèles de séries temporelles (ARIMA, SARIMAX)
- Valeur numérique : Prix prédit en USDT (uniquement pour BTCUSDT)
- `null` : Non disponible (pour ETHUSDT)

### Métriques de performance

#### Pour les modèles de classification (Random Forest, LSTM)
- **accuracy** : Proportion de prédictions correctes (0-1, plus élevé = meilleur)
- **precision** : Proportion de prédictions positives qui sont correctes
- **recall** : Proportion de cas positifs réellement identifiés
- **f1_score** : Moyenne harmonique de precision et recall
- **confusion_matrix** : Matrice de confusion [[vrais négatifs, faux positifs], [faux négatifs, vrais positifs]]

#### Pour les modèles de séries temporelles (ARIMA, SARIMAX)
- **mse** : Mean Squared Error (plus bas = meilleur)
- **mae** : Mean Absolute Error (plus bas = meilleur)
- **rmse** : Root Mean Squared Error (plus bas = meilleur)
- **r2_score** : Coefficient de détermination (0-1, plus élevé = meilleur, 1 = parfait)

## Notes importantes

1. **Données requises** : L'API nécessite que la base de données contienne des données historiques pour les symboles demandés.

2. **Modèles ARIMA/SARIMAX** : Ces modèles ne sont disponibles que pour BTCUSDT car ils sont entraînés uniquement sur cette paire.

3. **Taille des données** : L'API récupère les 100 dernières entrées pour chaque symbole avant de faire les prédictions.

4. **Normalisation** : Les données sont normalisées avant d'être utilisées par les modèles ML.
