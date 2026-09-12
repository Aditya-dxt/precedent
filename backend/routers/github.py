"""
GitHub Router
-------------
POST /api/publish/{submission_id} — auto-commit analysis artifacts to GitHub.
GET  /api/repository             — browse repository hierarchy.

Produces richly formatted, professionally structured Markdown artifacts:
  - analysis/topic-predictions.md  (full ranked topic matrix with confidence tiers)
  - analysis/syllabus-map.md       (topic-to-unit mapping)
  - mock-papers/mock-paper-0N.pdf  (ReportLab PDFs)
  - README.md                      (subject-level landing page with shields)
"""

from fastapi import APIRouter, HTTPException
from typing import List, Tuple, Optional
from datetime import datetime
import logging
import math

from models.schemas import PublishResponse, RepositoryResponse, MockPaper
from services import github_service, supabase_service
from services.paper_generator import render_paper_to_pdf

logger = logging.getLogger(__name__)
router = APIRouter()


# ── Helpers ────────────────────────────────────────────────────────────────────

def _confidence_tier(freq: float, marks: float) -> Tuple[str, str, str]:
    """Return (emoji, label, badge_color) for a topic based on composite score."""
    composite = (freq * 0.6) + (marks * 0.4)
    if composite >= 0.65:
        return "🔴", "Critical — Must Prepare", "critical"
    elif composite >= 0.45:
        return "🟠", "High Yield", "high"
    elif composite >= 0.28:
        return "🟡", "Moderate Probability", "moderate"
    else:
        return "🟢", "Low Priority", "low"


def _bar(value: float, width: int = 10) -> str:
    """Return a visual unicode progress bar, e.g. ████░░░░░░ 67%"""
    filled = round(value * width)
    return "█" * filled + "░" * (width - filled)


def _shield(label: str, message: str, color: str) -> str:
    """Return a shields.io badge markdown string."""
    label_enc = label.replace(" ", "%20").replace("-", "--")
    message_enc = message.replace(" ", "%20").replace("-", "--")
    return f"![{label}](https://img.shields.io/badge/{label_enc}-{message_enc}-{color}?style=flat-square)"


def _now_str() -> str:
    return datetime.utcnow().strftime("%B %d, %Y at %H:%M UTC")


def _year_str() -> str:
    return datetime.utcnow().strftime("%Y")


# ── Content Builders ───────────────────────────────────────────────────────────

