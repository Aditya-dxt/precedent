"""
GitHub Service
--------------
Auto-commits analysis artifacts to a structured GitHub repository.
Uses PyGithub with a service-account PAT.
"""

import os
import base64
import logging
from typing import List, Tuple, Optional
from github import Github, GithubException

logger = logging.getLogger(__name__)

REPO_NAME = os.getenv("GITHUB_REPO", "")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")


def _get_github_repo():
    """Return the GitHub repo object, or raise if not configured."""
    if not GITHUB_TOKEN or not REPO_NAME:
        raise ValueError("GITHUB_TOKEN and GITHUB_REPO env vars must be set for GitHub publishing.")
    g = Github(GITHUB_TOKEN)
    return g.get_repo(REPO_NAME)


def _safe_path(name: str) -> str:
    """Convert a display name to a safe directory path component."""
    return name.lower().replace(" ", "-").replace("/", "-").replace("\\", "-")


def commit_analysis(
    institution: str,
    course: str,
    subject: str,
    files: List[Tuple[str, bytes]],  # list of (filename, content_bytes)
    commit_message: str = "feat: add Precedent analysis",
) -> dict:
    """
    Commit multiple files to the repository under:
      precedent-repository/<institution>/<course>/<subject>/
    
    files: list of (relative_filename, content_bytes)
    Returns: { github_url, commit_sha, files_committed }
    """
    try:
        repo = _get_github_repo()
        base_path = f"precedent-repository/{_safe_path(institution)}/{_safe_path(course)}/{_safe_path(subject)}"
        committed = []

        for filename, content in files:
            full_path = f"{base_path}/{filename}"
            try:
                # Try to get existing file (for update)
                existing = repo.get_contents(full_path)
                repo.update_file(
                    path=full_path,
                    message=commit_message,
                    content=content,
                    sha=existing.sha,
                )
            except GithubException as e:
                if e.status == 404:
                    # File does not exist yet — create it
                    repo.create_file(
                        path=full_path,
                        message=commit_message,
                        content=content,
                    )
                else:
                    raise
            committed.append(full_path)
            logger.info(f"Committed: {full_path}")

        # Get latest commit SHA
        commits = repo.get_commits(path=base_path)
        latest_sha = commits[0].sha if commits.totalCount > 0 else "unknown"

        github_url = f"https://github.com/{REPO_NAME}/tree/main/{base_path}"
        return {
            "success": True,
            "github_url": github_url,
            "commit_sha": latest_sha[:7],
            "files_committed": committed,
        }

    except Exception as e:
        logger.error(f"GitHub commit failed: {e}")
        return {
            "success": False,
            "github_url": "",
            "commit_sha": "",
            "files_committed": [],
            "error": str(e),
        }


def get_repository_tree() -> dict:
    """
    Walk the precedent-repository/ directory and return a structured tree:
    { institutions: [ { name, courses: [ { name, subjects: [ { name, path, github_url } ] } ] } ] }
    """
    try:
        repo = _get_github_repo()
        try:
            contents = repo.get_contents("precedent-repository")
        except GithubException:
            return {"institutions": [], "total_subjects": 0, "total_institutions": 0}

        institutions = []
        total_subjects = 0

        for inst_content in contents:
            if inst_content.type != "dir":
                continue
            inst_name = inst_content.name.replace("-", " ").title()
            inst_courses = []

            try:
                course_contents = repo.get_contents(inst_content.path)
            except GithubException:
                continue

            for course_content in course_contents:
                if course_content.type != "dir":
                    continue
                course_name = course_content.name.replace("-", " ").title()
                subjects = []

                try:
                    subject_contents = repo.get_contents(course_content.path)
                except GithubException:
                    continue

                for subj_content in subject_contents:
                    if subj_content.type != "dir":
                        continue
                    subj_name = subj_content.name.replace("-", " ").title()
                    subjects.append({
                        "name": subj_name,
                        "path": subj_content.path,
                        "github_url": f"https://github.com/{REPO_NAME}/tree/main/{subj_content.path}",
                    })
                    total_subjects += 1

                if subjects:
                    inst_courses.append({"name": course_name, "subjects": subjects})

            if inst_courses:
                institutions.append({"name": inst_name, "courses": inst_courses})

        return {
            "institutions": institutions,
            "total_subjects": total_subjects,
            "total_institutions": len(institutions),
        }

    except Exception as e:
        logger.error(f"Failed to fetch repository tree: {e}")
        return {"institutions": [], "total_subjects": 0, "total_institutions": 0, "error": str(e)}
