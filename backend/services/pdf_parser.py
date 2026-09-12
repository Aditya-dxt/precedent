"""
PDF & Text Parser Service
-------------------------
Extracts syllabus topics from PDF or raw text.
Extracts questions, marks, and sections from PYQ PDFs.
Handles university examination layouts (AKTU, PSIT, VTU, Mumbai Univ, etc.)
"""

import re
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

try:
    import pymupdf as fitz
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False


def extract_text_from_pdf(path: str) -> str:
    """Extract full text from a PDF file using PyMuPDF with pdfplumber fallback."""
    text = ""
    if PYMUPDF_AVAILABLE:
        try:
            doc = fitz.open(path)
            for page in doc:
                text += page.get_text() + "\n"
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

    return text


def parse_syllabus(path: str) -> Dict[str, Any]:
    """Parse syllabus from PDF file path."""
    text = extract_text_from_pdf(path)
    if not text.strip():
        return {
            "topics": [],
            "units": [],
            "raw_text": "",
            "error": "Could not extract text from syllabus PDF. Please use 'Enter as Text' option or check if the PDF is scanned.",
        }
    return parse_syllabus_text(text)


def parse_syllabus_text(text: str) -> Dict[str, Any]:
    """
    Parse syllabus text directly into granular topics and units.
    Splits by units, modules, lines, commas, semicolons, and bullets.
    """
    if not text or not text.strip():
        return {"topics": [], "units": [], "raw_text": "", "error": "Syllabus text is empty."}

    cleaned_text = text.replace("\r\n", "\n").replace("\r", "\n")
    units = []
    all_topics = []

    # Detect unit headers (e.g. "UNIT 1", "UNIT-I", "Module 1", "CHAPTER 1")
    unit_regex = re.compile(
        r'(?:^|\n)\s*(UNIT\s*[-–—:]*\s*[IVX\d]+|MODULE\s*[-–—:]*\s*[IVX\d]+|CHAPTER\s*[-–—:]*\s*[IVX\d]+)[:\-\s]*(.*?)(?=(?:\n\s*(?:UNIT|MODULE|CHAPTER)\s*[-–—:]*\s*[IVX\d]+)|\Z)',
        re.IGNORECASE | re.DOTALL
    )

    matches = list(unit_regex.finditer(cleaned_text))

    if matches:
        for match in matches:
            unit_title = match.group(1).strip()
            unit_body = match.group(2).strip()
            unit_topics = _extract_subtopics_from_chunk(unit_body)
            if unit_topics:
                units.append({"unit": unit_title, "topics": unit_topics})
                all_topics.extend(unit_topics)

    # If no unit headers were detected, extract from the entire text
    if not all_topics:
        all_topics = _extract_subtopics_from_chunk(cleaned_text)

    # Deduplicate while preserving order
    seen = set()
    unique_topics = []
    for t in all_topics:
        norm = t.strip()
        key = norm.lower()
        if key not in seen and len(norm) >= 3:
            seen.add(key)
            unique_topics.append(norm)

    return {
        "topics": unique_topics,
        "units": units,
        "raw_text": text[:5000],
    }


