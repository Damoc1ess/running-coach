# filename: main.py
# Running Coach v2.2 - Polarized Data-Driven Training
# 100% des décisions basées sur les données de la montre
# v2.2: Génère les workouts pour DEMAIN (J+1) pour sync Coros

import requests
import json
import os
import re
from datetime import date, timedelta, datetime, time
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

VERSION = "2.2.1"

# ==============================================================================
# --- CONFIGURATION PAR DÉFAUT (peut être override par config.json) ---
# ==============================================================================
DEFAULT_CONFIG = {
    "polarized": {
        "easy_target_percent": 80,      # 80% des séances en Z1-Z2
        "hard_target_percent": 20,      # 20% des séances en Z4-Z5
        "min_days_between_hard": 2,     # Min 48h entre séances intenses
        "analysis_window_days": 21      # Fenêtre d'analyse de la distribution
    },
    "banister": {
        "ctl_days": 42,
        "atl_days": 7,
        "target_tsb": -15.0,
        "alb_lower_bound": -25.0,
        "tsb_recovery_threshold": -25.0  # TSB en dessous = forcer récup
    },
    "intensity_factors": {
        "recovery": 0.65,
        "easy": 0.72,
        "long_run": 0.70,
        "intervals": 0.85,
        "intervals_long": 0.88
    },
    "workout_templates": {
        "recovery": {
            "name": "Récupération",
            "category": "easy",
            "structure": "- {{ DURATION }} Zone 1-2\n\nCourse très facile, respiration aisée.\nObjectif: récupération active."
        },
        "easy": {
            "name": "Endurance Facile",
            "category": "easy",
            "structure": "- 5m Zone 1\n- {{ DURATION }} Zone 2\n- 5m Zone 1\n\nAllure conversationnelle.\nVous devez pouvoir tenir une conversation."
        },
        "long_run": {
            "name": "Sortie Longue",
            "category": "easy",
            "structure": "- 10m Zone 1\n- {{ DURATION }} Zone 2\n- 10m Zone 1\n\nSortie longue en endurance fondamentale.\nHydratez-vous régulièrement."
        },
        "intervals": {
            "name": "Fractionné VO2max",
            "category": "hard",
            "structure": "- 15m Zone 2\n- {{ REPS }}x({{ WORK }} Zone 5, {{ REST }} Zone 1)\n- 10m Zone 1\n\nIntervalles à haute intensité.\nRécupération complète entre les répétitions."
        },
        "intervals_long": {
            "name": "Fractionné Seuil",
            "category": "hard",
            "structure": "- 15m Zone 2\n- {{ REPS }}x({{ WORK }} Zone 4, {{ REST }} Zone 1)\n- 10m Zone 1\n\nIntervalles au seuil lactique.\nMaintenir une allure régulière."
        }
    },
    "operational_settings": {
        "live_mode": True,
        "timezone": "Europe/Brussels"
    },
    "weather": {
        "enabled": True,
        "location": {
            "name": "Lamorteau, Belgique",
            "lat": 49.55,
            "lon": 5.35
        },
        "workout_hour": 7  # Heure prévue du workout pour la prévision
    }
}


# ==============================================================================
# --- API CLIENT ---
# ==============================================================================
class IntervalsAPI:
    """Client pour l'API Intervals.icu"""
    BASE_URL = "https://intervals.icu"

    def __init__(self, athlete_id, api_key):
        if not athlete_id or not api_key:
            raise ValueError("Credentials manquants (ATHLETE_ID, API_KEY)")
        self.auth = ("API_KEY", api_key)
        self.athlete_id = athlete_id
        self.athlete_url = f"{self.BASE_URL}/api/v1/athlete/{athlete_id}"

    def get_wellness(self, for_date: date):
        """Récupère CTL, ATL, TSB depuis wellness."""
        url = f"{self.athlete_url}/wellness/{for_date.isoformat()}"
        try:
            response = requests.get(url, auth=self.auth, timeout=10)
            response.raise_for_status()
            data = response.json()
            return {
                "ctl": data.get('ctl') or 0,
                "atl": data.get('atl') or 0,
                "tsb": (data.get('ctl') or 0) - (data.get('atl') or 0),
                "resting_hr": data.get('restingHR'),
                "hrv": data.get('hrv')
            }
        except Exception as e:
            print(f"ERREUR API wellness: {e}")
            return None

    def get_wellness_range(self, start_date: date, end_date: date):
        """Récupère l'historique wellness sur une plage de dates."""
        url = f"{self.athlete_url}/wellness"
        params = {"oldest": start_date.isoformat(), "newest": end_date.isoformat()}
        try:
            response = requests.get(url, auth=self.auth, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
            result = []
            for item in data:
                sleep_secs = item.get('sleepSecs')
                result.append({
                    "date": item.get('id'),
                    "ctl": item.get('ctl') or 0,
                    "atl": item.get('atl') or 0,
                    "tsb": (item.get('ctl') or 0) - (item.get('atl') or 0),
                    "resting_hr": item.get('restingHR'),
                    "hrv": item.get('hrv'),
                    "sleep_hours": round(sleep_secs / 3600, 2) if sleep_secs else None,
                    "ramp_rate": item.get('rampRate')
                })
            return result
        except Exception as e:
            print(f"ERREUR API wellness range: {e}")
            return []

    def get_athlete_info(self):
        """Récupère le profil athlète."""
        try:
            response = requests.get(self.athlete_url, auth=self.auth, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"ERREUR API athlete: {e}")
            return {}

    def get_activities(self, start_date: date, end_date: date):
        """Récupère les activités récentes."""
        url = f"{self.athlete_url}/activities"
        params = {"oldest": start_date.isoformat(), "newest": end_date.isoformat()}
        try:
            response = requests.get(url, auth=self.auth, params=params, timeout=15)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"ERREUR API activities: {e}")
            return []

    def get_events(self, start_date: date, end_date: date):
        """Récupère les événements planifiés."""
        url = f"{self.athlete_url}/events?oldest={start_date.isoformat()}&newest={end_date.isoformat()}"
        try:
            response = requests.get(url, auth=self.auth, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"ERREUR API events: {e}")
            return []

    def create_workout(self, workout_data: dict):
        """Crée un workout sur le calendrier."""
        url = f"{self.athlete_url}/events"
        try:
            response = requests.post(url, auth=self.auth, json=workout_data, timeout=10)
            response.raise_for_status()
            print(f"✓ Workout créé: {workout_data.get('name')}")
            return response.json()
        except Exception as e:
            print(f"ERREUR création workout: {e}")
            return None

    def get_sport_settings(self, sport_type="Run"):
        """Récupère les paramètres spécifiques à un sport (zones HR, LTHR, etc.)."""
        url = f"{self.athlete_url}/sport-settings"
        try:
            response = requests.get(url, auth=self.auth, timeout=10)
            response.raise_for_status()
            settings = response.json()
            # Trouver les settings pour le sport demandé
            for s in settings:
                if sport_type in s.get('types', []):
                    return {
                        'lthr': s.get('lthr'),
                        'max_hr': s.get('max_hr'),
                        'hr_zones': s.get('hr_zones'),
                        'warmup_time': s.get('warmup_time'),
                        'cooldown_time': s.get('cooldown_time')
                    }
            return {}
        except Exception as e:
            print(f"ERREUR API sport-settings: {e}")
            return {}


