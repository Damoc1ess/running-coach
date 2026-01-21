"""
Running Coach - Documentation Technique
Explication detaillee de l'algorithme et des concepts
"""

import streamlit as st

st.set_page_config(
    page_title="Documentation - Running Coach",
    page_icon="📚",
    layout="wide"
)

st.title("Documentation Technique")
st.markdown("*Comprendre l'algorithme et les concepts scientifiques*")

# Navigation
section = st.sidebar.radio(
    "Sections",
    [
        "Vue d'ensemble",
        "Metriques cles",
        "Modele de Banister",
        "Entrainement polarise",
        "Algorithme de decision",
        "Types de seances",
        "Ajustements meteo",
        "Formules et calculs",
        "API Intervals.icu"
    ]
)

# ============================================
# VUE D'ENSEMBLE
# ============================================
if section == "Vue d'ensemble":
    st.header("Vue d'ensemble du projet")

    st.markdown("""
    ## Qu'est-ce que Running Coach ?

    Running Coach est un **systeme d'entrainement automatise** qui genere des seances de course
    a pied basees sur vos donnees physiologiques. Il utilise des modeles scientifiques pour :

    1. **Analyser votre etat de forme** via les donnees d'Intervals.icu
    2. **Decider si vous devez courir ou vous reposer** demain
    3. **Choisir le type de seance** adapte (facile, difficile, longue)
    4. **Calculer l'intensite optimale** (TSS, duree, distance)
    5. **Ajuster selon la meteo** prevue

    ---

    ## Architecture du systeme

    ```
    ┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
    │  Intervals.icu  │────▶│  Running Coach   │────▶│  Coros Watch    │
    │  (donnees)      │     │  (algorithme)    │     │  (execution)    │
    └─────────────────┘     └──────────────────┘     └─────────────────┘
            │                        │
            ▼                        ▼
    - Historique runs         - Decision RUN/REPOS
    - CTL, ATL, TSB           - Type de seance
    - FC repos, sommeil       - TSS cible
    - Zones cardiaques        - Duree, distance
    ```

    ---

    ## Philosophie : Data-Driven

    Toutes les decisions sont basees sur **vos donnees reelles**, pas sur des plans generiques :

    | Donnee | Utilisation |
    |--------|-------------|
    | CTL (Chronic Training Load) | Votre niveau de fitness actuel |
    | ATL (Acute Training Load) | Votre fatigue recente |
    | TSB (Training Stress Balance) | Votre fraicheur/forme du jour |
    | FC repos | Indicateur de recuperation |
    | Sommeil | Qualite de recuperation |
    | Historique | Patterns d'entrainement |

    ---

    ## Cycle quotidien

    ```
    21h00 : Le script s'execute automatiquement
       │
       ▼
    Recuperation des donnees Intervals.icu
       │
       ▼
    Analyse : DEMAIN = RUN ou REPOS ?
       │
       ├── REPOS : Pas de seance creee
       │
       └── RUN : Quel type ?
              │
              ├── Calcul du TSS cible
              ├── Selection du type (easy/hard)
              ├── Calcul duree/distance
              ├── Ajustement meteo
              │
              ▼
         Upload vers Intervals.icu
              │
              ▼
         Sync automatique vers Coros
    ```
    """)

