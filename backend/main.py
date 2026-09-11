"""
Precedent — FastAPI Backend
Main application entry point.
"""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

from routers import upload, analysis, planner, papers, github
from services.embeddings import load_model

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load the sentence-transformer model once at startup."""
    print("🚀 Loading embedding model (all-MiniLM-L6-v2)...")
    load_model()
    print("✅ Embedding model ready.")
    yield
    print("👋 Shutting down Precedent backend.")

app = FastAPI(
    title="Precedent API",
    description="AI Exam Pattern & Revision Platform",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
origins = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(upload.router, prefix="/api", tags=["upload"])
app.include_router(analysis.router, prefix="/api", tags=["analysis"])
app.include_router(planner.router, prefix="/api", tags=["planner"])
app.include_router(papers.router, prefix="/api", tags=["papers"])
app.include_router(github.router, prefix="/api", tags=["github"])

@app.get("/")
async def root():
    return {"message": "Precedent API — Your exam has a history. We read it.", "version": "1.0.0"}

@app.get("/health")
async def health():
    return {"status": "ok"}