def _extract_subtopics_from_chunk(chunk: str) -> List[str]:
    """
    Break down a syllabus text block into individual atomic topics.
    Splits by newlines, commas, semicolons, colons, bullets, and dashes.
    """
    topics = []
    # Stop words or noise phrases to discard
    noise = {
        'introduction', 'overview', 'basic concepts', 'advanced topics',
        'syllabus', 'course outcome', 'co1', 'co2', 'co3', 'co4', 'co5',
        'lecture', 'lectures', 'hours', 'marks', 'credits', 'text books',
        'reference books', 'prerequisites', 'objectives', 'outcomes',
        'module', 'unit', 'chapter', 'theory', 'practical'
    }

    # First split into lines/sentences
    raw_lines = chunk.split('\n')
    for raw_line in raw_lines:
        line = raw_line.strip()
        if not line:
            continue

        # Remove leading bullets, numbers, dashes e.g. "1.", "1.1", "-", "*"
        line = re.sub(r'^(?:[\d\.\-\*\•\–\—\)\(]+|[a-zA-Z][\.\)])\s*', '', line)

        # Split clauses by commas, semicolons, or " and "
        parts = re.split(r'[,;•\n\t]+', line)
        for part in parts:
            item = part.strip()
            # Clean punctuation from ends
            item = re.sub(r'^[:\-\s\.]+|[:\-\s\.]+$', '', item)

            # Strip colon prefixes like "Introduction: Algorithms" -> "Algorithms"
            if ':' in item:
                subparts = item.split(':')
                for sp in subparts:
                    sp_clean = sp.strip()
                    if len(sp_clean) >= 3 and sp_clean.lower() not in noise:
                        _add_valid_topic(sp_clean, topics, noise)
            else:
                _add_valid_topic(item, topics, noise)

    return topics


def _add_valid_topic(item: str, topics: List[str], noise: set):
    """Filter and validate a candidate topic string."""
    item = re.sub(r'\s+', ' ', item).strip()
    # Remove parenthetical info if overly long e.g. "(10 hours)"
    item = re.sub(r'\(\s*\d+\s*(?:hrs?|hours?|marks?|credits?)\s*\)', '', item, flags=re.IGNORECASE).strip()

    if not item or item.isdigit() or len(item) < 3 or len(item) > 90:
        return

    # Check if purely noise
    if item.lower() in noise:
        return

    # Title-case clean strings
    if item.isupper() and len(item) > 5:
        item = item.title()

    topics.append(item)


# ── PYQ Parsing ───────────────────────────────────────────────────────────────

def parse_pyq(path: str, year: int) -> Dict[str, Any]:
    """
    Parse a PYQ PDF and return extracted questions, sections, and total marks.
    Robust to AKTU/PSIT and common university question paper layouts.
    """
    text = extract_text_from_pdf(path)
    if not text.strip():
        return {
            "year": year,
            "questions": [],
            "sections": [],
            "total_marks": 100,
            "error": f"Could not extract text from PYQ {year}.",
        }

    # Normalize newlines
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Detect exam total marks from header (e.g. "Total Marks : 100", "Max Marks: 70")
    detected_total_marks = 100
    tm_match = re.search(r'(?:Total|Max|Maximum)\s*Marks?\s*[:\-=]?\s*(\d{2,3})', text, re.IGNORECASE)
    if tm_match:
        try:
            val = int(tm_match.group(1))
            if 30 <= val <= 200:
                detected_total_marks = val
        except Exception:
            pass

    # Split into Sections (Section A, Section B, Section C, PART A, etc.)
    section_pattern = re.compile(
        r'(?:^|\n)\s*(SECTION\s*[-–—:]*\s*[A-Z\d]|PART\s*[-–—:]*\s*[A-Z\d]|GROUP\s*[-–—:]*\s*[A-Z\d])[:\-\s]*(.*?)(?=(?:\n\s*(?:SECTION|PART|GROUP)\s*[-–—:]*\s*[A-Z\d])|\Z)',
        re.IGNORECASE | re.DOTALL
    )
    section_matches = list(section_pattern.finditer(text))

    questions = []
    sections = []
    running_total_marks = 0

    if section_matches:
        for match in section_matches:
            sec_header = match.group(1).strip()
            sec_body = match.group(2).strip()

            # Infer marks per question for this section from instructions like (10 x 2 = 20) or (3 x 10 = 30)
            default_marks = 5
            if 'a' in sec_header.lower():
                default_marks = 2
            elif 'b' in sec_header.lower():
                default_marks = 10
            elif 'c' in sec_header.lower():
                default_marks = 10

            mult_match = re.search(r'\(\s*\d+\s*[xX*]\s*(\d+)\s*=\s*(\d+)\s*\)', sec_body)
            if mult_match:
                try:
                    default_marks = int(mult_match.group(1))
                except Exception:
                    pass

            sec_qs = _extract_questions_from_text(sec_body, sec_header, default_marks)
            if sec_qs:
                sections.append({
                    "section": sec_header,
                    "questions": sec_qs,
                    "default_marks": default_marks,
                })
                questions.extend(sec_qs)
                running_total_marks += sum(q["marks"] for q in sec_qs)
    else:
        # Fallback if no sections
        questions = _extract_questions_from_text(text, "General", default_marks=5)
        running_total_marks = sum(q["marks"] for q in questions)
        sections = [{"section": "General", "questions": questions, "default_marks": 5}]

    final_total = detected_total_marks if detected_total_marks > 0 else max(running_total_marks, 100)

    return {
        "year": year,
        "questions": questions,
        "sections": sections,
        "total_marks": final_total,
    }


