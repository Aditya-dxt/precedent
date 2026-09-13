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


# ── Academic Topic Sanitization & Extraction ──────────────────────────────────

TECH_ACRONYMS = {
    'HTML', 'XML', 'CSS', 'SQL', 'DBMS', 'RDBMS', 'NOSQL', 'API', 'REST',
    'JSON', 'DOM', 'PHP', 'AJAX', 'JSX', 'TS', 'JS', 'DAA', 'OS', 'OOP',
    'CN', 'SE', '1NF', '2NF', '3NF', 'BCNF', '4NF', '5NF', 'TCP', 'UDP',
    'IP', 'IPV4', 'IPV6', 'HTTP', 'HTTPS', 'FTP', 'SSH', 'SMTP', 'DNS',
    'CPU', 'RAM', 'ROM', 'ALU', 'RISC', 'CISC', 'DMA', 'B-TREE', 'B+ TREE',
    'AVL', 'DFS', 'BFS', 'KMP', 'LCS', 'DP', 'NP', 'AI', 'ML', 'NLP'
}

GREETINGS_AND_SIGNOFFS = re.compile(
    r'^(?:dear\s+(?:students?|all|sir|madam|learners?|everyone|friends?)|'
    r'hello|hi\b|hey\b|good\s+(?:morning|afternoon|evening)|'
    r'regards|thanks|thank\s+you|best\s+(?:of\s+luck|wishes|regards)|'
    r'yours\s+(?:faithfully|sincerely)|sincerely|faculty|submitted\s+by|'
    r'all\s+the\s+best|good\s+luck|happy\s+learning|do\s+well)\b',
    re.IGNORECASE
)

NOTICE_AND_META_HEADERS = re.compile(
    r'(?:please\s+note|kindly\s+note|note\s*:|notice\b|instructions?|'
    r'syllabus\s+for|class\s+test|\bct\s*[-–—:]*\s*\d+|\bmst\s*[-–—:]*\s*\d+|'
    r'sessionals?|mid\s*term|end\s*term|unit\s*test|pre\s*university|put\s+exam|'
    r'exam\s+schedule|date\s*:|venue\s*:|time\s*:|timing\s*:|marks\s*:|'
    r'total\s+marks|duration\s*:|batch\s*:|semester\s*:|academic\s+year)\b',
    re.IGNORECASE
)

UNIT_HEADER_LINE = re.compile(
    r'^[_\*\~`#\s\-\–\—]*(?:unit|module|chapter|part|section)\s*[-–—:]*\s*[ivx\d]+[_\*\~`#\s\-\–\—:]*$',
    re.IGNORECASE
)

BIBLIO_HEADER_LINE = re.compile(
    r'^(?:text\s*books?|reference\s*books?|suggested\s*readings?|'
    r'books?\s*recommended|course\s*outcomes?|course\s*objectives?|'
    r'prerequisites?|web\s*references?|pedagogy|experiments?|lab\s*work)\b',
    re.IGNORECASE
)

STOPWORDS = {
    'the', 'and', 'for', 'with', 'what', 'how', 'from', 'this', 'that',
    'between', 'into', 'through', 'during', 'before', 'after', 'above',
    'below', 'to', 'from', 'up', 'down', 'in', 'out', 'on', 'off', 'over',
    'under', 'again', 'further', 'then', 'once', 'here', 'there', 'when',
    'where', 'why', 'how', 'all', 'any', 'both', 'each', 'few', 'more',
    'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own',
    'same', 'so', 'than', 'too', 'very', 'can', 'will', 'just', 'should'
}


