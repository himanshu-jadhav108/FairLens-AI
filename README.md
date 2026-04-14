# ⚖️ FairLens AI — Bias Auditing & Mitigation Platform

> *See the bias. Understand it. Fix it.*

FairLens AI is a full-stack ML platform for detecting, explaining, and mitigating algorithmic bias in classification models. Upload any CSV dataset, select your target and sensitive attribute, and the platform guides you through the complete fairness audit pipeline.

---

## 🔍 Problem Statement

Machine learning models are increasingly used in high-stakes decisions — hiring, lending, healthcare, criminal justice. These models can perpetuate and amplify historical biases present in training data, leading to systematically unfair outcomes for protected groups (based on gender, race, age, etc.).

Most organizations lack accessible, end-to-end tools to **detect**, **explain**, and **fix** bias without requiring deep ML expertise.

**FairLens AI bridges that gap.**

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 📂 **CSV Upload** | Drag & drop any tabular dataset |
| ⚡ **Bias Detection** | Demographic Parity + Equalized Odds metrics |
| 📊 **Group Charts** | Per-group prediction rates visualized with Recharts |
| 🔬 **SHAP Explainability** | Feature attribution with LinearExplainer |
| 🤖 **AI Explanation** | Human-readable bias report (Gemini placeholder) |
| 🛠 **Bias Mitigation** | Reweighting + drop sensitive feature |
| 📋 **Before vs After** | Full comparison dashboard with radar charts |
| 🎨 **Dark Dashboard UI** | Sleek, forensic-styled analyst interface |

---

## 🧱 Tech Stack

### Frontend
- **React 18** + **Vite** — fast, modern SPA
- **Recharts** — bar, radar, and comparison charts
- **Axios** — API communication
- **react-dropzone** — file upload UX
- **CSS Variables** — dark theme design system

### Backend
- **FastAPI** — async Python REST API
- **scikit-learn** — Logistic Regression, StandardScaler, train_test_split
- **SHAP** — LinearExplainer for feature attributions
- **fairlearn** (dependency included) — fairness metrics reference
- **pandas / numpy** — data manipulation
- **uvicorn** — ASGI server

### AI
- **Gemini API** — placeholder structured template (swap in real API key)

---

## 📸 Screenshots

```
┌────────────────────────────────────────────────────────┐
│  ⚖ FairLens  │  Upload Dataset                         │
│              │                                          │
│  ○ 01 Upload │  ┌────────────────────────────────────┐ │
│  ○ 02 Detect │  │  Drag & drop your CSV file          │ │
│  ○ 03 Explain│  │         📂                          │ │
│  ○ 04 Fix    │  └────────────────────────────────────┘ │
│  ○ 05 Report │                                          │
│              │  Target: [hired ▼]  Sensitive: [gender▼]│
│              │  [ ⚡ Run Bias Analysis ]                │
└────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────┐
│  Bias Detection Results                                 │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐   │
│  │ DPD: 0.2341  │ │ EOD: 0.1823  │ │ Acc: 0.72    │   │
│  │ HIGH BIAS    │ │ MODERATE     │ │ GOOD         │   │
│  └──────────────┘ └──────────────┘ └──────────────┘   │
│  ████████ Positive Rate by Gender ████████             │
│  Male   ████████████████████ 72%                       │
│  Female ██████████ 41%                                 │
└────────────────────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
fairlens-ai/
├── backend/
│   ├── app/
│   │   ├── main.py          ← FastAPI entry point
│   │   ├── state.py         ← In-memory session store
│   │   ├── ml_pipeline.py   ← Core ML: train, metrics, SHAP, fix
│   │   └── routes/
│   │       ├── upload.py    ← POST /api/upload
│   │       ├── analyze.py   ← POST /api/analyze
│   │       ├── explain.py   ← POST /api/explain, /api/ai-explain
│   │       └── fix.py       ← POST /api/fix
│   ├── requirements.txt
│   └── sample_data.csv      ← Hiring bias dataset (50 rows)
│
├── frontend/
│   ├── src/
│   │   ├── components/      ← UI components
│   │   ├── context/         ← Global app state (Context + reducer)
│   │   ├── lib/             ← API adapter and helpers
│   │   ├── pages/           ← Route-level pages
│   │   ├── App.tsx
│   │   └── index.css        ← Full design system
│   └── package.json
│
├── setup.md    ← Detailed setup instructions
└── README.md   ← This file
```

---

## 🚀 Quick Start

```powershell
# Backend (PowerShell)
cd backend
.\run_backend.ps1

# Frontend (new terminal)
cd frontend
.\run_frontend.ps1
```

```bash
# Backend (macOS/Linux)
cd backend
bash run_backend.sh

# Frontend (new terminal)
cd frontend
bash run_frontend.sh
```

Open **http://localhost:5173** and upload `backend/sample_data.csv`.

> Full instructions in [setup.md](./setup.md)

---

## 📐 ML Pipeline Details

```
CSV Upload
    │
    ▼
Encode categoricals → LabelEncoder
    │
    ▼
Train/Test Split (70/30, stratified)
    │
    ▼
Logistic Regression (max_iter=1000)
    │
    ├──► Demographic Parity Difference
    │    |P(Ŷ=1|A=0) - P(Ŷ=1|A=1)|
    │
    ├──► Equalized Odds Difference
    │    max(|TPR₀-TPR₁|, |FPR₀-FPR₁|)
    │
    └──► SHAP LinearExplainer
         → Feature attribution rankings

Apply Fix:
    → Compute sample weights (balance groups)
    → Drop sensitive column from features
    → Retrain with weighted samples
    → Recompute all metrics
```

---

## 🔮 Future Improvements

- [ ] **Real Gemini API integration** — live LLM explanations
- [ ] **More fairness metrics** — Calibration, Individual Fairness
- [ ] **More ML models** — Random Forest, XGBoost, Neural Networks
- [ ] **More mitigation strategies** — Adversarial debiasing, Threshold optimization, Equalized odds post-processing
- [ ] **Report export** — PDF/HTML audit report download
- [ ] **Dataset persistence** — PostgreSQL or Redis for multi-user support
- [ ] **Model comparison** — Compare multiple models' fairness profiles
- [ ] **Fairness constraints** — Train with fairlearn's GridSearch / ExponentiatedGradient
- [ ] **Authentication** — Multi-user org support
- [ ] **CI/CD** — Docker Compose deployment

---

## 📜 Fairness Metric Reference

| Metric | Formula | Fair Value |
|--------|---------|------------|
| Demographic Parity Difference | \|P(Ŷ=1\|A=0) - P(Ŷ=1\|A=1)\| | < 0.05 |
| Equalized Odds Difference | max over labels of \|TPR₀ - TPR₁\| | < 0.05 |
| Accuracy | (TP + TN) / N | Context-dependent |

---

## 👤 Author

Built as a Hackathon MVP — FairLens AI v1.0.0

*"Fairness is not a feature. It's a foundation."*

---

## 📄 License

MIT License — free to use, modify, and distribute.
