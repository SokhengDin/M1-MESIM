"""
generators.py
─────────────
All mathematical / statistical logic for the MESIM quadratic-equation trainer.

Public API
──────────
  generate_exercise()   → (a, b, c, delta, type_id)
  format_equation(a, b, c) → str
  load_stats()          → dict
  save_stats(score, total)
"""

import math
import os
import json
import numpy as np

# ─── STATS PERSISTENCE ───────────────────────────────────────────────────────
STATS_PATH = os.path.expanduser("~/.mesim_stats.json")

def load_stats() -> dict:
    """Return persisted session stats, or sensible defaults."""
    try:
        with open(STATS_PATH) as f:
            return json.load(f)
    except Exception:
        return {"sessions": 0, "total_score": 0.0,
                "total_exercises": 0, "best_pct": 0.0}

def save_stats(score: float, total: int) -> None:
    """Append one session's results to the persistent stats file."""
    s = load_stats()
    s["sessions"]        += 1
    s["total_score"]     += score
    s["total_exercises"] += total
    pct = (score / total * 100) if total else 0
    s["best_pct"] = max(s["best_pct"], pct)
    with open(STATS_PATH, "w") as f:
        json.dump(s, f)

# ─── HELPER: discrete inverse-CDF sampler ────────────────────────────────────
def generate_discrete_sample(values, probs, N=1):
    """Sample N values from a discrete distribution via inverse-CDF."""
    cdf, cumul = [], 0.0
    for p in probs:
        cumul += p
        cdf.append(cumul)
    samples = []
    for _ in range(N):
        U, k = np.random.rand(), 0
        while k < len(values) - 1 and U > cdf[k]:
            k += 1
        samples.append(values[k])
    return samples[0] if N == 1 else np.array(samples)

# ─── EQUATION FORMATTER ──────────────────────────────────────────────────────
def format_equation(a, b, c) -> str:
    """Return a human-readable string for ax² + bx + c = 0."""
    a, b, c = round(a, 4), round(b, 4), round(c, 4)

    def fmt(coef, var, first=False):
        if coef == 0: return ""
        if first:
            if coef == 1  and var: return var
            if coef == -1 and var: return f"-{var}"
            return f"{coef}{var}"
        if coef == 1  and var: return f" + {var}"
        if coef == -1 and var: return f" - {var}"
        if coef > 0:           return f" + {coef}{var}"
        return f" - {abs(coef)}{var}"

    return fmt(a, "x\u00b2", first=True) + fmt(b, "x") + fmt(c, "") + " = 0"

# ─── EXERCISE GENERATORS ─────────────────────────────────────────────────────
def _case1():
    """Type 1 — discriminant < 0 (guaranteed no real root)."""
    E       = [i for i in range(-9, 10) if i != 0]
    E_small = [1, 2, 3]
    pe = [1 / len(E)]       * len(E)
    ps = [1 / len(E_small)] * len(E_small)
    a = generate_discrete_sample(E, pe)
    b = generate_discrete_sample(E, pe)
    e = generate_discrete_sample(E_small, ps)
    c = (b**2 + e) / (4 * a)
    return a, b, c, b**2 - 4 * a * c

def _case2():
    """Type 2 — discriminant = 0 (one repeated root)."""
    E  = [i for i in range(-9, 10) if i != 0]
    Ep = list(range(1, 10))
    pe = [1 / len(E)]  * len(E)
    pl = [1/2, 1/36, 1/36, 1/6, 1/36, 1/36, 1/36, 1/36, 1/6]
    e   = generate_discrete_sample(E, pe)
    ell = generate_discrete_sample(Ep, pl)
    x0  = e / math.sqrt(ell)
    a, b, c = 1, -2 * x0, x0**2
    return a, b, c, b**2 - 4 * a * c

def _case3():
    """Type 3 — discriminant > 0 (two distinct real roots)."""
    E       = [i for i in range(-9, 10) if i != 0]
    Ep      = list(range(1, 10))
    E_small = [i for i in range(-3, 4) if i != 0]
    pe  = [1 / len(E)]       * len(E)
    pEp = [1 / len(Ep)]      * len(Ep)
    pEs = [1 / len(E_small)] * len(E_small)
    pZ  = [1/2 if i == 1 else 1 / (2 * 17) for i in E]

    if generate_discrete_sample([1, 2], [1/2, 1/2]) == 1:
        h  = generate_discrete_sample(E, pe)
        k  = generate_discrete_sample(E, pe)
        ll = generate_discrete_sample(E, pZ)
        x1, x2 = h / ll, k / ll
    else:
        h = generate_discrete_sample(E, pe)
        l = generate_discrete_sample(E_small, pEs)
        e = generate_discrete_sample(Ep, pEp)
        p = generate_discrete_sample(Ep, pEp)
        x1 = (-h - e * math.sqrt(p)) / l
        x2 = (-h + e * math.sqrt(p)) / l

    a, b, c = 1, -(x1 + x2), x1 * x2
    return a, b, c, b**2 - 4 * a * c

def generate_exercise() -> tuple:
    """Return one exercise as (a, b, c, delta, type_id) where type_id ∈ {1,2,3}."""
    E_set      = [1, 2, 3]
    type_probs = [1 / len(E_set)] * len(E_set)
    typ = generate_discrete_sample(E_set, type_probs)
    if   typ == 1: return (*_case1(), typ)
    elif typ == 2: return (*_case2(), typ)
    else:          return (*_case3(), typ)
