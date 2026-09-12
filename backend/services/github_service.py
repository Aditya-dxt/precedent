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


def _safe_folder(name: str) -> str:
    """
    Make a readable, GitHub-safe folder name.
    Keeps spaces and capitalisation, strips characters that break Git paths.
    """
    # Strip characters invalid in file paths
    safe = name.strip()
    for ch in ['\\', ':', '*', '?', '"', '<', '>', '|']:
        safe = safe.replace(ch, '')
    # Collapse multiple slashes / dots
    safe = safe.replace('/', '-').replace('..', '.')
    return safe.strip()


def commit_analysis(
    institution: str,
    course: str,
    subject: str,
    files: List[Tuple[str, bytes]],  # list of (relative_filename, content_bytes)
    commit_message: str = "feat: add Precedent analysis",
) -> dict:
    """
    Commit files directly under:
      {Institution Name}/{Subject Name}/...

    No 'precedent-repository' wrapper — institutions appear right at vault root.
    files: list of (relative_filename, content_bytes)
    Returns: { github_url, commit_sha, files_committed }
    """
    try:
        repo, repo_name = _get_github_repo()
        # Flat structure: Institution → Subject (no course level, no wrapper folder)
        base_path = f"{_safe_folder(institution)}/{_safe_folder(subject)}"
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

        github_url = f"https://github.com/{repo_name}/tree/main/{base_path}"
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
    Walk the vault root and return a structured tree.
    New structure: root → {Institution Name}/ → {Subject Name}/
    Skips root files (LICENSE, README.md) and any non-directory items.
    Returns:
      { institutions: [ { name, courses: [ { name, subjects: [ { name, path, github_url } ] } ] } ] }
    """
    # Root-level folders that are NOT institutions
    SKIP_DIRS = {"precedent-repository"}

    try:
        repo, repo_name = _get_github_repo()
        try:
            root_contents = repo.get_contents("")
        except GithubException:
            return {"institutions": [], "total_subjects": 0, "total_institutions": 0}

        institutions = []
        total_subjects = 0

        # Level 1: Institution folders at vault root
        for item in root_contents:
            if item.type != "dir":
                continue
            if item.name in SKIP_DIRS or item.name.startswith("."):
                continue

            inst_name = item.name  # Keep the real name (e.g. "Pranveer Singh Institute of Technology")
            subjects = []

            # Level 2: Subject folders inside institution
            try:
                subject_items = repo.get_contents(item.path)
            except GithubException:
                subject_items = []

            for s_item in subject_items:
                if s_item.type != "dir":
                    continue
                s_name = s_item.name  # Keep the real subject name
                github_url = f"https://github.com/{repo_name}/tree/main/{s_item.path}"
                subjects.append({
                    "name": s_name,
                    "path": s_item.path,
                    "github_url": github_url,
                })
                total_subjects += 1

            if subjects:
                # Wrap in courses list for schema compatibility
                institutions.append({
                    "name": inst_name,
                    "courses": [{"name": inst_name, "subjects": subjects}],
                })

        return {
            "institutions": institutions,
            "total_subjects": total_subjects,
            "total_institutions": len(institutions),
        }

    except Exception as e:
        logger.error(f"Failed to fetch repository tree: {e}")
        return {"institutions": [], "total_subjects": 0, "total_institutions": 0}

