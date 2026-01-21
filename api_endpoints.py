"""
Running Coach API - FastAPI Endpoints
API JSON pour integration Homepage et autres services
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import main

app = FastAPI(
    title="Running Coach API",
    description="API pour le dashboard Running Coach - Polarized Data-Driven Training",
    version=main.VERSION
)

# CORS pour permettre les appels depuis Homepage
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ========================================
# MODELES PYDANTIC
# ========================================
class WellnessResponse(BaseModel):
    ctl: float
    atl: float
    tsb: float
    acwr: float
    resting_hr: Optional[int] = None
    hrv: Optional[float] = None
    date: str


class DistributionResponse(BaseModel):
    total_runs: int
    easy_count: int
    hard_count: int
    easy_percent: float
    hard_percent: float
    target_easy: int
    target_hard: int
    days_analyzed: int


class WeatherInfo(BaseModel):
    temp: Optional[float] = None
    feels_like: Optional[float] = None
    humidity: Optional[int] = None
    heat_index: Optional[float] = None
    description: Optional[str] = None
    advice: Optional[str] = None
    adjustment_factor: Optional[float] = None


class NextWorkoutResponse(BaseModel):
    date: str
    name: str
    type: str
    category: Optional[str] = None
    duration: int
    distance: float
    tss: int
    reason: str
    decision_factors: Optional[List[str]] = None
    decision_log: Optional[List[str]] = None
    weather: Optional[WeatherInfo] = None


class TodayWorkoutResponse(BaseModel):
    date: str
    name: str
    type: str
    tss: int
    description: Optional[str] = None
    from_intervals: bool = True


class ActivityRecord(BaseModel):
    date: str
    name: str
    distance_km: float
    duration_min: float
    tss: int
    avg_hr: Optional[int] = None
    max_hr: Optional[int] = None
    intensity: Optional[int] = None


class WellnessRecord(BaseModel):
    date: str
    ctl: float
    atl: float
    tsb: float
    resting_hr: Optional[int] = None
    hrv: Optional[float] = None


class WellnessRecordWithACWR(BaseModel):
    date: str
    ctl: float
    atl: float
    tsb: float
    acwr: float
    resting_hr: Optional[int] = None
    hrv: Optional[float] = None


class WeeklyStats(BaseModel):
    week: int
    runs: int
    distance_km: float
    duration_min: int
    tss: int


class SummaryResponse(BaseModel):
    """Resume pour widget Homepage"""
    ctl: float
    atl: float
    tsb: float
    acwr: float
    next_workout: str
    next_date: str
    next_tss: int
    easy_percent: float
    hard_percent: float


class HealthResponse(BaseModel):
    status: str
    version: str


# ========================================
# ENDPOINTS
# ========================================
@app.get("/health", response_model=HealthResponse)
def health_check():
    """Verification de sante de l'API."""
    return HealthResponse(status="healthy", version=main.VERSION)


@app.get("/api/summary", response_model=SummaryResponse)
def get_summary():
    """
    Resume complet pour widget Homepage.
    Retourne les metriques principales et le prochain workout.
    """
    wellness = main.get_current_wellness()
    if 'error' in wellness:
        raise HTTPException(status_code=503, detail=wellness['error'])

    next_workout = main.get_next_workout_info()
    if 'error' in next_workout:
        next_workout = {
            'name': 'Erreur',
            'date': '',
            'tss': 0
        }

    distribution = main.get_distribution(21)
    if 'error' in distribution:
        distribution = {'easy_percent': 0, 'hard_percent': 0}

    return SummaryResponse(
        ctl=wellness['ctl'],
        atl=wellness['atl'],
        tsb=wellness['tsb'],
        acwr=wellness['acwr'],
        next_workout=next_workout.get('name', 'N/A'),
        next_date=next_workout.get('date', ''),
        next_tss=next_workout.get('tss', 0),
        easy_percent=distribution.get('easy_percent', 0),
        hard_percent=distribution.get('hard_percent', 0)
    )


@app.get("/api/wellness", response_model=WellnessResponse)
def get_wellness():
    """Retourne l'etat de forme actuel (CTL, ATL, TSB, ACWR)."""
    wellness = main.get_current_wellness()
    if 'error' in wellness:
        raise HTTPException(status_code=503, detail=wellness['error'])
    return WellnessResponse(**wellness)


@app.get("/api/distribution", response_model=DistributionResponse)
def get_distribution(days: int = 21):
    """
    Retourne la distribution polarisee (easy vs hard).

    Args:
        days: Nombre de jours a analyser (defaut: 21)
    """
    distribution = main.get_distribution(days)
    if 'error' in distribution:
        raise HTTPException(status_code=503, detail=distribution['error'])
    return DistributionResponse(**distribution)


