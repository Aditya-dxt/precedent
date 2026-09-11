"""
Supabase Service
----------------
CRUD helpers for all Precedent database tables.
"""

import os
import logging
from typing import Optional, List, Dict, Any
from supabase import create_client, Client

logger = logging.getLogger(__name__)

_client: Optional[Client] = None


def get_client() -> Client:
    global _client
    if _client is None:
        url = os.getenv("SUPABASE_URL", "")
        key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY", "")
        if not url or not key:
            raise ValueError("SUPABASE_URL and SUPABASE_ANON_KEY must be set.")
        _client = create_client(url, key)
    return _client


# ── Institutions ──────────────────────────────────────────────────────────────

def upsert_institution(name: str) -> str:
    """Insert or get institution, return its UUID."""
    client = get_client()
    res = client.table("institutions").select("id").eq("name", name).execute()
    if res.data:
        return res.data[0]["id"]
    ins = client.table("institutions").insert({"name": name}).execute()
    return ins.data[0]["id"]


def upsert_course(institution_id: str, name: str, code: str) -> str:
    client = get_client()
    res = client.table("courses").select("id").eq("institution_id", institution_id).eq("name", name).execute()
    if res.data:
        return res.data[0]["id"]
    ins = client.table("courses").insert({"institution_id": institution_id, "name": name, "code": code}).execute()
    return ins.data[0]["id"]


def upsert_subject(course_id: str, name: str) -> str:
    client = get_client()
    res = client.table("subjects").select("id").eq("course_id", course_id).eq("name", name).execute()
    if res.data:
        return res.data[0]["id"]
    ins = client.table("subjects").insert({"course_id": course_id, "name": name}).execute()
    return ins.data[0]["id"]


# ── Submissions ───────────────────────────────────────────────────────────────

def create_submission(subject_id: str, syllabus_url: str = "", uploaded_by: str = "anonymous") -> str:
    client = get_client()
    ins = client.table("submissions").insert({
        "subject_id": subject_id,
        "syllabus_url": syllabus_url,
        "uploaded_by": uploaded_by,
        "status": "pending",
    }).execute()
    return ins.data[0]["id"]


def update_submission_status(submission_id: str, status: str, job_data: Optional[Dict] = None):
    client = get_client()
    payload = {"status": status}
    if job_data is not None:
        payload["job_data"] = job_data
    client.table("submissions").update(payload).eq("id", submission_id).execute()


def get_submission(submission_id: str) -> Optional[Dict]:
    client = get_client()
    res = client.table("submissions").select("*").eq("id", submission_id).execute()
    return res.data[0] if res.data else None


# ── PYQs ──────────────────────────────────────────────────────────────────────

def create_pyq(submission_id: str, year: int, file_url: str = "") -> str:
    client = get_client()
    ins = client.table("pyqs").insert({
        "submission_id": submission_id,
        "year": year,
        "file_url": file_url,
    }).execute()
    return ins.data[0]["id"]


# ── Topics ────────────────────────────────────────────────────────────────────

def upsert_topics(subject_id: str, topics: List[Dict]) -> List[str]:
    """Insert/replace topic rows for a subject. Returns list of ids."""
    client = get_client()
    # Delete existing topics for this subject
    client.table("topics").delete().eq("subject_id", subject_id).execute()
    ids = []
    for t in topics:
        ins = client.table("topics").insert({
            "subject_id": subject_id,
            "name": t.get("name"),
            "frequency_score": t.get("frequency_score", 0.0),
            "marks_weight": t.get("marks_weight", 0.0),
            "cluster_data": t.get("cluster_data", {}),
        }).execute()
        ids.append(ins.data[0]["id"])
    return ids


def get_topics(subject_id: str) -> List[Dict]:
    client = get_client()
    res = client.table("topics").select("*").eq("subject_id", subject_id).order("frequency_score", desc=True).execute()
    return res.data or []


# ── Revision Plans ────────────────────────────────────────────────────────────

def save_revision_plan(subject_id: str, days: int, hours: float, plan_json: Dict, user_id: str = "anonymous") -> str:
    client = get_client()
    ins = client.table("revision_plans").insert({
        "user_id": user_id,
        "subject_id": subject_id,
        "days_available": days,
        "hours_per_day": hours,
        "plan_json": plan_json,
    }).execute()
    return ins.data[0]["id"]


# ── Mock Papers ───────────────────────────────────────────────────────────────

def save_mock_paper(subject_id: str, version: int, content_json: Dict, file_url: str = "") -> str:
    client = get_client()
    ins = client.table("mock_papers").insert({
        "subject_id": subject_id,
        "version": version,
        "content_json": content_json,
        "file_url": file_url,
    }).execute()
    return ins.data[0]["id"]


def get_mock_papers(subject_id: str) -> List[Dict]:
    client = get_client()
    res = client.table("mock_papers").select("*").eq("subject_id", subject_id).execute()
    return res.data or []
