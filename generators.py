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

    # Probability of full E, equally
    pe = [1 / len(E)] * len(E)

    # Probability of small E
    ps = [1 / len(E_small)] * len(E_small)
    # Generate Discrete sample a, b from full E
    a = generate_discrete_sample(E, pe)
    b = generate_discrete_sample(E, pe)

    # Generate Discrete sample c from small E
    e = generate_discrete_sample(E_small, ps)
    c = (b**2 + e) / (4 * abs(a))
    # Prevent minus 
    if a < 0:
        c = -c # Flip sign, so c > (b^2/4a)
    return a, b, c, b**2 - 4 * a * c

def _case2():
    """Type 2 — discriminant = 0 (one repeated root)."""
    # Full Set
    E  = [i for i in range(-9, 10) if i != 0]
    # Small Set
    Ep = list(range(1, 10))

    # Probability of full E, equally
    pe = [1 / len(E)]  * len(E)

    # Probability given in the instruction
    pl = [1/2, 1/36, 1/36, 1/6, 1/36, 1/36, 1/36, 1/36, 1/6]

    # Generate Discrete sample from full E 
    e   = generate_discrete_sample(E, pe)

    # Generate Discrete sample from full El with given probab
    ell = generate_discrete_sample(Ep, pl)

    # Formula from proejcts
    x0  = e / math.sqrt(ell)
    a, b, c = 1, -2 * x0, x0**2
    return a, b, c, b**2 - 4 * a * c

def _case3():
    """Type 3 — discriminant > 0 (two distinct real roots)."""
    # Full Set, include negative
    E       = [i for i in range(-9, 10) if i != 0]

    # Seet contains positive
    Ep      = list(range(1, 10))

    # Small Set
    E_small = [i for i in range(-3, 4) if i != 0]

    # probability
    pe  = [1 / len(E)]       * len(E)
    pEp = [1 / len(Ep)]      * len(Ep)
    pEs = [1 / len(E_small)] * len(E_small)

    # given probability, P(Z=1)=1/2
    pZ  = [1/2 if i == 1 else 1 / (2 * 17) for i in E]

    # Case 1
    if generate_discrete_sample([1, 2], [1/2, 1/2]) == 1:
        
        # h, k random on cardinal 18
        h  = generate_discrete_sample(E, pe)
        k  = generate_discrete_sample(E, pe)

        # l from Z which given
        ll = generate_discrete_sample(E, pZ)

        x1, x2 = h / ll, k / ll

    # Case 2
    else:
        # Sampling from set E
        h = generate_discrete_sample(E, pe)

        # Sampling from set E[-3,-2,-1,1,2,3]
        l = generate_discrete_sample(E_small, pEs)

        # Sampling from set E[1....9]
        e = generate_discrete_sample(Ep, pEp)
        p = generate_discrete_sample(Ep, pEp)

        # Calculate from the given formula
        a = l ** 2
        b = 2 * h * l
        c = h ** 2 - p * e ** 2
        return a, b, c, b ** 2 - 4 * a * c

    a, b, c = 1, -(x1 + x2), x1 * x2
    return a, b, c, b**2 - 4 * a * c

def generate_exercise() -> tuple:
    """Return one exercise as (a, b, c, delta, type_id) where type_id in {1,2,3}.

    Type probabilities:  1/5  (delta < 0),  2/5  (delta = 0),  2/5  (delta > 0)
    """
    # Set of exercise cases
    E_set      = [1, 2, 3]

    # Probabiltiy split type1, 20%, 40%, 40%
    type_probs = [1/5, 2/5, 2/5]

    # Generate type of problem
    typ = generate_discrete_sample(E_set, type_probs)

    if   typ == 1: return (*_case1(), typ)
    elif typ == 2: return (*_case2(), typ)
    else:          return (*_case3(), typ)
