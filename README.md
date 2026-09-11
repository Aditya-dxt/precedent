# Precedent — AI Exam Pattern & Revision Platform

> **"Your exam has a history. We read it."**  
> *Production-ready prototype for Horizon 2026 Round 1 MVP (Theme: AI in Education)*

---

## 🏛️ System Architecture

```
precedent/
├── backend/                  # FastAPI + Python Engine
│   ├── main.py               # FastAPI application lifecycle & CORS
│   ├── schema.sql            # Supabase PostgreSQL schema & RLS policies
│   ├── render.yaml           # One-click Render deployment configuration
│   ├── requirements.txt      # Python dependencies
│   ├── models/schemas.py     # Pydantic schemas for all payloads
│   ├── routers/              # upload, analysis, planner, papers, github
│   └── services/             # pdf_parser, embeddings, pattern_engine, optimizer, paper_generator, github_service, supabase_service
└── frontend/                 # React 18 + Vite + TypeScript + Tailwind CSS
    ├── vercel.json           # Vercel SPA routing
    ├── tailwind.config.ts    # Navy (#1B2A4A), Gold (#C9922A), Off-White (#F5F3EF)
    └── src/
        ├── pages/            # Landing, Upload, Processing, Dashboard, RevisionPlanner, MockPapers, Repository
        ├── components/       # Navbar, Footer, TopicCard, UploadZone, ProgressStep, MockPaperViewer, RepoTree
        └── lib/              # api.ts, supabase.ts, types.ts
```

---

## ⚡ Quickstart (Run Locally)

### 1. Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
copy .env.example .env

# Run FastAPI server
uvicorn main:app --reload --port 8000
```

### 2. Frontend

```bash
cd frontend

# Install dependencies (already built & verified)
npm install

# Configure environment variables
copy .env.example .env

# Start Vite dev server
npm run dev
```
Open [http://localhost:5173](http://localhost:5173) in your browser.

---

## 🚀 Deployment Guide

### Backend on Render (Free Tier)
1. Push repository to GitHub.
2. Log in to [render.com](https://render.com) and click **New + Web Service**.
3. Connect your repository and select the `backend` directory (or use `render.yaml`).
4. Set Build Command: `pip install -r requirements.txt`
5. Set Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
6. Fill in the Environment Variables listed below.

### Frontend on Vercel
1. Log in to [vercel.com](https://vercel.com) and click **Add New Project**.
2. Select root directory as `frontend`.
3. Framework Preset: **Vite**.
4. Configure the Environment Variables listed below.
5. Deploy.
