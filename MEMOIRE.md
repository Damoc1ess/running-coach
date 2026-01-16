# RUN - Coach Running Intelligent

## Vision du Projet
Créer un coach/programme d'analyse des courses basé sur les données de la montre **Coros Pace 3** pour :
- Optimiser efficacement la progression
- Minimiser le risque de blessure

---

## 1. Accès aux Données Coros

### Export des données
Coros ne propose **pas d'API publique**. L'accès aux données se fait via :

| Méthode | Format | Détails |
|---------|--------|---------|
| Export manuel | FIT, TCX, GPX | Via l'app Coros → Workout → Details → Export |
| Export en masse | FIT, TCX | Via [COROS Training Hub](https://training.coros.com) (desktop) |

**Limitation** : Les données quotidiennes (FC repos, pas, sommeil) ne sont pas exportables.

### Intégrations tierces disponibles
Synchronisation automatique possible avec :
- **Strava** - Réseau social sportif
- **Runalyze** - Analyse approfondie (recommandé)
- **TrainingPeaks** - Planification avancée
- **Stryd** - Analyse de puissance running
- **SportTracks** - Suivi et analyse
- **Tredict** - Planification indépendante

Sources : [Export COROS](https://support.coros.com/hc/en-us/articles/360043975752-Exporting-Workout-Data-and-Uploading-to-3rd-Party-Apps) | [Apps tierces](https://support.coros.com/hc/en-us/articles/360040256531-Supported-3rd-Party-Apps) | [Bulk Export](https://support.coros.com/hc/en-us/articles/25002333092500-Requesting-a-Bulk-Export-of-COROS-Data)

---

## 2. Données Disponibles (Format FIT)

### Données temps réel (par seconde)
- Position GPS (latitude, longitude)
- Fréquence cardiaque
- Vitesse / Allure
- Distance
- Altitude
- Cadence (pas/min)
- Température
- Puissance (si capteur Stryd)

### Données de session
- Durée dans chaque zone FC (5 zones)
- Durée dans chaque zone d'allure (5 zones)
- Durée dans chaque zone de puissance (5 zones)
- Training Load
- Splits par tour

### Métriques dérivées calculables
- **VO2max effectif** (relation FC/allure)
- **TRIMP** (Training Impulse)
- **GAP** (Grade Adjusted Pace)
- **Efficacité aérobie**
- **Découplage aérobie** (cardiac drift)
- **Indice de variabilité**

Sources : [Garmin FIT SDK](https://developer.garmin.com/fit/protocol/) | [FIT Description](https://apizone.suunto.com/fit-description)

---

## 3. Métriques Clés pour la Prévention des Blessures

### Acute-Chronic Workload Ratio (ACWR)
Le ratio charge aiguë / charge chronique compare les 7 derniers jours aux 28 jours précédents.

| ACWR | Interprétation | Risque |
|------|----------------|--------|
| < 0.8 | Désentraînement | Faible mais sous-optimal |
| **0.8 - 1.3** | **Zone optimale** | **Minimal** |
| 1.3 - 1.5 | Zone de danger | Modéré |
| 1.5 - 2.0 | Surcharge | Élevé (OR=1.69) |
| > 2.0 | Surcharge critique | Très élevé (OR=4.00) |

### Heart Rate Variability (HRV)
La VFC (Variabilité de Fréquence Cardiaque) est un indicateur de récupération et de tolérance à l'entraînement.

**Protocole recommandé** :
1. Mesure quotidienne au réveil
2. Calculer moyenne 7 jours (RMSSD)
3. Calculer coefficient de variation (CV)
4. Un CV élevé sur plusieurs semaines = signe précoce de maladaptation

**Interaction HRV × ACWR** :
- HRV normale/haute + ACWR élevé → Risque faible (tolérance OK)
- **HRV basse + ACWR élevé → Risque très élevé**

### Autres indicateurs
- **Training Load** (charge interne via FC ou RPE)
- **Monotonie** (variation de la charge)
- **Strain** (charge × monotonie)

Sources : [ACWR Study](https://pmc.ncbi.nlm.nih.gov/articles/PMC7047972/) | [HRV & Workload](https://pmc.ncbi.nlm.nih.gov/articles/PMC5721172/) | [HRV Applications](https://pmc.ncbi.nlm.nih.gov/articles/PMC11204851/)

---

## 4. Solutions Existantes Analysées

### Runalyze (Analyse uniquement)
**Avantages** :
- Gratuit et très complet
- Supporte Coros (sync auto via Strava ou import FIT)
- Calcule VO2max, TRIMP, prédictions courses
- Données privées par défaut
- Interface en français

**Limitations** :
- ❌ **Pas de création de plans d'entraînement**
- Pas d'alertes prédictives de blessure
- Outil d'analyse rétrospective uniquement

Source : [Runalyze](https://runalyze.com/)

---

### Comparaison Détaillée : TrainAsONE vs Athletica.ai

Ces deux solutions correspondent au besoin : **analyser le passé → adapter le futur**.

#### Tableau Comparatif

| Critère | **TrainAsONE** | **Athletica.ai** |
|---------|---------------|------------------|
| **Focus principal** | Running pur | Multi-sport (triathlon, vélo, running) |
| **Prévention blessures** | ⭐⭐⭐ **Core focus** - 63% réduction rapportée | ⭐⭐ Périodisation progressive |
| **Sync Coros** | ❌ Pas direct (via Strava) | ✅ **Direct** |
| **Adaptation IA** | Recalibre en 24h après chaque course | Ajuste selon récupération + forme |
| **Renforcement musculaire** | ❌ Limité | ✅ Inclus avec vidéos |
| **Interface** | Plus complexe, riche en données | Plus simple, épurée |
| **Distances** | 5K → Ultra | 5K → Ultra |
| **Créateur** | Équipe spécialisée running | Paul Laursen (chercheur HIIT) |

#### Tarification

| | TrainAsONE | Athletica.ai |
|--|-----------|--------------|
| **Gratuit** | ✅ Plan basique (1 objectif) | ✅ Essai 14 jours |
| **Essai premium** | 21 jours | 14 jours |
| **Mensuel** | ~12€/mois (~£9.99) | ~19€/mois ($19.90) |
| **Annuel** | ~115€/an (~£99.99) | ~175€/an ($189) |

#### TrainAsONE - Détails

**Points forts** :
- Focus #1 sur la **prévention des blessures** (argument marketing principal)
- Utilisateurs rapportent **63% de réduction des blessures**
- Recalibrage du plan sous 24h après chaque course
- Gestion fine de la charge : min 48h entre séances intenses
- Algorithmes basés sur données de dizaines de milliers de coureurs
- Ajustement selon altitude et météo (premium)
- Idéal pour coureurs "injury-prone" ou avec emploi du temps variable

**Limitations** :
- Pas de sync directe Coros (nécessite Strava)
- Interface plus complexe / technique
- Peu de renforcement musculaire

**Intégrations** : Garmin, Strava, Runkeeper, Fitbit, Polar, Suunto, Zwift, HRV4Training

Source : [TrainAsONE](https://trainasone.com/) | [Review 2025](https://ultramarathon.umit.net/trainasone-2025-review/)

#### Athletica.ai - Détails

**Points forts** :
- **Sync directe avec Coros**
- Renforcement musculaire intégré avec vidéos
- Interface plus simple et épurée
- AI Coach Avatar pour insights personnalisés
- Créé par Paul Laursen (chercheur reconnu en physiologie du sport)
- Périodisation progressive bien structurée
- Multi-sport si intérêt futur (triathlon, vélo)

**Limitations** :
- Plus cher
- Moins focalisé sur la prévention blessures running spécifiquement
- Moins de granularité dans l'adaptation quotidienne

**Intégrations** : Garmin, Coros, Wahoo, Strava, Intervals.icu, Concept2

Source : [Athletica.ai](https://athletica.ai/) | [Forum TrainerRoad](https://www.trainerroad.com/forum/t/another-ai-training-app-athletica-ai/82882)

#### Recommandation

| Si ta priorité est... | Choix recommandé |
|----------------------|------------------|
| Prévention blessures avant tout | **TrainAsONE** |
| Sync directe Coros (simplicité) | **Athletica.ai** |
| Budget serré | **TrainAsONE** (gratuit dispo) |
| Renforcement musculaire inclus | **Athletica.ai** |
| Interface data-rich | **TrainAsONE** |
| Interface simple | **Athletica.ai** |

**Suggestion** : Tester les deux via leurs essais gratuits (TrainAsONE 21j puis Athletica 14j).

---

### Autres Solutions (pour référence)

#### Striv
- Focus sur la **prévention des blessures** via analyse de forme
- Analyse foulée et pression
- Détecte changements = signes précoces de blessure
- Nécessite leurs capteurs spécifiques

Source : [Striv](https://striv.run/coaching)

#### HumanGO
- Plans personnalisés 5K à marathon
- Inclut renforcement, récupération, prévention
- Cross-training intégré

Source : [HumanGO](https://apps.apple.com/us/app/humango-ai-training-planner/id1554430755)

---

## 5. Valeur Ajoutée d'une Solution Custom

### Ce que les solutions existantes ne font pas bien :
1. **Intégration complète des métriques Coros** (toutes les apps n'exploitent pas tout)
2. **Alertes prédictives combinées** (HRV × ACWR × tendances)
3. **Personnalisation totale** des seuils et algorithmes
4. **Propriété des données** et analyses
5. **Visualisations sur mesure** adaptées à tes besoins

### Architecture envisageable :

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Coros Pace 3  │────▶│  Export FIT      │────▶│   Parsing       │
│   (courses)     │     │  (manuel/auto)   │     │   Python/Node   │
└─────────────────┘     └──────────────────┘     └────────┬────────┘
                                                          │
                                                          ▼
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Dashboard     │◀────│  Analyse/IA      │◀────│   Base données  │
│   (Web/App)     │     │  (Alertes,       │     │   (historique)  │
│                 │     │   prédictions)   │     │                 │
└─────────────────┘     └──────────────────┘     └─────────────────┘
```

---

## 6. Solution Choisie : Running Coach v2.0 (Custom)

Après analyse des solutions existantes, **aucune solution open source gratuite** ne propose à la fois :
- Analyse des données passées
- Génération automatique de plans adaptatifs
- Sync avec Coros

**Décision** : Développement d'une solution custom basée sur :
- [intervals-icu-planner](https://github.com/LucasVance/intervals-icu-planner) comme base
- API Intervals.icu (gratuit, sync directe Coros)
- Algorithmes scientifiques éprouvés (Banister, Seiler 80/20, Friel)

---

## 7. Running Coach v2.2 - 100% Data-Driven

### Philosophie

**100% des décisions basées sur les données** - aucun input humain requis, aucune règle arbitraire.

L'algorithme analyse automatiquement :
- Historique des courses (60 jours)
- Distribution d'intensité (21 jours)
- État de forme (CTL/ATL/TSB)
- Ratio charge aiguë/chronique (ACWR)
- Récupération depuis dernière séance

Et décide seul :
- **Si c'est un jour de course ou repos** (basé sur TSB/ACWR, pas de règle fixe)
- Le type de séance (easy ou hard)
- La durée optimale
- La distance estimée

### Localisation

- **Code source** : `/Projects/RUN/running-coach/`
- **GitHub** : https://github.com/Damoc1ess/running-coach
- **Déploiement** : Serveur homelab `~/running-coach/`

### Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Coros Pace 3  │────▶│  Intervals.icu   │────▶│  Running Coach  │
│   (courses)     │     │  (sync auto)     │     │  v2.2 (Python)  │
└─────────────────┘     └──────────────────┘     └────────┬────────┘
                                                          │
                                                          ▼
                        ┌──────────────────┐     ┌─────────────────┐
                        │  Coros App       │◀────│  Workout DEMAIN │
                        │  → Montre        │     │  (J+1)          │
                        └──────────────────┘     └─────────────────┘
```

**Important v2.2** : Le script génère les workouts pour **DEMAIN** (J+1), pas aujourd'hui.
Coros ne synchronise que les workouts futurs, pas ceux du jour même.

### Principe Polarisé (Seiler 80/20)

Basé sur les recherches de Stephen Seiler sur les athlètes d'élite :

| Zone | % Cible | Type |
|------|---------|------|
| Zone 1-2 (Easy) | **80%** | Récupération, Endurance, Long |
| Zone 3 (Tempo) | **≈0%** | Évitée ("gray zone") |
| Zone 4-5 (Hard) | **20%** | Intervalles VO2max/Seuil |

**Pourquoi éviter la Zone 3 ?**
- Trop dur pour récupérer rapidement
- Pas assez dur pour maximiser les adaptations
- Accumule fatigue sans bénéfice proportionnel

Sources : [Seiler Research](https://pubmed.ncbi.nlm.nih.gov/20861519/) | [Meta-analyse 2024](https://pmc.ncbi.nlm.nih.gov/articles/PMC11329428/)

### Algorithmes Implémentés

| Algorithme | Source | Usage |
|------------|--------|-------|
| **Fitness-Fatigue (PMC)** | Banister, 1975 | Calcul CTL/ATL/TSB |
| **ACWR** | Gabbett, 2016 | Ratio charge aiguë/chronique (risque blessure) |
| **Distribution Polarisée** | Seiler, 2010 | 80% easy / 20% hard |
| **Zones HR** | Joe Friel | 5 zones basées sur seuil lactique |
| **ALB (Acute Load Balance)** | ACWR adapté | Limite pics de charge |

### Logique de Décision (100% Data-Driven)

**Note v2.2** : Toutes les décisions sont prises pour **DEMAIN**, pas aujourd'hui.
Les calculs de "jours depuis" projettent jusqu'à demain.

```
ÉTAPE 1: DEMAIN est-il un jour de COURSE ou REPOS?
├── SI couru aujourd'hui          → évaluation repos (1j seulement)
├── SI TSB < -25                  → REPOS (surentraînement)
├── SI ACWR > 1.5                 → REPOS (risque blessure)
├── SI TSB > 15 ET 3j+ repos      → COURSE (risque désentraînement)
├── SI TSB > 5                    → COURSE (bien récupéré)
├── SI TSB > -15 ET 2j+ repos     → COURSE (récupération suffisante)
├── SI 4j+ sans courir            → COURSE (maintien fitness)
├── SI TSB < 0 ET < 2j repos      → REPOS (encore fatigué)
└── DÉFAUT                        → REPOS (en cas de doute)

ÉTAPE 2: Calculer TSS cible
├── Modèle Banister (CTL/ATL/TSB)
└── Cap ALB pour sécurité

ÉTAPE 3: Analyser distribution (21 jours)
├── Compter séances EASY (Z1-Z2)
├── Compter séances HARD (Z4-Z5)
└── Calculer ratio actuel

ÉTAPE 4: Sélectionner type (POLARISÉ)
├── SI TSB < -25           → RECOVERY
├── SI dernière hard < 48h → EASY
├── SI hard% > 25%         → EASY (rétablir 80/20)
├── SI hard% < 15% ET 4j+  → HARD
├── SI TSB > 5 ET 3j+      → HARD possible
└── DÉFAUT                 → EASY

ÉTAPE 5: Calculer durée
└── Durée = TSS / (IF² × 100)

ÉTAPE 6: Estimer distance
└── Distance = Durée × Pace Z2 moyen
```

### Données utilisées (toutes viennent de la montre)

| Donnée | Source | Utilisation |
|--------|--------|-------------|
| CTL (Chronic Training Load) | Intervals.icu | Niveau de fitness |
| ATL (Acute Training Load) | Intervals.icu | Niveau de fatigue |
| TSB (Training Stress Balance) | CTL - ATL | État de forme actuel |
| ACWR | ATL / CTL | Risque de blessure |
| Historique runs | Intervals.icu | Distribution, jours depuis run |
| FC max / seuil | Profil athlète | Zones HR |
| Pace moyen Z2 | Activités récentes | Estimation distance |

### Fonctionnalités v2.2

- [x] Récupération automatique CTL/ATL/TSB depuis Intervals.icu
- [x] Calcul du TSS optimal (modèle Banister)
- [x] **Distribution polarisée 80/20 automatique**
- [x] **Analyse de la distribution sur 21 jours**
- [x] **Décision COURSE/REPOS 100% data-driven (TSB + ACWR)**
- [x] **Aucune règle arbitraire (plus de "jour sur deux" fixe)**
- [x] Protection anti-blessure (ACWR > 1.5 → repos)
- [x] Calcul automatique des zones HR
- [x] **Calcul dynamique durée/distance**
- [x] Upload automatique → Sync montre Coros
- [x] Déploiement serveur avec cron
- [x] **v2.2.0: Génération pour DEMAIN (J+1)** - compatibilité sync Coros
- [x] **v2.2.1: LTHR récupéré depuis Intervals.icu** - plus d'estimation

### Templates de Séances (Polarisés)

| Template | Catégorie | Zones | Description |
|----------|-----------|-------|-------------|
| `recovery` | Easy | Z1-2 | Récupération active |
| `easy` | Easy | Z2 | Endurance facile |
| `long_run` | Easy | Z2 | Sortie longue |
| `intervals` | Hard | Z5 | Fractionné VO2max (1min/1min) |
| `intervals_long` | Hard | Z4 | Fractionné seuil (4min/2min) |

**Note** : Pas de template "tempo" (Zone 3) - conformément au principe polarisé.

### Configuration

Fichier `config.json` :
```json
{
  "polarized": {
    "easy_target_percent": 80,      // 80% séances faciles
    "hard_target_percent": 20,      // 20% séances intenses
    "min_days_between_hard": 2,     // Min 48h récup
    "analysis_window_days": 21      // Fenêtre analyse
  },
  "banister": {
    "ctl_days": 42,                 // Fenêtre fitness
    "atl_days": 7,                  // Fenêtre fatigue
    "target_tsb": -15.0,            // TSB cible
    "alb_lower_bound": -25.0,       // Limite charge
    "tsb_recovery_threshold": -25.0 // Seuil récup forcée
  },
  "operational_settings": {
    "live_mode": true,
    "timezone": "Europe/Paris"
  }
}
```

### Déploiement

#### Serveur Homelab
- **Adresse** : `192.168.1.42`
- **Chemin** : `~/running-coach/`
- **Cron** : Tous les jours à **21h** (après les courses du jour)
- **Credentials** : Fichier `.env` local

```bash
# Connexion
ssh florent@192.168.1.42

# Structure
~/running-coach/
├── main.py         # Script v2.2
├── config.json     # Configuration
├── .env            # ATHLETE_ID + API_KEY
├── run.sh          # Lanceur
└── log.txt         # Logs

# Cron configuré (21h pour avoir les données du jour)
0 21 * * * /home/florent/running-coach/run.sh
```

**Pourquoi 21h ?** Le script analyse les données du jour pour décider de demain.
Si exécuté le matin, une course l'après-midi invaliderait la prédiction.

#### Test manuel
```bash
cd ~/running-coach
source .env && export API_KEY ATHLETE_ID
python3 main.py
```

### Exemple de Sortie

```
============================================================
  RUNNING COACH v2.2.1 - Polarized Data-Driven
============================================================

📅 Aujourd'hui: 2026-01-16
📅 Planification pour: 2026-01-17 (DEMAIN)

📡 Récupération des données...
✓ 15 runs analysés sur 60 jours
✓ FC max: 172, LTHR: 167
✓ Pace Z2 moyen: 7.3 min/km

📊 État actuel:
  CTL: 11.2 | ATL: 17.6 | TSB: -6.3

🏃 Analyse COURSE/REPOS pour DEMAIN (2026-01-17):
  • TSB: -6.3
  • ACWR: 1.56
  • Jours depuis run (demain): 1
  • → Run aujourd'hui, évaluation repos
  • → REPOS demain (ACWR > 1.5, risque blessure)

  → ACWR trop élevé (1.56), risque de blessure

🛋️  DEMAIN (2026-01-17) est un jour de REPOS. Pas de séance générée.
```

**Note** : Le script a détecté un ACWR trop élevé après la course du jour → repos recommandé.

---

## 8. Configuration des Zones HR

### Paramètres configurés

| Plateforme | LTHR | FC Max |
|------------|------|--------|
| **Coros** | 167 bpm | (auto) |
| **Intervals.icu** | 167 bpm | 172 bpm |

### Zones HR (Lactate Threshold - Friel)

| Zone | Nom | % LTHR | FC (LTHR=167) |
|------|-----|--------|---------------|
| Z1 | Recovery | <80% | < 134 bpm |
| Z2 | Aerobic Endurance | 80-90% | 134-150 bpm |
| Z3 | Aerobic Power | 91-95% | 152-159 bpm |
| Z4 | Threshold | 96-102% | 160-170 bpm |
| Z5 | Anaerobic Endurance | 103-106% | 172-177 bpm |
| Z6 | Anaerobic Power | >106% | > 177 bpm |

### Comment déterminer son LTHR

1. **Test terrain 30 min** : Courir 30 min à fond, FC moyenne des 20 dernières minutes = LTHR
2. **Course longue** : FC moyenne d'un semi-marathon ÷ 0.96 ≈ LTHR
3. **Estimation** : FC max × 0.87 (moins précis)

### Configurer sur Coros

1. App Coros → Settings → Heart Rate Zone
2. Sélectionner **"Lactate Threshold Zone"**
3. Threshold HR → **167** (ou ta valeur)
4. Save

### Configurer sur Intervals.icu

Le script récupère automatiquement LTHR depuis :
`Settings → Sport Settings → Run → LTHR`

---

## 9. Sync Coros

### Comment ça marche

1. **Script** génère workout → **Intervals.icu** (API)
2. **Intervals.icu** push le plan → **Coros Cloud**
3. **App Coros** sync → **Montre**

### Configuration requise

Sur Intervals.icu (Settings → Connections → Coros) :
- [x] Download activities
- [x] Download wellness data
- [x] **Upload planned workouts** ← Important !

### Où trouver la séance sur Coros

1. App Coros → **Profil** → **Training Plan**
2. Chercher "**Intervals.icu**" dans les plans
3. La séance du jour apparaît automatiquement
4. Sync montre (tirer vers le bas)

---

## 10. Prochaines Améliorations Possibles

### Court terme
- [x] ~~Tester le script avec tes vraies données~~
- [x] ~~Implémenter distribution polarisée~~
- [x] ~~Déployer sur serveur homelab~~

### Moyen terme
- [ ] Ajouter périodisation automatique (base/build/peak/taper)
- [ ] Intégrer un objectif de course avec date
- [ ] Ajouter gestion des semaines de récupération (1/4)
- [ ] Prise en compte HRV pour ajustement quotidien

### Long terme
- [ ] Dashboard de visualisation web
- [ ] Prédictions de performance (estimations temps)
- [ ] Détection automatique de surentraînement

---

## 11. Ressources Techniques

### Parsing FIT
- [Garmin FIT SDK](https://developer.garmin.com/fit/cookbook/decoding-activity-files/)
- [FITfileR (R)](https://msmith.de/FITfileR/articles/FITfileR.html)
- [fitparse (Python)](https://github.com/dtcooper/python-fitparse)

### Calculs
- [Formules VO2max](https://runalyze.com/help/article/features)
- [TRIMP Calculation](https://www.trainingpeaks.com/learn/articles/what-is-training-stress-score/)
- [ACWR Guidelines](https://runabout.cc/monitoring-training-load-with-the-acute‑chronic-ratio)

---

*Document créé le 16 janvier 2026*
*Dernière mise à jour : 16 janvier 2026 - v2.2 (workouts J+1, LTHR depuis Intervals.icu, cron 21h)*
*Projet : RUN - Coach Running Intelligent*
