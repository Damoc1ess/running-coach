# Running Coach v2.0 - Polarized Data-Driven Training

Automated running coach that generates personalized workouts based on your training data. Uses the **polarized 80/20 training model** backed by scientific research.

**100% data-driven** - All decisions are made automatically based on your watch data. No manual input required.

## How It Works

```
Your Watch → Intervals.icu → Running Coach → Intervals.icu → Your Watch
     ↑                                                           ↓
     └───────────── Workout appears automatically ───────────────┘
```

The algorithm analyzes:
- Your training history (60 days)
- Intensity distribution (21 days)
- Current fitness (CTL/ATL/TSB)
- Recovery since last hard session

And automatically decides:
- Whether it's a running day (every other day)
- Workout type (easy or hard)
- Optimal duration
- Estimated distance

## The Science: Polarized Training (80/20)

Based on [Stephen Seiler's research](https://pubmed.ncbi.nlm.nih.gov/20861519/) on elite endurance athletes:

| Zone | Target % | Type |
|------|----------|------|
| Zone 1-2 (Easy) | **80%** | Recovery, Endurance, Long runs |
| Zone 3 (Tempo) | **~0%** | Avoided ("gray zone") |
| Zone 4-5 (Hard) | **20%** | VO2max/Threshold intervals |

**Why avoid Zone 3?**
- Too hard to recover quickly
- Not hard enough to maximize adaptations
- Accumulates fatigue without proportional benefit

## Decision Logic

```
STEP 1: Running day?
├── Ran today/yesterday → REST
└── 2+ days since run   → RUN

STEP 2: Calculate target TSS
├── Banister model (CTL/ATL/TSB)
└── ALB cap for safety

STEP 3: Analyze distribution (21 days)
├── Count EASY sessions (Z1-Z2)
├── Count HARD sessions (Z4-Z5)
└── Calculate current ratio

STEP 4: Select type (POLARIZED)
├── IF TSB < -25           → RECOVERY
├── IF last hard < 48h     → EASY
├── IF hard% > 25%         → EASY (restore 80/20)
├── IF hard% < 15% AND 4d+ → HARD
├── IF TSB > 5 AND 3d+     → HARD possible
└── DEFAULT                → EASY

STEP 5: Calculate duration
└── Duration = TSS / (IF² × 100)

STEP 6: Estimate distance
└── Distance = Duration × avg Z2 pace
```

## Algorithms Used

| Algorithm | Source | Purpose |
|-----------|--------|---------|
| **Fitness-Fatigue (PMC)** | Banister, 1975 | CTL/ATL/TSB calculation |
| **Polarized Distribution** | Seiler, 2010 | 80% easy / 20% hard |
| **HR Zones** | Joe Friel | 5 zones based on lactate threshold |
| **ALB (Acute Load Balance)** | ACWR adapted | Limits daily load spikes |

## Prerequisites

1. **Intervals.icu account** (free) - [intervals.icu](https://intervals.icu)
2. **Watch connected to Intervals.icu** (Coros, Garmin, Polar, etc.)
3. Python 3.10+

## Installation

```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/running-coach.git
cd running-coach

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # Linux/Mac
# or: .venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Copy and edit config
cp config.example.json config.json
```

## Configuration

### Get your Intervals.icu credentials

1. Go to [intervals.icu/settings](https://intervals.icu/settings)
2. Find your **Athlete ID** (format: `iXXXXXX`)
3. Generate an **API Key** in Developer Settings

### Set environment variables

```bash
export ATHLETE_ID="iXXXXXX"
export API_KEY="your-api-key"
```

Or create a `.env` file:
```
ATHLETE_ID=iXXXXXX
API_KEY=your-api-key
```

### Edit config.json

```json
{
  "polarized": {
    "easy_target_percent": 80,
    "hard_target_percent": 20,
    "min_days_between_hard": 2,
    "analysis_window_days": 21
  },
  "banister": {
    "ctl_days": 42,
    "atl_days": 7,
    "target_tsb": -15.0,
    "alb_lower_bound": -25.0,
    "tsb_recovery_threshold": -25.0
  },
  "operational_settings": {
    "live_mode": false,
    "timezone": "Europe/Paris"
  }
}
```

## Usage

### Test mode (dry run)
```bash
python main.py
```

### Live mode (uploads to Intervals.icu)
Set `"live_mode": true` in config.json, then:
```bash
python main.py
```

### Example output

```
============================================================
  RUNNING COACH v2.0.0 - Polarized Data-Driven
============================================================

📅 Date: 2026-01-16

📡 Fetching data...
✓ 14 runs analyzed over 60 days
✓ Max HR: 172, Threshold: 149
✓ Avg Z2 pace: 7.3 min/km

📊 Current state:
  CTL: 10.6 | ATL: 13.9 | TSB: -3.3

🏃 Running day? 2 days since last run
→ It's a RUNNING day!

🎯 Target TSS: 39 (ALB cap)

🧠 Decision:
  Distribution (21d): 83% easy, 17% hard
  Days since hard: 9
  Current TSB: -3.3
  → EASY (polarized 80/20 default)

📋 Selected workout: easy
⏱️  Duration: 45 min | Estimated distance: 6.2 km

📤 Uploading to Intervals.icu...
✓ Workout created: 39 TSS - Easy Endurance
✅ Upload successful!
```

## Automation

### Cron job (Linux/Mac)
```bash
# Edit crontab
crontab -e

# Add line (runs at 6am daily)
0 6 * * * cd /path/to/running-coach && source .env && python3 main.py >> log.txt 2>&1
```

### GitHub Actions
See `.github/workflows/daily_run.yml` for automated daily execution.

## Watch Sync (Coros/Garmin)

For workouts to appear on your watch:

1. Go to **Intervals.icu Settings → Connections**
2. Connect your watch brand (Coros, Garmin, etc.)
3. Enable **"Upload planned workouts"**
4. Workouts sync automatically to your watch

## Workout Templates

| Template | Category | Zones | Description |
|----------|----------|-------|-------------|
| `recovery` | Easy | Z1-2 | Active recovery |
| `easy` | Easy | Z2 | Easy endurance |
| `long_run` | Easy | Z2 | Long run |
| `intervals` | Hard | Z5 | VO2max intervals (1min/1min) |
| `intervals_long` | Hard | Z4 | Threshold intervals (4min/2min) |

**Note**: No "tempo" template (Zone 3) - following polarized principles.

## Contributing

Contributions welcome! Please:
1. Fork the repo
2. Create a feature branch
3. Submit a pull request

## References

- Seiler, S. (2010). [What is best practice for training intensity and duration distribution in endurance athletes?](https://pubmed.ncbi.nlm.nih.gov/20861519/)
- [Polarized vs Threshold Training Meta-Analysis (2024)](https://pmc.ncbi.nlm.nih.gov/articles/PMC11329428/)
- [Banister Fitness-Fatigue Model](https://www.trainingpeaks.com/learn/articles/what-is-training-stress-score/)
- [Friel HR Zones](https://www.trainingpeaks.com/blog/joe-friel-s-quick-guide-to-setting-zones/)

## License

MIT License - Do whatever you want with it.

---

*Built with science, powered by data.*