# ============================================
# METRIQUES CLES
# ============================================
elif section == "Metriques cles":
    st.header("Metriques cles expliquees")

    st.markdown("""
    ## CTL - Chronic Training Load (Charge Chronique)

    > **En francais** : Votre niveau de **fitness** ou **condition physique**

    Le CTL represente la moyenne ponderee de votre charge d'entrainement sur les **42 derniers jours**.
    C'est votre "capital fitness" accumule.

    | CTL | Interpretation |
    |-----|----------------|
    | < 20 | Debutant ou reprise |
    | 20-40 | Coureur recreatif |
    | 40-60 | Coureur regulier |
    | 60-80 | Coureur serieux |
    | > 80 | Athlete elite |

    **Formule simplifiee** :
    ```
    CTL(aujourd'hui) = CTL(hier) + (TSS(hier) - CTL(hier)) / 42
    ```

    Le CTL monte lentement (il faut du temps pour construire la fitness) et descend lentement
    (vous ne perdez pas votre forme en quelques jours).

    ---

    ## ATL - Acute Training Load (Charge Aigue)

    > **En francais** : Votre niveau de **fatigue** recente

    L'ATL represente la moyenne ponderee de votre charge sur les **7 derniers jours**.
    C'est votre fatigue accumulee recemment.

    | ATL vs CTL | Interpretation |
    |------------|----------------|
    | ATL < CTL | Vous etes frais, pret a forcer |
    | ATL = CTL | Equilibre charge/recuperation |
    | ATL > CTL | Fatigue accumulee, attention |

    **Formule simplifiee** :
    ```
    ATL(aujourd'hui) = ATL(hier) + (TSS(hier) - ATL(hier)) / 7
    ```

    L'ATL monte et descend rapidement car c'est une fenetre courte.

    ---

    ## TSB - Training Stress Balance (Equilibre)

    > **En francais** : Votre **forme du jour** ou **fraicheur**

    Le TSB est simplement : **TSB = CTL - ATL**

    C'est l'indicateur le plus important pour savoir si vous etes pret a performer.
    """)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        | TSB | Etat | Action |
        |-----|------|--------|
        | > +15 | Tres frais | Risque de perte de forme |
        | +5 a +15 | Frais | Ideal pour competition |
        | -5 a +5 | Equilibre | Entrainement normal |
        | -15 a -5 | Fatigue | Charge productive |
        | < -15 | Epuise | Repos necessaire |
        """)

    with col2:
        st.info("""
        **Exemple concret** :
        - CTL = 45 (bonne fitness)
        - ATL = 52 (semaine chargee)
        - TSB = 45 - 52 = **-7**

        → Vous etes legerement fatigue mais
        c'est normal apres une semaine d'entrainement.
        """)

    st.markdown("""
    ---

    ## ACWR - Acute:Chronic Workload Ratio

    > **En francais** : Ratio de charge aigue/chronique - **Indicateur de risque de blessure**

    L'ACWR compare votre charge recente a votre charge habituelle : **ACWR = ATL / CTL**
    """)

    st.warning("""
    **C'est l'indicateur de SECURITE le plus important !**

    Un ACWR trop eleve signifie que vous avez augmente votre charge trop rapidement
    par rapport a ce que votre corps est habitue a supporter.
    """)

    st.markdown("""
    | ACWR | Zone | Risque blessure | Action |
    |------|------|-----------------|--------|
    | < 0.8 | Sous-entrainement | Faible mais deconditionnement | Augmenter progressivement |
    | 0.8 - 1.3 | **Zone optimale** | Minimal | Continuer |
    | 1.3 - 1.5 | Zone d'attention | Modere | Surveiller |
    | > 1.5 | **Zone de danger** | Eleve | REPOS OBLIGATOIRE |

    **Regle d'or** : Ne jamais augmenter la charge de plus de 10% par semaine.

    ---

    ## TSS - Training Stress Score

    > **En francais** : Score de stress d'entrainement - **Intensite d'une seance**

    Le TSS quantifie la charge d'une seance en combinant duree et intensite.

    | TSS | Type de seance | Recuperation |
    |-----|----------------|--------------|
    | < 50 | Facile | Quelques heures |
    | 50-100 | Moderee | 24-48h |
    | 100-150 | Difficile | 48-72h |
    | > 150 | Tres difficile | 3-5 jours |

    **Formule** :
    ```
    TSS = (duree_secondes × IF² × 100) / 3600

    ou IF (Intensity Factor) = FC_moyenne / LTHR
    ```

    ---

    ## Readiness Score (Score de preparation)

    > **En francais** : A quel point etes-vous pret a vous entrainer ?

    C'est un score composite (0.5 a 1.1) calculant plusieurs facteurs :

    | Facteur | Poids | Ce qu'il mesure |
    |---------|-------|-----------------|
    | TSB | Eleve | Fraicheur generale |
    | FC repos | Moyen | Recuperation cardiaque |
    | Sommeil (3j) | Moyen | Qualite du repos |
    | RampRate | Faible | Vitesse de progression |
    | ACWR | Securite | Risque de blessure |

    | Score | Interpretation |
    |-------|----------------|
    | > 0.95 | Pret - Feu vert total |
    | 0.8 - 0.95 | Prudence - Seance moderee |
    | 0.6 - 0.8 | Attention - Seance legere |
    | < 0.6 | Stop - Repos recommande |
    """)

# ============================================
# MODELE DE BANISTER
# ============================================
elif section == "Modele de Banister":
    st.header("Le Modele de Banister (Fitness-Fatigue)")

    st.markdown("""
    ## Origine

    Le modele de Banister (aussi appele modele Fitness-Fatigue ou modele a deux composantes)
    a ete developpe par le Dr. Eric Banister dans les annees 1970-80.

    ## Concept fondamental

    L'entrainement produit **deux effets opposes** :

    1. **Effet positif (Fitness)** : Amelioration des capacites, monte lentement, dure longtemps
    2. **Effet negatif (Fatigue)** : Epuisement temporaire, monte vite, disparait vite

    La **performance** a un instant T est : **Performance = Fitness - Fatigue**
    """)

    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/4/4b/Fitness-fatigue_model.svg/800px-Fitness-fatigue_model.svg.png",
             caption="Schema du modele Fitness-Fatigue",
             use_container_width=True)

    st.markdown("""
    ## Application dans Running Coach

    | Concept Banister | Notre metrique |
    |------------------|----------------|
    | Fitness | CTL (42 jours) |
    | Fatigue | ATL (7 jours) |
    | Performance | TSB = CTL - ATL |

    ## Constantes de temps

    - **τ₁ (fitness)** = 42 jours : Il faut ~6 semaines pour construire de la fitness
    - **τ₂ (fatigue)** = 7 jours : La fatigue disparait en ~1 semaine

    ## Implications pratiques

    | Situation | TSB | Strategie |
    |-----------|-----|-----------|
    | Preparation competition | Augmenter vers +5/+15 | Reduire volume 1-2 semaines avant |
    | Construction de base | Maintenir -5 a -15 | Charge progressive |
    | Surmenage | < -25 | STOP - Repos complet |
    | Perte de forme | > +20 | Reprendre l'entrainement |

    ## Le "sweet spot"

    Pour progresser de maniere optimale, il faut maintenir un **TSB legerement negatif** (-5 a -15).

    Cela signifie que vous etes constamment un peu fatigue (ce qui stimule l'adaptation)
    mais pas au point de vous blesser ou de vous surentrainer.
    """)

    st.success("""
    **Notre cible TSB** : -15

    L'algorithme calcule le TSS de chaque seance pour maintenir votre TSB autour de cette valeur,
    vous gardant dans la zone d'adaptation optimale.
    """)

# ============================================
# ENTRAINEMENT POLARISE
# ============================================
elif section == "Entrainement polarise":
    st.header("L'entrainement polarise (80/20)")

    st.markdown("""
    ## Qu'est-ce que c'est ?

    L'entrainement polarise est une methode ou vous passez :
    - **80%** de votre temps a **basse intensite** (Zones 1-2)
    - **20%** de votre temps a **haute intensite** (Zones 4-5)
    - **Presque rien** en Zone 3 (le "trou noir")

    ## Pourquoi ca marche ?
    """)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        ### Seances EASY (80%)

        **But** : Developper l'endurance aerobique

        - Ameliore la capillarisation
        - Augmente les mitochondries
        - Economise les reserves de glycogene
        - Permet un volume eleve
        - Recuperation rapide

        **Intensite** : Vous devez pouvoir
        tenir une conversation complete.

        **Zones** : Z1 et Z2
        """)

    with col2:
        st.markdown("""
        ### Seances HARD (20%)

        **But** : Developper la VO2max et le seuil

        - Stimule le coeur (volume d'ejection)
        - Ameliore l'utilisation du lactate
        - Augmente la VO2max
        - Repousse le seuil lactique

        **Intensite** : Vous ne pouvez dire
        que quelques mots.

        **Zones** : Z4 et Z5
        """)

    st.markdown("""
    ---

    ## Pourquoi eviter la Zone 3 ?

    La Zone 3 est appelee le **"trou noir"** de l'entrainement :

    | Zone | Benefice | Fatigue | Ratio benefice/fatigue |
    |------|----------|---------|------------------------|
    | Z1-Z2 | Eleve (endurance) | Faible | **Excellent** |
    | Z3 | Moyen | Moyen-Eleve | Mauvais |
    | Z4-Z5 | Eleve (vitesse) | Eleve | **Bon** |

    En Z3, vous vous fatiguez trop pour les benefices obtenus. C'est trop dur pour
    accumuler du volume, et pas assez dur pour stimuler la VO2max.

    ---

    ## Implementation dans Running Coach
    """)

    st.code("""
    # Distribution cible sur 21 jours
    EASY  = 80%  (recuperation, endurance facile, sortie longue)
    HARD  = 20%  (fractionne VO2max, fractionne seuil)

    # Regles de decision
    SI distribution_hard > 25% ALORS forcer EASY
    SI distribution_hard < 15% ET jours_depuis_hard > 4 ALORS suggerer HARD
    SI jours_depuis_hard < 2 ALORS forcer EASY (recuperation)
    """, language="python")

    st.markdown("""
    ---

    ## Les zones cardiaques

    Vos zones sont calculees a partir de votre **LTHR** (Lactate Threshold Heart Rate) :
    """)

    zones_data = {
        "Zone": ["Z1", "Z2", "Z3", "Z4", "Z5"],
        "Nom": ["Recuperation", "Endurance", "Tempo", "Seuil", "VO2max"],
        "% LTHR": ["< 81%", "81-89%", "90-93%", "94-99%", "100%+"],
        "Sensation": [
            "Tres facile, conversation normale",
            "Facile, conversation possible",
            "Modere, phrases courtes",
            "Difficile, quelques mots",
            "Tres difficile, aucune parole"
        ],
        "Categorie": ["EASY", "EASY", "Eviter", "HARD", "HARD"]
    }
    st.table(zones_data)

    st.info("""
    **Votre LTHR** est recupere automatiquement depuis Intervals.icu.
    C'est la frequence cardiaque a votre seuil lactique (environ l'effort que vous pouvez
    tenir 1h en competition).
    """)

