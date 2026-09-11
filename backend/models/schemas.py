"""
Pydantic schemas for all request/response models.
"""
from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime


# ── Upload / Submission ──────────────────────────────────────────────────────

class SubmissionCreate(BaseModel):
    institution_name: str
    course_name: str
    course_code: str
    subject_name: str

class SubmissionResponse(BaseModel):
    submission_id: str
    subject_id: str
    status: str
    message: str

class StatusResponse(BaseModel):
    submission_id: str
    status: str           # pending | parsing | embedding | clustering | planning | publishing | done | error
    stage_message: str
    progress: int         # 0-100
    result: Optional[Any] = None


# ── Topics ───────────────────────────────────────────────────────────────────

class TopicItem(BaseModel):
    id: Optional[str] = None
    name: str
    frequency_score: float   # 0.0 – 1.0  (fraction of PYQ years it appeared)
    marks_weight: float      # normalised marks across all PYQs
    appeared_in_years: List[int] = []
    prep_time_hrs: float = 2.0   # estimated prep time; default 2h

class TopicsResponse(BaseModel):
    subject_id: str
    subject_name: str
    total_years_analyzed: int
    topics: List[TopicItem]


# ── Revision Planner ─────────────────────────────────────────────────────────

class PlannerRequest(BaseModel):
    subject_id: str
    days_available: int
    hours_per_day: float

class DayPlan(BaseModel):
    day: int
    topics: List[TopicItem]
    total_hours: float

class PlannerResponse(BaseModel):
    plan_id: Optional[str] = None
    subject_id: str
    days_available: int
    hours_per_day: float
    expected_marks_coverage: float   # e.g. 0.78 → "78%"
    days: List[DayPlan]


# ── Mock Papers ───────────────────────────────────────────────────────────────

class Question(BaseModel):
    number: str
    text: str
    marks: int
    type: str   # MCQ | short | long

class Section(BaseModel):
    title: str
    instructions: str
    questions: List[Question]
    total_marks: int

class MockPaper(BaseModel):
    paper_number: int
    subject: str
    course: str
    institution: str
    exam_duration: str
    total_marks: int
    sections: List[Section]
    generated_at: str

class MockPapersResponse(BaseModel):
    submission_id: str
    papers: List[MockPaper]


# ── GitHub / Repository ───────────────────────────────────────────────────────

class PublishResponse(BaseModel):
    success: bool
    github_url: str
    commit_sha: str
    files_committed: List[str]

class RepoSubject(BaseModel):
    name: str
    path: str
    github_url: str

class RepoCourse(BaseModel):
    name: str
    subjects: List[RepoSubject]

class RepoInstitution(BaseModel):
    name: str
    courses: List[RepoCourse]

class RepositoryResponse(BaseModel):
    institutions: List[RepoInstitution]
    total_subjects: int
    total_institutions: int
