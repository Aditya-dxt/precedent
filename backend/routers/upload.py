"""
Upload Router
-------------
Handles file upload, triggers analysis pipeline, and provides status polling.
Uses an in-memory job store for MVP (good enough for single-instance Render deploy).
"""

import os
import uuid
import asyncio
import tempfile
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse

from models.schemas import SubmissionResponse, StatusResponse
from services import pdf_parser, pattern_engine, supabase_service, paper_generator
from services.optimizer import build_revision_plan

logger = logging.getLogger(__name__)
router = APIRouter()

# In-memory job store: job_id → { status, progress, stage_message, result, error }
_jobs: Dict[str, Dict[str, Any]] = {}


def _update_job(job_id: str, status: str, progress: int, message: str, result: Any = None, error: str = ""):
    # Merge into existing dict to preserve metadata (institution, course, subject) set at init
    existing = _jobs.get(job_id, {})
    existing.update({
        "status": status,
        "progress": progress,
        "stage_message": message,
        "result": result,
        "error": error,
    })
    _jobs[job_id] = existing


async def _run_analysis_pipeline(
    job_id: str,
    submission_id: str,
    subject_id: str,
    institution: str,
    course: str,
    subject: str,
    syllabus_path: Optional[str],
    syllabus_text: Optional[str],
    pyq_paths: list,  # list of (year, path)
):
    """Background task: full analysis pipeline with status updates."""
    try:
        # ── Stage 1: Parse Syllabus ────────────────────────────────────────────
        if syllabus_text and syllabus_text.strip():
            _update_job(job_id, "parsing", 10, "Parsing syllabus text…")
            syllabus_result = pdf_parser.parse_syllabus_text(syllabus_text)
        elif syllabus_path:
            _update_job(job_id, "parsing", 10, "Parsing syllabus PDF…")
            syllabus_result = pdf_parser.parse_syllabus(syllabus_path)
        else:
            _update_job(job_id, "error", 0, "No syllabus PDF or text provided.",
                        error="Missing syllabus")
            return

        topics = syllabus_result.get("topics", [])
        if not topics:
            _update_job(job_id, "error", 0, "Could not extract topics from syllabus.",
                        error=syllabus_result.get("error", "Parsing failed"))
            return
        logger.info(f"[{job_id}] Extracted {len(topics)} topics from syllabus")

        # ── Stage 2: Parse PYQs ────────────────────────────────────────────────
        _update_job(job_id, "parsing_pyqs", 25, "Extracting questions from PYQ papers…")
        pyq_data = []
        for year, path in pyq_paths:
            result = pdf_parser.parse_pyq(path, int(year))
            pyq_data.append(result)
            logger.info(f"[{job_id}] PYQ {year}: {len(result.get('questions', []))} questions")

        # ── Stage 3: Embed & Cluster ──────────────────────────────────────────
        _update_job(job_id, "embedding", 45, "Computing semantic embeddings and detecting patterns…")
        await asyncio.sleep(0)  # yield to event loop
        ranked_topics = pattern_engine.analyze_patterns(topics, pyq_data)
        logger.info(f"[{job_id}] Ranked {len(ranked_topics)} topics")

        # ── Stage 4: Save topics to DB ─────────────────────────────────────────
        _update_job(job_id, "saving", 60, "Saving analysis results…")
        try:
            topic_dicts = [t.model_dump() for t in ranked_topics]
            supabase_service.upsert_topics(subject_id, topic_dicts)
            supabase_service.update_submission_status(submission_id, "analyzed", {"topics_count": len(ranked_topics)})
        except Exception as e:
            logger.warning(f"[{job_id}] DB save failed (non-fatal): {e}")

        # ── Stage 5: Generate Default Revision Plan (7 days, 4 hrs) ──────────
        _update_job(job_id, "planning", 75, "Building optimized revision plan…")
        plan = build_revision_plan(subject_id, ranked_topics, days_available=7, hours_per_day=4.0)

        # ── Stage 6: Generate Mock Papers ─────────────────────────────────────
        _update_job(job_id, "generating_papers", 85, "Generating mock exam papers…")
        topic_names = [t.name for t in ranked_topics]
        mock_papers = paper_generator.generate_mock_papers(
            subject_name=subject,
            course_name=course,
            institution_name=institution,
            topics=topic_names,
            pyq_data=pyq_data,
        )
        try:
            for mp in mock_papers:
                supabase_service.save_mock_paper(subject_id, mp.paper_number, mp.model_dump())
        except Exception as e:
            logger.warning(f"[{job_id}] Mock paper DB save failed (non-fatal): {e}")

        # ── Done ───────────────────────────────────────────────────────────────
        _update_job(
            job_id, "done", 100, "Analysis complete!",
            result={
                "submission_id": submission_id,
                "subject_id": subject_id,
                "topics": [t.model_dump() for t in ranked_topics],
                "plan": plan.model_dump(),
                "papers": [mp.model_dump() for mp in mock_papers],
                "total_years": len(pyq_data),
            }
        )

    except Exception as e:
        logger.exception(f"[{job_id}] Pipeline error: {e}")
        _update_job(job_id, "error", 0, f"Analysis failed: {str(e)}", error=str(e))
    finally:
        # Clean up temp files
        try:
            if syllabus_path:
                os.unlink(syllabus_path)
            for _, p in pyq_paths:
                os.unlink(p)
        except Exception:
            pass


