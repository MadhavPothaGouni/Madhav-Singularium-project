# tasks/scoring.py
from datetime import date, datetime
import math
import random

def _parse_date(val):
    if not val:
        return None
    if isinstance(val, date):
        return val
    try:
        # Accept ISO format YYYY-MM-DD
        return datetime.strptime(val, "%Y-%m-%d").date()
    except Exception:
        try:
            # Some UIs might send dd-mm-yyyy accidentally; try fallback (not recommended)
            return datetime.strptime(val, "%d-%m-%Y").date()
        except Exception:
            return None

def _is_sunday(dt):
    return dt.weekday() == 6  # Monday=0 ... Sunday=6

def calculate_task_score(task_data, weights=None):
    """
    Calculate a priority score for a single task.

    task_data: dict with keys: due_date (str or date or None), importance (1-10), estimated_hours (int),
               dependencies (list), in_cycle (bool, optional)
    weights: dict (optional) with keys:
       importance_mul, urgency_overdue, urgency_today, urgency_soon, urgency_week,
       effort_quick_bonus, effort_small_bonus, effort_medium_bonus, effort_large_penalty,
       dependency_penalty_per, dependency_cycle_pen, tie_base
    Returns:
       { "score": int, "components": { urgency, importance, effort, dependency_penalty, tie_breaker } }
    """
    # Default weights (mirror frontend default)
    defaults = {
        "importance_mul": 8,
        "urgency_overdue": 150,
        "urgency_today": 80,
        "urgency_soon": 50,
        "urgency_week": 20,
        "effort_quick_bonus": 12,
        "effort_small_bonus": 6,
        "effort_medium_bonus": 2,
        "effort_large_penalty": -5,
        "dependency_penalty_per": 5,
        "dependency_cycle_pen": 40,
        "tie_base": 5,
        # weekend multiplier (reduce urgency if due on Sunday)
        "weekend_urgency_multiplier": 0.5
    }
    if weights and isinstance(weights, dict):
        cfg = defaults.copy()
        cfg.update(weights)
    else:
        cfg = defaults

    # safe reads and defaults
    importance = int(task_data.get("importance") or 0)
    try:
        est_hours = int(task_data.get("estimated_hours") or 0)
    except Exception:
        est_hours = 0
    deps = task_data.get("dependencies") or []
    # allow both titles and numeric ids in dependencies
    dep_count = len([d for d in deps if d is not None])

    # 1) Urgency score
    today = date.today()
    due_date_raw = task_data.get("due_date")
    due_date = _parse_date(due_date_raw)
    days_until = None
    urgency_score = 0
    if due_date:
        delta = (due_date - today).days
        days_until = delta
        # overdue
        if delta < 0:
            urgency_score += cfg["urgency_overdue"]
        elif delta == 0:
            urgency_score += cfg["urgency_today"]
        elif delta <= 3:
            urgency_score += cfg["urgency_soon"]
        elif delta <= 7:
            urgency_score += cfg["urgency_week"]
        # weekend-aware: if due date is Sunday, reduce urgency contribution
        try:
            if _is_sunday(due_date):
                urgency_score = int(urgency_score * float(cfg.get("weekend_urgency_multiplier", 0.5)))
        except Exception:
            pass
    else:
        days_until = None
        urgency_score += 0

    # 2) Importance contribution
    # scale importance (1-10) by multiplier
    importance_score = int((importance or 0) * int(cfg.get("importance_mul", 8)))

    # 3) Effort / quick-win logic
    # Treat very small tasks as quick wins
    effort_score = 0
    if est_hours <= 0:
        # Invalid hours => neutral
        effort_score += 0
    elif est_hours <= 1:
        effort_score += int(cfg.get("effort_quick_bonus", 12))
    elif est_hours <= 3:
        effort_score += int(cfg.get("effort_small_bonus", 6))
    elif est_hours <= 8:
        effort_score += int(cfg.get("effort_medium_bonus", 2))
    else:
        effort_score += int(cfg.get("effort_large_penalty", -5))

    # 4) Dependency penalty (each dependency lowers score until resolved)
    dep_penalty = - int(cfg.get("dependency_penalty_per", 5)) * dep_count

    # 5) Circular dependency penalty
    cycle_penalty = 0
    if task_data.get("in_cycle") or task_data.get("circular"):
        cycle_penalty = - int(cfg.get("dependency_cycle_pen", 40))

    # 6) Tie-breaker (deterministic-ish: use hash of title or importance/time)
    tie_value = cfg.get("tie_base", 5)
    # produce small deterministic tie-breaker from title if available
    title = str(task_data.get("title") or "")
    if title:
        # deterministic integer from title
        tb = sum(ord(ch) for ch in title) % 7
    else:
        tb = 0
    tie_breaker = int(tie_value) + int(tb)

    # final score assembly
    raw_score = urgency_score + importance_score + effort_score + dep_penalty + cycle_penalty + tie_breaker

    # clamp/round to integer
    final_score = int(round(raw_score))

    components = {
        "urgency": urgency_score,
        "importance": importance_score,
        "effort": effort_score,
        "dependency_penalty": dep_penalty + cycle_penalty,
        "tie_breaker": tie_breaker,
        "days_until_due": days_until
    }

    return {"score": final_score, "components": components}
