"""
Running Coach Dashboard - Streamlit App
Visualisation des donnees d'entrainement polarise
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta
import os

# Import des fonctions du module principal
import main

# Configuration de la page
st.set_page_config(
    page_title="Running Coach",
    page_icon="🏃",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Style CSS personnalise
st.markdown("""
<style>
    .metric-card {
        background-color: #1e1e1e;
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
    }
    .status-green { color: #00ff00; }
    .status-orange { color: #ffa500; }
    .status-red { color: #ff0000; }
    .big-number {
        font-size: 2.5em;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)


def get_acwr_color(acwr: float) -> str:
    """Retourne la couleur selon la valeur ACWR."""
    if acwr < 0.8:
        return "blue"  # Sous-entrainement
    elif acwr <= 1.3:
        return "green"  # Optimal
    elif acwr <= 1.5:
        return "orange"  # Attention
    else:
        return "red"  # Danger


def get_tsb_color(tsb: float) -> str:
    """Retourne la couleur selon la valeur TSB."""
    if tsb > 10:
        return "blue"  # Tres repose
    elif tsb > -5:
        return "green"  # Forme optimale
    elif tsb > -15:
        return "orange"  # Fatigue moderee
    else:
        return "red"  # Fatigue importante


def create_gauge(value: float, title: str, min_val: float, max_val: float,
                 thresholds: list = None, colors: list = None) -> go.Figure:
    """Cree une jauge Plotly."""
    if thresholds is None:
        thresholds = [min_val, max_val]
    if colors is None:
        colors = ["green"]

    # Construire les steps pour les couleurs
    steps = []
    for i in range(len(thresholds) - 1):
        steps.append({
            'range': [thresholds[i], thresholds[i + 1]],
            'color': colors[i] if i < len(colors) else "gray"
        })

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        title={'text': title, 'font': {'size': 16}},
        gauge={
            'axis': {'range': [min_val, max_val], 'tickwidth': 1},
            'bar': {'color': "white"},
            'steps': steps,
            'threshold': {
                'line': {'color': "white", 'width': 2},
                'thickness': 0.75,
                'value': value
            }
        }
    ))

    fig.update_layout(
        height=200,
        margin=dict(l=20, r=20, t=40, b=20),
        paper_bgcolor='rgba(0,0,0,0)',
        font={'color': 'white'}
    )

    return fig


def main_dashboard():
    """Fonction principale du dashboard."""

    st.title("Running Coach Dashboard")
    st.caption(f"Version {main.VERSION} - Polarized Data-Driven Training")

    # Verification des credentials
    if not os.environ.get('API_KEY') or not os.environ.get('ATHLETE_ID'):
        st.error("Variables d'environnement API_KEY et ATHLETE_ID requises")
        st.info("Configurez les variables dans le fichier .env ou docker-compose.yml")
        return

    # Recuperation des donnees
    with st.spinner("Chargement des donnees..."):
        wellness = main.get_current_wellness()
        distribution = main.get_distribution(21)
        next_workout = main.get_next_workout_info()
        activity_history = main.get_activity_history(30)
        wellness_history = main.get_wellness_history(30)
        weekly_tss = main.get_weekly_tss(8)

    # Verification des erreurs
    if 'error' in wellness:
        st.error(f"Erreur wellness: {wellness['error']}")
        return

    # ========================================
    # LIGNE 1: Metriques principales
    # ========================================
    st.subheader("Etat de forme")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        tsb_color = get_tsb_color(wellness['tsb'])
        st.metric(
            label="CTL (Fitness)",
            value=f"{wellness['ctl']:.1f}",
            help="Chronic Training Load - Charge chronique sur 42 jours"
        )

    with col2:
        st.metric(
            label="ATL (Fatigue)",
            value=f"{wellness['atl']:.1f}",
            help="Acute Training Load - Charge aigue sur 7 jours"
        )

    with col3:
        delta_color = "normal" if wellness['tsb'] > -10 else "inverse"
        st.metric(
            label="TSB (Forme)",
            value=f"{wellness['tsb']:.1f}",
            delta=f"{'Repose' if wellness['tsb'] > 5 else 'Fatigue' if wellness['tsb'] < -10 else 'Normal'}",
            delta_color=delta_color,
            help="Training Stress Balance - Equilibre forme/fatigue"
        )

    with col4:
        acwr_color = get_acwr_color(wellness['acwr'])
        acwr_status = "Optimal" if 0.8 <= wellness['acwr'] <= 1.3 else "Attention" if wellness['acwr'] <= 1.5 else "Danger"
        st.metric(
            label="ACWR (Risque)",
            value=f"{wellness['acwr']:.2f}",
            delta=acwr_status,
            delta_color="normal" if acwr_status == "Optimal" else "inverse",
            help="Acute:Chronic Workload Ratio - Ratio risque blessure"
        )

    # ========================================
    # LIGNE 2: Jauges et Distribution
    # ========================================
    st.divider()

    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        st.subheader("Risque Blessure (ACWR)")
        fig_acwr = create_gauge(
            value=wellness['acwr'],
            title="ACWR",
            min_val=0,
            max_val=2.0,
            thresholds=[0, 0.8, 1.3, 1.5, 2.0],
            colors=["#3498db", "#2ecc71", "#f39c12", "#e74c3c"]
        )
        st.plotly_chart(fig_acwr, use_container_width=True)

        # Legende ACWR
        st.caption("""
        - **< 0.8**: Sous-entrainement
        - **0.8-1.3**: Zone optimale
        - **1.3-1.5**: Attention requise
        - **> 1.5**: Risque eleve
        """)

    with col2:
        st.subheader("Forme (TSB)")
        fig_tsb = create_gauge(
            value=wellness['tsb'],
            title="TSB",
            min_val=-30,
            max_val=30,
            thresholds=[-30, -15, -5, 10, 30],
            colors=["#e74c3c", "#f39c12", "#2ecc71", "#3498db"]
        )
        st.plotly_chart(fig_tsb, use_container_width=True)

        # Legende TSB
        st.caption("""
        - **< -15**: Fatigue importante
        - **-15 a -5**: Fatigue moderee
        - **-5 a 10**: Forme optimale
        - **> 10**: Tres repose
        """)

    with col3:
        st.subheader("Distribution Polarisee (21j)")

        if 'error' not in distribution:
            # Donut chart
            fig_dist = go.Figure(data=[go.Pie(
                labels=['Easy', 'Hard'],
                values=[distribution['easy_count'], distribution['hard_count']],
                hole=.6,
                marker_colors=['#2ecc71', '#e74c3c'],
                textinfo='label+percent',
                textposition='outside'
            )])

            # Ajouter texte central
            fig_dist.add_annotation(
                text=f"{distribution['easy_percent']:.0f}%<br>Easy",
                x=0.5, y=0.5,
                font_size=16,
                showarrow=False
            )

            fig_dist.update_layout(
                height=250,
                margin=dict(l=20, r=20, t=20, b=20),
                paper_bgcolor='rgba(0,0,0,0)',
                showlegend=False
            )

            st.plotly_chart(fig_dist, use_container_width=True)

            # Indicateur cible
            target_diff = distribution['easy_percent'] - 80
            if abs(target_diff) <= 5:
                st.success(f"Distribution: {distribution['easy_percent']:.0f}/{distribution['hard_percent']:.0f} - Cible 80/20 OK")
            elif target_diff > 5:
                st.info(f"Distribution: {distribution['easy_percent']:.0f}/{distribution['hard_percent']:.0f} - Plus de hard possible")
            else:
                st.warning(f"Distribution: {distribution['easy_percent']:.0f}/{distribution['hard_percent']:.0f} - Trop de hard")

    # ========================================
    # LIGNE 3: Prochaine seance
    # ========================================
    st.divider()
    st.subheader("Prochaine Seance")

    if 'error' not in next_workout:
        col1, col2 = st.columns([2, 1])

        with col1:
            workout_date = datetime.fromisoformat(next_workout['date'])
            st.markdown(f"### {workout_date.strftime('%A %d %B %Y')}")

            if next_workout['type'] == 'rest':
                st.info(f"**Repos** - {next_workout['reason']}")
            else:
                workout_type_display = {
                    'recovery': 'Recuperation',
                    'easy': 'Endurance Facile',
                    'long_run': 'Sortie Longue',
                    'intervals': 'Fractionne VO2max',
                    'intervals_long': 'Fractionne Seuil'
                }.get(next_workout['type'], next_workout['type'])

                st.success(f"**{workout_type_display}**")

                cols = st.columns(4)
                cols[0].metric("Duree", f"{next_workout['duration']} min")
                cols[1].metric("Distance", f"{next_workout['distance']} km")
                cols[2].metric("TSS", str(next_workout['tss']))
                cols[3].metric("Type", next_workout['category'].upper())

                # Raison de la decision
                with st.expander("Voir le raisonnement"):
                    st.markdown("**Facteurs de decision:**")
                    for factor in next_workout.get('decision_factors', []):
                        st.write(f"- {factor}")

                    st.markdown("**Logique de selection:**")
                    for log in next_workout.get('decision_log', []):
                        st.write(f"- {log}")

        with col2:
            # Meteo si disponible
            if next_workout.get('weather'):
                weather = next_workout['weather']
                st.markdown("**Meteo prevue:**")
                st.write(f"- {weather.get('description', '').capitalize()}")
                st.write(f"- Temperature: {weather.get('temp', 0):.1f} C")
                st.write(f"- Ressenti: {weather.get('feels_like', 0):.1f} C")
                st.write(f"- Humidite: {weather.get('humidity', 0)}%")

                if weather.get('advice'):
                    if weather.get('adjustment_factor', 1.0) < 1.0:
                        st.warning(f"Conseil: {weather['advice']}")
                    else:
                        st.info(f"Conseil: {weather['advice']}")
    else:
        st.error(f"Erreur: {next_workout.get('error', 'Inconnue')}")

    # ========================================
    # LIGNE 4: Evolution sur 30 jours
    # ========================================
    st.divider()
    st.subheader("Evolution sur 30 jours")

    if wellness_history:
        df_wellness = pd.DataFrame(wellness_history)
        df_wellness['date'] = pd.to_datetime(df_wellness['date'])

        fig_evolution = go.Figure()

        fig_evolution.add_trace(go.Scatter(
            x=df_wellness['date'],
            y=df_wellness['ctl'],
            mode='lines',
            name='CTL (Fitness)',
            line=dict(color='#3498db', width=2)
        ))

        fig_evolution.add_trace(go.Scatter(
            x=df_wellness['date'],
            y=df_wellness['atl'],
            mode='lines',
            name='ATL (Fatigue)',
            line=dict(color='#e74c3c', width=2)
        ))

        fig_evolution.add_trace(go.Scatter(
            x=df_wellness['date'],
            y=df_wellness['tsb'],
            mode='lines+markers',
            name='TSB (Forme)',
            line=dict(color='#2ecc71', width=2),
            fill='tozeroy',
            fillcolor='rgba(46, 204, 113, 0.1)'
        ))

        # Ligne zero pour TSB
        fig_evolution.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)

        fig_evolution.update_layout(
            height=400,
            margin=dict(l=20, r=20, t=20, b=20),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)'),
            yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)')
        )

        st.plotly_chart(fig_evolution, use_container_width=True)

    # ========================================
    # LIGNE 5: Historique et TSS/semaine
    # ========================================
    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Historique des courses (30j)")

        if activity_history:
            df_activities = pd.DataFrame(activity_history)
            df_display = df_activities[['date', 'name', 'distance_km', 'duration_min', 'tss']].copy()
            df_display.columns = ['Date', 'Nom', 'Distance (km)', 'Duree (min)', 'TSS']
            st.dataframe(df_display, hide_index=True, use_container_width=True)
        else:
            st.info("Aucune activite trouvee")

    with col2:
        st.subheader("TSS par semaine")

        if weekly_tss:
            df_weekly = pd.DataFrame(weekly_tss)
            df_weekly['week_label'] = df_weekly['week'].apply(
                lambda w: f"S-{w}" if w > 0 else "Cette semaine"
            )

            fig_weekly = go.Figure(data=[
                go.Bar(
                    x=df_weekly['week_label'],
                    y=df_weekly['tss'],
                    marker_color='#3498db',
                    text=df_weekly['tss'],
                    textposition='auto'
                )
            ])

            fig_weekly.update_layout(
                height=300,
                margin=dict(l=20, r=20, t=20, b=20),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                xaxis=dict(showgrid=False),
                yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)')
            )

            st.plotly_chart(fig_weekly, use_container_width=True)

            # Stats resumees
            total_tss = sum(w['tss'] for w in weekly_tss)
            avg_tss = total_tss / len(weekly_tss) if weekly_tss else 0
            st.caption(f"Moyenne: {avg_tss:.0f} TSS/semaine | Total 8 semaines: {total_tss:.0f} TSS")

    # ========================================
    # Footer
    # ========================================
    st.divider()
    st.caption(f"Derniere mise a jour: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    st.caption("Running Coach - Polarized Data-Driven Training")


if __name__ == "__main__":
    main_dashboard()