# ==============================================================================
# --- API MÉTÉO ---
# ==============================================================================
class WeatherAPI:
    """Client pour l'API OpenWeatherMap."""
    BASE_URL = "https://api.openweathermap.org/data/2.5"

    def __init__(self, api_key, lat, lon):
        self.api_key = api_key
        self.lat = lat
        self.lon = lon

    def get_forecast(self, target_date: date, target_hour: int = 7):
        """
        Récupère les prévisions météo pour une date et heure données.
        Utilise l'API forecast (gratuite, 5 jours, pas de 3h).
        """
        if not self.api_key:
            return None

        url = f"{self.BASE_URL}/forecast"
        params = {
            "lat": self.lat,
            "lon": self.lon,
            "appid": self.api_key,
            "units": "metric",
            "lang": "fr"
        }

        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            # Chercher la prévision la plus proche de target_date à target_hour
            target_dt = datetime.combine(target_date, time(target_hour, 0))
            best_forecast = None
            min_diff = float('inf')

            for item in data.get('list', []):
                forecast_dt = datetime.fromisoformat(item['dt_txt'].replace(' ', 'T'))
                diff = abs((forecast_dt - target_dt).total_seconds())
                if diff < min_diff:
                    min_diff = diff
                    best_forecast = item

            if best_forecast:
                main = best_forecast.get('main', {})
                weather = best_forecast.get('weather', [{}])[0]
                wind = best_forecast.get('wind', {})

                return {
                    'temp': main.get('temp'),
                    'feels_like': main.get('feels_like'),
                    'humidity': main.get('humidity'),
                    'description': weather.get('description', ''),
                    'icon': weather.get('icon', ''),
                    'wind_speed': wind.get('speed', 0),  # m/s
                    'forecast_time': best_forecast.get('dt_txt')
                }

            return None

        except Exception as e:
            print(f"ERREUR API météo: {e}")
            return None


def calculate_heat_adjustment(weather_data):
    """
    Calcule l'ajustement d'intensité basé sur les conditions météo.

    Basé sur:
    - ACSM Position Stand on Exertional Heat Illness
    - Périard et al. (2015) - Performance diminue ~2% par °C au-dessus de 25°C
    - Recommandations World Athletics pour compétitions en chaleur

    Retourne un facteur multiplicateur (0.0 à 1.0) et une description.
    """
    if not weather_data:
        return 1.0, None, "Météo non disponible"

    temp = weather_data.get('feels_like') or weather_data.get('temp', 20)
    humidity = weather_data.get('humidity', 50)
    description = weather_data.get('description', '')

    # Indice de chaleur simplifié (Heat Index approximatif)
    # Plus précis que la température seule pour le stress thermique
    if temp >= 20 and humidity > 40:
        # Formule simplifiée du Heat Index
        heat_index = temp + (0.05 * (humidity - 40))
    else:
        heat_index = temp

    # Déterminer l'ajustement
    if heat_index < 18:
        # Conditions fraîches - optimal pour la performance
        factor = 1.0
        advice = "Conditions optimales"
    elif heat_index < 22:
        # Conditions normales
        factor = 1.0
        advice = "Conditions normales"
    elif heat_index < 25:
        # Chaleur légère - vigilance
        factor = 0.95
        advice = "Chaleur légère - bien s'hydrater"
    elif heat_index < 28:
        # Chaleur modérée - réduction recommandée
        factor = 0.88
        advice = "Chaleur modérée - réduire l'intensité"
    elif heat_index < 32:
        # Chaleur élevée - réduction significative
        factor = 0.75
        advice = "Chaleur élevée - privilégier endurance facile"
    elif heat_index < 35:
        # Chaleur dangereuse
        factor = 0.60
        advice = "Chaleur dangereuse - sortie matinale uniquement"
    else:
        # Conditions extrêmes - repos recommandé
        factor = 0.0
        advice = "Conditions extrêmes - repos recommandé"

    weather_info = {
        'temp': temp,
        'feels_like': weather_data.get('feels_like'),
        'humidity': humidity,
        'heat_index': round(heat_index, 1),
        'description': description,
        'adjustment_factor': factor,
        'advice': advice
    }

    return factor, weather_info, advice


