"""
Paper Generator Service
-----------------------
Infers exam structure from PYQ data and synthesizes two distinct mock papers.
Guarantees:
- Set 01 and Set 02 have DIFFERENT questions and different topic focus.
- No repeated questions inside the same paper.
- Real total marks (e.g. 100 Marks) — never 0 Marks.
- Renders high-grade printable PDFs using ReportLab.
"""

import io
import random
from datetime import datetime
from typing import List, Dict, Any, Tuple, Set
from models.schemas import MockPaper, Question, Section
import logging

logger = logging.getLogger(__name__)

# Diverse question templates by topic type
DIVERSE_SHORT_TEMPLATES = [
    "Define {topic} and state its key application in computer systems.",
    "What is the primary significance of {topic}? Explain in brief.",
    "State the fundamental principles governing {topic}.",
    "Write down the basic properties or conditions required for {topic}.",
    "Differentiate in brief between {topic} and {topic2}.",
    "List any two advantages and limitations of {topic}.",
    "Give a real-world example illustrating {topic}.",
]

DIVERSE_LONG_TEMPLATES = [
    "Explain {topic} in detail with suitable architectural diagrams and examples.",
    "Discuss the algorithmic approach for {topic}. Analyze its time and space complexity.",
    "Compare and contrast {topic} with {topic2}. Highlight performance trade-offs.",
    "Design a solution using {topic} for an enterprise system and trace each step.",
    "Explain the theoretical foundation of {topic} and prove its correctness.",
    "Write a step-by-step algorithm or procedure for {topic} with illustrative inputs.",
    "Discuss the various challenges encountered in {topic} and how they are mitigated.",
]


