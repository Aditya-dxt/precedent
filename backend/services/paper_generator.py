"""
Paper Generator Service
-----------------------
Infers exam structure from parsed PYQs and generates two realistic mock papers.
Renders to PDF using ReportLab.
"""

import io
import random
from datetime import datetime
from typing import List, Dict, Any, Tuple
from models.schemas import MockPaper, Question, Section
import logging

logger = logging.getLogger(__name__)


# ── Structure Inference ────────────────────────────────────────────────────────

def infer_exam_structure(pyq_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Infer section layout, marks per section, and question types from PYQ data.
    Returns a structure dict used by generate_mock_papers.
    """
    section_counts: Dict[str, int] = {}
    section_marks: Dict[str, List[int]] = {}
    total_marks_list = []

    for pyq in pyq_data:
        total_marks_list.append(pyq.get("total_marks", 100))
        for section_data in pyq.get("sections", []):
            sec = section_data.get("section", "Section A")
            qs = section_data.get("questions", [])
            section_counts[sec] = section_counts.get(sec, 0) + len(qs)
            marks_in_sec = sum(q.get("marks", 5) for q in qs)
            section_marks.setdefault(sec, []).append(marks_in_sec)

    avg_total = int(sum(total_marks_list) / len(total_marks_list)) if total_marks_list else 100

    # Build section specs
    sections_spec = []
    if section_counts:
        for sec, count in sorted(section_counts.items()):
            avg_marks = int(sum(section_marks.get(sec, [30])) / max(len(section_marks.get(sec, [1])), 1))
            sections_spec.append({
                "name": sec,
                "avg_question_count": max(1, count // max(len(pyq_data), 1)),
                "avg_total_marks": avg_marks,
            })
    else:
        # Default 3-section structure
        sections_spec = [
            {"name": "Section A", "avg_question_count": 10, "avg_total_marks": 20},
            {"name": "Section B", "avg_question_count": 5,  "avg_total_marks": 30},
            {"name": "Section C", "avg_question_count": 3,  "avg_total_marks": 50},
        ]

    return {
        "total_marks": avg_total,
        "duration": "3 Hours",
        "sections": sections_spec,
    }


# ── Question Bank ─────────────────────────────────────────────────────────────

QUESTION_TEMPLATES = {
    "define": [
        "Define {topic}. State its key characteristics.",
        "What is {topic}? Give a brief explanation.",
        "State the definition of {topic} with an example.",
    ],
    "explain": [
        "Explain {topic} in detail with a suitable example.",
        "Describe the concept of {topic} and its importance.",
        "Discuss {topic} with respect to its application in real-world systems.",
    ],
    "compare": [
        "Compare and contrast {topic} with {topic2}. Highlight key differences.",
        "Differentiate between {topic} and {topic2} with examples.",
    ],
    "design": [
        "Design a {topic} for a university management system. Show all components.",
        "Implement {topic} and explain each step with a diagram.",
        "Write an algorithm for {topic}. Analyze its time and space complexity.",
    ],
}




def _generate_question(topic: str, marks: int, q_type: str, all_topics: List[str]) -> Question:
    """Generate a realistic exam question for a topic."""
    t2 = random.choice([t for t in all_topics if t != topic] or [topic])
    if q_type == "short" or marks <= 2:
        tmpl = random.choice(QUESTION_TEMPLATES["define"])
    elif marks <= 5:
        tmpl = random.choice(QUESTION_TEMPLATES["explain"])
    elif "compare" in q_type.lower():
        tmpl = random.choice(QUESTION_TEMPLATES["compare"])
    else:
        tmpl = random.choice(QUESTION_TEMPLATES["design"])

    text = tmpl.format(topic=topic, topic2=t2)
    return Question(
        number="",  # filled in later
        text=text,
        marks=marks,
        type=q_type,
    )


def generate_mock_papers(
    subject_name: str,
    course_name: str,
    institution_name: str,
    topics: List[str],
    pyq_data: List[Dict[str, Any]],
    num_papers: int = 2,
) -> List[MockPaper]:
    """
    Generate `num_papers` mock exam papers.
    Uses inferred structure from PYQs and the topic list.
    """
    structure = infer_exam_structure(pyq_data)
    if not topics:
        raise ValueError("Cannot generate mock papers: no topics provided. Upload and analyze a syllabus first.")

    topic_pool = list(topics)
    papers = []

    for paper_num in range(1, num_papers + 1):
        random.shuffle(topic_pool)
        sections_out = []
        topic_idx = 0

        for sec_spec in structure["sections"]:
            sec_name = sec_spec["name"]
            q_count = sec_spec["avg_question_count"]
            sec_marks_total = sec_spec["avg_total_marks"]
            marks_per_q = max(1, sec_marks_total // max(q_count, 1))

            # Determine question type by section
            if "a" in sec_name.lower() or marks_per_q <= 3:
                q_type = "short"
                instructions = f"Answer all questions. Each question carries {marks_per_q} mark(s)."
            elif "b" in sec_name.lower() or marks_per_q <= 8:
                q_type = "long"
                instructions = f"Attempt any {max(1, q_count-1)} out of {q_count} questions. Each question carries {marks_per_q} marks."
            else:
                q_type = "long"
                instructions = f"Attempt any {max(1, q_count-1)} out of {q_count} questions. Each question carries {marks_per_q} marks."

            questions_out = []
            for qi in range(q_count):
                t = topic_pool[topic_idx % len(topic_pool)]
                topic_idx += 1
                q = _generate_question(t, marks_per_q, q_type, topic_pool)
                q.number = f"Q{qi + 1}"
                questions_out.append(q)

            sections_out.append(Section(
                title=sec_name,
                instructions=instructions,
                questions=questions_out,
                total_marks=sec_marks_total,
            ))

        papers.append(MockPaper(
            paper_number=paper_num,
            subject=subject_name,
            course=course_name,
            institution=institution_name,
            exam_duration=structure["duration"],
            total_marks=structure["total_marks"],
            sections=sections_out,
            generated_at=datetime.utcnow().isoformat(),
        ))

    return papers


# ── PDF Rendering ─────────────────────────────────────────────────────────────

def render_paper_to_pdf(paper: MockPaper) -> bytes:
    """
    Render a MockPaper to PDF bytes using ReportLab.
    Styled to look like an actual university exam paper.
    """
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.lib import colors
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
        )
        from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=2.5 * cm,
            leftMargin=2.5 * cm,
            topMargin=2 * cm,
            bottomMargin=2 * cm,
        )

        styles = getSampleStyleSheet()
        navy = colors.HexColor("#1B2A4A")
        gold = colors.HexColor("#C9922A")

        title_style = ParagraphStyle("Title", parent=styles["Title"], textColor=navy, fontSize=14, spaceAfter=4)
        subtitle_style = ParagraphStyle("Subtitle", parent=styles["Normal"], textColor=navy, fontSize=11, alignment=TA_CENTER, spaceAfter=2)
        section_style = ParagraphStyle("Section", parent=styles["Heading2"], textColor=navy, fontSize=12, spaceBefore=12, spaceAfter=4, borderPad=4)
        instr_style = ParagraphStyle("Instr", parent=styles["Italic"], fontSize=9, textColor=colors.gray, spaceAfter=6)
        q_style = ParagraphStyle("Q", parent=styles["Normal"], fontSize=10, spaceAfter=8, leftIndent=12)
        marks_style = ParagraphStyle("Marks", parent=styles["Normal"], fontSize=9, textColor=gold, alignment=TA_RIGHT)

        story = []

        # Header
        story.append(Paragraph(paper.institution.upper(), ParagraphStyle("Inst", parent=styles["Title"], textColor=navy, fontSize=16, alignment=TA_CENTER)))
        story.append(Spacer(1, 0.2 * cm))
        story.append(HRFlowable(width="100%", thickness=2, color=gold))
        story.append(Spacer(1, 0.2 * cm))

        # Exam info table
        info_data = [
            ["Subject:", paper.subject, "Time:", paper.exam_duration],
            ["Course:", paper.course, "Max Marks:", str(paper.total_marks)],
            ["Paper:", f"Mock Paper {paper.paper_number}", "Date:", datetime.utcnow().strftime("%B %Y")],
        ]
        info_table = Table(info_data, colWidths=[3 * cm, 8 * cm, 3 * cm, 3 * cm])
        info_table.setStyle(TableStyle([
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
            ("TEXTCOLOR", (0, 0), (-1, -1), navy),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        story.append(info_table)
        story.append(HRFlowable(width="100%", thickness=1, color=navy))
        story.append(Spacer(1, 0.4 * cm))

        # General instructions
        story.append(Paragraph("<b>General Instructions:</b> Attempt all sections. Write clearly and legibly. Mobile phones and electronic devices are not permitted.", instr_style))
        story.append(Spacer(1, 0.3 * cm))

        # Sections
        for section in paper.sections:
            story.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey))
            story.append(Paragraph(f"<b>{section.title}</b>", section_style))
            story.append(Paragraph(section.instructions, instr_style))

            for q in section.questions:
                q_text = f"<b>{q.number}.</b> {q.text}"
                marks_text = f"[{q.marks} Marks]"
                row = Table(
                    [[Paragraph(q_text, q_style), Paragraph(marks_text, marks_style)]],
                    colWidths=[14 * cm, 3 * cm],
                )
                row.setStyle(TableStyle([
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]))
                story.append(row)

        story.append(Spacer(1, 0.5 * cm))
        story.append(HRFlowable(width="100%", thickness=2, color=gold))
        story.append(Paragraph("<i>— Generated by Precedent · Your exam has a history. We read it. —</i>",
                                ParagraphStyle("Footer", parent=styles["Normal"], fontSize=8, textColor=colors.grey, alignment=TA_CENTER, spaceBefore=6)))

        doc.build(story)
        return buffer.getvalue()

    except Exception as e:
        logger.error(f"PDF render failed: {e}")
        return b""
