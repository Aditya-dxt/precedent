"""
PDF Parser Service
-----------------
Extracts topics from syllabus PDFs and questions from PYQ PDFs.
Uses PyMuPDF (pymupdf) as primary parser; pdfplumber as fallback.
Handles malformed / scanned PDFs gracefully.
"""

import re
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

# ── PyMuPDF (primary) ─────────────────────────────────────────────────────────
try:
    import pymupdf as fitz  # new API name as of PyMuPDF 1.24+
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False

# ── pdfplumber (fallback) ─────────────────────────────────────────────────────
try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False


def extract_text_from_pdf(path: str) -> str:
    """Extract full text from a PDF file. Returns empty string on failure."""
    text = ""
    if PYMUPDF_AVAILABLE:
        try:
            doc = fitz.open(path)
            for page in doc:
                text += page.get_text()
            doc.close()
            if text.strip():
                return text
        except Exception as e:
            logger.warning(f"PyMuPDF failed on {path}: {e}")

    if PDFPLUMBER_AVAILABLE:
        try:
            with pdfplumber.open(path) as pdf:
                for page in pdf.pages:
                    t = page.extract_text()
                    if t:
                        text += t + "\n"
            return text
        except Exception as e:
            logger.warning(f"pdfplumber failed on {path}: {e}")

    logger.error(f"All PDF parsers failed for {path}")
    return ""


def parse_syllabus(path: str) -> Dict[str, Any]:
    """
    Parse a syllabus PDF and return a list of topic strings.
    Attempts to detect unit/module structure.
    Returns: { topics: List[str], units: List[dict], raw_text: str }
    """
    text = extract_text_from_pdf(path)
    if not text.strip():
        return {"topics": [], "units": [], "raw_text": "", "error": "Could not extract text from syllabus PDF. The file may be scanned/image-based."}

    topics = []
    units = []

    # Detect unit headers (e.g., "UNIT I", "Unit 1:", "Module 1")
    unit_pattern = re.compile(
        r'(UNIT\s+[IVX\d]+|Unit\s+\d+|MODULE\s+\d+|Module\s+\d+)[:\-\s]+(.*?)(?=UNIT\s+[IVX\d]+|Unit\s+\d+|MODULE\s+\d+|Module\s+\d+|\Z)',
        re.IGNORECASE | re.DOTALL
    )
    unit_matches = list(unit_pattern.finditer(text))

    if unit_matches:
        for match in unit_matches:
            unit_header = match.group(1).strip()
            unit_body = match.group(2).strip()
            # Extract individual topics: lines that look like topic titles
            lines = [l.strip() for l in unit_body.split('\n') if l.strip()]
            unit_topics = _extract_topics_from_lines(lines)
            units.append({"unit": unit_header, "topics": unit_topics})
            topics.extend(unit_topics)
    else:
        # Fallback: treat every non-empty line as a potential topic
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        topics = _extract_topics_from_lines(lines)

    # Deduplicate while preserving order
    seen = set()
    unique_topics = []
    for t in topics:
        key = t.lower()
        if key not in seen:
            seen.add(key)
            unique_topics.append(t)

    return {
        "topics": unique_topics,
        "units": units,
        "raw_text": text[:5000],  # truncate for storage
    }


def _extract_topics_from_lines(lines: List[str]) -> List[str]:
    """Heuristic: pick lines that look like topic names (not too long, not too short)."""
    topics = []
    for line in lines:
        line = re.sub(r'^[\d\.\-\*\•]+\s*', '', line)  # strip leading bullets/numbers
        line = line.strip()
        # Likely a topic if 3-100 chars and not all caps (page headers) and not a number
        if 3 < len(line) <= 100 and not line.isdigit() and not line.isupper():
            topics.append(line)
    return topics[:50]  # cap at 50 topics per unit


def parse_pyq(path: str, year: int) -> Dict[str, Any]:
    """
    Parse a PYQ PDF and return a list of questions with metadata.
    Returns: { year, questions: List[dict], sections: List[dict], total_marks: int }
    """
    text = extract_text_from_pdf(path)
    if not text.strip():
        return {
            "year": year,
            "questions": [],
            "sections": [],
            "total_marks": 0,
            "error": f"Could not extract text from PYQ {year}. The file may be scanned/image-based."
        }

    questions = []
    sections = []
    total_marks = 0

    # Detect section headers (Section A, PART A, etc.)
    section_pattern = re.compile(
        r'(SECTION\s+[A-Z]|PART\s+[A-Z]|Section\s+[A-Z]|Part\s+[A-Z])[:\-\s]*(.*?)(?=SECTION\s+[A-Z]|PART\s+[A-Z]|Section\s+[A-Z]|Part\s+[A-Z]|\Z)',
        re.IGNORECASE | re.DOTALL
    )
    section_matches = list(section_pattern.finditer(text))

    if section_matches:
        for match in section_matches:
            section_name = match.group(1).strip()
            section_body = match.group(2).strip()
            section_qs = _extract_questions_from_text(section_body, section_name)
            sections.append({"section": section_name, "questions": section_qs})
            questions.extend(section_qs)
    else:
        # No section structure detected — extract all questions
        questions = _extract_questions_from_text(text, "General")

    for q in questions:
        total_marks += q.get("marks", 0)

    return {
        "year": year,
        "questions": questions,
        "sections": sections,
        "total_marks": total_marks,
    }


def _extract_questions_from_text(text: str, section: str) -> List[Dict]:
    """Extract question dicts from a block of text."""
    questions = []

    # Match patterns like: "Q1.", "1.", "Q.1", "(i)", "a)" followed by question text
    q_pattern = re.compile(
        r'(?:Q\.?\s*\d+|^\d+[\.\)]\s*|^[a-z][\.\)]\s*|\([ivxIVX]+\)\s*)(.+?)(?=Q\.?\s*\d+|^\d+[\.\)]\s*|^[a-z][\.\)]\s*|\([ivxIVX]+\)\s*|\Z)',
        re.MULTILINE | re.DOTALL
    )

    # Marks pattern
    marks_pattern = re.compile(r'\[(\d+)\s*(?:marks?|M|Marks?)\]|\((\d+)\s*(?:marks?|M)\)', re.IGNORECASE)

    for match in q_pattern.finditer(text):
        q_text = match.group(1).strip()
        if len(q_text) < 10:
            continue

        # Extract marks from question text
        marks_match = marks_pattern.search(q_text)
        marks = 0
        if marks_match:
            marks = int(marks_match.group(1) or marks_match.group(2))
        else:
            # Heuristic: default based on section
            if "a" in section.lower():
                marks = 2
            elif "b" in section.lower():
                marks = 5
            else:
                marks = 10

        # Determine question type
        q_lower = q_text.lower()
        if any(w in q_lower for w in ["define", "list", "state", "what is", "who"]):
            q_type = "short"
        elif any(w in q_lower for w in ["explain", "describe", "discuss", "compare", "elaborate"]):
            q_type = "long"
        elif any(w in q_lower for w in ["design", "implement", "write", "draw", "code"]):
            q_type = "long"
        else:
            q_type = "short"

        questions.append({
            "text": q_text[:500],
            "marks": marks,
            "type": q_type,
            "section": section,
        })

    # Fallback: split by newlines if no pattern matched
    if not questions:
        lines = [l.strip() for l in text.split('\n') if len(l.strip()) > 20]
        for line in lines[:20]:
            questions.append({
                "text": line[:500],
                "marks": 5,
                "type": "short",
                "section": section,
            })

    return questions
