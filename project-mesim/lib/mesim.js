// ─── MESIM Math Engine ───────────────────────────────────────────────────────
// Discrete inverse-CDF sampler + quadratic exercise generators
// Mirrors the Python logic from project_app.py exactly.

// ── Core sampler ─────────────────────────────────────────────────────────────

/** Sample one value from a discrete distribution via inverse-CDF. */
export function discreteSample(values, probs) {
  const u = Math.random();
  let cumul = 0;
  for (let i = 0; i < values.length; i++) {
    cumul += probs[i];
    if (u <= cumul) return values[i];
  }
  return values[values.length - 1];
}

/** Sample from a uniform distribution over an array. */
export function uniformSample(arr) {
  const p = 1 / arr.length;
  return discreteSample(arr, arr.map(() => p));
}

/** Build an integer range [a, b] excluding certain values. */
export function intRange(a, b, exclude = []) {
  const out = [];
  for (let i = a; i <= b; i++) if (!exclude.includes(i)) out.push(i);
  return out;
}

// ── Exercise generators ───────────────────────────────────────────────────────

/** Case 1: Δ < 0  (prob 1/5) */
function generateCase1() {
  const E      = intRange(-9, 9, [0]);
  const Esmall = [1, 2, 3];
  const pe     = E.map(() => 1 / E.length);

  const a = discreteSample(E, pe);
  const b = discreteSample(E, pe);
  const e = uniformSample(Esmall);
  const c = (b * b + e) / (4 * a);
  return { a, b, c, delta: b * b - 4 * a * c };
}

/** Case 2: Δ = 0  (prob 2/5) */
function generateCase2() {
  const E  = intRange(-9, 9, [0]);
  const Ep = intRange(1, 9);
  const pe = E.map(() => 1 / E.length);
  // Specific distribution for ℓ (from the PDF p.17)
  const pl = [1/2, 1/36, 1/36, 1/6, 1/36, 1/36, 1/36, 1/36, 1/6];

  const e   = discreteSample(E, pe);
  const ell = discreteSample(Ep, pl);
  const x0  = e / Math.sqrt(ell);
  const a = 1, b = -2 * x0, c = x0 * x0;
  return { a, b, c, delta: b * b - 4 * a * c };
}

/** Case 3: Δ > 0  (prob 2/5) — two sub-cases chosen with prob 1/2 each */
function generateCase3() {
  const E      = intRange(-9, 9, [0]);
  const Ep     = intRange(1, 9);
  const Esmall = intRange(-3, 3, [0]);
  const pe     = E.map(() => 1 / E.length);
  const pEp    = Ep.map(() => 1 / Ep.length);
  const pEs    = Esmall.map(() => 1 / Esmall.length);
  // Z distribution: P(Z=1)=1/2, P(Z≠1)=1/(2×17) for each of the 17 other values in E
  const pZ     = E.map(i => i === 1 ? 0.5 : 1 / (2 * 17));

  let x1, x2;
  if (Math.random() < 0.5) {
    // Case 3.1 — rational roots h/ℓ, k/ℓ
    const h  = discreteSample(E, pe);
    const k  = discreteSample(E, pe);
    const ll = discreteSample(E, pZ);
    x1 = h / ll;
    x2 = k / ll;
  } else {
    // Case 3.2 — clear denominators so coefficients are integers:
    //   roots are x = (-h ± e√p) / l
    //   ⟹  ℓ²x² + 2hℓx + (h² - pe²) = 0
    const h = discreteSample(E, pe);
    const l = discreteSample(Esmall, pEs);
    const e = discreteSample(Ep, pEp);
    const p = discreteSample(Ep, pEp);
    const a = l * l;
    const b = 2 * h * l;
    const c = h * h - p * e * e;
    return { a, b, c, delta: b * b - 4 * a * c };
  }
  const a = 1, b = -(x1 + x2), c = x1 * x2;
  return { a, b, c, delta: b * b - 4 * a * c };
}

// ── Public API ────────────────────────────────────────────────────────────────

/**
 * Generate one exercise.
 * Returns { a, b, c, delta, typ } where typ ∈ {1, 2, 3}.
 */
export function generateExercise() {
  // Type 1: 1/5 (Δ<0),  Type 2: 2/5 (Δ=0),  Type 3: 2/5 (Δ>0)
  const typ = discreteSample([1, 2, 3], [1/5, 2/5, 2/5]);
  const data = typ === 1 ? generateCase1()
             : typ === 2 ? generateCase2()
             :              generateCase3();
  return { ...data, typ };
}

/** Generate n exercises. */
export function generateExercises(n) {
  return Array.from({ length: n }, generateExercise);
}

// ── Scoring helpers ───────────────────────────────────────────────────────────

/** Round to 4 decimal places (display precision). */
export function fmt4(n) {
  return Math.round(n * 10000) / 10000;
}

/** Number of real solutions given discriminant. */
export function countSolutions(delta) {
  if (delta < -1e-9)       return 0;
  if (Math.abs(delta) < 1e-9) return 1;
  return 2;
}

/** Score an answer: returns 0, 0.5, or 1. */
export function scoreAnswer(exercise, deltaStr, nsolStr) {
  const delta   = fmt4(exercise.delta);
  const correct = countSolutions(exercise.delta);
  let pts = 0;

  const ud = parseFloat(deltaStr);
  if (!isNaN(ud) && Math.abs(ud - delta) < 0.01) pts += 0.5;

  const un = parseInt(nsolStr, 10);
  if (!isNaN(un) && un === correct) pts += 0.5;

  return pts;
}

/** Format ax² + bx + c = 0 as a readable string. */
export function formatEquation(a, b, c) {
  a = fmt4(a); b = fmt4(b); c = fmt4(c);

  const term = (coef, variable, first = false) => {
    if (coef === 0) return "";
    const absC = Math.abs(coef);
    const sign = coef < 0 ? (first ? "−" : " − ") : first ? "" : " + ";
    const mag  = absC === 1 && variable ? "" : String(absC);
    return `${sign}${mag}${variable}`;
  };

  const s = term(a, "x²", true) + term(b, "x") + term(c, "");
  return (s || "0") + " = 0";
}

/** Compute exact solutions for display in correction screen. */
export function computeSolutions(a, b, _c, delta) {
  const nsol = countSolutions(delta);
  if (nsol === 0) return [];
  if (nsol === 1) return [fmt4(-b / (2 * a))];
  const sq = Math.sqrt(Math.abs(delta));
  return [fmt4((-b - sq) / (2 * a)), fmt4((-b + sq) / (2 * a))];
}