# ============================================
# ALGORITHME DE DECISION
# ============================================
elif section == "Algorithme de decision":
    st.header("L'algorithme de decision")

    st.markdown("""
    ## Etape 1 : Courir ou se reposer demain ?

    L'algorithme suit une **hierarchie de regles** pour decider :
    """)

    st.code("""
    FONCTION should_run_tomorrow():

        # Securite d'abord
        SI readiness_score < 0.6:
            RETOURNER REPOS ("Readiness trop bas")

        SI TSB < -25:
            RETOURNER REPOS ("Surmenage - TSB critique")

        SI ACWR > 1.5:
            RETOURNER REPOS ("Risque blessure - ACWR trop eleve")

        # Eviter le deconditionnement
        SI TSB > 15 ET jours_sans_run >= 3:
            RETOURNER RUN ("Trop de repos, risque deconditionnement")

        # Cas normal
        SI TSB > -15 ET readiness >= 0.6:
            SI jours_sans_run >= 2:
                RETOURNER RUN ("Recupere et 2j+ de repos")
            SINON SI couru_hier:
                RETOURNER evaluer_back_to_back()

        # Fatigue moderee
        SI TSB entre -15 et -5:
            RETOURNER RUN ("Charge productive")

        # Par defaut
        RETOURNER REPOS ("Securite")
    """, language="python")

    st.markdown("""
    ---

    ## Etape 2 : Seance facile ou difficile ?

    Si demain est un jour de course, quel type ?
    """)

    st.code("""
    FONCTION select_workout_type():

        # Analyser distribution 21 jours
        distribution = analyser_21_derniers_jours()
        jours_depuis_hard = compter_jours_depuis_seance_difficile()

        # Forcer EASY si besoin
        SI TSB < seuil_recuperation:
            RETOURNER EASY ("Recuperation prioritaire")

        SI jours_depuis_hard < 2:
            RETOURNER EASY ("Min 48h entre seances difficiles")

        SI distribution.hard > 25%:
            RETOURNER EASY ("Trop de hard, retour au 80/20")

        # Possibilite de HARD
        SI distribution.hard < 15% ET jours_depuis_hard >= 4:
            RETOURNER HARD ("Distribution desequilibree, hard possible")

        # Par defaut
        RETOURNER EASY ("Maintien 80/20")
    """, language="python")

    st.markdown("""
    ---

    ## Etape 3 : Calculer le TSS cible

    Le TSS est calcule pour vous ramener vers le TSB cible (-15) :
    """)

    st.code("""
    FONCTION calculate_target_tss():

        # Parametres Banister
        CTL_decay = 42  # jours
        ATL_decay = 7   # jours
        target_TSB = -15

        # TSS "theorique" pour atteindre le TSB cible
        tss_theorique = calculer_tss_banister(CTL, ATL, target_TSB)

        # Limite de securite : ALB (Acute Load Baseline)
        # Ne jamais depasser 1.5x la moyenne des 7 derniers jours
        ALB = moyenne_tss_7_jours * 1.5

        # Appliquer le readiness score
        tss_ajuste = tss_theorique * readiness_score

        # Plafonner a l'ALB
        tss_final = MIN(tss_ajuste, ALB)

        RETOURNER tss_final
    """, language="python")

    st.markdown("""
    ---

    ## Diagramme complet

    ```
                            ┌─────────────────┐
                            │   Collecte      │
                            │   donnees       │
                            └────────┬────────┘
                                     │
                            ┌────────▼────────┐
                            │  Readiness < 0.6│───OUI──▶ REPOS
                            │  TSB < -25      │
                            │  ACWR > 1.5     │
                            └────────┬────────┘
                                     │ NON
                            ┌────────▼────────┐
                            │  Conditions OK  │───OUI──▶ RUN
                            │  pour courir ?  │
                            └────────┬────────┘
                                     │ OUI
                    ┌────────────────┼────────────────┐
                    │                │                │
            ┌───────▼───────┐ ┌──────▼──────┐ ┌──────▼──────┐
            │  Recuperation │ │    Easy     │ │    Hard     │
            │  (TSB < -10)  │ │  (defaut)   │ │ (si 4j+)    │
            └───────┬───────┘ └──────┬──────┘ └──────┬──────┘
                    │                │                │
                    └────────────────┼────────────────┘
                                     │
                            ┌────────▼────────┐
                            │  Calcul TSS     │
                            │  Duree/Distance │
                            │  Ajust. meteo   │
                            └────────┬────────┘
                                     │
                            ┌────────▼────────┐
                            │    Upload       │
                            │  Intervals.icu  │
                            └─────────────────┘
    ```
    """)

