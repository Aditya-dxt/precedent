"""
Pattern Engine Service
----------------------
Orchestrates the question clustering and topic mapping pipeline:
  Embed & cluster questions -> Map to syllabus topics via hybrid semantic + lexical match -> Compute repeat frequency & marks weights.
"""

import re
import numpy as np
from typing import List, Dict, Any, Set
from collections import defaultdict
import logging

from services.embeddings import embed_texts, cluster_questions, cosine_similarity_matrix
from models.schemas import TopicItem

logger = logging.getLogger(__name__)


def _clean_tokens(text: str) -> Set[str]:
    """Extract lowercase significant words from text."""
    words = re.findall(r'[a-zA-Z0-9]{3,}', text.lower())
    stop = {'the', 'and', 'for', 'with', 'what', 'how', 'explain', 'describe', 'discuss', 'define', 'state', 'write', 'using', 'from', 'this', 'that', 'between'}
    return {w for w in words if w not in stop}


def analyze_patterns(
    topics: List[str],
    pyq_data: List[Dict[str, Any]],
) -> List[TopicItem]:
    """
    Map extracted PYQ questions to syllabus topics.
    Returns ranked TopicItem list with repeat frequency & marks allocation weights.
    """
    if not topics:
        return []

    total_years = max(len(pyq_data), 1)

    # Flatten questions from all PYQs
    flat_questions = []
    for pyq in pyq_data:
        year = pyq.get("year", 2024)
        for q in pyq.get("questions", []):
            flat_questions.append({
                "text": q.get("text", ""),
                "marks": max(q.get("marks", 5), 1),
                "year": year,
                "section": q.get("section", ""),
            })

    if not flat_questions:
        return _build_default_topics(topics, total_years)

    all_q_texts = [q["text"] for q in flat_questions]
    topic_tokens = {t: _clean_tokens(t) for t in topics}

    # Attempt semantic embeddings
    q_embeddings = embed_texts(all_q_texts)
    t_embeddings = embed_texts(topics)

    # Topic statistics tracker
    topic_stats = defaultdict(lambda: {"years": set(), "marks": 0, "q_count": 0})

    if q_embeddings is not None and t_embeddings is not None:
        sim_matrix = cosine_similarity_matrix(q_embeddings, t_embeddings)  # shape (num_q, num_topics)

        for q_idx, q_item in enumerate(flat_questions):
            q_toks = _clean_tokens(q_item["text"])
            best_t_idx = -1
            best_score = -1.0

            for t_idx, topic in enumerate(topics):
                sem_sim = float(sim_matrix[q_idx, t_idx])
                # Token overlap ratio
                t_toks = topic_tokens[topic]
                overlap = len(q_toks & t_toks) / max(len(t_toks), 1) if t_toks else 0.0

                combined = (0.55 * sem_sim) + (0.45 * overlap)
                if combined > best_score:
                    best_score = combined
                    best_t_idx = t_idx

            # If match confidence meets threshold, assign question to topic
            if best_score >= 0.28 and best_t_idx >= 0:
                matched_topic = topics[best_t_idx]
                topic_stats[matched_topic]["years"].add(q_item["year"])
                topic_stats[matched_topic]["marks"] += q_item["marks"]
                topic_stats[matched_topic]["q_count"] += 1
    else:
        # Lexical token matching fallback
        for q_item in flat_questions:
            q_toks = _clean_tokens(q_item["text"])
            best_topic = None
            best_overlap = 0

            for topic in topics:
                t_toks = topic_tokens[topic]
                overlap = len(q_toks & t_toks)
                if overlap > best_overlap:
                    best_overlap = overlap
                    best_topic = topic

            if best_topic and best_overlap >= 1:
                topic_stats[best_topic]["years"].add(q_item["year"])
                topic_stats[best_topic]["marks"] += q_item["marks"]
                topic_stats[best_topic]["q_count"] += 1

    # Calculate scores and normalize
    max_marks = max((s["marks"] for s in topic_stats.values()), default=1) or 1
    result: List[TopicItem] = []

    for topic_name in topics:
        stats = topic_stats.get(topic_name)
        if stats and stats["q_count"] > 0:
            years_list = sorted(list(stats["years"]))
            freq = len(years_list) / total_years
            marks_wt = min(stats["marks"] / max_marks, 1.0)
        else:
            years_list = []
            freq = 0.15  # baseline syllabus presence
            marks_wt = 0.10

        composite = (freq * 0.6) + (marks_wt * 0.4)
        if composite >= 0.5:
            prep = 3.0
        elif composite >= 0.25:
            prep = 2.0
        else:
            prep = 1.5

        result.append(TopicItem(
            name=topic_name,
            frequency_score=round(freq, 2),
            marks_weight=round(marks_wt, 2),
            appeared_in_years=years_list,
            prep_time_hrs=prep,
        ))

    # Rank by composite score descending
    result.sort(key=lambda t: (t.frequency_score * 0.6 + t.marks_weight * 0.4), reverse=True)
    return result


def _build_default_topics(topics: List[str], total_years: int) -> List[TopicItem]:
    """Default topic scoring when no question texts are available."""
    res = []
    for i, t in enumerate(topics):
        weight = max(0.9 - (i * 0.05), 0.3)
        res.append(TopicItem(
            name=t,
            frequency_score=round(weight, 2),
            marks_weight=round(weight, 2),
            appeared_in_years=[],
            prep_time_hrs=2.0,
        ))
    return res
