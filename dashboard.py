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
    initial_sidebar_state="expanded"
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

    # Selecteur de periode
    period_options = {
        "7 jours": 7,
        "30 jours": 30,
        "90 jours": 90,
        "180 jours": 180,
        "1 an": 365
    }
    selected_period = st.selectbox(
        "Periode d'analyse",
        options=list(period_options.keys()),
        index=1  # 30 jours par defaut
    )
    days = period_options[selected_period]

    # Recuperation des donnees
    with st.spinner("Chargement des donnees..."):
        wellness = main.get_current_wellness()
        distribution = main.get_distribution(21)
        today_workout = main.get_today_workout()
        next_workout = main.get_next_workout_info()
        activity_history = main.get_activity_history(days)
        wellness_history = main.get_wellness_history_with_acwr(days)
        weekly_tss = main.get_weekly_tss(8)
        readiness = main.get_readiness_score()

    # Verification des erreurs
    if 'error' in wellness:
        st.error(f"Erreur wellness: {wellness['error']}")
        return

    # ========================================
    # SIDEBAR: Readiness Score et Recuperation
    # ========================================
    st.sidebar.header("Readiness Score")

    if 'error' not in readiness:
        score = readiness.get('readiness_score', 1.0)
        status = readiness.get('status', 'N/A')

        # Couleur selon le score
        if score >= 1.0:
            score_color = "normal"
        elif score >= 0.85:
            score_color = "off"
        elif score >= 0.7:
            score_color = "inverse"
        else:
            score_color = "inverse"

        st.sidebar.metric(
            "Score Global",
            f"{score:.0%}",
            delta=status,
            delta_color=score_color,
            help="Score base sur TSB, sommeil, FC repos, ACWR et rampRate"
        )

        # Composants du score
        components = readiness.get('components', {})

        # Sommeil
        if components.get('sleep', {}).get('avg_3d'):
            sleep_avg = components['sleep']['avg_3d']
            sleep_color = "normal" if sleep_avg >= 7 else "inverse" if sleep_avg < 6 else "off"
            st.sidebar.metric(
                "Sommeil (3j)",
                f"{sleep_avg:.1f}h/nuit",
                delta="OK" if sleep_avg >= 7 else "Deficit" if sleep_avg < 6 else "Limite",
                delta_color=sleep_color
            )

        # FC Repos
        if components.get('resting_hr', {}).get('value'):
            hr_val = components['resting_hr']['value']
            hr_baseline = components['resting_hr'].get('baseline', hr_val)
            hr_elevation = components['resting_hr'].get('elevation', 0)
            hr_color = "normal" if hr_elevation < 5 else "inverse" if hr_elevation >= 7 else "off"
            st.sidebar.metric(
                "FC Repos",
                f"{hr_val} bpm",
                delta=f"+{hr_elevation:.0f} vs baseline" if hr_elevation > 0 else "Normal",
                delta_color=hr_color,
                help=f"Baseline: {hr_baseline:.0f} bpm (mediane 14j)"
            )

        # Recommandations
        recommendations = readiness.get('recommendations', [])
        if recommendations:
            st.sidebar.markdown("**Recommandations:**")
            for rec in recommendations[:3]:  # Max 3
                st.sidebar.caption(f"• {rec}")

        st.sidebar.divider()

    # ========================================
    # SIDEBAR: Etat a une date precise
    # ========================================
    if wellness_history:
        df_sidebar = pd.DataFrame(wellness_history)
        df_sidebar['date'] = pd.to_datetime(df_sidebar['date'])

        st.sidebar.header("Etat a une date")
        selected_date = st.sidebar.date_input(
            "Selectionner une date",
            value=datetime.now().date(),
            min_value=df_sidebar['date'].min().date(),
            max_value=df_sidebar['date'].max().date()
        )

        # Filtrer les donnees pour cette date
        date_data = df_sidebar[df_sidebar['date'].dt.date == selected_date]
        if not date_data.empty:
            row = date_data.iloc[0]
            st.sidebar.metric("CTL (Fitness)", f"{row['ctl']:.1f}")
            st.sidebar.metric("ATL (Fatigue)", f"{row['atl']:.1f}")
            st.sidebar.metric("TSB (Forme)", f"{row['tsb']:.1f}")

            # Colorer ACWR selon la zone
            acwr_val = row['acwr']
            if acwr_val < 0.8:
                acwr_status = "Sous-entrainement"
                acwr_delta_color = "off"
            elif acwr_val <= 1.3:
                acwr_status = "Optimal"
                acwr_delta_color = "normal"
            elif acwr_val <= 1.5:
                acwr_status = "Attention"
                acwr_delta_color = "inverse"
            else:
                acwr_status = "Danger"
                acwr_delta_color = "inverse"

            st.sidebar.metric(
                "ACWR (Risque)",
                f"{acwr_val:.2f}",
                delta=acwr_status,
                delta_color=acwr_delta_color
            )
        else:
            st.sidebar.info("Pas de donnees pour cette date")

        st.sidebar.divider()
        st.sidebar.caption(f"Donnees disponibles: {df_sidebar['date'].min().strftime('%d/%m/%Y')} - {df_sidebar['date'].max().strftime('%d/%m/%Y')}")

    # ========================================
    # LIGNE 1: Metriques principales
    # ========================================
    st.subheader("Etat de forme")

    col1, col2, col3, col4, col5 = st.columns(5)

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

    with col5:
        if 'error' not in readiness:
            r_score = readiness.get('readiness_score', 1.0)
            r_status = readiness.get('status', 'N/A')
            r_color = "normal" if r_score >= 0.85 else "inverse"
            st.metric(
                label="Readiness",
                value=f"{r_score:.0%}",
                delta=r_status,
                delta_color=r_color,
                help="Score de preparation multi-facteurs (TSB, sommeil, FC repos, ACWR)"
            )
        else:
            st.metric(label="Readiness", value="N/A")

    # ========================================
    # LIGNE 2: Jauges et Distribution
    # ========================================
    st.divider()

    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])

    with col1:
        st.subheader("Readiness Score")
        if 'error' not in readiness:
            fig_readiness = create_gauge(
                value=readiness.get('readiness_score', 1.0) * 100,
                title="Readiness",
                min_val=50,
                max_val=110,
                thresholds=[50, 70, 85, 100, 110],
                colors=["#e74c3c", "#f39c12", "#2ecc71", "#3498db"]
            )
            st.plotly_chart(fig_readiness, use_container_width=True)

            # Legende Readiness
            st.caption("""
            - **< 70%**: Repos recommande
            - **70-85%**: Prudence
            - **85-100%**: Pret
            - **> 100%**: Optimal
            """)
        else:
            st.warning("Score non disponible")

    with col2:
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

    with col3:
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

    with col4:
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
    # LIGNE 3: Seances Planifiees (Aujourd'hui + Demain)
    # ========================================
    st.divider()
    st.subheader("Seances Planifiees")

    workout_type_display_map = {
        'recovery': 'Recuperation',
        'easy': 'Endurance Facile',
        'long_run': 'Sortie Longue',
        'intervals': 'Fractionne VO2max',
        'intervals_long': 'Fractionne Seuil'
    }

    # --- AUJOURD'HUI ---
    st.markdown("#### Aujourd'hui")
    if today_workout:
        workout_date = datetime.fromisoformat(today_workout['date'])
        st.caption(workout_date.strftime('%A %d %B %Y'))

        workout_type = today_workout['type']
        workout_type_display = workout_type_display_map.get(workout_type, workout_type)

        if workout_type == 'recovery':
            st.info(f"**{today_workout['name']}**")
        elif workout_type in ['intervals', 'intervals_long']:
            st.error(f"**{today_workout['name']}** (Seance difficile)")
        else:
            st.success(f"**{today_workout['name']}**")

        cols = st.columns(2)
        cols[0].metric("TSS", str(today_workout['tss']))
        cols[1].metric("Type", workout_type_display)

        if today_workout.get('description'):
            with st.expander("Details de la seance"):
                st.markdown(today_workout['description'])
    else:
        st.info("Pas de seance planifiee - Jour de repos")

    st.markdown("---")

    # --- DEMAIN ---
    st.markdown("#### Demain")
    if 'error' not in next_workout:
        col1, col2 = st.columns([2, 1])

        with col1:
            workout_date = datetime.fromisoformat(next_workout['date'])
            st.caption(workout_date.strftime('%A %d %B %Y'))

            if next_workout['type'] == 'rest':
                st.info(f"**Repos** - {next_workout['reason']}")
            else:
                workout_type_display = workout_type_display_map.get(
                    next_workout['type'], next_workout['type']
                )

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
    # LIGNE 4: Evolution temporelle
    # ========================================
    st.divider()
    st.subheader(f"Evolution sur {days} jours")

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
            height=450,
            margin=dict(l=20, r=20, t=40, b=20),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            xaxis=dict(
                showgrid=True,
                gridcolor='rgba(255,255,255,0.1)',
                rangeslider=dict(visible=True),  # SLIDER INTERACTIF
                rangeselector=dict(
                    buttons=list([
                        dict(count=7, label="7j", step="day", stepmode="backward"),
                        dict(count=30, label="30j", step="day", stepmode="backward"),
                        dict(count=90, label="90j", step="day", stepmode="backward"),
                        dict(step="all", label="Tout")
                    ]),
                    bgcolor='rgba(50,50,50,0.8)',
                    activecolor='#3498db',
                    font=dict(color='white')
                )
            ),
            yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)'),
            hovermode='x unified'  # Affiche toutes les valeurs au survol
        )

        st.plotly_chart(fig_evolution, use_container_width=True)

        # ========================================
        # Graphique ACWR historique avec zones de risque
        # ========================================
        st.subheader("Evolution du risque de blessure (ACWR)")

        # Version simplifiee - ligne ACWR sans zones pour debug
        fig_acwr = go.Figure()

        # Convertir explicitement les données en listes Python
        dates_list = df_wellness['date'].tolist()
        acwr_list = [float(x) for x in df_wellness['acwr'].tolist()]

        # Tracer la ligne
        fig_acwr.add_trace(go.Scatter(
            x=dates_list,
            y=acwr_list,
            mode='lines+markers',
            name='ACWR',
            line=dict(color='red', width=2),
            marker=dict(size=6, color='red')
        ))

        # Lignes horizontales pour les seuils
        fig_acwr.add_hline(y=1.5, line_dash="dash", line_color="red", annotation_text="Danger")
        fig_acwr.add_hline(y=1.3, line_dash="dash", line_color="orange", annotation_text="Attention")
        fig_acwr.add_hline(y=0.8, line_dash="dash", line_color="green", annotation_text="Optimal")

        fig_acwr.update_layout(
            height=350,
            yaxis_range=[0, 2.5],
            hovermode='x unified'
        )

        st.plotly_chart(fig_acwr, use_container_width=True)

        # Legende ACWR
        col1, col2, col3, col4 = st.columns(4)
        col1.markdown("🔵 **< 0.8**: Sous-entrainement")
        col2.markdown("🟢 **0.8-1.3**: Zone optimale")
        col3.markdown("🟠 **1.3-1.5**: Attention")
        col4.markdown("🔴 **> 1.5**: Risque eleve")

    # ========================================
    # LIGNE 5: Historique et TSS/semaine
    # ========================================
    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        st.subheader(f"Historique des courses ({days}j)")

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
