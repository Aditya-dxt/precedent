"""
GitHub Service
--------------
Auto-commits analysis artifacts to a structured GitHub repository.
Uses PyGithub with a service-account or personal access token.
"""

import os
import base64
import logging
from typing import List, Tuple, Optional
from dotenv import load_dotenv
from github import Github, GithubException

# Load env variables
load_dotenv()

logger = logging.getLogger(__name__)


def _get_github_repo():
    """Return the GitHub repo object and repo name dynamically."""
    token = os.getenv("GITHUB_TOKEN", "").strip()
    repo_name = os.getenv("GITHUB_REPO", "").strip()

    if not token or not repo_name:
        load_dotenv()
        token = os.getenv("GITHUB_TOKEN", "").strip()
        repo_name = os.getenv("GITHUB_REPO", "").strip()

    if not token or not repo_name:
        raise ValueError("GITHUB_TOKEN and GITHUB_REPO env vars must be set for GitHub publishing.")

    g = Github(token)
    return g.get_repo(repo_name), repo_name


def _safe_path(name: str) -> str:
    """Sanitize string for use as a folder name."""
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
        repo, repo_name = _get_github_repo()
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

        github_url = f"https://github/{repo_name}/tree/main/{base_path}".replace("https://github/", "https://github.com/")
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
        repo, repo_name = _get_github_repo()
        try:
            contents = repo.get_contents("precedent-repository")
        except GithubException:
            return {"institutions": [], "total_subjects": 0, "total_institutions": 0}

        institutions = []
        total_subjects = 0

        # Level 1: Institutions
        for item in contents:
            if item.type != "dir":
                continue
            inst_name = item.name.replace("-", " ").title()
            courses = []

            # Level 2: Courses
            try:
                course_items = repo.get_contents(item.path)
            except GithubException:
                course_items = []

            for c_item in course_items:
                if c_item.type != "dir":
                    continue
                c_name = c_item.name.replace("-", " ").title()
                subjects = []

                # Level 3: Subjects
                try:
                    sub_items = repo.get_contents(c_item.path)
                except GithubException:
                    sub_items = []

                for s_item in sub_items:
                    if s_item.type != "dir":
                        continue
                    s_name = s_item.name.replace("-", " ").title()
                    github_url = f"https://github.com/{repo_name}/tree/main/{s_item.path}"
                    subjects.append({
                        "name": s_name,
                        "path": s_item.path,
                        "github_url": github_url,
                    })
                    total_subjects += 1

                if subjects:
                    courses.append({"name": c_name, "subjects": subjects})

            if courses:
                institutions.append({"name": inst_name, "courses": courses})

        return {
            "institutions": institutions,
            "total_subjects": total_subjects,
            "total_institutions": len(institutions),
        }

    except Exception as e:
        logger.error(f"Failed to fetch repository tree: {e}")
        return {"institutions": [], "total_subjects": 0, "total_institutions": 0}