def _extract_questions_from_text(text: str, section: str, default_marks: int = 5) -> List[Dict]:
    """
    Extract individual questions and their marks from a text block.
    Matches Q1, 1., (a), a., Question 1, etc.
    """
    questions = []

    # Regex for question start markers
    q_split_regex = re.compile(
        r'(?:^|\n)\s*(?:(?:Q(?:uestion)?\.?\s*\d+|[0-9]{1,2}\s*[\.\)]|\([a-z]\)|[a-z]\s*[\.\)]|\([ivxIVX]+\))\s*)',
        re.IGNORECASE
    )

    # Marks regex e.g. [07], [7], (7), [7 Marks], [CO1, 7], (10)
    marks_regex = re.compile(r'\[(?:\s*CO\d+\s*,)?\s*(\d{1,2})\s*(?:marks?|m)?\]|\(\s*(\d{1,2})\s*(?:marks?|m)\)', re.IGNORECASE)

    # Split text into question candidates
    splits = [m.start() for m in q_split_regex.finditer(text)]
    if splits:
        for idx in range(len(splits)):
            start = splits[idx]
            end = splits[idx + 1] if idx + 1 < len(splits) else len(text)
            q_chunk = text[start:end].strip()

            # Clean marker from beginning
            cleaned_q = q_split_regex.sub('', q_chunk, count=1).strip()
            # Collapse multi-whitespace
            cleaned_q = re.sub(r'\s+', ' ', cleaned_q).strip()

            # Skip noise or instructions
            if len(cleaned_q) < 12 or cleaned_q.lower().startswith(('attempt all', 'attempt any', 'note:', 'all questions carry')):
                continue

            # Extract marks
            marks = default_marks
            m_match = marks_regex.search(q_chunk)
            if m_match:
                try:
                    val = int(m_match.group(1) or m_match.group(2))
                    if 1 <= val <= 25:
                        marks = val
                except Exception:
                    pass

            # Classify question type
            q_lower = cleaned_q.lower()
            if any(w in q_lower for w in ['define', 'what is', 'state', 'list', 'name', 'differentiate in brief']):
                q_type = 'short'
            elif any(w in q_lower for w in ['explain', 'describe', 'discuss', 'compare', 'analyze', 'evaluate']):
                q_type = 'long'
            elif any(w in q_lower for w in ['design', 'derive', 'implement', 'write an algorithm', 'solve', 'calculate', 'prove']):
                q_type = 'long'
            else:
                q_type = 'short' if marks <= 3 else 'long'

            questions.append({
                "text": cleaned_q[:600],
                "marks": marks,
                "type": q_type,
                "section": section,
            })

    # Fallback: if regex didn't find questions, split by lines ending with '?' or lines > 25 chars
    if not questions:
        for line in text.split('\n'):
            line = line.strip()
            if len(line) > 20 and ('?' in line or any(line.lower().startswith(w) for w in ['what', 'why', 'explain', 'define', 'how', 'discuss', 'write'])):
                questions.append({
                    "text": line[:600],
                    "marks": default_marks,
                    "type": "short" if default_marks <= 3 else "long",
                    "section": section,
                })

    return questions