# ==============================================================================
# --- READINESS SCORE (ALGORITHME SCIENTIFIQUE) ---
# ==============================================================================
def calculate_readiness_score(wellness_history: list) -> dict:
    """
    Calcule un score de préparation basé sur des seuils scientifiques validés.

    Sources scientifiques:
    - Banister (1975): Modèle impulse-response CTL/ATL/TSB
    - PMC Sleep Studies: Seuil déficit sommeil < 6h cumulé
    - Runners Connect / Outside: Seuil FC repos +5-7 bpm
    - Intervals.icu: RampRate > 2.0 = progression trop rapide

    Retourne un dict avec:
    - readiness_score: multiplicateur de charge (0.5 à 1.1)
    - components: détail de chaque facteur
    - recommendations: conseils basés sur les données
    """
    from statistics import median, mean

    if not wellness_history or len(wellness_history) < 1:
        return {
            "readiness_score": 1.0,
            "components": {},
            "recommendations": ["Données insuffisantes pour l'analyse"]
        }

    today = wellness_history[-1]
    recommendations = []
    components = {}

    # =========================================================================
    # 1. TSB (Training Stress Balance) - Modèle Banister validé
    # =========================================================================
    tsb = today.get('tsb', today.get('ctl', 0) - today.get('atl', 0))

    if tsb < -25:
        tsb_modifier = 0.5
        recommendations.append("TSB très bas (<-25): repos recommandé (surentraînement)")
    elif tsb < -15:
        tsb_modifier = 0.75
        recommendations.append("TSB bas (<-15): réduire l'intensité")
    elif tsb < -5:
        tsb_modifier = 0.9
        recommendations.append("TSB modérément négatif: charge normale possible")
    elif tsb < 10:
        tsb_modifier = 1.0
    else:
        tsb_modifier = 1.0
        recommendations.append("TSB positif: bien reposé, prêt pour séance intense")

    components['tsb'] = {
        'value': round(tsb, 1),
        'modifier': tsb_modifier,
        'threshold': 'Banister model: TSB < -25 = overtraining'
    }

    # =========================================================================
    # 2. FC Repos - Élévation vs baseline (seuil scientifique: +5-7 bpm)
    # Sources: Runners Connect, Outside Online, études 1985/2015
    # =========================================================================
    hr_values = [w.get('resting_hr') for w in wellness_history[-14:] if w.get('resting_hr')]

    if hr_values and len(hr_values) >= 3:
        baseline_hr = median(hr_values)
        current_hr = today.get('resting_hr', baseline_hr)
        hr_elevation = current_hr - baseline_hr if current_hr else 0

        if hr_elevation >= 7:
            hr_modifier = 0.7
            recommendations.append(f"FC repos élevée (+{hr_elevation:.0f} bpm vs baseline): récupération insuffisante")
        elif hr_elevation >= 5:
            hr_modifier = 0.85
            recommendations.append(f"FC repos légèrement élevée (+{hr_elevation:.0f} bpm): vigilance")
        else:
            hr_modifier = 1.0

        components['resting_hr'] = {
            'value': current_hr,
            'baseline': round(baseline_hr, 1),
            'elevation': round(hr_elevation, 1),
            'modifier': hr_modifier,
            'threshold': 'Scientific: +5 bpm = warning, +7 bpm = not recovered'
        }
    else:
        hr_modifier = 1.0
        components['resting_hr'] = {'value': None, 'modifier': 1.0, 'note': 'Données insuffisantes'}

    # =========================================================================
    # 3. Sommeil - Moyenne 3 jours (dette cumulée, pas une seule nuit)
    # Sources: PMC Sleep and Athletic Performance, Gatorade SSI
    # Seuil: < 6h en moyenne = déficit dangereux
    # =========================================================================
    sleep_values = [w.get('sleep_hours') for w in wellness_history[-3:] if w.get('sleep_hours')]

    if sleep_values:
        avg_sleep_3d = mean(sleep_values)

        if avg_sleep_3d < 6.0:
            sleep_modifier = 0.75
            recommendations.append(f"Dette de sommeil ({avg_sleep_3d:.1f}h/nuit sur 3j): réduire la charge")
        elif avg_sleep_3d < 7.0:
            sleep_modifier = 0.90
            recommendations.append(f"Sommeil insuffisant ({avg_sleep_3d:.1f}h/nuit): récupération compromise")
        elif avg_sleep_3d >= 8.5:
            sleep_modifier = 1.05
            recommendations.append(f"Excellent sommeil ({avg_sleep_3d:.1f}h/nuit): prêt pour plus de charge")
        else:
            sleep_modifier = 1.0

        components['sleep'] = {
            'avg_3d': round(avg_sleep_3d, 1),
            'last_night': sleep_values[-1] if sleep_values else None,
            'modifier': sleep_modifier,
            'threshold': 'Scientific: <6h avg = dangerous deficit, 7-9h = recommended'
        }
    else:
        sleep_modifier = 1.0
        components['sleep'] = {'value': None, 'modifier': 1.0, 'note': 'Données non disponibles'}

    # =========================================================================
    # 4. RampRate - Progression trop rapide (seuil > 2.0)
    # Source: Intervals.icu, principe de progression progressive
    # =========================================================================
    ramp_rate = today.get('ramp_rate', 0)

    if ramp_rate and ramp_rate > 2.0:
        ramp_modifier = 0.85
        recommendations.append(f"Progression rapide (rampRate={ramp_rate:.1f}): risque de blessure")
    elif ramp_rate and ramp_rate < -0.5:
        ramp_modifier = 1.0
        recommendations.append(f"RampRate négatif ({ramp_rate:.1f}): désentraînement en cours")
    else:
        ramp_modifier = 1.0

    components['ramp_rate'] = {
        'value': round(ramp_rate, 2) if ramp_rate else None,
        'modifier': ramp_modifier,
        'threshold': 'Scientific: >2.0 = too fast progression'
    }

    # =========================================================================
    # 5. ACWR (Acute:Chronic Workload Ratio) - Informatif mais controversé
    # Source: Meta-analysis 2025, zone optimale 0.8-1.3
    # Note: Utilisé comme indicateur, pas comme facteur décisif
    # =========================================================================
    ctl = today.get('ctl', 0)
    atl = today.get('atl', 0)
    acwr = atl / ctl if ctl > 0 else 1.0

    if acwr > 1.5:
        acwr_modifier = 0.8
        recommendations.append(f"ACWR élevé ({acwr:.2f}): risque de blessure accru")
    elif acwr > 1.3:
        acwr_modifier = 0.9
        recommendations.append(f"ACWR zone attention ({acwr:.2f}): surveiller")
    elif acwr < 0.8:
        acwr_modifier = 1.0
        recommendations.append(f"ACWR bas ({acwr:.2f}): sous-entraînement possible")
    else:
        acwr_modifier = 1.0

    components['acwr'] = {
        'value': round(acwr, 2),
        'modifier': acwr_modifier,
        'threshold': 'Meta-analysis 2025: 0.8-1.3 = optimal, >1.5 = high risk'
    }

    # =========================================================================
    # Score final = produit des modificateurs
    # =========================================================================
    final_score = tsb_modifier * hr_modifier * sleep_modifier * ramp_modifier * acwr_modifier
    final_score = max(0.5, min(1.1, final_score))

    # Interprétation du score
    if final_score >= 1.0:
        status = "Prêt"
    elif final_score >= 0.85:
        status = "Modéré"
    elif final_score >= 0.7:
        status = "Prudence"
    else:
        status = "Repos recommandé"

    return {
        "readiness_score": round(final_score, 2),
        "status": status,
        "components": components,
        "recommendations": recommendations if recommendations else ["Tous les indicateurs sont normaux"]
    }


# ==============================================================================
# --- ANALYSEUR DE DONNÉES ---
# ==============================================================================
class DataAnalyzer:
    """Analyse les données d'entraînement pour les décisions."""

    def __init__(self, activities, athlete_info):
        self.activities = [a for a in activities if a.get('type') == 'Run']
        self.athlete_info = athlete_info or {}

        # Calculer les métriques de base
        self.max_hr = self._compute_max_hr()
        self.threshold_hr = self._compute_threshold_hr()
        self.avg_easy_pace = self._compute_avg_easy_pace()

    def _compute_max_hr(self):
        """Détermine la FC max depuis les données."""
        # D'abord depuis le profil
        if self.athlete_info.get('max_hr'):
            return self.athlete_info['max_hr']

        # Sinon depuis les activités
        max_observed = 0
        for a in self.activities:
            if a.get('max_heartrate'):
                max_observed = max(max_observed, a['max_heartrate'])

        return max_observed if max_observed > 0 else 190

    def _compute_threshold_hr(self):
        """Détermine la FC seuil."""
        if self.athlete_info.get('lthr'):
            return self.athlete_info['lthr']
        return int(self.max_hr * 0.87)

    def _compute_avg_easy_pace(self):
        """Calcule la pace moyenne en endurance (min/km)."""
        easy_paces = []
        for a in self.activities:
            # Filtre les runs faciles (IF < 0.80 ou avg HR < 85% max)
            avg_hr = a.get('average_heartrate', 0)
            if avg_hr > 0 and avg_hr < self.max_hr * 0.80:
                if a.get('moving_time') and a.get('distance') and a['distance'] > 0:
                    pace_sec_km = a['moving_time'] / (a['distance'] / 1000)
                    pace_min_km = pace_sec_km / 60
                    if 4.0 <= pace_min_km <= 9.0:  # Filtre les valeurs aberrantes
                        easy_paces.append(pace_min_km)

        if easy_paces:
            return sum(easy_paces) / len(easy_paces)
        return 6.0  # Défaut: 6:00 min/km

    def get_last_run_date(self):
        """Trouve la date du dernier run."""
        for a in sorted(self.activities, key=lambda x: x.get('start_date_local', ''), reverse=True):
            date_str = a.get('start_date_local', '')[:10]
            if date_str:
                return datetime.strptime(date_str, '%Y-%m-%d').date()
        return None

    def get_last_hard_workout_date(self):
        """Trouve la date de la dernière séance intense."""
        for a in sorted(self.activities, key=lambda x: x.get('start_date_local', ''), reverse=True):
            if self._is_hard_workout(a):
                date_str = a.get('start_date_local', '')[:10]
                return datetime.strptime(date_str, '%Y-%m-%d').date()
        return None

    def _is_hard_workout(self, activity):
        """Détermine si une activité est une séance intense."""
        # Check par le nom
        name = (activity.get('name') or '').lower()
        hard_keywords = ['interval', 'fractionn', 'tempo', 'threshold', 'seuil',
                         'speed', 'vma', 'vo2', 'fartlek', 'hard']
        if any(kw in name for kw in hard_keywords):
            return True

        # Check par intensité (IF > 0.85)
        if activity.get('icu_intensity') and activity['icu_intensity'] > 85:
            return True

        # Check par HR (avg > 88% de max pendant > 20min)
        avg_hr = activity.get('average_heartrate', 0)
        duration_min = (activity.get('moving_time', 0) or 0) / 60
        if avg_hr > 0 and self.max_hr > 0:
            if avg_hr / self.max_hr > 0.88 and duration_min > 20:
                return True

        # Check par variabilité (intervalles)
        if activity.get('variability_index') and activity['variability_index'] > 1.08:
            return True

        return False

    def get_training_distribution(self, days=21):
        """Calcule la distribution polarisée sur N jours."""
        cutoff = datetime.now().date() - timedelta(days=days)

        easy_count = 0
        hard_count = 0
        total_runs = 0

        for a in self.activities:
            date_str = a.get('start_date_local', '')[:10]
            if not date_str:
                continue
            activity_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            if activity_date < cutoff:
                continue

            total_runs += 1
            if self._is_hard_workout(a):
                hard_count += 1
            else:
                easy_count += 1

        return {
            "total_runs": total_runs,
            "easy_count": easy_count,
            "hard_count": hard_count,
            "easy_percent": (easy_count / total_runs * 100) if total_runs > 0 else 100,
            "hard_percent": (hard_count / total_runs * 100) if total_runs > 0 else 0
        }

    def get_weekly_stats(self, weeks=4):
        """Statistiques par semaine pour les N dernières semaines."""
        stats = []
        for week in range(weeks):
            end_date = datetime.now().date() - timedelta(days=week * 7)
            start_date = end_date - timedelta(days=7)

            week_runs = 0
            week_distance = 0
            week_duration = 0
            week_tss = 0

            for a in self.activities:
                date_str = a.get('start_date_local', '')[:10]
                if not date_str:
                    continue
                activity_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                if start_date <= activity_date <= end_date:
                    week_runs += 1
                    week_distance += (a.get('distance') or 0) / 1000
                    week_duration += (a.get('moving_time') or 0) / 60
                    week_tss += a.get('icu_training_load') or 0

            stats.append({
                "week": week,
                "runs": week_runs,
                "distance_km": round(week_distance, 1),
                "duration_min": round(week_duration),
                "tss": round(week_tss)
            })

        return stats

    def get_hr_zones(self):
        """Retourne les zones HR basées sur le seuil (Friel)."""
        lthr = self.threshold_hr
        return {
            "Z1": {"name": "Récupération", "min": 0, "max": int(lthr * 0.81)},
            "Z2": {"name": "Endurance", "min": int(lthr * 0.81), "max": int(lthr * 0.90)},
            "Z3": {"name": "Tempo", "min": int(lthr * 0.90), "max": int(lthr * 0.96)},
            "Z4": {"name": "Seuil", "min": int(lthr * 0.96), "max": int(lthr * 1.02)},
            "Z5": {"name": "VO2max", "min": int(lthr * 1.02), "max": self.max_hr}
        }