def _clean_and_sanitize_topic(candidate: str) -> Optional[str]:
    """
    Sanitize and validate a candidate topic string.
    Filters out greetings, notice sentences, unit headers, and non-academic text.
    """
    if not candidate:
        return None

    # 1. Strip markdown artifacts (*, _, ~, `, #)
    s = re.sub(r'[\*\_~`#]+', ' ', candidate)
    # 2. Strip bullet markers (e.g. "1.", "1.1", "(a)", "•", "-")
    s = re.sub(r'^\s*(?:\(?\d{1,2}(?:\.\d{1,2})*[\.\)]|\(?[a-zA-Z][\.\)]|[•\-\–\—\*]+)\s*', '', s)
    # Strip trailing punctuation
    s = re.sub(r'[\:\.\,\;\-\–\—\s]+$', '', s).strip()
    s = re.sub(r'\s+', ' ', s)

    if not s or len(s) < 2:
        return None

    # Quick check for greetings, test notices, unit headers, or bibliography
    if GREETINGS_AND_SIGNOFFS.search(s) or NOTICE_AND_META_HEADERS.search(s) or UNIT_HEADER_LINE.match(s) or BIBLIO_HEADER_LINE.search(s):
        return None

    # Strip imperative verbs and qualifiers (e.g. "Complete web development and other theoretical part" -> "Web Development")
    s = re.sub(r'^(?:complete|study|cover|prepare|learn|read|review|revise|introduction\s+to|overview\s+of|basics\s+of|fundamentals\s+of|principles\s+of)\s+', '', s, flags=re.IGNORECASE).strip()
    s = re.sub(r'\s+(?:and\s+other\s+(?:theoretical|practical)\s+parts?|and\s+numerical|theoretical\s+part|practical\s+part|and\s+its\s+applications?|in\s+detail|etc\.?)$', '', s, flags=re.IGNORECASE).strip()

    if not s or len(s) < 2 or len(s) > 65:
        return None

    # Re-verify after stripping
    if GREETINGS_AND_SIGNOFFS.search(s) or NOTICE_AND_META_HEADERS.search(s) or UNIT_HEADER_LINE.match(s):
        return None

    lower = s.lower()
    if lower in {'syllabus', 'unit', 'module', 'chapter', 'part', 'section', 'course', 'subject', 'theory', 'practical', 'all the best', 'good luck'}:
        return None

    # Reject full English sentences (word count > 7 or > 50% stopwords)
    words = s.split()
    if len(words) > 7:
        return None
    if len(words) >= 4:
        stop_count = sum(1 for w in words if w.lower() in STOPWORDS)
        if stop_count / len(words) >= 0.5:
            return None

    # Format words: preserve technical acronyms, title-case regular words
    clean_words = []
    for w in words:
        upper = w.upper()
        if upper in TECH_ACRONYMS or re.match(r'^\d+[A-Z]+$', upper):
            clean_words.append(upper)
        elif w.lower() in {'of', 'and', 'in', 'for', 'to', 'the', 'on', 'with', 'via', 'vs'}:
            clean_words.append(w.lower())
        else:
            clean_words.append(w.capitalize())

    final_str = ' '.join(clean_words)
    if final_str:
        final_str = final_str[0].upper() + final_str[1:]
    return final_str if len(final_str) >= 2 else None


def parse_syllabus_text(text: str) -> Dict[str, Any]:
    """
    Parse syllabus text directly into genuine academic topics.
    Strips out conversational text, greetings, test notices, and unit labels.
    """
    if not text or not text.strip():
        return {"topics": [], "units": [], "raw_text": "", "error": "Syllabus text is empty."}

    cleaned_text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = cleaned_text.split('\n')

    all_topics: List[str] = []
    units: List[Dict[str, Any]] = []
    current_unit_name = "General Topics"
    current_unit_topics: List[str] = []
    in_biblio = False

    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            continue

        # Check if entering bibliography section (Text Books, Reference Books)
        if BIBLIO_HEADER_LINE.search(line):
            in_biblio = True
            continue

        # Detect unit header lines (e.g. "_*-Unit 1-*_", "UNIT 1:", "Module 2")
        unit_match = re.search(r'^(?:[_\*\~`#\s\-\–\—]*)(UNIT\s*[-–—:]*\s*[IVX\d]+|MODULE\s*[-–—:]*\s*[IVX\d]+|CHAPTER\s*[-–—:]*\s*[IVX\d]+)', line, re.IGNORECASE)
        if unit_match:
            # New unit resets bibliography mode
            in_biblio = False
            if current_unit_topics:
                units.append({"unit": current_unit_name, "topics": list(current_unit_topics)})
                current_unit_topics = []

            current_unit_name = re.sub(r'[\*\_~`#]+', '', unit_match.group(1)).strip().title()

            # If line is ONLY the unit header, continue without adding as topic
            remaining = line[unit_match.end():].strip(' :-\t_*\n')
            if not remaining:
                continue
            line = remaining

        if in_biblio:
            continue

        # If line is a greeting or notice sentence, skip completely
        if GREETINGS_AND_SIGNOFFS.search(line) or NOTICE_AND_META_HEADERS.search(line) or UNIT_HEADER_LINE.match(line):
            continue

        # Split line by commas, semicolons, bullets, or colons
        subparts = re.split(r'[,;•\t]+', line)
        for part in subparts:
            # Also handle colons e.g. "Sorting: Merge Sort, Quick Sort"
            if ':' in part:
                for colon_sub in part.split(':'):
                    topic = _clean_and_sanitize_topic(colon_sub)
                    if topic and topic not in all_topics:
                        all_topics.append(topic)
                        current_unit_topics.append(topic)
            else:
                topic = _clean_and_sanitize_topic(part)
                if topic and topic not in all_topics:
                    all_topics.append(topic)
                    current_unit_topics.append(topic)

    if current_unit_topics:
        units.append({"unit": current_unit_name, "topics": current_unit_topics})

    return {
        "topics": all_topics,
        "units": units,
        "raw_text": text[:5000],
    }



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
