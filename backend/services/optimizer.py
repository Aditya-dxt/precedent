"""
Optimizer Service
-----------------
Knapsack-style revision planner.
Maximizes expected marks coverage within a given time budget.
Pure Python — no external solver libraries needed.
"""

from typing import List, Dict, Any
from models.schemas import TopicItem, DayPlan, PlannerResponse
import math


def run_knapsack(
    topics: List[TopicItem],
    total_hours: float,
) -> List[TopicItem]:
    """
    0/1 Knapsack solver to maximize composite score within total_hours budget.
    Each topic has a prep_time_hrs (weight) and a composite value.
    Uses DP with 0.5h granularity (multiply hours by 2 to get integer slots).
    """
    if not topics or total_hours <= 0:
        return []

    GRANULARITY = 2  # slots per hour (0.5h resolution)
    capacity = int(total_hours * GRANULARITY)

    n = len(topics)
    # Value = weighted composite of frequency and marks
    values = []
    weights = []
    for t in topics:
        composite = (t.frequency_score * 0.6) + (t.marks_weight * 0.4)
        values.append(composite)
        weight = max(1, int(t.prep_time_hrs * GRANULARITY))  # min 1 slot
        weights.append(weight)

    # DP table: dp[i][w] = max value using first i items with capacity w
    dp = [[0.0] * (capacity + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        w = weights[i - 1]
        v = values[i - 1]
        for j in range(capacity + 1):
            dp[i][j] = dp[i - 1][j]
            if j >= w:
                dp[i][j] = max(dp[i][j], dp[i - 1][j - w] + v)

    # Backtrack to find selected topics
    selected = []
    j = capacity
    for i in range(n, 0, -1):
        if dp[i][j] != dp[i - 1][j]:
            selected.append(topics[i - 1])
            j -= weights[i - 1]

    # Return in descending composite score order
    selected.sort(key=lambda t: (t.frequency_score * 0.6 + t.marks_weight * 0.4), reverse=True)
    return selected


def build_revision_plan(
    subject_id: str,
    topics: List[TopicItem],
    days_available: int,
    hours_per_day: float,
) -> PlannerResponse:
    """
    Build a day-by-day revision plan using the knapsack solver.
    """
    total_hours = days_available * hours_per_day

    # Select best topics that fit the total budget
    selected = run_knapsack(topics, total_hours)

    # Distribute topics across days (greedy bin packing)
    days: List[DayPlan] = []
    day_topics: List[TopicItem] = []
    day_hours = 0.0
    day_num = 1

    for topic in selected:
        if day_num > days_available:
            break
        # If adding this topic exceeds the day's hours, start a new day
        if day_hours + topic.prep_time_hrs > hours_per_day and day_topics:
            days.append(DayPlan(
                day=day_num,
                topics=day_topics,
                total_hours=round(day_hours, 1),
            ))
            day_num += 1
            day_topics = []
            day_hours = 0.0

        day_topics.append(topic)
        day_hours += topic.prep_time_hrs

    # Flush remaining topics into current day
    if day_topics and day_num <= days_available:
        days.append(DayPlan(
            day=day_num,
            topics=day_topics,
            total_hours=round(day_hours, 1),
        ))

    # Fill any remaining days with a "Review" placeholder if we ran out of topics
    while len(days) < days_available:
        days.append(DayPlan(
            day=len(days) + 1,
            topics=[],
            total_hours=0.0,
        ))

    # Compute expected marks coverage
    # = sum of marks_weight of selected topics / max possible marks_weight
    selected_marks = sum(t.marks_weight for t in selected)
    total_marks = sum(t.marks_weight for t in topics) if topics else 1.0
    coverage = min(selected_marks / total_marks, 1.0) if total_marks > 0 else 0.0

    return PlannerResponse(
        subject_id=subject_id,
        days_available=days_available,
        hours_per_day=hours_per_day,
        expected_marks_coverage=round(coverage, 3),
        days=days,
    )