# ============================================
# TYPES DE SEANCES
# ============================================
elif section == "Types de seances":
    st.header("Types de seances")

    st.markdown("""
    ## Vue d'ensemble

    | Type | Categorie | IF | But |
    |------|-----------|----|----|
    | recovery | EASY | 0.65 | Recuperation active |
    | easy | EASY | 0.72 | Endurance de base |
    | long_run | EASY | 0.70 | Endurance longue duree |
    | intervals | HARD | 0.85 | VO2max |
    | intervals_long | HARD | 0.88 | Seuil lactique |

    ---

    ## Seances EASY detaillees
    """)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.subheader("Recuperation")
        st.markdown("""
        **Quand** : Apres seance difficile, TSB tres bas

        **Structure** :
        - 100% Zone 1
        - 20-30 minutes
        - Allure tres lente

        **But** : Favoriser la circulation,
        eliminer les toxines, sans stress

        **IF** : 0.65
        """)

    with col2:
        st.subheader("Endurance Facile")
        st.markdown("""
        **Quand** : Seance par defaut

        **Structure** :
        - 5 min Z1 (echauffement)
        - Corps en Z2
        - 5 min Z1 (retour au calme)

        **But** : Construire l'endurance
        aerobique de base

        **IF** : 0.72
        """)

    with col3:
        st.subheader("Sortie Longue")
        st.markdown("""
        **Quand** : TSS cible > 60

        **Structure** :
        - 10 min Z1
        - Corps en Z2
        - 10 min Z1

        **But** : Endurance longue duree,
        adaptation metabolique

        **IF** : 0.70
        """)

    st.markdown("---")
    st.markdown("## Seances HARD detaillees")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Fractionne VO2max")
        st.markdown("""
        **Quand** : Distribution hard < 20%, 4j+ depuis dernier hard

        **Structure** :
        ```
        10 min Z1-Z2 (echauffement)
        4-6 x (3 min Z5 + 2 min Z1)
        10 min Z1 (retour au calme)
        ```

        **But** : Augmenter la VO2max,
        capacite cardiaque maximale

        **IF** : 0.85

        **Sensation** : Essoufle mais controlable,
        vous pouvez dire quelques mots
        """)

    with col2:
        st.subheader("Fractionne Seuil")
        st.markdown("""
        **Quand** : Alternative au VO2max, TSS cible eleve

        **Structure** :
        ```
        10 min Z1-Z2 (echauffement)
        3 x (8 min Z4 + 3 min Z1)
        10 min Z1 (retour au calme)
        ```

        **But** : Repousser le seuil lactique,
        endurance a haute intensite

        **IF** : 0.88

        **Sensation** : Difficile mais soutenable,
        rythme de competition 10km-semi
        """)

    st.markdown("""
    ---

    ## Selection automatique du type

    ```python
    SI categorie == EASY:
        SI TSB < seuil_recuperation:
            type = "recovery"
        SINON SI tss_cible > 60:
            type = "long_run"
        SINON:
            type = "easy"

    SINON SI categorie == HARD:
        SI tss_cible > 70:
            type = "intervals_long"  # Seuil
        SINON:
            type = "intervals"  # VO2max
    ```
    """)