# ==============================================================================
# --- MOTEUR DE DÉCISION POLARISÉ ---
# ==============================================================================
class PolarizedEngine:
    """Moteur de décision 100% data-driven avec distribution polarisée et readiness score."""

    def __init__(self, config, analyzer, wellness, today, wellness_history=None):
        self.config = config
        self.analyzer = analyzer
        self.wellness = wellness
        self.today = today
        self.tomorrow = today + timedelta(days=1)
        self.wellness_history = wellness_history or []

        # Calcul du readiness score si historique disponible
        if self.wellness_history:
            self.readiness = calculate_readiness_score(self.wellness_history)
        else:
            self.readiness = {"readiness_score": 1.0, "status": "N/A", "components": {}, "recommendations": []}

        # Paramètres polarisés
        pol_config = config.get('polarized', DEFAULT_CONFIG['polarized'])
        self.easy_target = pol_config.get('easy_target_percent', 80)
        self.hard_target = pol_config.get('hard_target_percent', 20)
        self.min_days_hard = pol_config.get('min_days_between_hard', 2)
        self.analysis_window = pol_config.get('analysis_window_days', 21)

        # Paramètres Banister
        ban_config = config.get('banister', DEFAULT_CONFIG['banister'])
        self.ctl_days = ban_config.get('ctl_days', 42)
        self.atl_days = ban_config.get('atl_days', 7)
        self.target_tsb = ban_config.get('target_tsb', -15)
        self.alb_lower = ban_config.get('alb_lower_bound', -25)
        self.tsb_recovery = ban_config.get('tsb_recovery_threshold', -25)

    def should_run_tomorrow(self):
        """Détermine si DEMAIN est un jour de course - basé sur données + readiness score scientifique."""
        tsb = self.wellness['tsb']
        ctl = self.wellness['ctl']
        atl = self.wellness['atl']

        last_run = self.analyzer.get_last_run_date()
        # Pour demain: on calcule les jours depuis le dernier run jusqu'à DEMAIN
        days_since = (self.tomorrow - last_run).days if last_run else 999

        # Calcul du ratio charge aiguë/chronique (ACWR simplifié)
        acwr = atl / ctl if ctl > 0 else 1.0

        # Readiness score (algorithme scientifique multi-facteurs)
        readiness_score = self.readiness.get('readiness_score', 1.0)
        readiness_status = self.readiness.get('status', 'N/A')

        decision_factors = []
        decision_factors.append(f"TSB: {tsb:.1f}")
        decision_factors.append(f"ACWR: {acwr:.2f}")
        decision_factors.append(f"Readiness Score: {readiness_score:.2f} ({readiness_status})")
        decision_factors.append(f"Jours depuis run (demain): {days_since}")

        # Ajouter les recommandations du readiness score
        for rec in self.readiness.get('recommendations', []):
            decision_factors.append(f"  • {rec}")

        # === RÈGLES BASÉES SUR READINESS SCORE SCIENTIFIQUE ===

        # RÈGLE 0: Readiness score très bas → REPOS (basé sur multi-facteurs scientifiques)
        if readiness_score < 0.6:
            decision_factors.append("→ REPOS demain (Readiness < 0.6, récupération multi-facteurs)")
            return False, f"Readiness score bas ({readiness_score:.2f}), récupération nécessaire", decision_factors

        # RÈGLE 1: Aura couru aujourd'hui → on vérifie si assez de repos
        if days_since == 1:
            decision_factors.append("→ Run aujourd'hui, évaluation repos")

        # RÈGLE 2: TSB très négatif → REPOS (surentraînement)
        if tsb < -25:
            decision_factors.append("→ REPOS demain (TSB < -25, surentraînement)")
            return False, f"TSB trop bas ({tsb:.1f}), récupération nécessaire", decision_factors

        # RÈGLE 3: ACWR trop élevé → REPOS (risque blessure)
        if acwr > 1.5:
            decision_factors.append("→ REPOS demain (ACWR > 1.5, risque blessure)")
            return False, f"ACWR trop élevé ({acwr:.2f}), risque de blessure", decision_factors

        # RÈGLE 3b: Readiness modéré + TSB négatif → REPOS prudent
        if readiness_score < 0.75 and tsb < -10:
            decision_factors.append("→ REPOS demain (Readiness < 0.75 + TSB négatif)")
            return False, f"Readiness modéré ({readiness_score:.2f}) avec TSB négatif", decision_factors

        # RÈGLE 4: TSB très positif + plusieurs jours sans run → COURSE (désentraînement)
        if tsb > 15 and days_since >= 3:
            decision_factors.append("→ COURSE demain (TSB > 15, risque désentraînement)")
            return True, f"Bien reposé (TSB {tsb:.1f}) et {days_since}j sans run demain", decision_factors

        # RÈGLE 5: TSB positif → COURSE (récupéré)
        if tsb > 5:
            decision_factors.append("→ COURSE demain (TSB > 5, bien récupéré)")
            return True, f"Récupéré (TSB {tsb:.1f})", decision_factors

        # RÈGLE 6: TSB modérément négatif mais assez de repos ET readiness OK → COURSE
        if tsb > -15 and days_since >= 2 and readiness_score >= 0.75:
            decision_factors.append("→ COURSE demain (TSB > -15, 2j+ repos, readiness OK)")
            return True, f"TSB acceptable ({tsb:.1f}) et readiness OK ({readiness_score:.2f})", decision_factors

        # RÈGLE 7: Beaucoup de jours sans run → COURSE (même si fatigué)
        if days_since >= 4:
            decision_factors.append("→ COURSE demain (4j+ sans run, maintien fitness)")
            return True, f"{days_since}j sans courir demain, maintien de la fitness", decision_factors

        # RÈGLE 8: TSB négatif et peu de repos → REPOS
        if tsb < 0 and days_since < 2:
            decision_factors.append("→ REPOS demain (TSB négatif, repos insuffisant)")
            return False, f"Encore fatigué (TSB {tsb:.1f}), besoin de repos", decision_factors

        # DÉFAUT: En cas de doute, récupérer
        decision_factors.append("→ REPOS demain (défaut prudent)")
        return False, "Récupération par défaut", decision_factors

    def calculate_target_tss(self):
        """Calcule le TSS cible basé sur le modèle Banister, ajusté par le readiness score."""
        ctl = self.wellness['ctl']
        atl = self.wellness['atl']

        c = self.ctl_days
        a = self.atl_days

        # Formule Banister pour atteindre TSB cible
        numerator = self.target_tsb - (ctl * (c - 1) / c) + (atl * (a - 1) / a)
        denominator = (1 / c) - (1 / a)

        tss_for_tsb = numerator / denominator if denominator != 0 else 50

        # Cap ALB (sécurité anti-blessure)
        tss_cap = atl - self.alb_lower

        final_tss = min(tss_for_tsb, tss_cap)
        final_tss = max(20, final_tss)  # Minimum 20 TSS

        reason = "TSB" if tss_for_tsb <= tss_cap else "ALB cap"

        # Appliquer le readiness score comme modificateur
        readiness_score = self.readiness.get('readiness_score', 1.0)
        original_tss = final_tss
        final_tss = round(final_tss * readiness_score)
        final_tss = max(20, final_tss)  # Minimum 20 TSS après ajustement

        if readiness_score < 1.0:
            reason += f" + Readiness ({readiness_score:.0%})"

        return {
            "target_tss": round(final_tss),
            "original_tss": round(original_tss),
            "tss_for_tsb": round(tss_for_tsb),
            "tss_cap": round(tss_cap),
            "readiness_modifier": readiness_score,
            "reason": reason
        }

    def select_workout_type(self):
        """Sélectionne le type de séance basé sur la distribution polarisée."""
        distribution = self.analyzer.get_training_distribution(self.analysis_window)
        last_hard = self.analyzer.get_last_hard_workout_date()
        tsb = self.wellness['tsb']

        # Pour demain: on calcule les jours depuis la dernière séance hard jusqu'à DEMAIN
        days_since_hard = (self.tomorrow - last_hard).days if last_hard else 999

        decision_log = []
        decision_log.append(f"Distribution ({self.analysis_window}j): {distribution['easy_percent']:.0f}% easy, {distribution['hard_percent']:.0f}% hard")
        decision_log.append(f"Jours depuis hard: {days_since_hard}")
        decision_log.append(f"TSB actuel: {tsb:.1f}")

        # RÈGLE 1: TSB trop bas → Recovery
        if tsb < self.tsb_recovery:
            decision_log.append(f"→ RECOVERY (TSB {tsb:.1f} < {self.tsb_recovery})")
            return "recovery", decision_log

        # RÈGLE 2: Pas assez de récup depuis dernière hard → Easy
        if days_since_hard < self.min_days_hard:
            decision_log.append(f"→ EASY (seulement {days_since_hard}j depuis hard, min {self.min_days_hard})")
            return "easy", decision_log

        # RÈGLE 3: Trop de hard récemment → Easy
        if distribution['hard_percent'] > 25:
            decision_log.append(f"→ EASY (hard% {distribution['hard_percent']:.0f}% > 25%, rétablir 80/20)")
            return "easy", decision_log

        # RÈGLE 4: Pas assez de hard ET bien reposé → Hard
        if distribution['hard_percent'] < 15 and days_since_hard >= 4:
            decision_log.append(f"→ HARD (hard% {distribution['hard_percent']:.0f}% < 15%, {days_since_hard}j depuis hard)")
            return "intervals", decision_log

        # RÈGLE 5: Bien reposé et distribution OK → possibilité de hard
        if tsb > 5 and days_since_hard >= 3 and distribution['hard_percent'] < 22:
            decision_log.append(f"→ HARD (TSB positif {tsb:.1f}, distribution OK)")
            return "intervals", decision_log

        # DÉFAUT: Easy (maintient 80/20)
        weekly_stats = self.analyzer.get_weekly_stats(1)
        if weekly_stats and weekly_stats[0]['distance_km'] > 25:
            decision_log.append(f"→ EASY (volume hebdo {weekly_stats[0]['distance_km']:.0f}km, maintenance)")
        else:
            decision_log.append(f"→ EASY (défaut polarisé 80/20)")

        return "easy", decision_log

    def choose_specific_workout(self, workout_category, target_tss):
        """Choisit le workout spécifique selon la catégorie et le TSS."""
        templates = self.config.get('workout_templates', DEFAULT_CONFIG['workout_templates'])

        if workout_category == "recovery":
            return "recovery"

        if workout_category == "easy":
            # Long run si TSS > 60 et conditions favorables
            if target_tss > 60:
                return "long_run"
            return "easy"

        if workout_category == "intervals":
            # Intervalles longs si TSS > 50, courts sinon
            if target_tss > 50:
                return "intervals_long"
            return "intervals"

        return "easy"

    def calculate_workout_duration(self, workout_type, target_tss):
        """Calcule la durée optimale basée sur le TSS et l'IF."""
        intensity_factors = self.config.get('intensity_factors', DEFAULT_CONFIG['intensity_factors'])

        if_value = intensity_factors.get(workout_type, 0.72)

        # TSS = duration_hr * IF² * 100
        # duration_hr = TSS / (IF² * 100)
        duration_hr = target_tss / ((if_value ** 2) * 100)
        duration_min = max(20, round(duration_hr * 60))

        # Caps de sécurité
        if workout_type == "recovery":
            duration_min = min(duration_min, 40)
        elif workout_type == "easy":
            duration_min = min(duration_min, 75)
        elif workout_type == "long_run":
            duration_min = min(duration_min, 120)
        elif "intervals" in workout_type:
            duration_min = min(duration_min, 60)

        return duration_min

    def estimate_distance(self, duration_min, workout_type):
        """Estime la distance basée sur la durée et le pace moyen."""
        avg_pace = self.analyzer.avg_easy_pace  # min/km

        # Ajuster le pace selon le type
        pace_adjustments = {
            "recovery": 1.15,      # 15% plus lent
            "easy": 1.0,
            "long_run": 1.05,      # 5% plus lent
            "intervals": 0.92,     # Plus rapide en moyenne
            "intervals_long": 0.95
        }

        adjusted_pace = avg_pace * pace_adjustments.get(workout_type, 1.0)
        distance_km = duration_min / adjusted_pace

        return round(distance_km, 1)


