"""
Script de diagnostic pour ARIMA et SARIMAX
Permet de tester, entraîner et diagnostiquer les modèles de séries temporelles
"""

import pandas as pd
import numpy as np
import joblib
import os
import sys
from datetime import datetime
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.statespace.sarimax import SARIMAX
from statsmodels.tsa.stattools import adfuller, kpss
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
import matplotlib.pyplot as plt
from sqlalchemy import create_engine, text
from sklearn.metrics import mean_absolute_error, mean_squared_error

def diagnose_data():
    """Diagnostiquer les données BTC disponibles"""
    print("=" * 80)
    print("🔍 DIAGNOSTIC DES DONNÉES BTC")
    print("=" * 80)
    
    # Connexion à la base de données
    db_url = os.getenv("DATABASE_URL", "postgresql://nassim:datascientest@localhost:5432/crypto")
    engine = create_engine(db_url)
    
    try:
        query = """
            SELECT symbol, COUNT(*) as count, 
                   MIN(timestamp) as earliest, 
                   MAX(timestamp) as latest,
                   MIN(close) as min_close,
                   MAX(close) as max_close,
                   AVG(close) as avg_close
            FROM binance_historical_data_with_metrics
            WHERE symbol = 'BTCUSDT'
            GROUP BY symbol
        """
        
        result = pd.read_sql(text(query), engine)
        if not result.empty:
            print(f"✓ Symbol: {result['symbol'].values[0]}")
            print(f"  - Points de données: {result['count'].values[0]}")
            print(f"  - Plage temporelle: {result['earliest'].values[0]} → {result['latest'].values[0]}")
            print(f"  - Prix min: ${result['min_close'].values[0]:.2f}")
            print(f"  - Prix max: ${result['max_close'].values[0]:.2f}")
            print(f"  - Prix moyen: ${result['avg_close'].values[0]:.2f}")
        else:
            print("❌ Aucune donnée BTC trouvée")
            return None
            
        # Charger les données détaillées
        query_data = """
            SELECT timestamp, close FROM binance_historical_data_with_metrics
            WHERE symbol = 'BTCUSDT'
            ORDER BY timestamp ASC
        """
        
        df = pd.read_sql(text(query_data), engine)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        ts = df.set_index('timestamp')['close']
        
        print(f"\n✓ Données chargées: {len(ts)} points")
        print(f"  - NaN: {ts.isnull().sum()}")
        print(f"  - Inf: {np.isinf(ts).sum()}")
        
        return ts
        
    except Exception as e:
        print(f"❌ Erreur lors de la connexion: {e}")
        return None


def test_stationarity(ts, name="Série"):
    """Tester la stationnarité avec ADF et KPSS"""
    print(f"\n📊 Test de stationnarité: {name}")
    print("-" * 60)
    
    try:
        # Test ADF (Augmented Dickey-Fuller)
        adf_result = adfuller(ts.dropna(), autolag='AIC')
        print(f"ADF Test:")
        print(f"  - Statistic: {adf_result[0]:.6f}")
        print(f"  - p-value: {adf_result[1]:.6f}")
        print(f"  - Conclusion: {'Stationnaire' if adf_result[1] < 0.05 else 'Non-stationnaire'}")
        
        # Test KPSS
        kpss_result = kpss(ts.dropna(), regression='c', nlags='auto')
        print(f"\nKPSS Test:")
        print(f"  - Statistic: {kpss_result[0]:.6f}")
        print(f"  - p-value: {kpss_result[1]:.6f}")
        print(f"  - Conclusion: {'Stationnaire' if kpss_result[1] > 0.05 else 'Non-stationnaire'}")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")


def train_and_test_arima(ts, order=(1, 1, 1)):
    """Entraîner et tester ARIMA"""
    print("\n" + "=" * 80)
    print(f"🤖 ENTRAÎNEMENT ARIMA {order}")
    print("=" * 80)
    
    try:
        # Division train/test
        train_size = int(len(ts) * 0.8)
        train, test = ts[:train_size], ts[train_size:]
        
        print(f"✓ Données train: {len(train)}, test: {len(test)}")
        
        # Entraînement
        print(f"\n📌 Entraînement du modèle ARIMA{order}...")
        model = ARIMA(train, order=order)
        model_fit = model.fit()
        
        print(model_fit.summary())
        
        # Test
        print(f"\n📌 Prédictions sur le set de test...")
        forecast = model_fit.forecast(steps=len(test))
        
        mae = mean_absolute_error(test, forecast)
        rmse = np.sqrt(mean_squared_error(test, forecast))
        
        print(f"✓ MAE: {mae:.4f}")
        print(f"✓ RMSE: {rmse:.4f}")
        
        # Prédiction future
        print(f"\n📌 Prédiction pour les 5 prochains jours...")
        future_forecast = model_fit.get_forecast(steps=5)
        print(f"Prédictions:\n{future_forecast.predicted_mean}")
        
        return model_fit, mae, rmse
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return None, None, None


