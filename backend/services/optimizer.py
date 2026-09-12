"""
Optimizer Service
-----------------
Knapsack-style revision planner.
Maximizes expected marks coverage within student's available days and daily study hours.
Pure Python dynamic programming solver.
"""

from typing import List
from models.schemas import TopicItem, DayPlan, PlannerResponse


def run_knapsack(
    topics: List[TopicItem],
    total_hours: float,
) -> List[TopicItem]:
    """
    0/1 Knapsack solver to maximize composite score within total_hours budget.
    """
    if not topics or total_hours <= 0:
        return []

    GRANULARITY = 2  # 0.5 hour slots
    capacity = int(total_hours * GRANULARITY)
    n = len(topics)

    values = []
    weights = []
    for t in topics:
        # Guarantee minimum value so topics are never ignored as 0
        comp = max((t.frequency_score * 0.65) + (t.marks_weight * 0.35), 0.15)
        values.append(comp)
        weight = max(1, int(max(t.prep_time_hrs, 1.0) * GRANULARITY))
        weights.append(weight)

    # DP table: dp[i][w]
    dp = [[0.0] * (capacity + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        w = weights[i - 1]
        v = values[i - 1]
        for j in range(capacity + 1):
            dp[i][j] = dp[i - 1][j]
            if j >= w:
                dp[i][j] = max(dp[i][j], dp[i - 1][j - w] + v)

    # Backtrack
    selected = []
    j = capacity
    for i in range(n, 0, -1):
        if dp[i][j] != dp[i - 1][j]:
            selected.append(topics[i - 1])
            j -= weights[i - 1]

    # If capacity permits more topics that weren't picked by DP, include them
    remaining_slots = j
    selected_names = {t.name for t in selected}
    for idx, t in enumerate(topics):
        if t.name not in selected_names:
            w = weights[idx]
            if w <= remaining_slots:
                selected.append(t)
                selected_names.add(t.name)
                remaining_slots -= w

    # Sort descending by composite yield
    selected.sort(key=lambda t: (t.frequency_score * 0.65 + t.marks_weight * 0.35), reverse=True)
    return selected


def build_revision_plan(
    subject_id: str,
    topics: List[TopicItem],
    days_available: int,
    hours_per_day: float,
) -> PlannerResponse:
    """
    Build day-by-day revision plan using knapsack optimizer.
    """
    total_hours = max(days_available * hours_per_day, 1.0)

    # Select best topics that fit total hours budget
    selected = run_knapsack(topics, total_hours)
    if not selected and topics:
        selected = topics[:max(days_available * 2, 1)]

    # Distribute topics across days
    days: List[DayPlan] = []
    day_topics: List[TopicItem] = []
    day_hours = 0.0
    day_num = 1

    for topic in selected:
        if day_num > days_available:
            break
        t_hrs = max(topic.prep_time_hrs, 1.0)
        if (day_hours + t_hrs > hours_per_day) and day_topics:
            days.append(DayPlan(
                day=day_num,
                topics=day_topics,
                total_hours=round(day_hours, 1),
            ))
            day_num += 1
            day_topics = []
            day_hours = 0.0

        day_topics.append(topic)
        day_hours += t_hrs

    # Flush current day
    if day_topics and day_num <= days_available:
        days.append(DayPlan(
            day=day_num,
            topics=day_topics,
            total_hours=round(day_hours, 1),
        ))

    # Fill remaining days with topic review & practice tests
    while len(days) < days_available:
        days.append(DayPlan(
            day=len(days) + 1,
            topics=[],
            total_hours=0.0,
        ))

    # Calculate expected marks coverage percentage
    if topics:
        total_potential_weight = sum(max(t.marks_weight, 0.1) for t in topics)
        selected_weight = sum(max(t.marks_weight, 0.1) for t in selected)
        coverage = min(selected_weight / max(total_potential_weight, 0.1), 1.0)
        # Ensure minimum visible percentage reflecting selected topics ratio
        coverage = max(coverage, len(selected) / len(topics))
    else:
        coverage = 0.0

    return PlannerResponse(
        subject_id=subject_id,
        days_available=days_available,
        hours_per_day=hours_per_day,
        expected_marks_coverage=round(coverage, 2),
        days=days,
    )
