import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import numpy as np
from typing import Optional

# Configuration de la page
st.set_page_config(
    page_title="CryptoBot ML Predictions",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Styles CSS personnalisés
st.markdown("""
    <style>
    .metric-container {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .prediction-true {
        background-color: #d4edda;
        padding: 15px;
        border-radius: 8px;
        border-left: 4px solid #28a745;
    }
    .prediction-false {
        background-color: #f8d7da;
        padding: 15px;
        border-radius: 8px;
        border-left: 4px solid #dc3545;
    }
    </style>
    """, unsafe_allow_html=True)

# ==================== Configuration API ====================
API_BASE_URL = "http://app:8000"
if "API_BASE_URL" not in st.session_state:
    st.session_state.API_BASE_URL = API_BASE_URL


def check_api_health():
    """Vérifie si l'API est accessible."""
    try:
        response = requests.get(f"{st.session_state.API_BASE_URL}/health", timeout=5)
        return response.status_code == 200
    except Exception as e:
        return False


@st.cache_data(ttl=600)
def get_available_symbols():
    """Récupère la liste des symboles disponibles depuis l'API."""
    try:
        response = requests.get(f"{st.session_state.API_BASE_URL}/symbols", timeout=5)
        if response.status_code == 200:
            data = response.json()
            return data.get("symbols", ["BTCUSDT", "ETHUSDT"])
        return ["BTCUSDT", "ETHUSDT"]
    except Exception as e:
        return ["BTCUSDT", "ETHUSDT"]


def get_prediction(symbol: str) -> Optional[dict]:
    """Récupère une prédiction pour un symbole donné."""
    try:
        payload = {"symbol": symbol.upper()}
        response = requests.post(
            f"{st.session_state.API_BASE_URL}/predict",
            json=payload,
            timeout=10
        )
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Erreur API: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        st.error(f"Erreur lors de la récupération de la prédiction: {e}")
        return None


def get_metrics(symbol: str) -> Optional[dict]:
    """Récupère les métriques de performance pour un symbole."""
    try:
        response = requests.get(
            f"{st.session_state.API_BASE_URL}/metrics/{symbol.upper()}",
            timeout=10
        )
        if response.status_code == 200:
            return response.json()
        else:
            st.warning(f"Impossible de récupérer les métriques: {response.status_code}")
            return None
    except Exception as e:
        st.warning(f"Erreur lors de la récupération des métriques: {e}")
        return None


def get_all_metrics() -> Optional[dict]:
    """Récupère les métriques globales pour tous les symboles."""
    try:
        response = requests.get(
            f"{st.session_state.API_BASE_URL}/metrics",
            timeout=10
        )
        if response.status_code == 200:
            return response.json()
        else:
            st.warning(f"Impossible de récupérer les métriques globales: {response.status_code}")
            return None
    except Exception as e:
        st.warning(f"Erreur lors de la récupération des métriques globales: {e}")
        return None


def create_prediction_comparison_chart(prediction_data):
    """Crée un graphique de comparaison des prédictions des modèles."""
    predictions = prediction_data.get("predictions", {})
    
    models = []
    values = []
    colors = []
    
    if "random_forest" in predictions and predictions["random_forest"] is not None:
        rf_val = predictions["random_forest"]
        models.append("Random Forest")
        values.append(1 if rf_val == 1 else 0)
        colors.append("#1f77b4")
    
    if "lstm" in predictions and predictions["lstm"] is not None:
        lstm_val = predictions["lstm"]
        models.append("LSTM")
        values.append(1 if lstm_val == 1 else 0)
        colors.append("#ff7f0e")
    
    fig = go.Figure(data=[
        go.Bar(
            x=models,
            y=values,
            marker_color=colors,
            text=["📈 HAUSSE" if v == 1 else "📉 BAISSE" for v in values],
            textposition="outside",
            hovertemplate="<b>%{x}</b><br>Prédiction: %{text}<extra></extra>"
        )
    ])
    
    fig.update_layout(
        title="Comparaison des Prédictions des Classifieurs",
        xaxis_title="Modèle",
        yaxis_title="Signal (1=Hausse, 0=Baisse)",
        yaxis=dict(range=[0, 1.2]),
        height=400,
        showlegend=False,
        template="plotly_white"
    )
    
    return fig


def create_metrics_comparison_chart(symbols_metrics):
    """Crée un graphique de comparaison des métriques entre modèles."""
    models_data = {
        "Random Forest": [],
        "LSTM": []
    }
    
    symbols_list = []
    
    for symbol, data in symbols_metrics.items():
        if "classification" in data and "error" not in data:
            symbols_list.append(symbol)
            
            class_metrics = data["classification"]
            
            rf_acc = class_metrics.get("random_forest", {}).get("accuracy", 0)
            lstm_acc = class_metrics.get("lstm", {}).get("accuracy", 0)
            
            models_data["Random Forest"].append(rf_acc * 100)
            models_data["LSTM"].append(lstm_acc * 100)
    
    fig = go.Figure(data=[
        go.Bar(name="Random Forest", x=symbols_list, y=models_data["Random Forest"], marker_color="#1f77b4"),
        go.Bar(name="LSTM", x=symbols_list, y=models_data["LSTM"], marker_color="#ff7f0e")
    ])
    
    fig.update_layout(
        title="Comparaison des Accuracies par Modèle et Symbole",
        xaxis_title="Symbole",
        yaxis_title="Accuracy (%)",
        barmode="group",
        height=400,
        template="plotly_white",
        hovermode="x unified"
    )
    
    return fig


def create_prediction_history_chart(df_comparisons, model="random_forest"):
    """Crée un graphique d'historique des prédictions."""
    if df_comparisons.empty:
        return None
    
    correct_col = f"correct_{model}"
    pred_col = f"prediction_{model}"
    actual_col = "actual"
    
    if correct_col not in df_comparisons.columns:
        return None
    
    df_plot = pd.DataFrame({
        'Prédiction': df_comparisons[pred_col],
        'Réalité': df_comparisons[actual_col],
        'Correct': df_comparisons[correct_col],
        'Index': range(len(df_comparisons))
    })
    
    fig = go.Figure()
    
    correct = df_plot[df_plot['Correct'] == 1]
    fig.add_trace(go.Scatter(
        x=correct['Index'],
        y=correct['Réalité'],
        mode='markers',
        name='Correct',
        marker=dict(size=8, color='#28a745', symbol='circle'),
        hovertemplate="<b>Prédiction Correcte</b><br>Index: %{x}<br>Valeur: %{y}<extra></extra>"
    ))
    
    incorrect = df_plot[df_plot['Correct'] == 0]
    fig.add_trace(go.Scatter(
        x=incorrect['Index'],
        y=incorrect['Réalité'],
        mode='markers',
        name='Incorrect',
        marker=dict(size=8, color='#dc3545', symbol='x'),
        hovertemplate="<b>Prédiction Incorrecte</b><br>Index: %{x}<br>Valeur: %{y}<extra></extra>"
    ))
    
    fig.update_layout(
        title=f"Historique des Prédictions - {model.upper()}",
        xaxis_title="Index",
        yaxis_title="Valeur",
        height=400,
        template="plotly_white",
        hovermode="closest"
    )
    
    return fig


def create_historical_and_predictions_chart(symbol: str, current_prediction: dict = None) -> Optional[go.Figure]:
    """Crée un graphique montrant les données historiques et les prédictions des 4 modèles."""
    try:
        response = requests.post(
            f"{st.session_state.API_BASE_URL}/evaluate",
            json={"symbol": symbol, "limit": 500},
            timeout=15
        )
        if response.status_code != 200:
            return None

        data = response.json()
        comparisons = data.get("comparisons", [])
        if not comparisons:
            return None

        df = pd.DataFrame(comparisons)

        # ✅ CORRECTION: Vérifier d'abord si actual_price existe et a des valeurs valides
        if 'actual_price' in df.columns:
            prices = df['actual_price'].astype(float).values
            # Vérifier que les prix sont dans une plage réaliste
            if prices.max() < 100:  # Si les prix sont anormalement bas (normalisés)
                st.warning("⚠️ Les prix semblent être normalisés. Vérifiez l'inverse transformation dans l'API.")
        elif 'price' in df.columns:
            prices = df['price'].astype(float).values
        else:
            # Fallback: utiliser actual mais afficher un warning
            prices = df['actual'].astype(float).values
            if prices.max() < 100:
                st.warning("⚠️ Attention: Les prix affichés semblent être normalisés (0-1). Impossible de dénormaliser sans le scaler.")

        if len(prices) < 2:
            return None

        # ✅ CORRECTION: Utiliser les vrais timestamps si disponibles
        if 'timestamp' in df.columns:
            dates = pd.to_datetime(df['timestamp'])
        else:
            dates = pd.date_range(end=datetime.now(), periods=len(df), freq='D')

        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=dates,
            y=prices,
            mode='lines',
            name='Prix Réel (Historique)',
            line=dict(color='#FF0000', width=3),
            hovertemplate="<b>Prix Réel</b><br>Date: %{x}<br>Prix: $%{y:.2f}<extra></extra>"
        ))

        # ✅ CORRECTION: Utiliser la prédiction passée en paramètre
        if current_prediction:
            predictions_data = current_prediction.get("predictions", {})

            last_date = dates.iloc[-1] if isinstance(dates, pd.Series) else dates[-1]
            future_date = last_date + timedelta(days=1)
            last_actual = float(prices[-1])

            # ✅ CORRECTION: Calculer une volatilité réaliste basée sur les données historiques
            if len(prices) > 30:
                # Calculer le pourcentage moyen de variation sur 30 jours
                # np.diff(prices[-30:]) donne 29 valeurs, donc on divise par prices[-30:-1]
                pct_changes = np.abs(np.diff(prices[-30:]) / prices[-30:-1])
                avg_pct = float(np.mean(pct_changes))
                # Limiter entre 0.5% et 5%
                avg_pct = max(min(avg_pct, 0.05), 0.005)
            else:
                avg_pct = 0.02  # 2% par défaut

            # Fonction pour convertir les prédictions en prix
            def prediction_to_price(pred_val, pred_type="classifier"):
                try:
                    val = float(pred_val)
                except (TypeError, ValueError):
                    return last_actual
                
                # Si c'est déjà un prix (ARIMA/SARIMAX)
                if pred_type == "regression" and val > 10:
                    return val
                
                # Si c'est un classifieur (0 ou 1)
                if pred_type == "classifier":
                    if val == 1:  # Hausse
                        return last_actual * (1 + avg_pct)
                    else:  # Baisse
                        return last_actual * (1 - avg_pct)
                
                return last_actual

            # Récupérer les prédictions
            rf_pred = predictions_data.get("random_forest")
            lstm_pred = predictions_data.get("lstm")
            arima_pred = predictions_data.get("arima")
            sarimax_pred = predictions_data.get("sarimax")

            # Convertir en prix
            rf_price = prediction_to_price(rf_pred, "classifier")
            lstm_price = prediction_to_price(lstm_pred, "classifier")
            arima_price = arima_pred if arima_pred is not None else last_actual
            sarimax_price = sarimax_pred if sarimax_pred is not None else last_actual

            # Ajouter les marqueurs de prédiction
            fig.add_trace(go.Scatter(
                x=[future_date],
                y=[rf_price],
                mode='markers+text',
                name='Random Forest',
                marker=dict(size=12, color='#1f77b4', symbol='star'),
                text=[f'RF: {"↗" if rf_pred == 1 else "↘"}'],
                textposition='top center',
                hovertemplate="<b>Random Forest</b><br>Signal: %{text}<br>Prix estimé: $%{y:.2f}<extra></extra>"
            ))

            fig.add_trace(go.Scatter(
                x=[future_date],
                y=[lstm_price],
                mode='markers+text',
                name='LSTM',
                marker=dict(size=12, color='#ff7f0e', symbol='diamond'),
                text=[f'LSTM: {"↗" if lstm_pred == 1 else "↘"}'],
                textposition='middle right',
                hovertemplate="<b>LSTM</b><br>Signal: %{text}<br>Prix estimé: $%{y:.2f}<extra></extra>"
            ))

            if arima_pred is not None:
                fig.add_trace(go.Scatter(
                    x=[future_date],
                    y=[arima_price],
                    mode='markers+text',
                    name='ARIMA',
                    marker=dict(size=12, color='#2ca02c', symbol='triangle-up'),
                    text=['ARIMA'],
                    textposition='bottom center',
                    hovertemplate="<b>ARIMA</b><br>Prix prédit: $%{y:.2f}<extra></extra>"
                ))

            if sarimax_pred is not None:
                fig.add_trace(go.Scatter(
                    x=[future_date],
                    y=[sarimax_price],
                    mode='markers+text',
                    name='SARIMAX',
                    marker=dict(size=12, color='#d62728', symbol='square'),
                    text=['SARIMAX'],
                    textposition='middle left',
                    hovertemplate="<b>SARIMAX</b><br>Prix prédit: $%{y:.2f}<extra></extra>"
                ))

        fig.update_layout(
            title=f"Historique et Prédictions - {symbol}",
            xaxis_title="Date",
            yaxis_title="Prix ($)",
            hovermode='x unified',
            height=500,
            template="plotly_white",
            xaxis=dict(showgrid=True, gridwidth=1, gridcolor='LightGray'),
            yaxis=dict(showgrid=True, gridwidth=1, gridcolor='LightGray')
        )

        return fig

    except Exception as e:
        st.error(f"Erreur lors de la création du graphique: {e}")
        return None


