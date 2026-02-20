# 📚 Guide ARIMA/SARIMAX - Diagnostic et Solutions

## 🔴 Problèmes Trouvés

### 1. **Format de Données**
**Problème** : Passage d'un DataFrame au lieu d'une Series
```python
# ❌ AVANT (incorrect)
ts_data = ts_data.set_index('timestamp').asfreq('D').ffill().bfill()  # DataFrame

# ✅ APRÈS (correct)
ts_series = ts_df.set_index('timestamp')['close']  # Series
```

### 2. **Gestion des Erreurs**
**Problème** : Les exceptions étaient silencieuses, impossible de déboguer
```python
# ❌ AVANT - Erreur invisible
except Exception as e:
    print(f"Erreur lors de l'entraînement: {e}")
    # Continue sans rien faire...

# ✅ APRÈS - Diagnostic complet
except Exception as e:
    print(f"❌ Erreur: {e}")
    print(f"Type: {type(e).__name__}")
    traceback.print_exc()  # Stack trace complet
```

### 3. **Prédictions Non-Stationnaires**
**Problème** : Les séries de crypto n'étaient pas stationnaires
**Solution** : Différenciation (d=1) dans ARIMA

### 4. **Manque de Données**
**Problème** : Besoin d'au moins 50-100 points pour un bon entraînement
**Vérification** : Script ajouté pour diagnostiquer les données

---

## 🔧 Corrections Apportées

### A. Script d'Entraînement (`02_train_models.py`)
✅ Meilleure gestion des données temporelles
✅ Affichage détaillé du processus
✅ Vérification de la stationnarité
✅ Calcul des MAE pour validation

### B. Endpoint API (`main.py`)
✅ Utilisation de `.get_forecast()` au lieu de `.forecast()`
✅ Gestion améliorée des erreurs
✅ Messages de diagnostic
✅ Retour des raisons d'échec

### C. Script de Diagnostic (`diagnostic_arima.py`) - **NOUVEAU**
✅ Analyse complète des données
✅ Test de stationnarité (ADF, KPSS)
✅ Comparaison de multiples modèles ARIMA
✅ Graphiques ACF/PACF
✅ Recommandations automatiques

---

## 📊 Comment Utiliser le Diagnostic

### 1. **Entrer dans le conteneur**
```bash
cd /home/nassbuntu/projet/AVR25-CDE-OPA-1/cryptobot/prod
sudo docker-compose exec app bash
```

### 2. **Exécuter le diagnostic**
```bash
python scripts/diagnostic_arima.py
```

### 3. **Résultats attendus**

```
🔍 DIAGNOSTIC DES DONNÉES BTC
================================================================================
✓ Symbol: BTCUSDT
  - Points de données: 150
  - Plage temporelle: 2024-10-01 → 2026-01-18
  - Prix min: $28000.00
  - Prix max: $45000.00
  - Prix moyen: $35000.00

📊 Test de stationnarité
================================================================================
ADF Test:
  - Statistic: -1.234567
  - p-value: 0.123456
  - Conclusion: Non-stationnaire

KPSS Test:
  - Statistic: 0.654321
  - p-value: 0.010000
  - Conclusion: Non-stationnaire

📈 COMPARAISON DE DIFFÉRENTS MODÈLES ARIMA
================================================================================
Testage ARIMA(1,0,0)...
✓ MAE: 1234.56, RMSE: 1567.89, AIC: 2345.67

Testage ARIMA(0,1,1)...
✓ MAE: 980.45, RMSE: 1234.56, AIC: 2234.56

Testage ARIMA(1,1,1)...
✓ MAE: 856.23, RMSE: 1089.45, AIC: 2123.45

🏆 Meilleur modèle: ARIMA(1,1,1) avec MAE=856.23
```

---

## 🎯 Recommandations ARIMA/SARIMAX

### Pour les Cryptomonnaies

| Modèle | Ordre Recommandé | Quand l'utiliser |
|--------|-----------------|-----------------|
| **ARIMA** | (1,1,1) | Données stables, pas de saisonnalité |
| **SARIMAX** | (1,1,1)x(1,1,1,7) | Données avec saisonnalité hebdomadaire |
| **ARIMA** | (2,1,2) | Volatilité élevée (testé d'abord) |

### Paramètres Expliqués

**ARIMA(p,d,q)**:
- **p=1** : AutoRegressive - utilise 1 valeur précédente
- **d=1** : Intégration - première différence (rend stationnaire)
- **q=1** : Moving Average - utilise 1 erreur précédente

**SARIMAX(p,d,q)x(P,D,Q,s)**:
- **s=7** : Saisonnalité hebdomadaire
- **P,D,Q** : Paramètres saisonniers (généralement 1,1,1 ou 0,0,1)

---

## 🚨 Dépannage Courant

### Erreur: "ValueError: Unable to initialize statespace representation"
**Cause** : Données avec NaN ou Inf
**Solution** : 
```python
ts = ts.dropna()  # Supprimer NaN
ts = ts[np.isfinite(ts)]  # Supprimer Inf
```

### Erreur: "x0 does not have the correct shape"
**Cause** : Les données ne sont pas une pandas Series
**Solution** :
```python
ts = ts_df.set_index('timestamp')['close']  # Assurer que c'est une Series
```

### Prédictions complètement fausses
**Cause** : Pas assez de données ou mauvais ordre (p,d,q)
**Solution** :
1. Vérifier >= 50 points
2. Tester différents ordres avec le diagnostic
3. Augmenter d pour plus de différenciation

### Temps d'entraînement très long (> 5 min)
**Cause** : Trop de données ou paramètres trop complexes
**Solution** :
```python
model = SARIMAX(...)
model.fit(maxiter=100, disp=False)  # Réduire itérations
```

---

## 📈 Résultats Attendus

Après les corrections, vous devriez voir :

### Dans les logs d'entraînement
```
✓ Modèle ARIMA entraîné et sauvegardé.
  MAE sur test set: 856.23
  Résumé:
                           SARIMAX Results
================================================================================
Dep. Variable:                    close   No. Observations:                  120
Model:                 ARIMA(1, 1, 1)   Log Likelihood               -2345.67
Method:                       css-mle   AIC                           4699.34
  ...
```

### Dans les prédictions API
```json
{
  "symbol": "BTCUSDT",
  "predictions": {
    "random_forest": 1,
    "lstm": 1,
    "arima": 42500.50,
    "sarimax": 42480.25
  },
  "notes": {
    "arima_note": null,
    "sarimax_note": null
  }
}
```

---

## 🎓 Ressources Additionnelles

- **Stationarité** : https://en.wikipedia.org/wiki/Stationary_process
- **ARIMA** : https://otexts.com/fpp2/arima.html
- **SARIMAX** : https://www.statsmodels.org/stable/generated/statsmodels.tsa.statespace.sarimax.SARIMAX.html
- **Données Crypto** : Consultez [API Documentation](API_USAGE.md)

---

## ✅ Checklist de Vérification

Avant de conclure que ARIMA/SARIMAX ne fonctionne pas :

- [ ] Exécuter le script diagnostic_arima.py
- [ ] Vérifier >= 50 points de données BTC
- [ ] Vérifier pas de NaN/Inf dans les données
- [ ] Tester différents ordres (p,d,q)
- [ ] Vérifier les MAE/RMSE sur le test set
- [ ] Consulter les graphiques ACF/PACF
- [ ] Comparer avec les logs d'entraînement

---

**Dernière mise à jour**: 2026-01-18
**Statut**: ✅ Corrections appliquées et testées
