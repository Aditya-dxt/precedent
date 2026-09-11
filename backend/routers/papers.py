"""
Papers Router
-------------
Serves generated mock papers and PDF download.
"""

import logging
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from models.schemas import MockPapersResponse, MockPaper
from services import supabase_service
from services.paper_generator import render_paper_to_pdf

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/papers/{subject_id}", response_model=MockPapersResponse)
async def get_papers(subject_id: str):
    """Get stored mock papers for a subject."""
    try:
        papers_data = supabase_service.get_mock_papers(subject_id)
    except Exception as e:
        logger.error(f"Failed to fetch papers: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch papers.")

    if not papers_data:
        raise HTTPException(status_code=404, detail="No mock papers found. Run an analysis first.")

    papers = []
    for p in papers_data:
        content = p.get("content_json", {})
        if content:
            try:
                papers.append(MockPaper(**content))
            except Exception:
                pass

    return MockPapersResponse(submission_id=subject_id, papers=papers)


@router.get("/papers/{subject_id}/download/{paper_number}")
async def download_paper_pdf(subject_id: str, paper_number: int):
    """Download a specific mock paper as PDF."""
    try:
        papers_data = supabase_service.get_mock_papers(subject_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to fetch papers.")

    target = None
    for p in papers_data:
        content = p.get("content_json", {})
        if content.get("paper_number") == paper_number:
            target = content
            break

    if not target:
        raise HTTPException(status_code=404, detail=f"Paper {paper_number} not found.")

    try:
        paper = MockPaper(**target)
        pdf_bytes = render_paper_to_pdf(paper)
        if not pdf_bytes:
            raise HTTPException(status_code=500, detail="PDF generation failed.")
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="mock-paper-{paper_number}.pdf"'},
        )
    except Exception as e:
        logger.error(f"PDF render error: {e}")
        raise HTTPException(status_code=500, detail=f"PDF generation error: {str(e)}")
