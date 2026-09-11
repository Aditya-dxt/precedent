"""
Planner Router
--------------
Accepts revision parameters and returns a knapsack-optimized day-by-day plan.
"""

import logging
from fastapi import APIRouter, HTTPException
from models.schemas import PlannerRequest, PlannerResponse, TopicItem
from services import supabase_service
from services.optimizer import build_revision_plan

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/planner", response_model=PlannerResponse)
async def create_plan(req: PlannerRequest):
    """
    Generate a marks-optimized revision plan.
    Fetches topics from DB for the given subject_id.
    """
    try:
        topics_data = supabase_service.get_topics(req.subject_id)
    except Exception as e:
        logger.warning(f"DB fetch failed, using empty topics: {e}")
        topics_data = []

    if not topics_data:
        raise HTTPException(
            status_code=404,
            detail="No topics found for this subject. Complete an analysis first."
        )

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

    plan = build_revision_plan(
        subject_id=req.subject_id,
        topics=topics,
        days_available=req.days_available,
        hours_per_day=req.hours_per_day,
    )

    # Save to DB
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

    return plan