# ==============================================================================
# --- CONSTRUCTEUR DE WORKOUT ---
# ==============================================================================
class WorkoutBuilder:
    """Construit le workout final pour upload."""

    def __init__(self, config, analyzer):
        self.config = config
        self.analyzer = analyzer
        self.templates = config.get('workout_templates', DEFAULT_CONFIG['workout_templates'])

    def build(self, workout_type, target_tss, duration_min, distance_km,
              wellness, decision_log, workout_date, weather_info=None):
        """Construit le workout complet."""

        template = self.templates.get(workout_type, self.templates.get('easy'))

        # Nom du workout
        name = f"{target_tss} TSS - {template['name']}"

        # Structure avec durée calculée
        structure = template['structure']

        # Remplacer les variables de durée
        main_duration = duration_min - 20  # Enlever échauffement/retour au calme
        main_duration = max(10, main_duration)

        if duration_min >= 60:
            hours = main_duration // 60
            mins = main_duration % 60
            duration_str = f"{hours}h{mins:02d}" if mins > 0 else f"{hours}h"
        else:
            duration_str = f"{main_duration}m"

        structure = structure.replace('{{ DURATION }}', duration_str)

        # Pour les intervalles, calculer les répétitions
        if '{{ REPS }}' in structure:
            if workout_type == "intervals":
                # Intervalles courts: 1min effort, 1min récup
                reps = max(4, min(12, main_duration // 3))
                structure = structure.replace('{{ REPS }}', str(reps))
                structure = structure.replace('{{ WORK }}', '1m')
                structure = structure.replace('{{ REST }}', '1m')
            elif workout_type == "intervals_long":
                # Intervalles longs: 3-4min effort, 2min récup
                reps = max(3, min(6, main_duration // 6))
                structure = structure.replace('{{ REPS }}', str(reps))
                structure = structure.replace('{{ WORK }}', '4m')
                structure = structure.replace('{{ REST }}', '2m')

        # Zones HR pour référence
        hr_zones = self.analyzer.get_hr_zones()
        zones_text = "\n\nZones HR:\n"
        for z, data in hr_zones.items():
            zones_text += f"  {z}: {data['min']}-{data['max']} bpm\n"

        # Section météo
        weather_text = ""
        if weather_info:
            weather_text = f"""
Meteo prevue:
* {weather_info.get('description', '').capitalize()}
* Temperature: {weather_info.get('temp', 0):.1f} C (ressenti: {weather_info.get('feels_like', weather_info.get('temp', 0)):.1f} C)
* Humidite: {weather_info.get('humidity', 0)}%
* Indice chaleur: {weather_info.get('heat_index', 0)} C
* Conseil: {weather_info.get('advice', '')}
"""
            if weather_info.get('adjustment_factor', 1.0) < 1.0:
                weather_text += f"* TSS reduit de {(1 - weather_info['adjustment_factor']) * 100:.0f}% (chaleur)\n"

        # Rationale
        rationale = f"""
---
Decisions data-driven:
{chr(10).join('* ' + log for log in decision_log)}

Etat actuel:
* CTL (Fitness): {wellness['ctl']:.1f}
* ATL (Fatigue): {wellness['atl']:.1f}
* TSB (Forme): {wellness['tsb']:.1f}
{weather_text}
Objectifs:
* TSS cible: {target_tss}
* Duree: {duration_min} min
* Distance estimee: {distance_km} km
{zones_text}
---
Running Coach v{VERSION} - Polarized Data-Driven
"""

        description = structure + rationale

        workout_datetime = datetime.combine(workout_date, time(7, 0))

        return {
            "category": "WORKOUT",
            "type": "Run",
            "name": name,
            "start_date_local": workout_datetime.isoformat(),
            "description": description,
            "load": target_tss
        }


# ==============================================================================
# --- FONCTIONS D'EXPORT POUR DASHBOARD ---
# ==============================================================================
def _get_initialized_components():
    """Initialise les composants nécessaires pour les fonctions d'export."""
    # Charger config
    config = DEFAULT_CONFIG.copy()
    try:
        with open("config.json") as f:
            user_config = json.load(f)
            for key in user_config:
                if isinstance(user_config[key], dict) and key in config:
                    config[key].update(user_config[key])
                else:
                    config[key] = user_config[key]
    except (FileNotFoundError, json.JSONDecodeError):
        pass

    # Timezone
    try:
        tz_str = config.get('operational_settings', {}).get('timezone', 'Europe/Paris')
        tz = ZoneInfo(tz_str)
        today = datetime.now(tz).date()
    except:
        today = date.today()

    # Credentials
    try:
        api_key = os.environ['API_KEY']
        athlete_id = os.environ['ATHLETE_ID']
    except KeyError:
        return None, None, None, None, None

    weather_api_key = os.environ.get('OPENWEATHER_API_KEY', '')

    # API
    api = IntervalsAPI(athlete_id, api_key)

    return config, today, api, weather_api_key, None


def get_current_wellness() -> dict:
    """Retourne l'état de forme actuel (CTL, ATL, TSB, ACWR)."""
    config, today, api, _, _ = _get_initialized_components()
    if not api:
        return {"error": "API non configurée"}

    wellness = api.get_wellness(today)
    if not wellness:
        return {"error": "Données wellness non disponibles"}

    # Calculer ACWR
    ctl = wellness['ctl']
    atl = wellness['atl']
    acwr = atl / ctl if ctl > 0 else 1.0

    return {
        "ctl": wellness['ctl'],
        "atl": wellness['atl'],
        "tsb": wellness['tsb'],
        "acwr": round(acwr, 2),
        "resting_hr": wellness.get('resting_hr'),
        "hrv": wellness.get('hrv'),
        "date": today.isoformat()
    }


def get_distribution(days: int = 21) -> dict:
    """Retourne la distribution polarisée (easy vs hard) sur N jours."""
    config, today, api, _, _ = _get_initialized_components()
    if not api:
        return {"error": "API non configurée"}

    athlete_info = api.get_athlete_info()
    activities = api.get_activities(today - timedelta(days=60), today)

    analyzer = DataAnalyzer(activities, athlete_info)
    distribution = analyzer.get_training_distribution(days)

    return {
        "total_runs": distribution['total_runs'],
        "easy_count": distribution['easy_count'],
        "hard_count": distribution['hard_count'],
        "easy_percent": round(distribution['easy_percent'], 1),
        "hard_percent": round(distribution['hard_percent'], 1),
        "target_easy": 80,
        "target_hard": 20,
        "days_analyzed": days
    }


def get_readiness_score() -> dict:
    """Retourne le readiness score basé sur algorithme scientifique multi-facteurs."""
    config, today, api, _, _ = _get_initialized_components()
    if not api:
        return {"error": "API non configurée"}

    # Récupérer 14 jours d'historique pour le calcul
    start_date = today - timedelta(days=14)
    wellness_history = api.get_wellness_range(start_date, today)

    if not wellness_history:
        return {"error": "Données wellness non disponibles"}

    readiness = calculate_readiness_score(wellness_history)
    readiness['date'] = today.isoformat()
    return readiness


def get_next_workout_info() -> dict:
    """Retourne les informations sur la prochaine séance planifiée."""
    config, today, api, weather_api_key, _ = _get_initialized_components()
    if not api:
        return {"error": "API non configurée"}

    tomorrow = today + timedelta(days=1)

    # Données
    wellness = api.get_wellness(today)
    if not wellness:
        return {"error": "Données wellness non disponibles"}

    # Récupérer l'historique wellness pour le readiness score (14 jours)
    wellness_history = api.get_wellness_range(today - timedelta(days=14), today)

    athlete_info = api.get_athlete_info()
    activities = api.get_activities(today - timedelta(days=60), today)

    # Sport settings
    sport_settings = api.get_sport_settings("Run")
    if sport_settings.get('lthr'):
        athlete_info['lthr'] = sport_settings['lthr']
    if sport_settings.get('max_hr'):
        athlete_info['max_hr'] = sport_settings['max_hr']

    analyzer = DataAnalyzer(activities, athlete_info)
    engine = PolarizedEngine(config, analyzer, wellness, today, wellness_history)

    # Décision course/repos
    should_run, reason, factors = engine.should_run_tomorrow()

    if not should_run:
        return {
            "date": tomorrow.isoformat(),
            "name": "Repos",
            "type": "rest",
            "duration": 0,
            "distance": 0,
            "tss": 0,
            "reason": reason,
            "decision_factors": factors
        }

    # Calcul du workout
    tss_data = engine.calculate_target_tss()
    workout_category, decision_log = engine.select_workout_type()
    workout_type = engine.choose_specific_workout(workout_category, tss_data['target_tss'])
    duration_min = engine.calculate_workout_duration(workout_type, tss_data['target_tss'])
    distance_km = engine.estimate_distance(duration_min, workout_type)

    templates = config.get('workout_templates', DEFAULT_CONFIG['workout_templates'])
    template = templates.get(workout_type, templates.get('easy'))

    # Météo
    weather_info = None
    weather_config = config.get('weather', DEFAULT_CONFIG['weather'])
    if weather_config.get('enabled', True) and weather_api_key:
        location = weather_config.get('location', DEFAULT_CONFIG['weather']['location'])
        workout_hour = weather_config.get('workout_hour', 7)
        weather_api = WeatherAPI(
            api_key=weather_api_key,
            lat=location['lat'],
            lon=location['lon']
        )
        weather_data = weather_api.get_forecast(tomorrow, workout_hour)
        if weather_data:
            _, weather_info, _ = calculate_heat_adjustment(weather_data)

    return {
        "date": tomorrow.isoformat(),
        "name": template['name'],
        "type": workout_type,
        "category": workout_category,
        "duration": duration_min,
        "distance": distance_km,
        "tss": tss_data['target_tss'],
        "reason": reason,
        "decision_factors": factors,
        "decision_log": decision_log,
        "weather": weather_info
    }


def get_today_workout() -> dict:
    """Récupère le workout planifié pour aujourd'hui depuis Intervals.icu."""
    config, today, api, _, _ = _get_initialized_components()
    if not api:
        return None

    events = api.get_events(today, today)
    for event in events:
        if event.get('category') == 'WORKOUT' and 'Run' in str(event.get('type', '')):
            name = event.get('name', '')

            # Extraire TSS du nom (format: "XX TSS - Type")
            tss = 0
            if 'TSS' in name:
                try:
                    tss = int(name.split('TSS')[0].strip())
                except ValueError:
                    tss = event.get('load', 0)
            else:
                tss = event.get('load', 0)

            # Extraire type du nom
            workout_type = 'easy'
            name_lower = name.lower()
            if 'récup' in name_lower or 'recup' in name_lower:
                workout_type = 'recovery'
            elif 'long' in name_lower:
                workout_type = 'long_run'
            elif 'fractionné' in name_lower or 'vo2' in name_lower or 'interval' in name_lower:
                workout_type = 'intervals'

            return {
                "date": event.get('start_date_local', today.isoformat())[:10],
                "name": name,
                "type": workout_type,
                "tss": tss,
                "description": event.get('description', ''),
                "from_intervals": True
            }

    return None


def get_activity_history(days: int = 60) -> list:
    """Retourne l'historique des activités sur N jours."""
    config, today, api, _, _ = _get_initialized_components()
    if not api:
        return []

    activities = api.get_activities(today - timedelta(days=days), today)

    result = []
    for a in activities:
        if a.get('type') != 'Run':
            continue
        result.append({
            "date": a.get('start_date_local', '')[:10],
            "name": a.get('name', 'Run'),
            "distance_km": round((a.get('distance') or 0) / 1000, 2),
            "duration_min": round((a.get('moving_time') or 0) / 60, 1),
            "tss": a.get('icu_training_load') or 0,
            "avg_hr": a.get('average_heartrate'),
            "max_hr": a.get('max_heartrate'),
            "intensity": a.get('icu_intensity')
        })

    return sorted(result, key=lambda x: x['date'], reverse=True)


def get_wellness_history(days: int = 30) -> list:
    """Retourne l'historique wellness (CTL, ATL, TSB) sur N jours."""
    config, today, api, _, _ = _get_initialized_components()
    if not api:
        return []

    start_date = today - timedelta(days=days)
    wellness_data = api.get_wellness_range(start_date, today)

    return wellness_data


def get_wellness_history_with_acwr(days: int = 30) -> list:
    """Retourne l'historique wellness avec ACWR calcule pour chaque jour."""
    history = get_wellness_history(days)
    for item in history:
        ctl = item.get('ctl', 0)
        atl = item.get('atl', 0)
        item['acwr'] = round(atl / ctl, 2) if ctl > 0 else 1.0
    return history


def get_weekly_tss(weeks: int = 8) -> list:
    """Retourne le TSS par semaine sur N semaines."""
    config, today, api, _, _ = _get_initialized_components()
    if not api:
        return []

    athlete_info = api.get_athlete_info()
    activities = api.get_activities(today - timedelta(days=weeks * 7 + 7), today)

    analyzer = DataAnalyzer(activities, athlete_info)
    return analyzer.get_weekly_stats(weeks)


# ==============================================================================
# --- MAIN ---
# ==============================================================================
def main():
    print(f"\n{'='*60}")
    print(f"  RUNNING COACH v{VERSION} - Polarized Data-Driven")
    print(f"{'='*60}\n")

    # Charger config
    config = DEFAULT_CONFIG.copy()
    try:
        with open("config.json") as f:
            user_config = json.load(f)
            # Merge configs
            for key in user_config:
                if isinstance(user_config[key], dict) and key in config:
                    config[key].update(user_config[key])
                else:
                    config[key] = user_config[key]
    except FileNotFoundError:
        print("Info: Pas de config.json, utilisation des defauts")
    except json.JSONDecodeError as e:
        print(f"Attention: Erreur config.json: {e}, utilisation des defauts")

    # Timezone
    try:
        tz_str = config.get('operational_settings', {}).get('timezone', 'Europe/Paris')
        tz = ZoneInfo(tz_str)
        today = datetime.now(tz).date()
    except:
        today = date.today()

    tomorrow = today + timedelta(days=1)
    print(f"Date: Aujourd'hui: {today.isoformat()}")
    print(f"Date: Planification pour: {tomorrow.isoformat()} (DEMAIN)")

    # Credentials
    try:
        api_key = os.environ['API_KEY']
        athlete_id = os.environ['ATHLETE_ID']
    except KeyError as e:
        print(f"Erreur: Variable manquante: {e}")
        return

    # Clé API météo (optionnelle)
    weather_api_key = os.environ.get('OPENWEATHER_API_KEY', '')

    # API
    api = IntervalsAPI(athlete_id, api_key)

    # Données
    print("\nRecuperation des donnees...")
    wellness = api.get_wellness(today)
    if not wellness:
        print("Erreur: Impossible de recuperer wellness")
        return

    # Récupérer l'historique wellness pour le readiness score (14 jours)
    wellness_history = api.get_wellness_range(today - timedelta(days=14), today)

    athlete_info = api.get_athlete_info()
    activities = api.get_activities(today - timedelta(days=60), today)

    # Récupérer les paramètres HR depuis sport-settings
    sport_settings = api.get_sport_settings("Run")
    if sport_settings.get('lthr'):
        athlete_info['lthr'] = sport_settings['lthr']
    if sport_settings.get('max_hr'):
        athlete_info['max_hr'] = sport_settings['max_hr']

    # Analyseur
    analyzer = DataAnalyzer(activities, athlete_info)
    run_count = len(analyzer.activities)
    print(f"OK: {run_count} runs analyses sur 60 jours")
    print(f"OK: FC max: {analyzer.max_hr}, LTHR: {analyzer.threshold_hr}")
    print(f"OK: Pace Z2 moyen: {analyzer.avg_easy_pace:.1f} min/km")

    # État actuel
    print(f"\nEtat actuel:")
    print(f"  CTL: {wellness['ctl']:.1f} | ATL: {wellness['atl']:.1f} | TSB: {wellness['tsb']:.1f}")

    # Calcul du readiness score
    readiness = calculate_readiness_score(wellness_history)
    print(f"  Readiness Score: {readiness['readiness_score']:.2f} ({readiness['status']})")
    if readiness['components'].get('sleep', {}).get('avg_3d'):
        print(f"  Sommeil (3j): {readiness['components']['sleep']['avg_3d']:.1f}h/nuit")
    if readiness['components'].get('resting_hr', {}).get('baseline'):
        print(f"  FC repos: {readiness['components']['resting_hr'].get('value')} bpm (baseline: {readiness['components']['resting_hr']['baseline']:.0f})")

    # Moteur de décision
    engine = PolarizedEngine(config, analyzer, wellness, today, wellness_history)

    # Étape 1: Jour de course DEMAIN? (100% data-driven)
    should_run, reason, factors = engine.should_run_tomorrow()
    print(f"\nAnalyse COURSE/REPOS pour DEMAIN ({tomorrow.isoformat()}):")
    for factor in factors:
        print(f"  * {factor}")
    print(f"\n  -> {reason}")

    if not should_run:
        print(f"\nDEMAIN ({tomorrow.isoformat()}) est un jour de REPOS. Pas de seance generee.")
        print(f"\n{'='*60}")
        return

    print(f"\nDEMAIN ({tomorrow.isoformat()}) est un jour de COURSE!")

    # Étape 2: TSS cible
    tss_data = engine.calculate_target_tss()
    original_tss = tss_data['target_tss']
    print(f"\nTSS cible: {original_tss} ({tss_data['reason']})")

    # Étape 2b: Ajustement météo
    weather_config = config.get('weather', DEFAULT_CONFIG['weather'])
    weather_data = None
    weather_info = None
    weather_adjustment = 1.0

    if weather_config.get('enabled', True) and weather_api_key:
        location = weather_config.get('location', DEFAULT_CONFIG['weather']['location'])
        workout_hour = weather_config.get('workout_hour', 7)

        weather_api = WeatherAPI(
            api_key=weather_api_key,
            lat=location['lat'],
            lon=location['lon']
        )

        print(f"\nRecuperation meteo pour {location.get('name', 'votre position')}...")
        weather_data = weather_api.get_forecast(tomorrow, workout_hour)

        if weather_data:
            weather_adjustment, weather_info, weather_advice = calculate_heat_adjustment(weather_data)

            print(f"  Prevision: {weather_data['description']}")
            print(f"  Temperature: {weather_data['temp']:.1f} C (ressenti: {weather_data.get('feels_like', weather_data['temp']):.1f} C)")
            print(f"  Humidite: {weather_data['humidity']}%")

            if weather_info:
                print(f"  Indice chaleur: {weather_info['heat_index']} C")

            if weather_adjustment < 1.0:
                adjusted_tss = int(original_tss * weather_adjustment)
                print(f"  Attention: {weather_advice}")
                print(f"  -> TSS ajuste: {original_tss} x {weather_adjustment:.0%} = {adjusted_tss}")
                tss_data['target_tss'] = adjusted_tss
                tss_data['weather_adjusted'] = True
                tss_data['original_tss'] = original_tss
            else:
                print(f"  OK: {weather_advice}")
                tss_data['weather_adjusted'] = False

            if weather_adjustment == 0.0:
                print(f"\nConditions meteo extremes - REPOS recommande demain.")
                print(f"\n{'='*60}")
                return
        else:
            print("  Attention: Previsions non disponibles")
    elif not weather_api_key and weather_config.get('enabled', True):
        print("\nMeteo: OPENWEATHER_API_KEY non configuree (ajustement desactive)")

    # Étape 3: Type de séance
    workout_category, decision_log = engine.select_workout_type()
    print(f"\nDecision:")
    for log in decision_log:
        print(f"  {log}")

    # Étape 4: Workout spécifique
    workout_type = engine.choose_specific_workout(workout_category, tss_data['target_tss'])
    print(f"\nWorkout selectionne: {workout_type}")

    # Étape 5: Durée et distance
    duration_min = engine.calculate_workout_duration(workout_type, tss_data['target_tss'])
    distance_km = engine.estimate_distance(duration_min, workout_type)
    print(f"Duree: {duration_min} min | Distance estimee: {distance_km} km")

    # Vérifier si workout déjà planifié pour DEMAIN
    existing = api.get_events(tomorrow, tomorrow)
    for event in existing:
        if event.get('category') == 'WORKOUT' and 'Run' in str(event.get('type', '')):
            print(f"\nAttention: Workout deja planifie pour DEMAIN ({tomorrow.isoformat()}): {event.get('name')}")
            print("-> Pas de nouvelle seance creee.")
            print(f"\n{'='*60}")
            return

    # Construire le workout pour DEMAIN
    builder = WorkoutBuilder(config, analyzer)
    workout = builder.build(
        workout_type=workout_type,
        target_tss=tss_data['target_tss'],
        duration_min=duration_min,
        distance_km=distance_km,
        wellness=wellness,
        decision_log=decision_log,
        workout_date=tomorrow,
        weather_info=weather_info
    )

    print(f"\nWorkout genere pour DEMAIN:")
    print(f"  Nom: {workout['name']}")
    print(f"  Date: {tomorrow.isoformat()}")
    print(f"  TSS: {workout['load']}")

    # Upload
    if config.get('operational_settings', {}).get('live_mode', False):
        print("\nUpload vers Intervals.icu...")
        result = api.create_workout(workout)
        if result:
            print("OK: Workout uploade avec succes!")
        else:
            print("Erreur: Echec de l'upload")
    else:
        print("\nMode DRY RUN - Workout non uploade")
        print("\n--- Description ---")
        print(workout['description'])

    print(f"\n{'='*60}")
    print("  Script termine")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