def train_and_test_sarimax(ts, order=(1, 1, 1), seasonal=(1, 1, 1, 7)):
    """Entraîner et tester SARIMAX"""
    print("\n" + "=" * 80)
    print(f"🤖 ENTRAÎNEMENT SARIMAX {order}x{seasonal}")
    print("=" * 80)
    
    try:
        # Division train/test
        train_size = int(len(ts) * 0.8)
        train, test = ts[:train_size], ts[train_size:]
        
        print(f"✓ Données train: {len(train)}, test: {len(test)}")
        
        # Entraînement
        print(f"\n📌 Entraînement du modèle SARIMAX...")
        model = SARIMAX(train, order=order, seasonal_order=seasonal)
        model_fit = model.fit(maxiter=200, disp=False)
        
        print(model_fit.summary())
        
        # Test
        print(f"\n📌 Prédictions sur le set de test...")
        forecast = model_fit.forecast(steps=len(test))
        
        mae = mean_absolute_error(test, forecast)
        rmse = np.sqrt(mean_squared_error(test, forecast))
        
        print(f"✓ MAE: {mae:.4f}")
        print(f"✓ RMSE: {rmse:.4f}")
        
        # Prédiction future
        print(f"\n📌 Prédiction pour les 5 prochains jours...")
        future_forecast = model_fit.get_forecast(steps=5)
        print(f"Prédictions:\n{future_forecast.predicted_mean}")
        
        return model_fit, mae, rmse
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return None, None, None


def compare_models(ts):
    """Comparer différents modèles ARIMA"""
    print("\n" + "=" * 80)
    print("📈 COMPARAISON DE DIFFÉRENTS MODÈLES ARIMA")
    print("=" * 80)
    
    orders = [(1, 0, 0), (0, 1, 1), (1, 1, 1), (2, 1, 2), (1, 1, 2)]
    results = []
    
    train_size = int(len(ts) * 0.8)
    train, test = ts[:train_size], ts[train_size:]
    
    for order in orders:
        try:
            print(f"\nTestage ARIMA{order}...")
            model = ARIMA(train, order=order)
            model_fit = model.fit()
            forecast = model_fit.forecast(steps=len(test))
            mae = mean_absolute_error(test, forecast)
            rmse = np.sqrt(mean_squared_error(test, forecast))
            aic = model_fit.aic
            
            results.append({
                'order': order,
                'MAE': mae,
                'RMSE': rmse,
                'AIC': aic
            })
            
            print(f"✓ MAE: {mae:.4f}, RMSE: {rmse:.4f}, AIC: {aic:.2f}")
            
        except Exception as e:
            print(f"❌ Erreur avec {order}: {e}")
    
    # Afficher le meilleur modèle
    if results:
        best = min(results, key=lambda x: x['MAE'])
        print(f"\n🏆 Meilleur modèle: ARIMA{best['order']} avec MAE={best['MAE']:.4f}")
        
        results_df = pd.DataFrame(results)
        print(f"\nRésumé des résultats:")
        print(results_df.to_string(index=False))


def main():
    """Fonction principale"""
    print("\n" + "🔧 " * 40)
    print("SCRIPT DE DIAGNOSTIC ARIMA/SARIMAX")
    print("🔧 " * 40 + "\n")
    
    # 1. Diagnostiquer les données
    ts = diagnose_data()
    if ts is None:
        return
    
    # 2. Test de stationnarité
    test_stationarity(ts, "Close Price")
    test_stationarity(ts.diff().dropna(), "Différence première (Close)")
    
    # 3. Visualiser les ACF/PACF
    print("\n📊 Génération des graphiques ACF/PACF...")
    try:
        fig, axes = plt.subplots(2, 2, figsize=(12, 8))
        
        plot_acf(ts.dropna(), lags=20, ax=axes[0, 0])
        axes[0, 0].set_title("ACF - Close Price")
        
        plot_pacf(ts.dropna(), lags=20, ax=axes[0, 1])
        axes[0, 1].set_title("PACF - Close Price")
        
        plot_acf(ts.diff().dropna(), lags=20, ax=axes[1, 0])
        axes[1, 0].set_title("ACF - Différence première")
        
        plot_pacf(ts.diff().dropna(), lags=20, ax=axes[1, 1])
        axes[1, 1].set_title("PACF - Différence première")
        
        plt.tight_layout()
        plt.savefig('/tmp/arima_diagnostic.png')
        print("✓ Graphiques sauvegardés: /tmp/arima_diagnostic.png")
    except Exception as e:
        print(f"⚠️ Erreur graphiques: {e}")
    
    # 4. Comparer les modèles
    compare_models(ts)
    
    # 5. Entraîner le meilleur modèle ARIMA
    arima_model, mae_arima, rmse_arima = train_and_test_arima(ts, order=(1, 1, 1))
    
    # 6. Entraîner SARIMAX
    sarimax_model, mae_sarimax, rmse_sarimax = train_and_test_sarimax(ts, order=(1, 1, 1), seasonal=(1, 1, 1, 7))
    
    # 7. Résumé final
    print("\n" + "=" * 80)
    print("📊 RÉSUMÉ FINAL")
    print("=" * 80)
    print(f"ARIMA(1,1,1):     MAE={mae_arima:.4f}, RMSE={rmse_arima:.4f}")
    print(f"SARIMAX(1,1,1)x(1,1,1,7): MAE={mae_sarimax:.4f}, RMSE={rmse_sarimax:.4f}")
    
    if mae_sarimax is not None and mae_sarimax < mae_arima:
        print("\n✓ SARIMAX semble plus performant")
    elif mae_arima is not None:
        print("\n✓ ARIMA semble plus performant")


if __name__ == "__main__":
    main()
