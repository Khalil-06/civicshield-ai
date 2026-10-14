# 🛡️ CivicShield AI
### *"Turning scattered citizen reports into one prioritized picture of a community emergency."*

> Built for **PromptWars: AI for Better Living & Smarter Communities**

---

## 🚨 The Problem

During community emergencies — fires, accidents, floods, medical crises — information is fragmented across citizens. Emergency teams receive many reports about the same event while struggling to determine what's most urgent.

This creates:
- Information overload and duplicate reports
- Delayed prioritization
- Difficulty identifying vulnerable locations
- Raw citizen data that never becomes actionable intelligence

> **"Communities don't simply lack emergency information. They lack a system that transforms scattered citizen information into one clear, prioritized, explainable picture of what is happening."**

---

## ✅ The Solution

**CivicShield AI** is an AI-powered community emergency intelligence platform with one core innovation:

### ⚡ INCIDENT FUSION

When multiple citizens report the same emergency independently, CivicShield AI:

1. Analyzes every report with Gemini AI
2. Detects semantically and geographically related reports
3. Groups them into a single **Unified Incident**
4. Calculates an **Explainable Priority Score** (0–100)
5. Produces recommended actions for human responders

**Instead of:**
```
Incident 1 — Smoke near school
Incident 2 — Fire behind school
Incident 3 — Students evacuating
Incident 4 — Heavy smoke in Zone A
```

**CivicShield shows:**
```
🔥 POSSIBLE UNIFIED INCIDENT — SCHOOL FIRE, ZONE A
Priority: 96/100 · Severity: CRITICAL · Supporting Reports: 4
Confidence: 82% · AI-generated — human verification required
```

---

## 🌟 Features

| Feature | Description |
|---|---|
| **AI Incident Analysis** | Gemini AI extracts type, severity, risk, summary, priority score, reason |
| **Explainable Priority** | Every score comes with human-readable reasoning |
| **Incident Fusion** | Deduplicates and merges related citizen reports |
| **Command Dashboard** | Professional emergency intelligence display |
| **Demo Mode** | One-click hackathon demo with 5 realistic reports |
| **Fallback Mode** | Works without Gemini API using local heuristics |
| **Citizen Report Form** | Beautiful, intuitive public reporting page |
| **Live Statistics** | Active incidents, critical, high priority, fused counts |

---

## 🏗️ Architecture

```
civicshield-ai/
├── backend/
│   ├── main.py              # FastAPI application + all routes
│   ├── ai_engine.py         # Gemini AI analysis + local fallback
│   ├── incident_fusion.py   # Incident Fusion Engine
│   ├── database.py          # SQLite persistence layer
│   ├── models.py            # Pydantic data models
│   └── requirements.txt
├── frontend/
│   └── index.html           # Complete single-file SPA
├── .env                     # Your secrets (never commit)
├── .env.example             # Template for .env
├── .gitignore
└── README.md
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | Python 3.13 + FastAPI |
| **AI** | Google Gemini 2.5 Flash (google-genai SDK) |
| **Database** | SQLite (zero-configuration, local) |
| **Frontend** | Vanilla HTML/CSS/JavaScript (single file SPA) |
| **Server** | Uvicorn ASGI |

---

## ⚙️ Setup

### Prerequisites
- Python 3.10+
- A Google Gemini API key (get one free at [aistudio.google.com](https://aistudio.google.com))

### 1. Clone / Navigate to the project
```bash
cd civicshield-ai
```

### 2. Create and activate virtual environment
```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r backend/requirements.txt
```

### 4. Set up environment variables
```bash
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY
```

Your `.env` file:
```
GEMINI_API_KEY=your_actual_key_here
```

### 5. Start the backend
```bash
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

### 6. Start the frontend (new terminal)
```bash
python -m http.server 3000 --directory frontend
```

### 7. Open the app
```
http://localhost:3000
```

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Project info |
| `GET` | `/health` | Health check |
| `POST` | `/incidents` | Submit report (AI analysis + fusion) |
| `POST` | `/incidents/analyze` | Analyze only (no save) |
| `GET` | `/incidents` | List all incidents |
| `GET` | `/incidents/{id}` | Get single incident |
| `GET` | `/dashboard/stats` | Dashboard statistics |
| `POST` | `/demo/load` | Load demo scenario |
| `DELETE` | `/incidents/reset` | Clear all incidents |

Interactive API docs: `http://localhost:8000/docs`

---

## 🎬 Hackathon Demo Flow

1. Open `http://localhost:3000`
2. Click **"🎬 Try Demo"** (or press Demo in the nav)
3. Watch 5 citizen reports load automatically
4. AI analyzes each report
5. Incident Fusion detects related reports
6. Dashboard shows:
   - **Unified Incident** with 5 supporting reports
   - **Priority Score: 95+/100**
   - **Severity: CRITICAL**
   - **Fusion Confidence: 82%**
   - Full recommended actions
7. Click into Command Center to see the full dashboard
8. Submit your own custom report via **🚨 Report Now**

---

## 🛡️ Environment Variables

| Variable | Required | Description |
|---|---|---|
| `GEMINI_API_KEY` | Yes (for live AI) | Your Google AI Studio key |

> **Security**: The API key is loaded server-side only via `.env`. It is never exposed in frontend code.

---

## 🤖 Responsible AI Statement

CivicShield AI is a **prototype decision-support system**.

- AI outputs are recommendations only
- All recommendations require verification by authorized human responders  
- CivicShield does NOT autonomously dispatch police, fire, or medical services
- CivicShield does NOT replace emergency communication systems (dial 112/911)
- AI analysis is clearly labeled as "AI-generated — human verification required"

---

## 🔮 Future Scope

The following capabilities are not implemented in this prototype but represent a clear path to production deployment:

- **Real emergency service integrations** (CAD system APIs, dispatch systems)
- **Multilingual citizen reporting** (regional language support)
- **Voice reporting** (WhatsApp/phone-based report submission)
- **Computer vision** (photo/video analysis of incident scenes)
- **Real-time geospatial intelligence** (live incident mapping)
- **City-scale deployment** (multi-zone monitoring, IoT sensor integration)
- **Predictive risk mapping** (historical data + ML for hotspot detection)
- **Mobile app** (native iOS/Android citizen reporting)

---

## 📊 Impact

| Metric | Without CivicShield | With CivicShield |
|---|---|---|
| Report processing | Manual, slow | AI-instant |
| Duplicate reports | Confuse responders | Automatically fused |
| Priority decisions | Subjective | Explainable AI score |
| Information per incident | Fragmented | Unified |
| Responder confidence | Low context | Full picture |

---

*Built with ❤️ for PromptWars 2026 — AI for Better Living & Smarter Communities*
