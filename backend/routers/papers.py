"""
Papers Router
-------------
GET /api/papers/{subject_id} — retrieve generated mock papers.
GET /api/papers/{subject_id}/download/{paper_number} — download mock paper PDF.
Resilient: checks Supabase DB and in-memory job cache.
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
import logging

from models.schemas import MockPapersResponse, MockPaper
from services import supabase_service
from services.paper_generator import render_paper_to_pdf

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/papers/{subject_id}", response_model=MockPapersResponse)
async def get_papers(subject_id: str):
    """Get stored mock papers for a subject."""
    from routers.upload import _jobs

    papers = []

    # 1. Try Supabase DB
    try:
        papers_data = supabase_service.get_mock_papers(subject_id)
        for p in papers_data:
            content = p.get("content_json", {})
            if content:
                try:
                    papers.append(MockPaper(**content))
                except Exception:
                    pass
    except Exception as e:
        logger.warning(f"DB papers fetch failed: {e}")

    # 2. Fallback to in-memory job cache
    if not papers:
        job = _jobs.get(subject_id, {})
        job_result = job.get("result", {})
        cached_papers = job_result.get("papers", [])
        for p in cached_papers:
            try:
                papers.append(MockPaper(**p) if isinstance(p, dict) else p)
            except Exception:
                pass

    if not papers:
        raise HTTPException(status_code=404, detail="No mock papers found. Run an analysis first.")

    return MockPapersResponse(submission_id=subject_id, papers=papers)


@router.get("/papers/{subject_id}/download/{paper_number}")
async def download_paper_pdf(subject_id: str, paper_number: int):
    """Download a specific mock paper as PDF."""
    from routers.upload import _jobs

    target = None

    # 1. Try Supabase DB
    try:
        papers_data = supabase_service.get_mock_papers(subject_id)
        for p in papers_data:
            content = p.get("content_json", {})
            if content.get("paper_number") == paper_number:
                target = content
                break
    except Exception:
        pass

    # 2. Fallback to in-memory cache
    if not target:
        job = _jobs.get(subject_id, {})
        cached_papers = job.get("result", {}).get("papers", [])
        for p in cached_papers:
            p_dict = p if isinstance(p, dict) else p.model_dump()
            if p_dict.get("paper_number") == paper_number:
                target = p_dict
                break

    if not target:
        raise HTTPException(status_code=404, detail=f"Paper {paper_number} not found.")

    try:
        paper_obj = MockPaper(**target)
        pdf_bytes = render_paper_to_pdf(paper_obj)
        if not pdf_bytes:
            raise ValueError("Empty PDF rendered")

        filename = f"Mock_Paper_0{paper_number}_{paper_obj.subject.replace(' ', '_')}.pdf"
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )
    except Exception as e:
        logger.error(f"PDF download error: {e}")
        raise HTTPException(status_code=500, detail="Failed to render PDF.")