# ============================================
# AJUSTEMENTS METEO
# ============================================
elif section == "Ajustements meteo":
    st.header("Ajustements meteo")

    st.markdown("""
    ## Pourquoi la meteo compte ?

    La chaleur augmente significativement le stress physiologique.
    Courir par 30°C est beaucoup plus difficile que par 15°C, meme effort percu egal.

    L'algorithme ajuste le TSS cible en fonction de l'**indice de chaleur**
    (combinaison temperature + humidite).

    ---

    ## Table d'ajustement
    """)

    meteo_data = {
        "Indice chaleur": ["< 18°C", "18-22°C", "22-25°C", "25-28°C", "28-32°C", "32-35°C", "> 35°C"],
        "Facteur": ["1.0", "1.0", "0.95", "0.88", "0.75", "0.60", "0.0"],
        "Conseil": [
            "Conditions optimales",
            "Conditions optimales",
            "Legere reduction recommandee",
            "Reduire l'intensite",
            "Reduire significativement",
            "Seance facile uniquement",
            "Repos recommande (danger)"
        ],
        "TSS 50 devient": ["50", "50", "47", "44", "37", "30", "0 (repos)"]
    }
    st.table(meteo_data)

    st.markdown("""
    ---

    ## Calcul de l'indice de chaleur

    L'indice de chaleur combine temperature et humidite :

    ```python
    def heat_index(temp_celsius, humidity_percent):
        # Formule simplifiee de Steadman
        if temp_celsius < 27:
            return temp_celsius

        # Au-dessus de 27°C, l'humidite compte
        hi = -8.784 + 1.611*temp + 2.338*humidity ...
        return hi
    ```

    | Temp | Humidite 30% | Humidite 60% | Humidite 90% |
    |------|--------------|--------------|--------------|
    | 25°C | 25°C | 26°C | 28°C |
    | 30°C | 29°C | 33°C | 41°C |
    | 35°C | 35°C | 45°C | 54°C |

    ---

    ## Impact sur les seances
    """)

    col1, col2 = st.columns(2)

    with col1:
        st.success("""
        **Conditions fraiches (< 18°C)**

        - Aucun ajustement
        - Seances hard possibles
        - TSS normal
        - Performances optimales
        """)

    with col2:
        st.error("""
        **Canicule (> 32°C)**

        - Reduction 40%+ du TSS
        - Seances hard deconseillees
        - Hydratation ++
        - Risque coup de chaleur
        """)

    st.info("""
    **Note** : La meteo est recuperee via OpenWeatherMap pour le lendemain
    a l'heure prevue de votre seance (configurable).
    """)