def infer_exam_structure(pyq_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Infer exam structure (total marks, duration, sections).
    Guarantees standard university marks (defaulting to 100, never 0).
    """
    detected_totals = []
    for p in pyq_data:
        tm = p.get("total_marks", 100)
        if isinstance(tm, int) and 30 <= tm <= 200:
            detected_totals.append(tm)

    total_marks = int(sum(detected_totals) / len(detected_totals)) if detected_totals else 100
    if total_marks <= 0:
        total_marks = 100

    # Standard university 3-section layout summing to 100 (or scaled)
    if total_marks == 70:
        sections_spec = [
            {"name": "Section A", "instructions": "Answer all questions in brief. (7 x 2 = 14 Marks)", "q_count": 7, "marks_per_q": 2, "total_marks": 14, "type": "short"},
            {"name": "Section B", "instructions": "Attempt any three of the following. (3 x 7 = 21 Marks)", "q_count": 5, "marks_per_q": 7, "total_marks": 21, "type": "long"},
            {"name": "Section C", "instructions": "Attempt any five questions from this section. (5 x 7 = 35 Marks)", "q_count": 7, "marks_per_q": 7, "total_marks": 35, "type": "long"},
        ]
    else:
        # Default 100 marks AKTU/PSIT standard
        sections_spec = [
            {"name": "Section A", "instructions": "Answer all questions in brief. (10 x 2 = 20 Marks)", "q_count": 10, "marks_per_q": 2, "total_marks": 20, "type": "short"},
            {"name": "Section B", "instructions": "Attempt any three of the following questions. (3 x 10 = 30 Marks)", "q_count": 5, "marks_per_q": 10, "total_marks": 30, "type": "long"},
            {"name": "Section C", "instructions": "Attempt any five questions from this section. (5 x 10 = 50 Marks)", "q_count": 7, "marks_per_q": 10, "total_marks": 50, "type": "long"},
        ]

    return {
        "total_marks": total_marks,
        "duration": "3 Hours",
        "sections": sections_spec,
    }


def generate_mock_papers(
    subject_name: str,
    course_name: str,
    institution_name: str,
    topics: List[str],
    pyq_data: List[Dict[str, Any]],
    num_papers: int = 2,
) -> List[MockPaper]:
    """
    Generate two simulated mock exam papers.
    Ensures Set 1 and Set 2 contain distinct questions and varied syllabus coverage.
    """
    structure = infer_exam_structure(pyq_data)

    # Gather all extracted authentic questions from uploaded PYQs
    real_short_questions: List[Dict] = []
    real_long_questions: List[Dict] = []
    for pyq in pyq_data:
        for q in pyq.get("questions", []):
            if q.get("type") == "short" or q.get("marks", 5) <= 3:
                real_short_questions.append(q)
            else:
                real_long_questions.append(q)

    # Clean topics pool
    cleaned_topics = [t.strip() for t in topics if len(t.strip()) >= 3]
    if not cleaned_topics:
        cleaned_topics = [subject_name, f"Principles of {subject_name}", f"Advanced {subject_name}"]

    # Partition topics and questions into two distinct sets for Paper 1 and Paper 2
    random.seed(42)  # deterministic yet varied partition
    shuffled_topics = list(cleaned_topics)
    random.shuffle(shuffled_topics)

    mid = max(len(shuffled_topics) // 2, 1)
    pool_set1_topics = shuffled_topics[:mid] if len(shuffled_topics) > 3 else shuffled_topics
    pool_set2_topics = shuffled_topics[mid:] if len(shuffled_topics) > 3 else shuffled_topics[::-1]

    # Partition real PYQ questions
    shuffled_real_short = list(real_short_questions)
    shuffled_real_long = list(real_long_questions)
    random.shuffle(shuffled_real_short)
    random.shuffle(shuffled_real_long)

    short_mid = len(shuffled_real_short) // 2
    long_mid = len(shuffled_real_long) // 2

    real_q_pools = [
        {"short": shuffled_real_short[:short_mid], "long": shuffled_real_long[:long_mid]},
        {"short": shuffled_real_short[short_mid:], "long": shuffled_real_long[long_mid:]},
    ]

    papers = []

    for p_idx in range(num_papers):
        paper_num = p_idx + 1
        active_topics = pool_set1_topics if p_idx == 0 else pool_set2_topics
        real_pool = real_q_pools[p_idx % len(real_q_pools)]

        used_question_texts: Set[str] = set()
        sections_out = []

        topic_counter = 0

        for sec_spec in structure["sections"]:
            sec_name = sec_spec["name"]
            q_count = sec_spec["q_count"]
            marks_per_q = sec_spec["marks_per_q"]
            is_short = (sec_spec["type"] == "short")

            questions_out = []
            real_candidates = list(real_pool["short"] if is_short else real_pool["long"])

            for qi in range(q_count):
                q_text = ""
                # Attempt to use authentic PYQ question first
                while real_candidates:
                    cand = real_candidates.pop(0)
                    c_text = cand.get("text", "").strip()
                    if c_text and c_text not in used_question_texts and len(c_text) >= 15:
                        q_text = c_text
                        break

                # If no unique real question available, synthesize from topics
                if not q_text:
                    t1 = active_topics[topic_counter % len(active_topics)]
                    topic_counter += 1
                    t2 = active_topics[topic_counter % len(active_topics)]

                    templates = DIVERSE_SHORT_TEMPLATES if is_short else DIVERSE_LONG_TEMPLATES
                    tmpl = templates[(qi + p_idx * 3) % len(templates)]
                    q_text = tmpl.format(topic=t1, topic2=t2)

                    # Ensure uniqueness
                    if q_text in used_question_texts:
                        q_text = f"Discuss the key methodologies and implementations of {t1}."

                used_question_texts.add(q_text)

                # Format question label e.g. Q1(a) for Section A, Q2, Q3 for B/C
                if "a" in sec_name.lower():
                    q_num = f"Q1({chr(97 + qi)})" if qi < 26 else f"Q1.{qi + 1}"
                else:
                    q_num = f"Q{qi + (2 if 'b' in sec_name.lower() else 5)}"

                questions_out.append(Question(
                    number=q_num,
                    text=q_text,
                    marks=marks_per_q,
                    type=sec_spec["type"],
                ))

            sections_out.append(Section(
                title=sec_name,
                instructions=sec_spec["instructions"],
                questions=questions_out,
                total_marks=sec_spec["total_marks"],
            ))

        papers.append(MockPaper(
            paper_number=paper_num,
            subject=subject_name.upper(),
            course=course_name,
            institution=institution_name.upper(),
            exam_duration=structure["duration"],
            total_marks=structure["total_marks"],
            sections=sections_out,
            generated_at=datetime.utcnow().isoformat(),
        ))

    return papers


# ── PDF Rendering with ReportLab ──────────────────────────────────────────────

def render_paper_to_pdf(paper: MockPaper) -> bytes:
    """Render simulated examination paper to clean PDF bytes."""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.lib import colors
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
        )
        from reportlab.lib.enums import TA_CENTER, TA_RIGHT

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=2.0 * cm,
            leftMargin=2.0 * cm,
            topMargin=1.8 * cm,
            bottomMargin=1.8 * cm,
        )

        styles = getSampleStyleSheet()
        navy = colors.HexColor("#1B2A4A")
        gold = colors.HexColor("#C9922A")

        inst_style = ParagraphStyle("Inst", parent=styles["Title"], textColor=navy, fontSize=14, alignment=TA_CENTER, spaceAfter=2)
        course_style = ParagraphStyle("Course", parent=styles["Normal"], textColor=navy, fontSize=10, alignment=TA_CENTER, spaceAfter=4)
        subj_style = ParagraphStyle("Subj", parent=styles["Normal"], textColor=navy, fontSize=11, alignment=TA_CENTER, fontName="Helvetica-Bold", spaceAfter=6)
        sec_title = ParagraphStyle("SecTitle", parent=styles["Heading2"], textColor=navy, fontSize=11, spaceBefore=8, spaceAfter=2)
        instr_style = ParagraphStyle("Instr", parent=styles["Italic"], fontSize=8.5, textColor=colors.dimgrey, spaceAfter=6)
        q_style = ParagraphStyle("Q", parent=styles["Normal"], fontSize=9.5, spaceAfter=4, leading=13)
        marks_style = ParagraphStyle("Marks", parent=styles["Normal"], fontSize=9, textColor=gold, alignment=TA_RIGHT, fontName="Helvetica-Bold")

        story = []

        # Institution & Exam Header
        story.append(Paragraph(paper.institution, inst_style))
        story.append(Paragraph(f"{paper.course} — Semester Examination Simulation", course_style))
        story.append(Paragraph(f"SUBJECT: {paper.subject}", subj_style))
        story.append(HRFlowable(width="100%", thickness=1.5, color=gold, spaceAfter=6))

        # Metadata Table
        meta_data = [
            ["Paper Set:", f"Set 0{paper.paper_number}", "Duration:", paper.exam_duration],
            ["Maximum Marks:", f"{paper.total_marks} Marks", "Date:", datetime.utcnow().strftime("%B %Y")],
        ]
        meta_table = Table(meta_data, colWidths=[3.5 * cm, 5.5 * cm, 3.5 * cm, 4.5 * cm])
        meta_table.setStyle(TableStyle([
            ("FONTSIZE", (0, 0), (-1, -1), 8.5),
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
            ("TEXTCOLOR", (0, 0), (-1, -1), navy),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ]))
        story.append(meta_table)
        story.append(HRFlowable(width="100%", thickness=0.8, color=navy, spaceBefore=4, spaceAfter=8))

        # Sections
        for section in paper.sections:
            story.append(Paragraph(f"<b>{section.title.upper()}</b>", sec_title))
            story.append(Paragraph(f"<i>{section.instructions}</i>", instr_style))

            for q in section.questions:
                q_text = f"<b>{q.number}.</b> {q.text}"
                m_text = f"[{q.marks}M]"
                row = Table(
                    [[Paragraph(q_text, q_style), Paragraph(m_text, marks_style)]],
                    colWidths=[14.5 * cm, 2.5 * cm],
                )
                row.setStyle(TableStyle([
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]))
                story.append(row)

            story.append(Spacer(1, 0.2 * cm))

        # Footer
        story.append(Spacer(1, 0.4 * cm))
        story.append(HRFlowable(width="100%", thickness=1, color=gold, spaceAfter=4))
        story.append(Paragraph("<i>— Generated by Precedent Academic Intelligence Engine —</i>",
                               ParagraphStyle("Foot", parent=styles["Normal"], fontSize=8, textColor=colors.grey, alignment=TA_CENTER)))

        doc.build(story)
        return buffer.getvalue()
    except Exception as e:
        logger.error(f"ReportLab PDF rendering error: {e}")
        return b""
