from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
from .scoring import calculate_task_score
from datetime import date

def make_explanation(task, breakdown):
    parts = []
    urgency = breakdown.get("urgency", 0)
    if urgency >= 150:
        parts.append("Overdue — do it immediately")
    elif urgency >= 80:
        parts.append("Due today")
    elif urgency >= 50:
        parts.append("Due very soon")
    elif urgency > 0:
        parts.append("Upcoming deadline")
    else:
        parts.append("No close deadline")
    parts.append(f"Importance contributes {breakdown.get('importance',0)} pts")
    eff = breakdown.get("effort",0)
    if eff >= 10:
        parts.append("Quick-win (low effort)")
    elif eff > 0:
        parts.append("Moderate effort")
    else:
        parts.append("High effort")
    dp = breakdown.get("dependency_penalty",0)
    if dp < 0:
        num_deps = int(abs(dp) // 5) if dp != 0 else 0
        parts.append(f"Penalty for dependencies (approx {num_deps})")
    return ". ".join(parts) + "."

def detect_cycles(tasks):
    id_map = {}
    nodes = []
    for i, t in enumerate(tasks):
        node_id = None
        if isinstance(t, dict) and t.get("id"):
            node_id = str(t.get("id"))
        elif isinstance(t, dict) and t.get("title"):
            node_id = str(t.get("title"))
        else:
            node_id = f"#{i}"
        id_map[node_id] = i
        nodes.append({"id": node_id, "index": i, "deps": t.get("dependencies") or []})
    adj = {i: [] for i in range(len(tasks))}
    for node in nodes:
        i = node["index"]
        for d in node["deps"]:
            if d is None:
                continue
            ds = str(d)
            if ds in id_map:
                adj[i].append(id_map[ds])
    visited = [0] * len(tasks)
    in_cycle_set = set()
    def dfs(u, stack):
        if visited[u] == 1:
            try:
                idx = stack.index(u)
                for v in stack[idx:]:
                    in_cycle_set.add(v)
            except ValueError:
                in_cycle_set.add(u)
            return
        if visited[u] == 2:
            return
        visited[u] = 1
        stack.append(u)
        for v in adj.get(u, []):
            dfs(v, stack)
        stack.pop()
        visited[u] = 2
    for i in range(len(tasks)):
        if visited[i] == 0:
            dfs(i, [])
    return in_cycle_set

@csrf_exempt
@require_http_methods(["POST"])
def analyze_tasks(request):
    """
    POST body can be:
    - a JSON array (old), or
    - an object: { "tasks": [...], "weights": { ... } }
    Returns enriched list of tasks with score, breakdown, priority, explanation, circular.
    """
    try:
        body = request.body.decode("utf-8")
        payload = json.loads(body)
    except Exception as e:
        return JsonResponse({"error": "Invalid JSON: " + str(e)}, status=400)

    
    if isinstance(payload, dict) and "tasks" in payload:
        tasks = payload.get("tasks", [])
        weights = payload.get("weights") or {}
    elif isinstance(payload, list):
        tasks = payload
        weights = {}
    else:
        return JsonResponse({"error": "Expected JSON array or {tasks: [...], weights: {...}}"}, status=400)

    if not isinstance(tasks, list):
        return JsonResponse({"error": "Expected tasks to be a list."}, status=400)

    
    cycle_indexes = detect_cycles(tasks)

    enriched = []
    for idx, t in enumerate(tasks):
        task_copy = dict(t) if isinstance(t, dict) else {}
        if idx in cycle_indexes:
            task_copy["in_cycle"] = True
        else:
            task_copy["in_cycle"] = False
        
        result = calculate_task_score(task_copy, weights=weights)
        score = result["score"]
        breakdown = result["components"]
        if score >= 120:
            priority = "Critical"
        elif score >= 80:
            priority = "High"
        elif score >= 40:
            priority = "Medium"
        else:
            priority = "Low"
        explanation = make_explanation(task_copy, breakdown)
        if task_copy.get("in_cycle"):
            explanation = "CIRCULAR DEPENDENCY DETECTED — resolve dependencies first. " + explanation
        out = dict(t) if isinstance(t, dict) else {}
        out["score"] = score
        out["breakdown"] = breakdown
        out["priority"] = priority
        out["explanation"] = explanation
        out["circular"] = bool(task_copy.get("in_cycle", False))
        enriched.append(out)

    sorted_tasks = sorted(enriched, key=lambda x: x["score"], reverse=True)
    return JsonResponse(sorted_tasks, safe=False)

@require_http_methods(["GET"])
def suggest_tasks(request):
    use_sample = request.GET.get("use_sample", "0") == "1"
    if use_sample:
        sample = [
            {"title": "Submit tax form", "due_date": "2025-12-01", "importance": 9, "estimated_hours": 1, "dependencies": []},
            {"title": "Finish assignment", "due_date": "2025-11-30", "importance": 8, "estimated_hours": 4, "dependencies": []},
            {"title": "Deep refactor", "due_date": None, "importance": 6, "estimated_hours": 18, "dependencies": []},
        ]
        cycle_indexes = detect_cycles(sample)
        enriched = []
        for idx, t in enumerate(sample):
            tc = dict(t)
            tc["in_cycle"] = idx in cycle_indexes
            res = calculate_task_score(tc)
            score = res["score"]
            breakdown = res["components"]
            priority = "Critical" if score >= 120 else ("High" if score >= 80 else ("Medium" if score >= 40 else "Low"))
            explanation = make_explanation(tc, breakdown)
            if tc["in_cycle"]:
                explanation = "CIRCULAR DEPENDENCY DETECTED — resolve dependencies first. " + explanation
            out = dict(t)
            out["score"] = score
            out["breakdown"] = breakdown
            out["priority"] = priority
            out["explanation"] = explanation
            out["circular"] = bool(tc["in_cycle"])
            enriched.append(out)
        enriched_sorted = sorted(enriched, key=lambda x: x["score"], reverse=True)
        top3 = enriched_sorted[:3]
        return JsonResponse({"top": top3, "explanation": "Top tasks chosen by combining urgency, importance and quick-win bias."})
    return JsonResponse({"message": "Call POST /api/tasks/analyze/ with tasks or use ?use_sample=1"}, status=200)
