"""
Planner Router
--------------
POST /api/planner — generate a marks-optimized revision plan given days & hours.
Resilient: checks request payload, in-memory job store, and Supabase DB.
"""

from fastapi import APIRouter, HTTPException
import logging
from typing import List

from models.schemas import PlannerRequest, PlannerResponse, TopicItem
from services.optimizer import build_revision_plan
from services import supabase_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/planner", response_model=PlannerResponse)
async def create_plan(req: PlannerRequest):
    """
    Generate a marks-optimized revision plan.
    Resilient topic lookup:
      1. Uses req.topics directly if passed from frontend.
      2. Checks in-memory job cache from recent analysis.
      3. Queries Supabase DB.
    """
    from routers.upload import _jobs

    topics: List[TopicItem] = []

    # 1. Use topics directly from request payload if available
    if req.topics:
        topics = req.topics

    # 2. Check in-memory job store
    if not topics:
        job = _jobs.get(req.subject_id, {})
        job_result = job.get("result", {})
        cached_topics = job_result.get("topics", [])
        if cached_topics:
            topics = [TopicItem(**t) if isinstance(t, dict) else t for t in cached_topics]

    # 3. Check Supabase DB
    if not topics:
        try:
            topics_data = supabase_service.get_topics(req.subject_id)
            if topics_data:
                topics = [
                    TopicItem(
                        id=t.get("id"),
                        name=t.get("name", ""),
                        frequency_score=t.get("frequency_score", 0.0),
                        marks_weight=t.get("marks_weight", 0.0),
                        appeared_in_years=t.get("cluster_data", {}).get("appeared_in_years", []),
                        prep_time_hrs=t.get("cluster_data", {}).get("prep_time_hrs", 2.0),
                    )
                    for t in topics_data
                ]
        except Exception as e:
            logger.warning(f"DB fetch failed: {e}")

    if not topics:
        raise HTTPException(
            status_code=404,
            detail="No topics found for this subject. Complete an analysis first."
        )

    plan = build_revision_plan(
        subject_id=req.subject_id,
        topics=topics,
        days_available=req.days_available,
        hours_per_day=req.hours_per_day,
    )

    # Save to DB if available
    try:
        plan_id = supabase_service.save_revision_plan(
            subject_id=req.subject_id,
            days=req.days_available,
            hours=req.hours_per_day,
            plan_json=plan.model_dump(),
        )
        plan.plan_id = plan_id
    except Exception as e:
        logger.warning(f"Plan DB save failed (non-fatal): {e}")

    # Cache updated plan in memory
    if req.subject_id in _jobs and "result" in _jobs[req.subject_id]:
        _jobs[req.subject_id]["result"]["plan"] = plan.model_dump()

    return plan