def _build_topic_predictions_md(
    institution: str,
    course: str,
    subject: str,
    topics: List[dict],
    total_years: int,
) -> bytes:
    """
    Build a richly formatted topic-predictions.md with:
    - Badges and header
    - Executive summary statistics
    - Confidence-tier legend
    - Full ranked table with visual bars
    - Confidence tier breakdown sections
    - Methodology and disclaimer
    """
    now = _now_str()
    year = _year_str()

    # Compute stats
    n = len(topics)
    critical = [t for t in topics if (_confidence_tier(
        t.get("frequency_score", 0), t.get("marks_weight", 0))[1] == "Critical — Must Prepare")]
    high = [t for t in topics if (_confidence_tier(
        t.get("frequency_score", 0), t.get("marks_weight", 0))[1] == "High Yield")]
    avg_freq = (sum(t.get("frequency_score", 0) for t in topics) / n * 100) if n else 0
    top3 = topics[:3] if len(topics) >= 3 else topics

    lines = []

    # ── Header ──────────────────────────────────────────────────────────────
    lines += [
        f"<div align=\"center\">\n\n",
        f"# 📊 Exam Pattern Analysis Report\n",
        f"## {subject}\n\n",
        f"*{course}*  \n",
        f"*{institution}*\n\n",
        f"{_shield('Precedent', 'AI Analysis', '1B2A4A')}  ",
        f"{_shield('Topics Identified', str(n), '0ea5e9')}  ",
        f"{_shield('PYQ Years Analysed', str(total_years) if total_years else 'Multi-Year', '7c3aed')}  ",
        f"{_shield('Generated', year, 'C9922A')}  \n\n",
        f"</div>\n\n",
        "---\n\n",
    ]

    # ── Quick Stats ─────────────────────────────────────────────────────────
    lines += [
        "## ⚡ Executive Summary\n\n",
        "> **Precedent** ran semantic similarity clustering on your uploaded PYQ papers against the parsed syllabus.\n",
        "> The table below ranks every identified topic by its historical repeat probability.\n\n",
        "| Metric | Value |\n",
        "| :--- | :--- |\n",
        f"| 🎯 **Total Topics Identified** | `{n}` |\n",
        f"| 🔴 **Critical Topics** *(≥65% composite)* | `{len(critical)}` |\n",
        f"| 🟠 **High-Yield Topics** *(45–65% composite)* | `{len(high)}` |\n",
        f"| 📅 **PYQ Years Analysed** | `{total_years if total_years else 'Multi-Year'}` |\n",
        f"| 📈 **Average Repeat Frequency** | `{avg_freq:.1f}%` |\n",
        f"| 🏫 **Institution** | {institution} |\n",
        f"| 📚 **Course / Program** | {course} |\n",
        f"| 🕒 **Analysis Generated** | {now} |\n\n",
    ]

    # ── Top 3 Spotlight ─────────────────────────────────────────────────────
    if top3:
        lines += [
            "### 🏆 Top 3 Most Likely Exam Topics\n\n",
        ]
        medals = ["🥇", "🥈", "🥉"]
        for i, t in enumerate(top3):
            name = t.get("name", "")
            freq = t.get("frequency_score", 0)
            marks = t.get("marks_weight", 0)
            emoji, tier, _ = _confidence_tier(freq, marks)
            lines.append(
                f"| {medals[i]} | **`{name}`** | Repeat: **{freq*100:.0f}%** | Marks Weight: **{marks*100:.0f}%** | {emoji} {tier} |\n"
            )
        lines.append("\n")

    # ── Confidence Tier Legend ───────────────────────────────────────────────
    lines += [
        "---\n\n",
        "## 🗺️ Confidence Tier Legend\n\n",
        "| Tier | Composite Score | Recommendation |\n",
        "| :--- | :--- | :--- |\n",
        "| 🔴 **Critical** | ≥ 65% | Extremely high repeat history — prepare thoroughly |\n",
        "| 🟠 **High Yield** | 45–65% | Frequently examined — strong preparation advised |\n",
        "| 🟡 **Moderate** | 28–45% | Appears periodically — solid understanding recommended |\n",
        "| 🟢 **Low Priority** | < 28% | Rare or baseline syllabus coverage |\n\n",
        "> 💡 *Composite Score = (Repeat Frequency × 0.60) + (Marks Weight × 0.40)*\n\n",
        "---\n\n",
    ]

    # ── Full Ranked Table ────────────────────────────────────────────────────
    lines += [
        "## 📋 Complete Ranked Topic Matrix\n\n",
        "| Rank | Priority | Topic / Competency | Repeat Frequency | Marks Weight | Confidence |\n",
        "| :---: | :---: | :--- | :--- | :--- | :--- |\n",
    ]

    for i, t in enumerate(topics, 1):
        name = t.get("name", "Unknown")
        freq = t.get("frequency_score", 0.0)
        marks = t.get("marks_weight", 0.0)
        years_appeared = t.get("appeared_in_years", [])
        emoji, tier, _ = _confidence_tier(freq, marks)

        freq_bar = _bar(freq, 8)
        marks_bar = _bar(marks, 8)

        years_str = ", ".join(str(y) for y in sorted(years_appeared)) if years_appeared else "—"

        lines.append(
            f"| **{i:02d}** | {emoji} | **{name}** | `{freq_bar}` **{freq*100:.0f}%** | "
            f"`{marks_bar}` **{marks*100:.0f}%** | {tier} |\n"
        )

    lines.append("\n")

    # ── Tier-Grouped Breakdowns ──────────────────────────────────────────────
    tier_groups = {
        "🔴 Critical Topics — Must Prepare": [
            t for t in topics
            if _confidence_tier(t.get("frequency_score", 0), t.get("marks_weight", 0))[1] == "Critical — Must Prepare"
        ],
        "🟠 High-Yield Topics": [
            t for t in topics
            if _confidence_tier(t.get("frequency_score", 0), t.get("marks_weight", 0))[1] == "High Yield"
        ],
        "🟡 Moderate Probability Topics": [
            t for t in topics
            if _confidence_tier(t.get("frequency_score", 0), t.get("marks_weight", 0))[1] == "Moderate Probability"
        ],
    }

    lines.append("---\n\n## 🔍 Topic Deep-Dive by Confidence Tier\n\n")

    for tier_title, tier_topics in tier_groups.items():
        if not tier_topics:
            continue
        lines.append(f"### {tier_title}\n\n")
        for t in tier_topics:
            name = t.get("name", "")
            freq = t.get("frequency_score", 0.0)
            marks = t.get("marks_weight", 0.0)
            appeared = t.get("appeared_in_years", [])
            appeared_str = " · ".join(f"`{y}`" for y in sorted(appeared)) if appeared else "_Data inferred from pattern matching_"
            composite = (freq * 0.6) + (marks * 0.4)
            lines += [
                f"<details>\n",
                f"<summary><strong>{name}</strong> &nbsp;|&nbsp; Composite Score: <code>{composite*100:.0f}%</code></summary>\n\n",
                f"| Field | Value |\n",
                f"| :--- | :--- |\n",
                f"| **Repeat Frequency** | {_bar(freq)} `{freq*100:.0f}%` |\n",
                f"| **Marks Allocation Weight** | {_bar(marks)} `{marks*100:.0f}%` |\n",
                f"| **Appeared in Years** | {appeared_str} |\n",
                f"| **Composite Confidence** | `{composite*100:.0f}%` |\n\n",
                f"</details>\n\n",
            ]

    # ── Methodology ─────────────────────────────────────────────────────────
    lines += [
        "---\n\n",
        "## 🔬 Methodology\n\n",
        "This analysis was generated by the **Precedent Academic Intelligence Engine** using the following pipeline:\n\n",
        "```\n",
        "┌─────────────────────┐     ┌──────────────────────┐     ┌──────────────────────────┐\n",
        "│  Syllabus Parser    │────▶│  Semantic Embeddings │────▶│  Topic-Question Matcher  │\n",
        "│  (Unit/Module       │     │  all-MiniLM-L6-v2    │     │  Hybrid: Cosine (55%) +  │\n",
        "│   Extraction)       │     │  sentence-transformers│    │  Token Overlap (45%)     │\n",
        "└─────────────────────┘     └──────────────────────┘     └──────────────┬───────────┘\n",
        "                                                                         │\n",
        "┌─────────────────────┐     ┌──────────────────────┐     ┌──────────────▼───────────┐\n",
        "│  Mock Paper Gen     │◀────│  Knapsack Optimizer  │◀────│  Frequency + Marks       │\n",
        "│  (ReportLab PDFs)   │     │  (0/1 DP, 0.5hr      │     │  Score Aggregation       │\n",
        "│                     │     │   granularity)       │     │                          │\n",
        "└─────────────────────┘     └──────────────────────┘     └──────────────────────────┘\n",
        "```\n\n",
        "**Scoring Formula:**\n\n",
        "```\n",
        "Repeat Frequency  = (Matched Questions in PYQs) / (Total PYQ Questions) × adjustment\n",
        "Marks Weight      = (Marks of Matched Questions) / (Total PYQ Marks)\n",
        "Composite Score   = (Frequency × 0.60) + (Marks Weight × 0.40)\n",
        "```\n\n",
        "**Semantic Matching Threshold:** `≥ 0.28` combined cosine + token-overlap score  \n",
        "**Baseline Floor:** Topics not matched to any question receive `freq=0.15, marks=0.10` to reflect syllabus presence\n\n",
    ]

    # ── Disclaimer & Footer ──────────────────────────────────────────────────
    lines += [
        "---\n\n",
        "## ⚠️ Disclaimer\n\n",
        "> This document is generated by an AI-assisted pattern analysis tool and is intended for **supplementary study guidance only**.\n",
        "> It does not guarantee the exact questions in any examination.\n",
        "> Always refer to your official syllabus and faculty guidance as primary resources.\n\n",
        "---\n\n",
        "<div align=\"center\">\n\n",
        f"*Generated by [Precedent](https://github.com/Aditya-dxt/precedent) · {now}*  \n",
        f"*Open-access for academic use · Contributed to the Precedent Knowledge Repository*\n\n",
        "</div>\n",
    ]

    return "".join(lines).encode("utf-8")


