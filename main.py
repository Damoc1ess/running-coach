# filename: main.py
# Running Coach v2.0 - Polarized Data-Driven Training
# 100% des décisions basées sur les données de la montre

import requests
import json
import os
import re
from datetime import date, timedelta, datetime, time
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

VERSION = "2.0.0"

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
        "timezone": "Europe/Paris"
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
    """Moteur de décision 100% data-driven avec distribution polarisée."""

    def __init__(self, config, analyzer, wellness, today):
        self.config = config
        self.analyzer = analyzer
        self.wellness = wellness
        self.today = today

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

    def should_run_today(self):
        """Détermine si c'est un jour de course (logique jour sur deux)."""
        last_run = self.analyzer.get_last_run_date()
        if not last_run:
            return True, "Aucun run récent trouvé"

        days_since = (self.today - last_run).days

        if days_since == 0:
            return False, "Déjà couru aujourd'hui"
        elif days_since == 1:
            return False, "Couru hier - jour de repos"
        else:
            return True, f"{days_since} jours depuis dernier run"

    def calculate_target_tss(self):
        """Calcule le TSS cible basé sur le modèle Banister."""
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

        return {
            "target_tss": round(final_tss),
            "tss_for_tsb": round(tss_for_tsb),
            "tss_cap": round(tss_cap),
            "reason": reason
        }

    def select_workout_type(self):
        """Sélectionne le type de séance basé sur la distribution polarisée."""
        distribution = self.analyzer.get_training_distribution(self.analysis_window)
        last_hard = self.analyzer.get_last_hard_workout_date()
        tsb = self.wellness['tsb']

        days_since_hard = (self.today - last_hard).days if last_hard else 999

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
              wellness, decision_log, workout_date):
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

        # Rationale
        rationale = f"""
---
📊 Décisions data-driven:
{chr(10).join('• ' + log for log in decision_log)}

📈 État actuel:
• CTL (Fitness): {wellness['ctl']:.1f}
• ATL (Fatigue): {wellness['atl']:.1f}
• TSB (Forme): {wellness['tsb']:.1f}

🎯 Objectifs:
• TSS cible: {target_tss}
• Durée: {duration_min} min
• Distance estimée: {distance_km} km
{zones_text}
---
🤖 Running Coach v{VERSION} - Polarized Data-Driven
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
        print("ℹ️  Pas de config.json, utilisation des défauts")
    except json.JSONDecodeError as e:
        print(f"⚠️  Erreur config.json: {e}, utilisation des défauts")

    # Timezone
    try:
        tz_str = config.get('operational_settings', {}).get('timezone', 'Europe/Paris')
        tz = ZoneInfo(tz_str)
        today = datetime.now(tz).date()
    except:
        today = date.today()

    print(f"📅 Date: {today.isoformat()}")

    # Credentials
    try:
        api_key = os.environ['API_KEY']
        athlete_id = os.environ['ATHLETE_ID']
    except KeyError as e:
        print(f"❌ Variable manquante: {e}")
        return

    # API
    api = IntervalsAPI(athlete_id, api_key)

    # Données
    print("\n📡 Récupération des données...")
    wellness = api.get_wellness(today)
    if not wellness:
        print("❌ Impossible de récupérer wellness")
        return

    athlete_info = api.get_athlete_info()
    activities = api.get_activities(today - timedelta(days=60), today)

    # Analyseur
    analyzer = DataAnalyzer(activities, athlete_info)
    run_count = len(analyzer.activities)
    print(f"✓ {run_count} runs analysés sur 60 jours")
    print(f"✓ FC max: {analyzer.max_hr}, Seuil: {analyzer.threshold_hr}")
    print(f"✓ Pace Z2 moyen: {analyzer.avg_easy_pace:.1f} min/km")

    # État actuel
    print(f"\n📊 État actuel:")
    print(f"  CTL: {wellness['ctl']:.1f} | ATL: {wellness['atl']:.1f} | TSB: {wellness['tsb']:.1f}")

    # Moteur de décision
    engine = PolarizedEngine(config, analyzer, wellness, today)

    # Étape 1: Jour de course?
    should_run, reason = engine.should_run_today()
    print(f"\n🏃 Jour de course? {reason}")

    if not should_run:
        print("→ C'est un jour de REPOS. Pas de séance générée.")
        print(f"\n{'='*60}")
        return

    print("→ C'est un jour de COURSE!")

    # Étape 2: TSS cible
    tss_data = engine.calculate_target_tss()
    print(f"\n🎯 TSS cible: {tss_data['target_tss']} ({tss_data['reason']})")

    # Étape 3: Type de séance
    workout_category, decision_log = engine.select_workout_type()
    print(f"\n🧠 Décision:")
    for log in decision_log:
        print(f"  {log}")

    # Étape 4: Workout spécifique
    workout_type = engine.choose_specific_workout(workout_category, tss_data['target_tss'])
    print(f"\n📋 Workout sélectionné: {workout_type}")

    # Étape 5: Durée et distance
    duration_min = engine.calculate_workout_duration(workout_type, tss_data['target_tss'])
    distance_km = engine.estimate_distance(duration_min, workout_type)
    print(f"⏱️  Durée: {duration_min} min | Distance estimée: {distance_km} km")

    # Vérifier si workout déjà planifié
    existing = api.get_events(today, today)
    for event in existing:
        if event.get('category') == 'WORKOUT' and 'Run' in str(event.get('type', '')):
            print(f"\n⚠️  Workout déjà planifié pour aujourd'hui: {event.get('name')}")
            print("→ Pas de nouvelle séance créée.")
            print(f"\n{'='*60}")
            return

    # Construire le workout
    builder = WorkoutBuilder(config, analyzer)
    workout = builder.build(
        workout_type=workout_type,
        target_tss=tss_data['target_tss'],
        duration_min=duration_min,
        distance_km=distance_km,
        wellness=wellness,
        decision_log=decision_log,
        workout_date=today
    )

    print(f"\n📝 Workout généré:")
    print(f"  Nom: {workout['name']}")
    print(f"  Date: {today.isoformat()}")
    print(f"  TSS: {workout['load']}")

    # Upload
    if config.get('operational_settings', {}).get('live_mode', False):
        print("\n📤 Upload vers Intervals.icu...")
        result = api.create_workout(workout)
        if result:
            print("✅ Workout uploadé avec succès!")
        else:
            print("❌ Échec de l'upload")
    else:
        print("\n🔒 Mode DRY RUN - Workout non uploadé")
        print("\n--- Description ---")
        print(workout['description'])

    print(f"\n{'='*60}")
    print("  Script terminé")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