# ============================================
# FORMULES ET CALCULS
# ============================================
elif section == "Formules et calculs":
    st.header("Formules et calculs detailles")

    st.markdown("""
    ## 1. Modele exponentiel (Banister)

    Les metriques CTL et ATL suivent un **declin exponentiel** :

    ```
    CTL(n) = CTL(n-1) × e^(-1/τ₁) + TSS(n-1) × (1 - e^(-1/τ₁))
    ATL(n) = ATL(n-1) × e^(-1/τ₂) + TSS(n-1) × (1 - e^(-1/τ₂))

    avec τ₁ = 42 jours (fitness)
         τ₂ = 7 jours (fatigue)
    ```

    En simplifiant (approximation discrete) :
    ```
    CTL(n) = CTL(n-1) + (TSS(n-1) - CTL(n-1)) / 42
    ATL(n) = ATL(n-1) + (TSS(n-1) - ATL(n-1)) / 7
    ```

    ---

    ## 2. TSS (Training Stress Score)

    Le TSS quantifie le stress d'une seance :

    ```
    TSS = (t × IF² × 100) / 3600

    ou :
    - t = duree en secondes
    - IF = Intensity Factor = FC_moyenne / LTHR
    ```

    **Exemple** :
    - Seance de 45 min (2700 sec)
    - FC moyenne 140 bpm, LTHR 167 bpm
    - IF = 140/167 = 0.84
    - TSS = (2700 × 0.84² × 100) / 3600 = **53**

    ---

    ## 3. Calcul du TSS cible

    Pour maintenir un TSB cible, on inverse la formule :

    ```
    # On veut TSB(n+1) = target_TSB
    # TSB = CTL - ATL
    # Donc on cherche TSS tel que CTL(n+1) - ATL(n+1) = target_TSB

    TSS_ideal = (
        (target_TSB - CTL + ATL) × ATL_decay × CTL_decay
    ) / (CTL_decay - ATL_decay)

    # Avec les valeurs par defaut :
    TSS_ideal = (target_TSB - CTL + ATL) × 42 × 7 / (42 - 7)
    TSS_ideal = (target_TSB - TSB) × 8.4
    ```

    ---

    ## 4. ACWR (Acute:Chronic Workload Ratio)

    ```
    ACWR = ATL / CTL

    # Zones de risque (basees sur recherches Gabbett et al.)
    ACWR < 0.8  → Sous-entrainement (risque modere)
    0.8-1.3     → Zone optimale (risque minimal)
    1.3-1.5     → Zone d'attention (risque modere)
    ACWR > 1.5  → Zone de danger (risque eleve de blessure)
    ```

    ---

    ## 5. Readiness Score

    Score composite multiplicatif :

    ```python
    def calculate_readiness():
        score = 1.0

        # Facteur TSB (normalise autour de 0)
        tsb_modifier = 1 + (TSB / 50)  # TSB=0 → 1.0, TSB=-25 → 0.5
        score *= max(0.5, min(1.1, tsb_modifier))

        # Facteur FC repos (elevation par rapport baseline)
        if resting_hr > baseline_hr:
            hr_elevation = (resting_hr - baseline_hr) / baseline_hr
            score *= max(0.7, 1 - hr_elevation)

        # Facteur sommeil (dette sur 3 jours)
        sleep_avg = moyenne_sommeil_3j
        if sleep_avg < 7:
            score *= max(0.8, sleep_avg / 7)

        # Facteur ACWR (securite)
        if ACWR > 1.5:
            score *= 0.5  # Reduction forte
        elif ACWR > 1.3:
            score *= 0.8  # Reduction moderee

        return score  # Entre 0.5 et 1.1
    ```

    ---

    ## 6. Duree et distance estimees

    ```python
    def calculate_duration(workout_type, target_tss):
        IF = intensity_factors[workout_type]
        # TSS = (t × IF² × 100) / 3600
        # Donc t = TSS × 3600 / (IF² × 100)
        duration_sec = target_tss * 3600 / (IF * IF * 100)
        return duration_sec / 60  # en minutes

    def estimate_distance(duration_min, workout_type):
        # Pace moyen en Z2 (recupere depuis historique)
        pace_z2 = 7.3  # min/km (exemple)

        # Ajustement selon type
        pace_adjustments = {
            'recovery': 1.15,     # +15% plus lent
            'easy': 1.0,          # Pace Z2
            'long_run': 1.05,     # +5% plus lent
            'intervals': 0.85,    # -15% plus rapide (moyenne)
            'intervals_long': 0.90
        }

        effective_pace = pace_z2 * pace_adjustments[workout_type]
        return duration_min / effective_pace
    ```

    ---

    ## 7. Zones cardiaques

    Calculees a partir du LTHR (seuil lactique) :

    ```python
    def calculate_zones(lthr, max_hr):
        return {
            'Z1': (0, int(lthr * 0.81)),           # < 81% LTHR
            'Z2': (int(lthr * 0.81), int(lthr * 0.89)),  # 81-89%
            'Z3': (int(lthr * 0.90), int(lthr * 0.93)),  # 90-93%
            'Z4': (int(lthr * 0.94), int(lthr * 0.99)),  # 94-99%
            'Z5': (lthr, max_hr)                    # 100%+
        }
    ```
    """)

    st.info("""
    **References scientifiques** :
    - Banister et al. (1975) - Modele Fitness-Fatigue
    - Coggan (2003) - Training Stress Score
    - Seiler (2010) - Entrainement polarise
    - Gabbett (2016) - ACWR et risque de blessure
    """)