@app.get("/api/next-workout", response_model=NextWorkoutResponse)
def get_next_workout():
    """Retourne les informations sur la prochaine seance planifiee."""
    workout = main.get_next_workout_info()
    if 'error' in workout:
        raise HTTPException(status_code=503, detail=workout['error'])

    # Convertir weather dict en WeatherInfo si present
    if workout.get('weather'):
        workout['weather'] = WeatherInfo(**workout['weather'])

    return NextWorkoutResponse(**workout)


@app.get("/api/today-workout")
def get_today_workout():
    """Retourne le workout planifie pour aujourd'hui (depuis Intervals.icu)."""
    workout = main.get_today_workout()
    if workout:
        return TodayWorkoutResponse(**workout)
    return {"message": "Pas de workout aujourd'hui", "type": "rest", "tss": 0}


@app.get("/api/activities", response_model=List[ActivityRecord])
def get_activities(days: int = 30):
    """
    Retourne l'historique des activites.

    Args:
        days: Nombre de jours d'historique (defaut: 30)
    """
    activities = main.get_activity_history(days)
    return [ActivityRecord(**a) for a in activities]


@app.get("/api/wellness-history", response_model=List[WellnessRecord])
def get_wellness_history(days: int = 30):
    """
    Retourne l'historique wellness (CTL, ATL, TSB).

    Args:
        days: Nombre de jours d'historique (defaut: 30)
    """
    history = main.get_wellness_history(days)
    return [WellnessRecord(**w) for w in history]


@app.get("/api/wellness-history-acwr", response_model=List[WellnessRecordWithACWR])
def get_wellness_history_acwr(days: int = 30):
    """
    Retourne l'historique wellness avec ACWR calcule pour chaque jour.

    Args:
        days: Nombre de jours d'historique (defaut: 30)
    """
    history = main.get_wellness_history_with_acwr(days)
    return [WellnessRecordWithACWR(**w) for w in history]


@app.get("/api/weekly-tss", response_model=List[WeeklyStats])
def get_weekly_tss(weeks: int = 8):
    """
    Retourne le TSS par semaine.

    Args:
        weeks: Nombre de semaines (defaut: 8)
    """
    stats = main.get_weekly_tss(weeks)
    return [WeeklyStats(**s) for s in stats]


# ========================================
# READINESS SCORE (Algorithme Scientifique)
# ========================================
class ReadinessComponent(BaseModel):
    value: Optional[float] = None
    modifier: float
    threshold: Optional[str] = None
    baseline: Optional[float] = None
    elevation: Optional[float] = None
    avg_3d: Optional[float] = None
    last_night: Optional[float] = None
    note: Optional[str] = None


class ReadinessResponse(BaseModel):
    readiness_score: float
    status: str
    date: str
    components: dict
    recommendations: List[str]


@app.get("/api/readiness", response_model=ReadinessResponse)
def get_readiness():
    """
    Retourne le readiness score base sur algorithme scientifique multi-facteurs.

    Sources scientifiques:
    - Banister (1975): Modele impulse-response CTL/ATL/TSB
    - PMC Sleep Studies: Seuil deficit sommeil < 6h cumule
    - Runners Connect / Outside: Seuil FC repos +5-7 bpm
    - Meta-analysis 2025: ACWR zone optimale 0.8-1.3
    """
    readiness = main.get_readiness_score()
    if 'error' in readiness:
        raise HTTPException(status_code=503, detail=readiness['error'])
    return ReadinessResponse(**readiness)


# ========================================
# ENDPOINT SPECIFIQUE HOMEPAGE
# ========================================
@app.get("/api/homepage-widget")
def get_homepage_widget():
    """
    Endpoint optimise pour le widget Homepage.
    Format simplifie avec valeurs pre-formatees.
    """
    wellness = main.get_current_wellness()
    next_workout = main.get_next_workout_info()
    distribution = main.get_distribution(21)

    # Determiner le statut ACWR
    acwr = wellness.get('acwr', 1.0)
    if acwr < 0.8:
        acwr_status = "Sous-entrainement"
    elif acwr <= 1.3:
        acwr_status = "Optimal"
    elif acwr <= 1.5:
        acwr_status = "Attention"
    else:
        acwr_status = "Danger"

    # Determiner le statut TSB
    tsb = wellness.get('tsb', 0)
    if tsb > 10:
        tsb_status = "Tres repose"
    elif tsb > -5:
        tsb_status = "Forme optimale"
    elif tsb > -15:
        tsb_status = "Fatigue moderee"
    else:
        tsb_status = "Fatigue importante"

    return {
        "tsb": round(wellness.get('tsb', 0), 1),
        "tsb_status": tsb_status,
        "acwr": round(wellness.get('acwr', 1.0), 2),
        "acwr_status": acwr_status,
        "ctl": round(wellness.get('ctl', 0), 1),
        "atl": round(wellness.get('atl', 0), 1),
        "next_workout": next_workout.get('name', 'N/A'),
        "next_workout_type": next_workout.get('type', 'unknown'),
        "distribution": f"{distribution.get('easy_percent', 0):.0f}/{distribution.get('hard_percent', 0):.0f}"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
