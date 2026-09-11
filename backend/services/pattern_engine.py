"""
Pattern Engine Service
----------------------
Orchestrates the full analysis pipeline:
  parse → embed → cluster → map to topics → compute scores → rank topics
"""

import numpy as np
from typing import List, Dict, Any
from collections import defaultdict
import logging

from services.embeddings import embed_texts, cluster_questions, map_clusters_to_topics, cosine_similarity_matrix
from models.schemas import TopicItem

logger = logging.getLogger(__name__)

# Estimated prep time in hours per topic based on marks weight
PREP_TIME_LOOKUP = {
    "high": 3.0,
    "medium": 2.0,
    "low": 1.0,
}


def analyze_patterns(
    topics: List[str],
    pyq_data: List[Dict[str, Any]],  # list of {year, questions: [{text, marks, section}]}
) -> List[TopicItem]:
    """
    Main analysis function.
    Returns a ranked list of TopicItems sorted by composite score (descending).
    """
    if not topics:
        logger.warning("No topics found in syllabus")
        return []

    if not pyq_data:
        logger.warning("No PYQ data provided")
        return _build_default_topics(topics)

    total_years = len(pyq_data)
    all_questions = []
    question_years = []  # which year each question came from

    for pyq in pyq_data:
        qs = pyq.get("questions", [])
        for q in qs:
            all_questions.append(q.get("text", ""))
            question_years.append(pyq.get("year", 0))

    if not all_questions:
        return _build_default_topics(topics)

    logger.info(f"Embedding {len(all_questions)} questions across {total_years} years...")

    # 1. Embed all questions
    q_embeddings = embed_texts(all_questions)
    # 2. Embed all syllabus topics
    topic_embeddings = embed_texts(topics)

    if q_embeddings is None or topic_embeddings is None:
        logger.warning("Embeddings failed; using keyword-based matching fallback")
        return _keyword_fallback(topics, pyq_data, total_years)

    # 3. Cluster questions by semantic similarity
    clusters = cluster_questions(all_questions, q_embeddings, threshold=0.70)
    logger.info(f"Found {len(clusters)} question clusters from {len(all_questions)} questions")

    # 4. Compute representative embedding per cluster (centroid)
    cluster_centroids = []
    cluster_year_sets = []  # set of years represented in each cluster
    cluster_total_marks = []

    for cluster_indices in clusters:
        centroid = np.mean(q_embeddings[cluster_indices], axis=0)
        cluster_centroids.append(centroid)

        years_in_cluster = set(question_years[i] for i in cluster_indices)
        cluster_year_sets.append(years_in_cluster)

        # Sum marks for questions in this cluster
        marks_sum = 0
        for idx in cluster_indices:
            for pyq in pyq_data:
                for q in pyq.get("questions", []):
                    if q.get("text", "") == all_questions[idx]:
                        marks_sum += q.get("marks", 0)
        cluster_total_marks.append(marks_sum)

    cluster_centroids_arr = np.array(cluster_centroids)

    # 5. Map each cluster to a syllabus topic
    topic_assignments = map_clusters_to_topics(cluster_centroids_arr, topics, topic_embeddings)

    # 6. Aggregate per-topic stats
    topic_stats = defaultdict(lambda: {"years": set(), "marks": 0, "cluster_count": 0})
    for ci, topic_idx in enumerate(topic_assignments):
        if topic_idx < len(topics):
            t_name = topics[topic_idx]
            topic_stats[t_name]["years"].update(cluster_year_sets[ci])
            topic_stats[t_name]["marks"] += cluster_total_marks[ci]
            topic_stats[t_name]["cluster_count"] += 1

    # 7. Compute scores
    max_marks = max((s["marks"] for s in topic_stats.values()), default=1) or 1
    result: List[TopicItem] = []

    for topic_name in topics:
        stats = topic_stats.get(topic_name, {"years": set(), "marks": 0, "cluster_count": 0})
        years_appeared = stats["years"]
        frequency_score = len(years_appeared) / total_years if total_years > 0 else 0.0
        marks_weight = stats["marks"] / max_marks if max_marks > 0 else 0.0

        # Prep time heuristic
        composite = (frequency_score * 0.6) + (marks_weight * 0.4)
        if composite >= 0.6:
            prep = 3.0
        elif composite >= 0.3:
            prep = 2.0
        else:
            prep = 1.0

        result.append(TopicItem(
            name=topic_name,
            frequency_score=round(frequency_score, 3),
            marks_weight=round(marks_weight, 3),
            appeared_in_years=sorted(list(years_appeared)),
            prep_time_hrs=prep,
        ))

    # Sort by composite score descending
    result.sort(key=lambda t: (t.frequency_score * 0.6 + t.marks_weight * 0.4), reverse=True)
    return result


def _build_default_topics(topics: List[str]) -> List[TopicItem]:
    """Build topic items with neutral scores when no PYQ data is available."""
    return [
        TopicItem(
            name=t,
            frequency_score=0.0,
            marks_weight=0.0,
            appeared_in_years=[],
            prep_time_hrs=2.0,
        ) for t in topics
    ]


def _keyword_fallback(topics: List[str], pyq_data: List[Dict], total_years: int) -> List[TopicItem]:
    """
    Simple keyword-overlap fallback when embeddings are unavailable.
    Counts how many PYQ questions mention words from each topic.
    """
    result = []
    for topic in topics:
        topic_words = set(topic.lower().split())
        years_appeared = set()
        marks_total = 0

        for pyq in pyq_data:
            for q in pyq.get("questions", []):
                q_words = set(q.get("text", "").lower().split())
                overlap = len(topic_words & q_words)
                if overlap >= 1:
                    years_appeared.add(pyq.get("year", 0))
                    marks_total += q.get("marks", 0)

        freq = len(years_appeared) / total_years if total_years > 0 else 0.0
        result.append(TopicItem(
            name=topic,
            frequency_score=round(freq, 3),
            marks_weight=round(min(marks_total / 100.0, 1.0), 3),
            appeared_in_years=sorted(list(years_appeared)),
            prep_time_hrs=2.0 if freq < 0.5 else 3.0,
        ))

    result.sort(key=lambda t: t.frequency_score, reverse=True)
    return result