# ==================== Interface Principale ====================
def main():
    st.title("🤖 CryptoBot - ML Prediction Dashboard")
    st.markdown("Tableau de bord des prédictions machine learning pour les cryptomonnaies")

    if not check_api_health():
        st.error("⚠️ L'API n'est pas accessible. Veuillez vérifier que le service est démarré.")
        st.stop()

    st.sidebar.title("⚙️ Configuration")
    
    api_url_input = st.sidebar.text_input(
        "URL de l'API",
        value=st.session_state.API_BASE_URL,
        help="Adresse de base de l'API (ex: http://localhost:8000)"
    )
    if api_url_input != st.session_state.API_BASE_URL:
        st.session_state.API_BASE_URL = api_url_input
        st.rerun()

    menu = st.sidebar.radio(
        "Navigation",
        ["📊 Prédictions", "📈 Métriques", "📉 Historique", "ℹ️ À propos"]
    )

    # ==================== PAGE: PRÉDICTIONS ====================
    if menu == "📊 Prédictions":
        st.header("Prédictions Actuelles")
        
        symbols = get_available_symbols()
        selected_symbol = st.selectbox(
            "Sélectionnez une cryptomonnaie",
            symbols,
            index=0
        )

        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Obtenir la prédiction", use_container_width=True):
                prediction = get_prediction(selected_symbol)
                if prediction:
                    st.session_state.last_prediction = prediction
                    st.success("Prédiction obtenue avec succès!")

        with col2:
            refresh_interval = st.selectbox(
                "Rafraîchir automatiquement tous les",
                ["Désactiver", "30 secondes", "1 minute", "5 minutes"],
                index=0
            )

        if "last_prediction" in st.session_state:
            pred = st.session_state.last_prediction
            st.markdown("---")
            st.subheader(f"Résultats pour {pred['symbol']}")

            col1, col2, col3, col4 = st.columns(4)

            predictions_data = pred.get("predictions", {})

            with col1:
                rf_pred = predictions_data.get("random_forest", -1)
                direction = "📈 HAUSSE" if rf_pred == 1 else "📉 BAISSE"
                st.metric(
                    "Random Forest",
                    direction,
                    delta="Classifieur"
                )

            with col2:
                lstm_pred = predictions_data.get("lstm", -1)
                direction = "📈 HAUSSE" if lstm_pred == 1 else "📉 BAISSE"
                st.metric(
                    "LSTM",
                    direction,
                    delta="Classifieur"
                )

            with col3:
                arima_pred = predictions_data.get("arima")
                if arima_pred:
                    st.metric(
                        "ARIMA",
                        f"${arima_pred:.2f}",
                        delta="Prédiction prix"
                    )
                else:
                    st.metric(
                        "ARIMA",
                        "N/A",
                        delta="Non disponible"
                    )

            with col4:
                sarimax_pred = predictions_data.get("sarimax")
                if sarimax_pred:
                    st.metric(
                        "SARIMAX",
                        f"${sarimax_pred:.2f}",
                        delta="Prédiction prix"
                    )
                else:
                    st.metric(
                        "SARIMAX",
                        "N/A",
                        delta="Non disponible"
                    )

            st.markdown("---")
            st.subheader("Détails de la Prédiction")
            col1, col2 = st.columns(2)

            with col1:
                st.write(f"**Symbole:** {pred['symbol']}")
                st.write(f"**Heure:** {pred['timestamp']}")

            with col2:
                st.json(predictions_data)
            
            st.markdown("---")
            st.subheader("📊 Comparaison des Prédictions")
            fig = create_prediction_comparison_chart(pred)
            st.plotly_chart(fig, use_container_width=True)
            
            # ✅ CORRECTION: Passer la prédiction courante au graphique
            st.markdown("---")
            st.subheader("📈 Historique et Prédictions")
            fig_historical = create_historical_and_predictions_chart(selected_symbol, pred)
            if fig_historical:
                st.plotly_chart(fig_historical, use_container_width=True)
            else:
                st.info("Impossible de charger le graphique historique. Veuillez réessayer.")

        else:
            st.info("Cliquez sur 'Obtenir la prédiction' pour afficher les résultats.")

    # ==================== PAGE: MÉTRIQUES ====================
    elif menu == "📈 Métriques":
        st.header("Métriques de Performance")

        tab1, tab2 = st.tabs(["Vue globale", "Par symbole"])

        with tab1:
            st.subheader("Performance Globale Tous Modèles")
            if st.button("🔄 Rafraîchir les métriques globales", use_container_width=True):
                metrics = get_all_metrics()
                if metrics:
                    st.session_state.global_metrics = metrics
                    st.success("Métriques mises à jour!")

            if "global_metrics" in st.session_state:
                metrics = st.session_state.global_metrics
                overall = metrics.get("overall_metrics", {})

                st.markdown("### 📊 Graphique Comparatif")
                fig_comparison = create_metrics_comparison_chart(overall)
                st.plotly_chart(fig_comparison, use_container_width=True)

                st.markdown("---")

                for symbol, data in overall.items():
                    st.markdown(f"### {symbol}")

                    if "error" in data:
                        st.error(f"Erreur: {data['error']}")
                    else:
                        if "classification" in data:
                            class_metrics = data["classification"]
                            cols = st.columns(4)

                            with cols[0]:
                                st.metric(
                                    "Random Forest Accuracy",
                                    f"{class_metrics.get('random_forest', {}).get('accuracy', 0):.2%}"
                                )

                            with cols[1]:
                                st.metric(
                                    "LSTM Accuracy",
                                    f"{class_metrics.get('lstm', {}).get('accuracy', 0):.2%}"
                                )

                            with cols[2]:
                                st.metric(
                                    "Random Forest F1",
                                    f"{class_metrics.get('random_forest', {}).get('f1_score', 0):.3f}"
                                )

                            with cols[3]:
                                st.metric(
                                    "LSTM F1",
                                    f"{class_metrics.get('lstm', {}).get('f1_score', 0):.3f}"
                                )

                        if "time_series" in data:
                            st.markdown("#### Modèles Séries Temporelles")
                            ts_metrics = data["time_series"]

                            if "error" not in ts_metrics:
                                ts_cols = st.columns(2)
                                with ts_cols[0]:
                                    if "arima" in ts_metrics:
                                        st.metric(
                                            "ARIMA MAE",
                                            f"{ts_metrics['arima'].get('mae', 0):.2f}"
                                        )

                                with ts_cols[1]:
                                    if "sarimax" in ts_metrics:
                                        st.metric(
                                            "SARIMAX MAE",
                                            f"{ts_metrics['sarimax'].get('mae', 0):.2f}"
                                        )
                            else:
                                st.warning(f"Pas de données pour séries temporelles: {ts_metrics.get('error')}")

            else:
                st.info("Cliquez sur 'Rafraîchir les métriques globales' pour charger les données.")

        with tab2:
            st.subheader("Métriques par Symbole")
            symbols = get_available_symbols()
            selected_symbol = st.selectbox(
                "Sélectionnez un symbole",
                symbols,
                key="metrics_symbol_select"
            )

            if st.button("🔄 Charger les métriques", use_container_width=True):
                metrics = get_metrics(selected_symbol)
                if metrics:
                    st.session_state.symbol_metrics = {selected_symbol: metrics}
                    st.success(f"Métriques pour {selected_symbol} chargées!")

            if "symbol_metrics" in st.session_state and selected_symbol in st.session_state.symbol_metrics:
                metrics = st.session_state.symbol_metrics[selected_symbol]

                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Nombre d'échantillons", metrics.get("test_samples", 0))

                if "classification" in metrics:
                    class_metrics = metrics["classification"]
                    with col2:
                        st.metric(
                            "Random Forest Accuracy",
                            f"{class_metrics.get('random_forest', {}).get('accuracy', 0):.2%}"
                        )
                    with col3:
                        st.metric(
                            "LSTM Accuracy",
                            f"{class_metrics.get('lstm', {}).get('accuracy', 0):.2%}"
                        )

                st.markdown("---")
                st.write(metrics)

            else:
                st.info(f"Cliquez sur 'Charger les métriques' pour afficher les données de {selected_symbol}.")

    # ==================== PAGE: HISTORIQUE ====================
    elif menu == "📉 Historique":
        st.header("Historique et Comparaisons")
        st.info("Cette section affichera l'historique des prédictions et les comparaisons avec les valeurs réelles.")

        symbols = get_available_symbols()
        selected_symbol = st.selectbox(
            "Sélectionnez un symbole",
            symbols,
            key="history_symbol_select"
        )

        num_samples = st.slider(
            "Nombre d'échantillons à comparer",
            min_value=10,
            max_value=500,
            value=50,
            step=10
        )

        if st.button("📊 Charger l'historique", use_container_width=True):
            try:
                response = requests.post(
                    f"{st.session_state.API_BASE_URL}/evaluate",
                    json={"symbol": selected_symbol, "limit": num_samples},
                    timeout=15
                )
                if response.status_code == 200:
                    data = response.json()
                    st.session_state.evaluation_data = data
                    st.success("Données chargées!")
                else:
                    st.error(f"Erreur: {response.status_code}")
            except Exception as e:
                st.error(f"Erreur lors du chargement: {e}")

        if "evaluation_data" in st.session_state:
            eval_data = st.session_state.evaluation_data
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total d'échantillons", eval_data.get("total_samples", 0))
            with col2:
                summary = eval_data.get("summary", {})
                st.metric(
                    "Random Forest Accuracy",
                    f"{summary.get('random_forest_accuracy', 0):.2%}"
                )
            with col3:
                st.metric(
                    "LSTM Accuracy",
                    f"{summary.get('lstm_accuracy', 0):.2%}"
                )

            st.markdown("---")
            st.subheader("Détails des Prédictions")
            comparisons = eval_data.get("comparisons", [])
            if comparisons:
                df_comparisons = pd.DataFrame(comparisons)
                
                tab1, tab2, tab3 = st.tabs(["Tableau", "Random Forest", "LSTM"])
                
                with tab1:
                    st.dataframe(df_comparisons, use_container_width=True)

                with tab2:
                    fig_rf = create_prediction_history_chart(df_comparisons, "random_forest")
                    if fig_rf:
                        st.plotly_chart(fig_rf, use_container_width=True)
                    else:
                        st.warning("Impossible de créer le graphique Random Forest")

                with tab3:
                    fig_lstm = create_prediction_history_chart(df_comparisons, "lstm")
                    if fig_lstm:
                        st.plotly_chart(fig_lstm, use_container_width=True)
                    else:
                        st.warning("Impossible de créer le graphique LSTM")

                st.markdown("---")
                csv = df_comparisons.to_csv(index=False)
                st.download_button(
                    label="📥 Télécharger CSV",
                    data=csv,
                    file_name=f"predictions_{selected_symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
            else:
                st.warning("Aucune donnée de comparaison disponible.")

    # ==================== PAGE: À PROPOS ====================
    elif menu == "ℹ️ À propos":
        st.header("À Propos de CryptoBot")

        st.markdown("""
        ### 📱 Vue d'ensemble
        CryptoBot est une application de prédiction des mouvements des cryptomonnaies basée sur le machine learning.
        Elle utilise plusieurs modèles pour fournir des prédictions robustes.

        ### 🤖 Modèles Disponibles
        
        **Classifieurs (Prédiction de direction: Hausse/Baisse)**
        - **Random Forest**: Classifieur d'ensemble robuste
        - **LSTM (Long Short-Term Memory)**: Réseau de neurones pour séries temporelles
        
        **Régresseurs (Prédiction de prix)**
        - **ARIMA**: Modèle autorégressif intégré à moyenne mobile
        - **SARIMAX**: ARIMA saisonnier avec composantes exogènes
        
        ### 💰 Cryptomonnaies Supportées
        """)

        symbols = get_available_symbols()
        for symbol in symbols:
            st.markdown(f"- **{symbol}**")

        st.markdown("""
        ### 📊 Fonctionnalités
        1. **Prédictions en Temps Réel**: Obtenez des prédictions instantanées pour les cryptomonnaies
        2. **Métriques de Performance**: Consultez l'accuracy et d'autres métriques des modèles
        3. **Historique**: Comparez les prédictions avec les valeurs réelles
        4. **Tableau de Bord**: Interface intuitive et conviviale

        ### 🏗️ Architecture
        - **Backend**: FastAPI (Python)
        - **Frontend**: Streamlit
        - **Base de Données**: PostgreSQL
        - **ML Models**: TensorFlow, Scikit-learn, Statsmodels

        ### 📧 Support
        Pour toute question ou problème, veuillez contacter l'équipe de développement.
        """)

        st.markdown("---")
        st.markdown("**Version**: 1.0.0  |  **Dernière mise à jour**: 2026-01-24")


if __name__ == "__main__":
    main()