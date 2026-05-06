"""Approach 1 scorer: weighted similarity over the 6 feature dims.

Per validation/approaches.md §"Score per tool". Progressive: dims the
user hasn't filled yet are skipped (weight redistributed across the
present dims), so the scorer works after Q1, Q2, Q3, or Q4.

Hard-exclusion via tool.excluded_paradigms: if any of the user's
paradigms appears in tool.excluded_paradigms, that tool's score is
zeroed (it gets ranked last).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class UserVector:
    industry: str | None = None
    role: str | None = None
    stack: list[str] = field(default_factory=list)
    task_shape: list[str] = field(default_factory=list)
    paradigm: list[str] = field(default_factory=list)
    setup_tolerance: str | None = None
    maturity: str | None = None  # ai-naive vs ai-mature

    def filled_dims(self) -> set[str]:
        out: set[str] = set()
        if self.industry: out.add("industry")
        if self.role: out.add("role")
        if self.stack: out.add("stack")
        if self.task_shape: out.add("task_shape")
        if self.paradigm: out.add("paradigm")
        if self.setup_tolerance: out.add("setup")
        if self.maturity: out.add("maturity")
        return out


# --- normalization helpers -------------------------------------------------

def _norm(s: str) -> str:
    return s.strip().lower().replace("-", "_").replace(" ", "_").replace("/", "_")


def _norm_list(xs: list[str]) -> set[str]:
    return {_norm(x) for x in xs if x}


# --- per-dim similarity ----------------------------------------------------

def sim_industry(user: UserVector, tool: dict) -> float:
    """1.0 if the user's industry is in the tool's industry list, 0.5
    if the tool tagged 'generic', else 0.0."""
    u_ind = _norm(user.industry or "")
    t_inds = _norm_list(tool.get("industry") or [])
    if not u_ind:
        return 0.0
    if u_ind in t_inds:
        return 1.0
    if "generic" in t_inds:
        return 0.5
    return 0.0


def sim_role(user: UserVector, tool: dict) -> float:
    """Token-level Jaccard between user role and tool.role_fit, with
    bonus for exact substring match. Generic 'knowledge_worker' fits
    everyone at 0.4."""
    if not user.role:
        return 0.0
    u_tokens = set(_norm(user.role).split("_"))
    t_roles = tool.get("role_fit") or []
    if not t_roles:
        return 0.0
    best = 0.0
    for r in t_roles:
        r_norm = _norm(r)
        if r_norm in {"knowledge_worker", "anyone", "generic"}:
            best = max(best, 0.4)
            continue
        r_tokens = set(r_norm.split("_"))
        if not r_tokens or not u_tokens:
            continue
        inter = u_tokens & r_tokens
        union = u_tokens | r_tokens
        jacc = len(inter) / len(union) if union else 0.0
        # exact-substring bonus
        if r_norm in _norm(user.role) or _norm(user.role) in r_norm:
            jacc = max(jacc, 0.7)
        best = max(best, jacc)
    return best


def sim_stack(user: UserVector, tool: dict) -> float:
    """Jaccard over the user's stack and the tool's stack_integrations.
    Empty stack on either side -> 0 (don't reward absence)."""
    u = _norm_list(user.stack)
    t = _norm_list(tool.get("stack_integrations") or [])
    if not u or not t:
        return 0.0
    inter = u & t
    union = u | t
    return len(inter) / len(union)


def sim_task_shape(user: UserVector, tool: dict) -> float:
    u = _norm_list(user.task_shape)
    t = _norm_list(tool.get("task_shape") or [])
    if not u or not t:
        return 0.0
    inter = u & t
    return len(inter) / len(u)  # recall over user's shapes


def sim_paradigm(user: UserVector, tool: dict) -> float:
    u = _norm_list(user.paradigm)
    t = _norm_list(tool.get("paradigm") or [])
    if not u or not t:
        return 0.0
    inter = u & t
    return len(inter) / len(u)


def fit_setup(user: UserVector, tool: dict) -> float:
    """1.0 if user can tolerate at least the tool's setup; else 0.3."""
    if not user.setup_tolerance:
        return 0.0
    order = {"under_2min": 1, "around_10min": 2, "willing_to_customize": 3}
    u = order.get(_norm(user.setup_tolerance), 0)
    t = order.get(_norm(tool.get("setup_tolerance") or ""), 0)
    if u == 0 or t == 0:
        return 0.0
    return 1.0 if u >= t else 0.3


def fit_maturity(user: UserVector, tool: dict) -> float:
    """1.0 if user's maturity meets the tool's required maturity."""
    if not user.maturity:
        return 0.0
    order = {"low": 1, "medium": 2, "high": 3}
    u = order.get(_norm(user.maturity), 0)
    t = order.get(_norm(tool.get("maturity_required") or ""), 0)
    if u == 0 or t == 0:
        return 0.0
    return 1.0 if u >= t else 0.4


# --- aggregation -----------------------------------------------------------

DIM_SCORERS = {
    "industry": sim_industry,
    "role": sim_role,
    "stack": sim_stack,
    "task_shape": sim_task_shape,
    "paradigm": sim_paradigm,
    "setup": fit_setup,
    "maturity": fit_maturity,
}


def score_tool(
    user: UserVector,
    tool: dict,
    weights: dict[str, float] | None = None,
) -> tuple[float, dict[str, float]]:
    """Return (score, per_dim_breakdown). Only dims the user has filled
    contribute; their weights are renormalized to sum to 1.0 across the
    present dims, so an early-stage user (Q1 only) still gets a 0..1
    score."""
    weights = weights or {k: 1.0 for k in DIM_SCORERS}
    present = user.filled_dims()
    active_w = {k: weights[k] for k in present if k in weights}
    w_sum = sum(active_w.values()) or 1.0
    breakdown: dict[str, float] = {}
    total = 0.0
    for dim, w in active_w.items():
        s = DIM_SCORERS[dim](user, tool)
        breakdown[dim] = s
        total += (w / w_sum) * s

    # Hard exclusion: if user's paradigm appears in tool.excluded_paradigms,
    # zero the tool. The breakdown still records the would-be score for
    # debugging.
    excluded = _norm_list(tool.get("excluded_paradigms") or [])
    if excluded & _norm_list(user.paradigm):
        breakdown["__excluded__"] = 1.0
        return 0.0, breakdown

    return total, breakdown


def rank_tools(
    user: UserVector,
    tools: list[dict],
    top_k: int | None = None,
    weights: dict[str, float] | None = None,
) -> list[dict[str, Any]]:
    """Score every tool, return sorted list of dicts:
        {"slug", "name", "score", "breakdown", "tool_features"}
    """
    out: list[dict[str, Any]] = []
    for t in tools:
        score, breakdown = score_tool(user, t, weights)
        out.append({
            "slug": t.get("slug"),
            "name": t.get("name"),
            "score": score,
            "breakdown": breakdown,
            "tool_features": t,
        })
    out.sort(key=lambda x: x["score"], reverse=True)
    if top_k is not None:
        out = out[:top_k]
    return out