def _build_subject_readme(
    institution: str,
    course: str,
    subject: str,
    topics: List[dict],
    num_papers: int,
    total_years: int,
) -> bytes:
    """
    Build a polished README.md for the subject folder with:
    - Shields/badges, description, directory tree, quick stats, topic preview table.
    """
    n = len(topics)
    critical_count = sum(
        1 for t in topics
        if _confidence_tier(t.get("frequency_score", 0), t.get("marks_weight", 0))[1] == "Critical — Must Prepare"
    )
    now = _now_str()
    year = _year_str()

    slug_subject = subject.replace(" ", "-").replace("/", "-")

    lines = [
        f"<div align=\"center\">\n\n",
        f"# 📘 {subject}\n\n",
        f"**{course}**  \n",
        f"_{institution}_\n\n",
        f"{_shield('Precedent', 'Knowledge%20Archive', '1B2A4A')}  ",
        f"{_shield('Topics', str(n), '0ea5e9')}  ",
        f"{_shield('Mock%20Papers', str(num_papers), '7c3aed')}  ",
        f"{_shield('PYQ%20Years', str(total_years) if total_years else 'Multi', 'C9922A')}  ",
        f"{_shield('Published', year, '16a34a')}  \n\n",
        f"</div>\n\n",
        "---\n\n",

        "## 📖 About This Subject Archive\n\n",
        f"This directory is part of the **[Precedent Academic Knowledge Repository](https://github.com/Aditya-dxt/precedent-vault)** — ",
        f"an open-access archive of AI-generated exam pattern analyses contributed by students using the Precedent platform.\n\n",
        f"> **Subject:** {subject}  \n",
        f"> **Course:** {course}  \n",
        f"> **Institution:** {institution}  \n",
        f"> **Analysed:** {now}  \n\n",
        "---\n\n",

        "## 📁 Directory Structure\n\n",
        "```\n",
        f"{slug_subject}/\n",
        "├── README.md                          ← You are here\n",
        "├── analysis/\n",
        "│   └── topic-predictions.md           ← Full ranked topic matrix\n",
        "└── mock-papers/\n",
    ]
    for i in range(1, num_papers + 1):
        lines.append(f"    ├── mock-paper-0{i}.pdf              ← Pattern-synthesized exam paper Set 0{i}\n")
    lines += [
        "```\n\n",
        "---\n\n",

        "## 📊 Quick Stats\n\n",
        "| 🎯 Topics Identified | 🔴 Critical Topics | 📄 Mock Papers | 📅 PYQ Coverage |\n",
        "| :---: | :---: | :---: | :---: |\n",
        f"| **{n}** | **{critical_count}** | **{num_papers}** | **{total_years if total_years else 'Multi'} Year(s)** |\n\n",
        "---\n\n",

        "## 🏆 Top Predicted Topics\n\n",
        "| Rank | Topic | Confidence | Repeat % | Marks % |\n",
        "| :---: | :--- | :---: | :---: | :---: |\n",
    ]

    for i, t in enumerate(topics[:10], 1):
        name = t.get("name", "")
        freq = t.get("frequency_score", 0.0)
        marks = t.get("marks_weight", 0.0)
        emoji, tier, _ = _confidence_tier(freq, marks)
        lines.append(
            f"| **{i:02d}** | {name} | {emoji} {tier} | **{freq*100:.0f}%** | **{marks*100:.0f}%** |\n"
        )

    if n > 10:
        lines.append(f"\n> 📄 *See [topic-predictions.md](analysis/topic-predictions.md) for all {n} topics.*\n")

    lines += [
        "\n---\n\n",

        "## 📝 What's Inside\n\n",
        "### `analysis/topic-predictions.md`\n",
        "A complete AI-generated exam pattern report including:\n",
        "- ✅ Full ranked topic matrix with visual confidence bars\n",
        "- ✅ Confidence-tier classification (Critical / High / Moderate / Low)\n",
        "- ✅ Per-topic drill-down with repeat frequency and marks allocation\n",
        "- ✅ Methodology explanation and scoring formula\n\n",

        "### `mock-papers/`\n",
        f"**{num_papers} simulated examination papers** generated by mirroring the structural patterns, ",
        "section layouts, and marks distributions of the uploaded PYQ papers:\n",
        "- ✅ Authentic PYQ questions reused where available\n",
        "- ✅ Pattern-synthesized questions for remaining slots\n",
        "- ✅ Standard AKTU-format sectioning (Section A / B / C)\n",
        "- ✅ Distinct question sets across Set 01 and Set 02\n\n",

        "---\n\n",

        "## 🚀 How to Use This Archive\n\n",
        "1. **Prioritise by tier** — Prepare 🔴 Critical topics first, then 🟠 High Yield\n",
        "2. **Download mock papers** — Practice under exam conditions using the PDF papers\n",
        "3. **Cross-reference syllabus** — Verify predicted topics against your official syllabus\n",
        "4. **Track revision** — Use the Precedent platform's Revision Planner for optimised scheduling\n\n",

        "---\n\n",

        "## 🛠️ Generated By\n\n",
        "| Tool | Version | Purpose |\n",
        "| :--- | :--- | :--- |\n",
        "| [Precedent Platform](https://github.com/Aditya-dxt/precedent) | Latest | Analysis engine |\n",
        "| `sentence-transformers` | `all-MiniLM-L6-v2` | Semantic embedding |\n",
        "| `scikit-learn` | — | Cosine similarity |\n",
        "| `PyMuPDF` + `pdfplumber` | — | PDF extraction |\n",
        "| `ReportLab` | — | Mock paper PDF generation |\n\n",

        "---\n\n",

        "<div align=\"center\">\n\n",
        f"*This archive was auto-generated by the [Precedent Platform](https://github.com/Aditya-dxt/precedent).*  \n",
        f"*Open-access for academic communities · Published {now}*\n\n",
        f"[![Precedent](https://img.shields.io/badge/Powered%20by-Precedent-1B2A4A?style=for-the-badge)](https://github.com/Aditya-dxt/precedent)\n\n",
        "</div>\n",
    ]

    return "".join(lines).encode("utf-8")


