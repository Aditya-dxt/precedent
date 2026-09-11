"""
Analysis Router
---------------
Direct analysis endpoint for subjects already in the database.
"""

import logging
from fastapi import APIRouter, HTTPException
from models.schemas import TopicsResponse
from services import supabase_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/topics/{subject_id}", response_model=TopicsResponse)
async def get_topics(subject_id: str):
    """Get ranked topics for a given subject."""
    try:
        topics_data = supabase_service.get_topics(subject_id)
    except Exception as e:
        logger.error(f"Failed to fetch topics: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch topics from database.")

    if not topics_data:
        raise HTTPException(status_code=404, detail="No topics found for this subject. Run an analysis first.")

    from models.schemas import TopicItem
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

    return TopicsResponse(
        subject_id=subject_id,
        subject_name=topics_data[0].get("name", ""),
        total_years_analyzed=topics_data[0].get("cluster_data", {}).get("total_years", 1) if topics_data else 0,
        topics=topics,
    )