# ============================================
# API INTERVALS.ICU
# ============================================
elif section == "API Intervals.icu":
    st.header("API Intervals.icu - Reference technique")

    st.markdown("""
    ## Vue d'ensemble

    Running Coach utilise l'**API REST d'Intervals.icu** pour recuperer vos donnees d'entrainement
    et uploader les seances generees. Toutes les requetes sont authentifiees via HTTP Basic Auth.

    ```python
    BASE_URL = "https://intervals.icu"
    AUTH = ("API_KEY", votre_api_key)
    ATHLETE_URL = f"{BASE_URL}/api/v1/athlete/{athlete_id}"
    ```

    ---

    ## Endpoints utilises
    """)

    # Tableau des endpoints
    endpoints_data = {
        "Endpoint": [
            "GET /athlete/{id}/wellness/{date}",
            "GET /athlete/{id}/wellness",
            "GET /athlete/{id}",
            "GET /athlete/{id}/activities",
            "GET /athlete/{id}/events",
            "POST /athlete/{id}/events",
            "GET /athlete/{id}/sport-settings"
        ],
        "Methode": ["get_wellness()", "get_wellness_range()", "get_athlete_info()",
                    "get_activities()", "get_events()", "create_workout()", "get_sport_settings()"],
        "Usage": [
            "CTL, ATL, TSB du jour",
            "Historique wellness (graphiques)",
            "Profil athlete",
            "Historique des courses",
            "Seances planifiees",
            "Upload workout genere",
            "LTHR, zones HR"
        ]
    }
    st.table(endpoints_data)

    st.markdown("---")

    # GET wellness/{date}
    st.subheader("1. GET /wellness/{date}")
    st.markdown("**But** : Recuperer les metriques de forme pour une date specifique")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Requete**")
        st.code("""
GET /api/v1/athlete/{id}/wellness/2026-01-21
Authorization: Basic (API_KEY, key)
        """, language="http")

    with col2:
        st.markdown("**Reponse (extrait)**")
        st.code("""
{
  "id": "2026-01-21",
  "ctl": 45.2,
  "atl": 52.1,
  "restingHR": 48,
  "hrv": 65,
  "sleepSecs": 27000,
  "weight": 70.5
}
        """, language="json")

    st.markdown("**Champs utilises par Running Coach** :")
    wellness_fields = {
        "Champ API": ["ctl", "atl", "(calcule)", "restingHR", "hrv"],
        "Variable interne": ["ctl", "atl", "tsb", "resting_hr", "hrv"],
        "Utilisation": [
            "Niveau de fitness (42j)",
            "Niveau de fatigue (7j)",
            "Forme du jour (CTL - ATL)",
            "Recuperation cardiaque",
            "Variabilite cardiaque"
        ],
        "Impact decision": [
            "Calcul TSS cible",
            "Calcul TSS cible, ACWR",
            "Decision RUN/REPOS",
            "Readiness score",
            "Readiness score (si dispo)"
        ]
    }
    st.table(wellness_fields)

    st.markdown("---")

    # GET wellness (range)
    st.subheader("2. GET /wellness (plage de dates)")
    st.markdown("**But** : Recuperer l'historique wellness pour les graphiques et analyses")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Requete**")
        st.code("""
GET /api/v1/athlete/{id}/wellness
  ?oldest=2025-12-01
  &newest=2026-01-21
Authorization: Basic (API_KEY, key)
        """, language="http")

    with col2:
        st.markdown("**Reponse (extrait)**")
        st.code("""
[
  {
    "id": "2026-01-21",
    "ctl": 45.2,
    "atl": 52.1,
    "restingHR": 48,
    "sleepSecs": 27000,
    "rampRate": 1.2
  },
  {
    "id": "2026-01-20",
    ...
  }
]
        """, language="json")

    st.markdown("**Champs supplementaires utilises** :")
    st.markdown("""
    | Champ API | Utilisation |
    |-----------|-------------|
    | `sleepSecs` | Converti en heures, moyenne 3j pour readiness |
    | `rampRate` | Vitesse de progression CTL (alerte si > 2.0) |
    """)

    st.markdown("---")

    # GET athlete
    st.subheader("3. GET /athlete/{id}")
    st.markdown("**But** : Recuperer le profil athlete (zones par defaut, infos generales)")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Requete**")
        st.code("""
GET /api/v1/athlete/{id}
Authorization: Basic (API_KEY, key)
        """, language="http")

    with col2:
        st.markdown("**Reponse (extrait)**")
        st.code("""
{
  "id": "i12345",
  "name": "Athlete Name",
  "email": "...",
  "lthr": 167,
  "max_hr": 185,
  "weight": 70.5,
  "birthday": "1990-01-01"
}
        """, language="json")

    st.info("""
    **Note** : Le LTHR du profil athlete est un fallback.
    La source preferee est `sport-settings` (plus precis par sport).
    """)

    st.markdown("---")

    # GET activities
    st.subheader("4. GET /activities")
    st.markdown("**But** : Recuperer l'historique des activites pour l'analyse de distribution")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Requete**")
        st.code("""
GET /api/v1/athlete/{id}/activities
  ?oldest=2025-12-01
  &newest=2026-01-21
Authorization: Basic (API_KEY, key)
        """, language="http")

    with col2:
        st.markdown("**Reponse (extrait)**")
        st.code("""
[
  {
    "id": "i123456789",
    "start_date_local": "2026-01-20T07:30:00",
    "type": "Run",
    "icu_training_load": 52,
    "moving_time": 2700,
    "distance": 8500,
    "average_heartrate": 142,
    "pace": 318
  }
]
        """, language="json")

    st.markdown("**Champs utilises** :")
    activities_fields = {
        "Champ API": ["type", "icu_training_load", "moving_time", "distance", "average_heartrate", "pace"],
        "Utilisation": [
            "Filtrer les courses (Run)",
            "TSS de la seance",
            "Duree en secondes",
            "Distance en metres",
            "FC moyenne (calcul IF)",
            "Allure (sec/km) pour estimations"
        ]
    }
    st.table(activities_fields)

    st.markdown("""
    **Analyses effectuees** :
    - Distribution EASY/HARD sur 21 jours
    - Jours depuis derniere seance difficile
    - Allure moyenne Z2 (pour estimer distances)
    - Frequence d'entrainement
    """)

    st.markdown("---")

    # GET events
    st.subheader("5. GET /events")
    st.markdown("**But** : Recuperer les seances planifiees (workouts futurs)")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Requete**")
        st.code("""
GET /api/v1/athlete/{id}/events
  ?oldest=2026-01-21
  &newest=2026-01-22
Authorization: Basic (API_KEY, key)
        """, language="http")

    with col2:
        st.markdown("**Reponse (extrait)**")
        st.code("""
[
  {
    "id": 12345,
    "start_date_local": "2026-01-22",
    "category": "WORKOUT",
    "type": "Run",
    "name": "45 TSS - Endurance Facile",
    "load": 45,
    "description": "5min Z1..."
  }
]
        """, language="json")

    st.markdown("""
    **Utilisation** :
    - Verifier si une seance existe deja pour demain
    - Recuperer le workout d'aujourd'hui (pour affichage dashboard)
    - Eviter les doublons lors de l'upload
    """)

    st.markdown("---")

    # POST events
    st.subheader("6. POST /events (Upload workout)")
    st.markdown("**But** : Creer une seance planifiee sur le calendrier Intervals.icu")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Requete**")
        st.code("""
POST /api/v1/athlete/{id}/events
Authorization: Basic (API_KEY, key)
Content-Type: application/json

{
  "category": "WORKOUT",
  "start_date_local": "2026-01-22",
  "type": "Run",
  "name": "45 TSS - Endurance Facile",
  "description": "Seance generee...\\n5min Z1...",
  "load": 45,
  "moving_time": 2700
}
        """, language="http")

    with col2:
        st.markdown("**Reponse**")
        st.code("""
{
  "id": 12345,
  "start_date_local": "2026-01-22",
  "category": "WORKOUT",
  ...
}
        """, language="json")

    st.markdown("**Champs envoyes** :")
    upload_fields = {
        "Champ": ["category", "start_date_local", "type", "name", "description", "load", "moving_time"],
        "Valeur": [
            "WORKOUT (constante)",
            "Date J+1 (demain)",
            "Run (constante)",
            "XX TSS - Type Seance",
            "Details structures + zones",
            "TSS cible",
            "Duree en secondes"
        ]
    }
    st.table(upload_fields)

    st.success("""
    **Sync automatique** : Une fois uploade sur Intervals.icu, le workout est automatiquement
    synchronise vers votre montre Coros (si connectee dans les settings Intervals).
    """)

    st.markdown("---")

    # GET sport-settings
    st.subheader("7. GET /sport-settings")
    st.markdown("**But** : Recuperer les parametres specifiques a la course (LTHR, zones)")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Requete**")
        st.code("""
GET /api/v1/athlete/{id}/sport-settings
Authorization: Basic (API_KEY, key)
        """, language="http")

    with col2:
        st.markdown("**Reponse (extrait)**")
        st.code("""
[
  {
    "types": ["Run", "VirtualRun"],
    "lthr": 167,
    "max_hr": 185,
    "hr_zones": [135, 150, 158, 165, 175],
    "warmup_time": 600,
    "cooldown_time": 300
  },
  {
    "types": ["Ride"],
    "lthr": 162,
    ...
  }
]
        """, language="json")

    st.markdown("**Champs utilises (filtre sur Run)** :")
    sport_fields = {
        "Champ API": ["lthr", "max_hr", "hr_zones"],
        "Utilisation": [
            "Seuil lactique HR → Calcul IF, zones",
            "FC max → Zone 5 plafond",
            "Bornes des zones (optionnel)"
        ]
    }
    st.table(sport_fields)

    st.info("""
    **Priorite LTHR** : `sport-settings[Run].lthr` > `athlete.lthr` > estimation (220-age)
    """)

    st.markdown("---")

    # Schema recapitulatif
    st.subheader("Schema du flux de donnees")

    st.code("""
    ┌─────────────────────────────────────────────────────────────────────┐
    │                         INTERVALS.ICU API                           │
    └─────────────────────────────────────────────────────────────────────┘
                    │                           ▲
                    │ GET                       │ POST
                    ▼                           │
    ┌───────────────────────────────┐    ┌─────────────────────────────┐
    │  LECTURE (analyse)            │    │  ECRITURE                   │
    ├───────────────────────────────┤    ├─────────────────────────────┤
    │ • wellness/{date}             │    │ • events (workout J+1)      │
    │   → CTL, ATL, TSB, FC repos   │    │   → TSS, duree, description │
    │                               │    │                             │
    │ • wellness (range)            │    └─────────────────────────────┘
    │   → Historique, rampRate      │
    │                               │
    │ • activities                  │
    │   → Distribution, pace Z2     │
    │                               │
    │ • events                      │
    │   → Workout existant          │
    │                               │
    │ • sport-settings              │
    │   → LTHR, zones HR            │
    │                               │
    │ • athlete                     │
    │   → Profil (fallback LTHR)    │
    └───────────────────────────────┘
                    │
                    ▼
    ┌───────────────────────────────┐
    │  RUNNING COACH (algorithme)   │
    ├───────────────────────────────┤
    │ • Readiness score             │
    │ • Decision RUN/REPOS          │
    │ • Type seance (EASY/HARD)     │
    │ • TSS cible (Banister)        │
    │ • Duree, distance             │
    │ • Ajustement meteo            │
    └───────────────────────────────┘
    """, language="text")

    st.markdown("---")

    # Code reference
    st.subheader("Reference code : IntervalsAPI")

    st.markdown("**Classe complete dans `main.py`** :")

    st.code("""
class IntervalsAPI:
    BASE_URL = "https://intervals.icu"

    def __init__(self, athlete_id, api_key):
        self.auth = ("API_KEY", api_key)
        self.athlete_url = f"{self.BASE_URL}/api/v1/athlete/{athlete_id}"

    def get_wellness(self, for_date: date) -> dict:
        # GET /wellness/{date}
        # Retourne: {ctl, atl, tsb, resting_hr, hrv}

    def get_wellness_range(self, start: date, end: date) -> list:
        # GET /wellness?oldest=...&newest=...
        # Retourne: [{date, ctl, atl, tsb, sleep_hours, ramp_rate}, ...]

    def get_athlete_info(self) -> dict:
        # GET /athlete/{id}
        # Retourne: profil complet

    def get_activities(self, start: date, end: date) -> list:
        # GET /activities?oldest=...&newest=...
        # Retourne: liste des activites

    def get_events(self, start: date, end: date) -> list:
        # GET /events?oldest=...&newest=...
        # Retourne: liste des evenements planifies

    def create_workout(self, workout_data: dict) -> dict:
        # POST /events
        # Cree un workout, retourne l'evenement cree

    def get_sport_settings(self, sport_type="Run") -> dict:
        # GET /sport-settings
        # Retourne: {lthr, max_hr, hr_zones} pour le sport
    """, language="python")

    st.markdown("---")

    st.info("""
    **Documentation officielle** : [intervals.icu/api/v1/docs](https://intervals.icu/api/v1/docs)

    L'API Intervals.icu est gratuite et bien documentee. Elle permet l'acces complet
    a toutes vos donnees d'entrainement.
    """)

# Footer
st.markdown("---")
st.caption("Running Coach v2.2.1 - Documentation technique")