# ── Router Endpoints ───────────────────────────────────────────────────────────

@router.post("/publish/{submission_id}", response_model=PublishResponse)
async def publish_to_github(submission_id: str):
    """
    Commit richly formatted analysis artifacts for a submission to GitHub.
    Resilient: retrieves institution, course, subject, topics & papers from memory or DB.
    """
    from routers.upload import _jobs

    institution = "University Academic Archive"
    course = "Computer Science and Engineering"
    subject = "Academic Subject"
    topics = []
    papers_data = []
    total_years = 0

    # 1. Retrieve from in-memory analysis job cache
    job = _jobs.get(submission_id, {})
    if job:
        institution = job.get("institution") or institution
        course = job.get("course") or course
        subject = job.get("subject") or subject
        job_result = job.get("result", {})
        topics = job_result.get("topics", [])
        papers_data = job_result.get("papers", [])
        total_years = job_result.get("total_years", 0)

    # 2. Try Supabase if topics still missing
    if not topics:
        try:
            sub = supabase_service.get_submission(submission_id)
            if sub:
                db_topics = supabase_service.get_topics(sub.get("subject_id", submission_id))
                if db_topics:
                    topics = db_topics
        except Exception as e:
            logger.warning(f"Supabase fetch during publish skipped: {e}")

    # ── Build all content files ────────────────────────────────────────────
    num_papers = len(papers_data)

    topic_predictions_md = _build_topic_predictions_md(
        institution=institution,
        course=course,
        subject=subject,
        topics=topics,
        total_years=total_years,
    )

    subject_readme_md = _build_subject_readme(
        institution=institution,
        course=course,
        subject=subject,
        topics=topics,
        num_papers=num_papers,
        total_years=total_years,
    )

    files: List[Tuple[str, bytes]] = [
        ("analysis/topic-predictions.md", topic_predictions_md),
        ("README.md", subject_readme_md),
    ]

    # Render and include mock paper PDFs
    for p_idx, p in enumerate(papers_data):
        try:
            paper_obj = MockPaper(**p) if isinstance(p, dict) else p
            pdf_bytes = render_paper_to_pdf(paper_obj)
            if pdf_bytes:
                files.append((f"mock-papers/mock-paper-0{paper_obj.paper_number}.pdf", pdf_bytes))
        except Exception as e:
            logger.warning(f"Could not render paper {p_idx + 1} for GitHub commit: {e}")

    # ── Commit to GitHub ───────────────────────────────────────────────────
    commit_msg = (
        f"feat(archive): publish exam pattern analysis for {subject}\n\n"
        f"Institution : {institution}\n"
        f"Course      : {course}\n"
        f"Topics      : {len(topics)} identified\n"
        f"Mock Papers : {num_papers} generated\n"
        f"Generated   : {_now_str()}\n\n"
        f"Auto-published via Precedent Academic Intelligence Engine."
    )

    result = github_service.commit_analysis(
        institution=institution,
        course=course,
        subject=subject,
        files=files,
        commit_message=commit_msg,
    )

    if not result.get("success"):
        raise HTTPException(
            status_code=500,
            detail=f"GitHub publish failed: {result.get('error', 'Check GITHUB_TOKEN and GITHUB_REPO')}"
        )

    # Best-effort DB status update
    try:
        supabase_service.update_submission_status(submission_id, "published", {"github_url": result["github_url"]})
    except Exception:
        pass

    return PublishResponse(
        success=True,
        github_url=result["github_url"],
        commit_sha=result["commit_sha"],
        files_committed=result["files_committed"],
    )


@router.get("/repository", response_model=RepositoryResponse)
async def get_repository():
    """Browse the Precedent GitHub repository tree."""
    try:
        tree = github_service.get_repository_tree()
        return RepositoryResponse(**tree)
    except Exception as e:
        logger.error(f"Repository fetch error: {e}")
        return RepositoryResponse(
            institutions=[],
            total_subjects=0,
            total_institutions=0,
        )