@router.post("/upload", response_model=SubmissionResponse)
async def upload_files(
    background_tasks: BackgroundTasks,
    institution_name: str = Form(...),
    course_name: str = Form(...),
    course_code: str = Form(...),
    subject_name: str = Form(...),
    syllabus: Optional[UploadFile] = File(None),
    syllabus_text: Optional[str] = Form(None),
    pyqs: list[UploadFile] = File(...),
    years: str = Form(...),  # comma-separated years e.g. "2022,2023,2024"
):
    """
    Upload syllabus (PDF or raw text) + PYQ files and start the analysis pipeline.
    Returns a job_id for polling status.
    """
    if (not syllabus or not syllabus.filename) and (not syllabus_text or not syllabus_text.strip()):
        raise HTTPException(status_code=400, detail="Please provide either an official syllabus PDF or syllabus text.")

    job_id = str(uuid.uuid4())

    # ── Save uploaded syllabus file to temp if provided ───────────────────────
    syllabus_tmp_path = None
    if syllabus and syllabus.filename:
        syllabus_suffix = Path(syllabus.filename or "syllabus.pdf").suffix or ".pdf"
        syllabus_tmp = tempfile.NamedTemporaryFile(delete=False, suffix=syllabus_suffix)
        syllabus_tmp.write(await syllabus.read())
        syllabus_tmp.close()
        syllabus_tmp_path = syllabus_tmp.name

    # PYQs
    year_list = [y.strip() for y in years.split(",")]
    if len(year_list) != len(pyqs):
        # Pad or trim years
        while len(year_list) < len(pyqs):
            year_list.append(str(2020 + len(year_list)))
        year_list = year_list[:len(pyqs)]

    pyq_paths = []
    for i, pyq_file in enumerate(pyqs):
        pyq_suffix = Path(pyq_file.filename or "pyq.pdf").suffix or ".pdf"
        pyq_tmp = tempfile.NamedTemporaryFile(delete=False, suffix=pyq_suffix)
        pyq_tmp.write(await pyq_file.read())
        pyq_tmp.close()
        pyq_paths.append((year_list[i], pyq_tmp.name))

    # ── Create DB records ──────────────────────────────────────────────────────
    subject_id = job_id  # Use job_id as subject_id for MVP
    submission_id = job_id

    try:
        inst_id = supabase_service.upsert_institution(institution_name)
        course_id = supabase_service.upsert_course(inst_id, course_name, course_code)
        subject_id = supabase_service.upsert_subject(course_id, subject_name)
        submission_id = supabase_service.create_submission(subject_id)
        for year, _ in pyq_paths:
            supabase_service.create_pyq(submission_id, int(year))
    except Exception as e:
        logger.warning(f"DB record creation failed (non-fatal): {e}")

    # Pre-seed metadata so github.py can retrieve institution/course/subject later
    _jobs[job_id] = {
        "institution": institution_name,
        "course": course_name,
        "subject": subject_name,
    }
    # Initialize job status (merges into the pre-seeded dict above)
    _update_job(job_id, "pending", 0, "Upload received, starting analysis…")

    # Launch background pipeline
    background_tasks.add_task(
        _run_analysis_pipeline,
        job_id=job_id,
        submission_id=submission_id,
        subject_id=subject_id,
        institution=institution_name,
        course=course_name,
        subject=subject_name,
        syllabus_path=syllabus_tmp_path,
        syllabus_text=syllabus_text,
        pyq_paths=pyq_paths,
    )

    return SubmissionResponse(
        submission_id=job_id,
        subject_id=subject_id,
        status="pending",
        message="Files received. Analysis started.",
    )


@router.get("/status/{job_id}", response_model=StatusResponse)
async def get_status(job_id: str):
    """Poll the status of an analysis job."""
    job = _jobs.get(job_id)
    if not job:
        # Check DB as fallback
        try:
            sub = supabase_service.get_submission(job_id)
            if sub:
                return StatusResponse(
                    submission_id=job_id,
                    status=sub.get("status", "unknown"),
                    stage_message="Retrieved from database.",
                    progress=100 if sub.get("status") == "done" else 50,
                    result=sub.get("job_data"),
                )
        except Exception:
            pass
        raise HTTPException(status_code=404, detail="Job not found. It may have expired.")

    return StatusResponse(
        submission_id=job_id,
        status=job["status"],
        stage_message=job["stage_message"],
        progress=job["progress"],
        result=job.get("result"),
    )
