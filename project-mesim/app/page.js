"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import Image from "next/image";
import katex from "katex";
import {
  Compass, PenLine, Trophy, ArrowRight, RotateCcw,
  SkipForward, Check, X, Minus, LayoutList, Clock, Menu, Moon, Sun,
} from "lucide-react";
import {
  generateExercises, countSolutions, computeSolutions, scoreAnswer, fmt4,
} from "@/lib/mesim";

// ── Dark mode hook ────────────────────────────────────────────────────────────
function useDarkMode() {
  const [dark, setDark] = useState(false);
  useEffect(() => {
    const saved = localStorage.getItem("mesim-dark");
    if (saved === "1") { setDark(true); document.documentElement.classList.add("dark"); }
  }, []);
  const toggle = () => setDark(d => {
    const next = !d;
    document.documentElement.classList.toggle("dark", next);
    localStorage.setItem("mesim-dark", next ? "1" : "0");
    return next;
  });
  return [dark, toggle];
}

// ── localStorage stats ────────────────────────────────────────────────────────
function loadStats() {
  try { return JSON.parse(localStorage.getItem("mesim-stats") || "null") || { sessions: 0, totalPct: 0, best: null }; }
  catch { return { sessions: 0, totalPct: 0, best: null }; }
}
function saveStats(score, total) {
  const pct = total > 0 ? Math.round((score / total) * 100) : 0;
  const s = loadStats();
  s.sessions += 1;
  s.totalPct += pct;
  if (s.best === null || pct > s.best) s.best = pct;
  localStorage.setItem("mesim-stats", JSON.stringify(s));
}

// ── KaTeX ─────────────────────────────────────────────────────────────────────
function KTex({ tex, block = false, className = "" }) {
  const html = katex.renderToString(tex, { throwOnError: false, displayMode: block });
  const Tag = block ? "div" : "span";
  return <Tag className={className} dangerouslySetInnerHTML={{ __html: html }} />;
}

/** Reduce a float to an irreducible fraction string for LaTeX, e.g. -5/4 → "-\\frac{5}{4}" */
function toLatexCoef(v) {
  const n0 = Math.round(v * 10000), d0 = 10000;
  let a = Math.abs(n0), b = d0;
  while (b) { [a, b] = [b, a % b]; }
  const n = n0 / a, d = d0 / a;
  if (Math.abs(n / d - v) > 1e-9) return String(fmt4(v));
  if (d === 1) return String(n);
  return n < 0 ? `-\\frac{${-n}}{${d}}` : `\\frac{${n}}{${d}}`;
}

/** Build LaTeX string for ax²+bx+c=0 */
function toLatex(a, b, c) {
  const parts = [];
  const push = (coef, v, first = false) => {
    if (coef === 0) return;
    const neg = coef < 0;
    const absV = Math.abs(coef);
    const mag = absV === 1 && v ? "" : toLatexCoef(absV);
    parts.push(first ? (neg ? `-${mag}${v}` : `${mag}${v}`) : `${neg ? "-" : "+"} ${mag}${v}`);
  };
  push(a, "x^2", true); push(b, "x"); push(c, "");
  return (parts.join(" ") || "0") + " = 0";
}

// ── Timer ring ────────────────────────────────────────────────────────────────
function TimerRing({ timeLeft, total = 120 }) {
  const r = 26, circ = 2 * Math.PI * r;
  const frac = timeLeft / total;
  const color = frac > 0.4 ? "#16a34a" : frac > 0.15 ? "#d97706" : "#dc2626";
  const m = Math.floor(timeLeft / 60), s = timeLeft % 60;
  return (
    <div className="relative flex items-center justify-center w-16 h-16">
      <svg className="absolute inset-0 -rotate-90" viewBox="0 0 64 64">
        <circle cx="32" cy="32" r={r} fill="none" stroke="var(--border)" strokeWidth="5" />
        <circle cx="32" cy="32" r={r} fill="none" stroke={color} strokeWidth="5"
          strokeDasharray={`${Math.max(0, frac * circ)} ${circ}`} strokeLinecap="round"
          style={{ transition: "stroke-dasharray 0.9s linear, stroke 0.4s" }} />
      </svg>
      <span className="relative text-[11px] font-bold tabular-nums" style={{ color: "var(--foreground)" }}>
        {m}:{String(s).padStart(2, "0")}
      </span>
    </div>
  );
}

// ── Score ring (animated) ─────────────────────────────────────────────────────
function ScoreRing({ score, total }) {
  const r = 54, circ = 2 * Math.PI * r;
  const pct = total > 0 ? score / total : 0;
  const color = pct >= 0.8 ? "#16a34a" : pct >= 0.5 ? "#d97706" : "#dc2626";
  const [drawn, setDrawn] = useState(0);

  useEffect(() => {
    // Animate from 0 to pct over 1s
    const start = performance.now();
    const duration = 1000;
    const frame = (now) => {
      const t = Math.min((now - start) / duration, 1);
      const ease = 1 - Math.pow(1 - t, 3);
      setDrawn(ease * pct);
      if (t < 1) requestAnimationFrame(frame);
    };
    requestAnimationFrame(frame);
  }, [pct]);

  return (
    <div className="relative flex items-center justify-center w-36 h-36">
      <svg className="absolute inset-0 -rotate-90" viewBox="0 0 144 144">
        <circle cx="72" cy="72" r={r} fill="none" stroke="var(--border)" strokeWidth="10" />
        <circle cx="72" cy="72" r={r} fill="none" stroke={color} strokeWidth="10"
          strokeDasharray={`${drawn * circ} ${circ}`} strokeLinecap="round" />
      </svg>
      <div className="relative text-center leading-tight">
        <p className="text-2xl font-bold" style={{ color: "var(--foreground)" }}>{score}/{total}</p>
        <p className="text-sm" style={{ color: "var(--muted)" }}>{Math.round(pct * 100)}%</p>
      </div>
    </div>
  );
}

// ── Sidebar ───────────────────────────────────────────────────────────────────
function Sidebar({ screen, exercises, currentIdx, scores, open, onClose, onReview, dark, toggleDark }) {
  const isQuiz = screen === "quiz" || screen === "correction";
  const navItems = [
    { key: "intro",   Icon: Compass, label: "Introduction" },
    { key: "quiz",    Icon: PenLine, label: "Exercises"    },
    { key: "summary", Icon: Trophy,  label: "Results"      },
  ];

  return (
    <>
      {open && <div className="fixed inset-0 z-40 bg-black/40 md:hidden" onClick={onClose} />}

      <aside
        className="sidebar-nav fixed inset-y-0 left-0 z-50 flex flex-col border-r w-60 shrink-0 h-full overflow-y-auto transition-transform duration-200"
        style={{ transform: open ? "translateX(0)" : "translateX(-100%)", background: "var(--surface)", borderColor: "var(--border)" }}
      >
        {/* Logo + dark toggle */}
        <div className="flex flex-col items-center pt-8 pb-1 px-4 relative">
          <Image src="/logo.svg" alt="ENSIIE" width={138} height={55} className="object-contain" priority />
          <span className="mt-2 text-[10px] font-bold tracking-[0.2em] uppercase" style={{ color: "var(--muted)" }}>MESIM</span>
          <button onClick={toggleDark}
            className="absolute top-3 right-3 w-7 h-7 rounded-full flex items-center justify-center transition-colors hover:opacity-70"
            style={{ color: "var(--muted)" }} title={dark ? "Light mode" : "Dark mode"}>
            {dark ? <Sun size={14} /> : <Moon size={14} />}
          </button>
        </div>

        <div className="mx-4 my-4 h-px" style={{ background: "var(--border)" }} />

        {/* Main nav */}
        <nav className="flex flex-col gap-1 px-3">
          {navItems.map(({ key, Icon, label }) => {
            const active = key === "quiz" ? isQuiz : screen === key;
            return (
              <div key={key} onClick={onClose}
                className="flex items-center gap-2.5 px-3 py-2.5 rounded-xl select-none transition-all cursor-default"
                style={{
                  background: active ? "var(--surface-2)" : "transparent",
                  color: active ? "var(--foreground)" : "var(--muted)",
                }}>
                <Icon size={15} style={{ color: active ? "var(--accent)" : "inherit" }} />
                <span className={`text-[13px] ${active ? "font-semibold" : ""}`}>{label}</span>
              </div>
            );
          })}
        </nav>

        {/* Exercise navigator */}
        {exercises.length > 0 && (
          <>
            <div className="mx-4 my-4 h-px" style={{ background: "var(--border)" }} />
            <div className="px-4 flex-1 overflow-y-auto">
              <div className="flex items-center gap-1.5 mb-3">
                <LayoutList size={13} style={{ color: "var(--muted)" }} />
                <span className="text-[11px] font-bold uppercase tracking-widest" style={{ color: "var(--muted)" }}>Questions</span>
              </div>

              <div className="flex flex-wrap gap-1.5">
                {exercises.map((_, i) => {
                  const sc = scores[i];
                  const isCur = isQuiz && i === currentIdx && sc === undefined;
                  const state = isCur ? "current"
                    : sc === 1   ? "correct"
                    : sc === 0.5 ? "partial"
                    : sc === 0   ? "wrong"
                    : "pending";

                  const isDone = sc !== undefined;
                  const canReview = isDone && onReview;

                  const stateStyle = {
                    current: { background: "var(--accent)", borderColor: "var(--accent)", color: "#fff" },
                    correct: { background: "#f0fdf4", borderColor: "#bbf7d0", color: "#16a34a" },
                    partial: { background: "#fffbeb", borderColor: "#fde68a", color: "#d97706" },
                    wrong:   { background: "#fef2f2", borderColor: "#fecaca", color: "#dc2626" },
                    pending: { background: "var(--surface-2)", borderColor: "var(--border)", color: "var(--muted)" },
                  }[state];

                  return (
                    <div key={i} title={isDone ? `Exercise ${i + 1} — click to review` : `Exercise ${i + 1}`}
                      onClick={() => isDone && onReview(i)}
                      className={`w-7 h-7 rounded-full flex items-center justify-center text-[11px] font-bold transition-transform
                        ${canReview ? "cursor-pointer hover:scale-110" : "cursor-default"}`}
                      style={{ ...stateStyle, border: `1px solid ${stateStyle.borderColor}` }}>
                      {state === "correct" ? <Check size={11} />
                        : state === "partial" ? <Minus size={11} />
                        : state === "wrong"   ? <X size={11} />
                        : i + 1}
                    </div>
                  );
                })}
              </div>

              {/* Legend */}
              <div className="mt-4 flex flex-col gap-1">
                {[
                  { color: "#16a34a", bg: "#f0fdf4", border: "#bbf7d0", Icon: Check,  label: "Correct" },
                  { color: "#d97706", bg: "#fffbeb", border: "#fde68a", Icon: Minus,  label: "Partial" },
                  { color: "#dc2626", bg: "#fef2f2", border: "#fecaca", Icon: X,      label: "Wrong"   },
                  { color: null,      bg: null,      border: null,       Icon: null,   label: "Pending" },
                ].map(({ color, bg, border, Icon: I, label }) => (
                  <div key={label} className="flex items-center gap-2">
                    <div className="w-4 h-4 rounded-full border flex items-center justify-center"
                      style={{ background: bg || "var(--surface-2)", borderColor: border || "var(--border)", color: color || "var(--muted)" }}>
                      {I && <I size={9} />}
                    </div>
                    <span className="text-[10px]" style={{ color: "var(--muted)" }}>{label}</span>
                  </div>
                ))}
                {exercises.some((_, i) => scores[i] !== undefined) && (
                  <p className="text-[9px] mt-1" style={{ color: "var(--muted)" }}>Click a done exercise to review</p>
                )}
              </div>
            </div>
          </>
        )}

        <div className="mt-auto px-4 pb-6">
          <div className="h-px mb-4" style={{ background: "var(--border)" }} />
          <p className="text-[10px] text-center tracking-wide" style={{ color: "var(--muted)" }}>ENSIIE · MESIM · 2026</p>
        </div>
      </aside>
    </>
  );
}

// ── Generation Details Modal ──────────────────────────────────────────────────
function GenerationDetails() {
  const [open, setOpen] = useState(false);
  const [tab,  setTab]  = useState(1);

  const cases = {
    1: {
      label: "Type 1 — Δ < 0", color: "#dc2626", border: "#fecaca", bg: "#fef2f2",
      rows: [
        { label: "Sets",    content: <><KTex tex="\mathbb{E} = \{-9,\ldots,-1,1,\ldots,9\}" />&ensp;<KTex tex="E_s = \{1,2,3\}" /></> },
        { label: "Sample",  content: <><KTex tex="a,b \sim \mathcal{U}(\mathbb{E})" />&ensp;<KTex tex="e \sim \mathcal{U}(E_s)" /></> },
        { label: "Compute", content: <KTex tex="c = \dfrac{b^2 + e}{4a}" /> },
        { label: "Result",  content: <><KTex tex="\Delta = b^2 - 4ac = -e < 0" />&ensp;— always negative</> },
        { label: "Why",     content: "By construction Δ = −e, and e ∈ {1,2,3}, so Δ is always strictly negative." },
      ],
    },
    2: {
      label: "Type 2 — Δ = 0", color: "#d97706", border: "#fde68a", bg: "#fffbeb",
      rows: [
        { label: "Sets",   content: <><KTex tex="\mathbb{E} = \{-9,\ldots,-1,1,\ldots,9\}" />&ensp;<KTex tex="\mathbb{E}^+ = \{1,\ldots,9\}" /></> },
        { label: "Sample", content: <><KTex tex="e \sim \mathcal{U}(\mathbb{E})" />&ensp;<KTex tex="\ell \sim Z" /> where <KTex tex="\mathbb{P}(Z=1)=\tfrac{1}{2}" />, <KTex tex="\mathbb{P}(Z=4)=\mathbb{P}(Z=9)=\tfrac{1}{6}" />, <KTex tex="\mathbb{P}(Z=i)=\tfrac{1}{36}" /> for <KTex tex="i\in\{2,3,5,6,7,8\}" /></> },
        { label: "Root",   content: <KTex tex="x_0 = \dfrac{e}{\sqrt{\ell}}" /> },
        { label: "Coeffs", content: <KTex tex="a=1,\quad b=-2x_0,\quad c=x_0^2" /> },
        { label: "Result", content: <><KTex tex="\Delta = b^2 - 4ac = 0" />&ensp;— always zero</> },
        { label: "Why",    content: <><KTex tex="\Delta = 4x_0^2 - 4x_0^2 = 0" /> by construction.</> },
      ],
    },
    3: {
      label: "Type 3 — Δ > 0", color: "#16a34a", border: "#bbf7d0", bg: "#f0fdf4",
      rows: [
        { label: "Split",    content: "Sub-case chosen with probability ½ each: 3.1 rational roots, 3.2 irrational roots." },
        { label: "Case 3.1", content: <><KTex tex="h,k\sim\mathcal{U}(\mathbb{E})" />, <KTex tex="\ell\sim Z" /> with <KTex tex="\mathbb{P}(Z=1)=\tfrac{1}{2}" />&ensp;→&ensp;<KTex tex="x_1=h/\ell,\; x_2=k/\ell" /></> },
        { label: "Case 3.2", content: <><KTex tex="h\sim\mathcal{U}(\mathbb{E})" />, <KTex tex="e,p\sim\mathcal{U}(\mathbb{E}^+)" />, <KTex tex="\ell\sim\mathcal{U}(\{-3,\ldots,3\}\setminus\{0\})" />&ensp;→&ensp;<KTex tex="x_{1,2}=\dfrac{-h\mp e\sqrt{p}}{\ell}" /></> },
        { label: "Coeffs",   content: <KTex tex="a=1,\quad b=-(x_1+x_2),\quad c=x_1 x_2" /> },
        { label: "Result",   content: <><KTex tex="\Delta = (x_1-x_2)^2 > 0" />&ensp;since <KTex tex="x_1 \neq x_2" /></> },
      ],
    },
  };

  const c = tab !== "algo" ? cases[tab] : null;

  return (
    <>
      <button onClick={() => setOpen(true)}
        className="w-full flex items-center justify-between px-5 py-3.5 rounded-2xl border transition-all group"
        style={{ background: "var(--surface)", borderColor: "var(--border)" }}>
        <div className="flex items-center gap-2.5">
          <span className="text-[13px] font-semibold" style={{ color: "var(--foreground)" }}>How exercises are generated</span>
          <span className="text-[10px] px-2 py-0.5 rounded-full font-medium border"
            style={{ background: "var(--surface-2)", color: "var(--muted)", borderColor: "var(--border)" }}>
            Inverse-CDF method
          </span>
        </div>
        <svg className="w-4 h-4 transition-colors" style={{ color: "var(--muted)" }}
          fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M13 16h-1v-4h-1m1-4h.01M12 2a10 10 0 110 20A10 10 0 0112 2z" />
        </svg>
      </button>

      {open && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 md:p-6"
          style={{ backgroundColor: "rgba(0,0,0,0.5)" }} onClick={() => setOpen(false)}>
          <div className="rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90dvh] flex flex-col overflow-hidden"
            style={{ background: "var(--surface)" }} onClick={e => e.stopPropagation()}>
            <div className="flex items-center justify-between px-6 py-4 border-b shrink-0"
              style={{ borderColor: "var(--border)" }}>
              <div className="flex items-center gap-2.5">
                <span className="text-[15px] font-bold" style={{ color: "var(--foreground)" }}>How exercises are generated</span>
                <span className="text-[10px] px-2 py-0.5 rounded-full font-medium border"
                  style={{ background: "var(--surface-2)", color: "var(--muted)", borderColor: "var(--border)" }}>
                  Inverse-CDF method
                </span>
              </div>
              <button onClick={() => setOpen(false)}
                className="w-7 h-7 rounded-full flex items-center justify-center transition-colors"
                style={{ color: "var(--muted)" }}>
                <svg fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2} className="w-4 h-4">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <div className="overflow-y-auto px-6 py-5">
              <div className="rounded-xl px-4 py-3 text-[12px] leading-relaxed mb-4 border"
                style={{ background: "var(--surface-2)", borderColor: "var(--border)", color: "var(--muted)" }}>
                <span className="font-semibold" style={{ color: "var(--foreground)" }}>Core idea — Inverse-CDF sampling:&ensp;</span>
                To sample from a discrete distribution with values <KTex tex="(a_1,\ldots,a_n)" /> and probabilities <KTex tex="(p_1,\ldots,p_n)" />,
                compute the CDF <KTex tex="F_k = p_1+\cdots+p_k" />, draw <KTex tex="U\sim\mathcal{U}(]0,1[)" />,
                then return <KTex tex="a_k" /> where <KTex tex="k = \min\{i : U \leq F_i\}" />.
              </div>

              <div className="rounded-xl border overflow-hidden" style={{ borderColor: "var(--border)" }}>
                <div className="flex border-b" style={{ background: "var(--surface-2)", borderColor: "var(--border)" }}>
                  {[1, 2, 3].map(t => (
                    <button key={t} onClick={() => setTab(t)}
                      className="flex-1 py-2.5 text-[12px] font-semibold transition-all border-b-2"
                      style={{
                        background: tab === t ? "var(--surface)" : "transparent",
                        borderBottomColor: tab === t ? cases[t].color : "transparent",
                        color: tab === t ? cases[t].color : "var(--muted)",
                      }}>
                      Type {t}&ensp;
                      <span className="text-[10px] font-normal">
                        {t === 1 ? "Δ < 0" : t === 2 ? "Δ = 0" : "Δ > 0"}
                      </span>
                    </button>
                  ))}
                  <button onClick={() => setTab("algo")}
                    className="flex-1 py-2.5 text-[12px] font-semibold transition-all border-b-2"
                    style={{
                      background: tab === "algo" ? "var(--surface)" : "transparent",
                      borderBottomColor: tab === "algo" ? "#6366f1" : "transparent",
                      color: tab === "algo" ? "#6366f1" : "var(--muted)",
                    }}>
                    Algorithm
                  </button>
                </div>

                {tab !== "algo" && c && (
                  <div>
                    <div className="px-4 py-2 border-b"
                      style={{ background: c.bg, borderColor: c.border }}>
                      <span className="text-[11px] font-bold uppercase tracking-widest" style={{ color: c.color }}>{c.label}</span>
                    </div>
                    <div className="divide-y" style={{ '--tw-divide-opacity': 1 }}>
                      {c.rows.map(({ label, content }) => (
                        <div key={label} className="flex gap-4 px-4 py-3 text-[12px] leading-relaxed border-b last:border-b-0"
                          style={{ background: "var(--surface)", borderColor: "var(--border)" }}>
                          <span className="w-20 shrink-0 font-semibold pt-0.5" style={{ color: "var(--muted)" }}>{label}</span>
                          <span className="flex flex-wrap items-center gap-x-1.5 gap-y-1" style={{ color: "var(--foreground)" }}>{content}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {tab === "algo" && (
                  <div>
                    <div className="px-4 py-2.5" style={{ background: "#27272a" }}>
                      <span className="text-[11px] font-bold uppercase tracking-widest" style={{ color: "#71717a" }}>Inverse-CDF Sampler</span>
                    </div>
                    <div className="grid grid-cols-2 divide-x border-b" style={{ borderColor: "var(--border)" }}>
                      {[
                        { label: "Input", color: "#f43f5e", content: <span style={{ color: "var(--muted)" }}>values <KTex tex="(a_1,\ldots,a_n)" />, probs <KTex tex="(p_1,\ldots,p_n)" /></span> },
                        { label: "Output", color: "#6366f1", content: <span style={{ color: "var(--muted)" }}>sampled value <KTex tex="a_k" /></span> },
                      ].map(({ label, color, content }) => (
                        <div key={label} className="px-4 py-2.5 text-[12px] flex items-center gap-2"
                          style={{ background: "var(--surface-2)", borderColor: "var(--border)" }}>
                          <span className="font-bold shrink-0" style={{ color }}>{label}</span>
                          {content}
                        </div>
                      ))}
                    </div>
                    <table className="w-full text-[12px]">
                      <tbody>
                        {[
                          { step: "1", keyword: null,     line: <span>Compute CDF:&ensp;<KTex tex="F_k \leftarrow p_1 + \cdots + p_k" />&ensp;for <KTex tex="k = 1, \ldots, n" /></span> },
                          { step: "2", keyword: null,     line: <span>Draw&ensp;<KTex tex="U \sim \mathcal{U}(]0,1[)" /></span> },
                          { step: "3", keyword: null,     line: <span>Set&ensp;<KTex tex="k \leftarrow 0" /></span> },
                          { step: "4", keyword: "while",  line: <span><KTex tex="U > F_k" />&ensp;<span style={{ color: "var(--muted)" }}>and</span>&ensp;<KTex tex="k < n" />&ensp;<span style={{ color: "#6366f1" }} className="font-semibold">do</span></span> },
                          { step: "",  keyword: null,     line: <KTex tex="k \leftarrow k + 1" />, indent: true },
                          { step: "5", keyword: "return", line: <KTex tex="a_k" /> },
                        ].map(({ step, keyword, line, indent }, i) => (
                          <tr key={i} style={{ background: indent ? "var(--surface-2)" : "var(--surface)" }}>
                            <td className="w-8 px-4 py-2.5 font-mono text-center select-none border-b" style={{ color: "var(--muted)", borderColor: "var(--border)" }}>{step}</td>
                            <td className="px-2 py-2.5 w-16 border-b" style={{ borderColor: "var(--border)" }}>
                              {keyword && <span className="font-semibold font-mono" style={{ color: "#6366f1" }}>{keyword}</span>}
                            </td>
                            <td className="px-2 py-2.5 border-b" style={{ color: "var(--foreground)", borderColor: "var(--border)" }}>
                              <span className={`flex items-center gap-1 flex-wrap ${indent ? "pl-5" : ""}`}>{line}</span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

// ── Intro ─────────────────────────────────────────────────────────────────────
function IntroScreen({ onStart }) {
  const [count, setCount] = useState("5");
  const go = () => { const n = parseInt(count); if (n > 0) onStart(n); };
  const [stats, setStats] = useState(null);
  useEffect(() => { setStats(loadStats()); }, []);

  return (
    <div className="flex flex-col gap-5">
      <div>
        <h1 className="text-[22px] font-bold" style={{ color: "var(--foreground)" }}>Quadratic Equation Trainer</h1>
        <p className="text-[13px] mt-0.5" style={{ color: "var(--muted)" }}>Practice solving ax² + bx + c = 0 step by step</p>
        <div className="mt-4 h-px" style={{ background: "var(--border)" }} />
      </div>

      {/* Stats bar — only rendered after client mount to avoid hydration mismatch */}
      {stats && stats.sessions > 0 && (
        <div className="flex gap-3 flex-wrap">
          {[
            { label: "Sessions", value: String(stats.sessions) },
            { label: "Best",     value: `${stats.best}%` },
            { label: "Average",  value: `${Math.round(stats.totalPct / stats.sessions)}%` },
          ].map(({ label, value }) => (
            <div key={label} className="flex flex-col items-center px-4 py-2.5 rounded-xl border flex-1 min-w-[80px]"
              style={{ background: "var(--surface)", borderColor: "var(--border)" }}>
              <span className="text-[18px] font-bold" style={{ color: "var(--accent)" }}>{value}</span>
              <span className="text-[10px] font-medium uppercase tracking-widest" style={{ color: "var(--muted)" }}>{label}</span>
            </div>
          ))}
        </div>
      )}

      {/* Theory */}
      <div className="rounded-2xl border p-6 flex flex-col gap-5" style={{ background: "var(--surface)", borderColor: "var(--border)" }}>
        <div className="rounded-xl py-5 flex justify-center overflow-x-auto border"
          style={{ background: "var(--surface-2)", borderColor: "var(--border)" }}>
          <KTex tex="ax^2 + bx + c = 0" block />
        </div>
        <div className="flex flex-col items-center gap-1">
          <span className="text-[11px] font-bold uppercase tracking-widest" style={{ color: "var(--muted)" }}>Discriminant</span>
          <KTex tex="\Delta = b^2 - 4ac" />
        </div>
        <div className="flex flex-col gap-2">
          {[
            { tex: "\\Delta < 0", desc: "No real solution",                         color: "#dc2626", bg: "#fef2f2", border: "#fecaca" },
            { tex: "\\Delta = 0", desc: "One solution:  x = −b / (2a)",             color: "#d97706", bg: "#fffbeb", border: "#fde68a" },
            { tex: "\\Delta > 0", desc: "Two solutions:  x₁,₂ = (−b ± √Δ) / (2a)", color: "#16a34a", bg: "#f0fdf4", border: "#bbf7d0" },
          ].map(({ tex, desc, color, bg, border }) => (
            <div key={tex} className="flex items-center gap-4 rounded-xl border px-4 py-3"
              style={{ background: bg, borderColor: border }}>
              <span className="font-bold w-16 shrink-0" style={{ color }}><KTex tex={tex} /></span>
              <span className="text-sm" style={{ color: "var(--muted)" }}>→</span>
              <span className="text-[13px]" style={{ color: "var(--foreground)" }}>{desc}</span>
            </div>
          ))}
        </div>
      </div>

      <GenerationDetails />

      {/* Config */}
      <div className="rounded-2xl border p-6" style={{ background: "var(--surface)", borderColor: "var(--border)" }}>
        <p className="text-[14px] font-semibold mb-1" style={{ color: "var(--foreground)" }}>Configure your session</p>
        <p className="text-[12px] mb-5" style={{ color: "var(--muted)" }}>Type 1: 1/5 · Type 2: 2/5 · Type 3: 2/5</p>
        <div className="flex items-center gap-3">
          <input type="number" min="1" max="100" value={count}
            onChange={e => setCount(e.target.value)}
            onKeyDown={e => e.key === "Enter" && go()}
            className="w-24 h-11 text-center rounded-xl border text-[15px] font-semibold outline-none transition"
            style={{ background: "var(--surface-2)", borderColor: "var(--border)", color: "var(--foreground)" }} />
          <button onClick={go}
            className="h-11 px-5 rounded-xl text-white text-[13px] font-bold flex items-center gap-2 transition-all active:scale-[0.97]"
            style={{ background: "var(--accent)" }}>
            Start Quiz <ArrowRight size={15} />
          </button>
        </div>
      </div>

      <div className="flex gap-2 flex-wrap">
        {[
          { label: "Type 1 · Δ < 0 · 1/5", color: "#dc2626", bg: "#fef2f2", border: "#fecaca" },
          { label: "Type 2 · Δ = 0 · 2/5", color: "#d97706", bg: "#fffbeb", border: "#fde68a" },
          { label: "Type 3 · Δ > 0 · 2/5", color: "#16a34a", bg: "#f0fdf4", border: "#bbf7d0" },
        ].map(({ label, color, bg, border }) => (
          <span key={label} className="text-[11px] px-3 py-1.5 rounded-full border font-medium"
            style={{ color, background: bg, borderColor: border }}>{label}</span>
        ))}
      </div>
    </div>
  );
}

// ── Quiz ──────────────────────────────────────────────────────────────────────
function QuizScreen({ exercise, idx, total, onSubmit, onSkip }) {
  const { a, b, c, typ } = exercise;
  const [dVal, setDVal] = useState("");
  const [nVal, setNVal] = useState("");
  const [time, setTime] = useState(120);
  const [dError, setDError] = useState(false);
  const [nError, setNError] = useState(false);
  const ans = useRef({ d: "", n: "" });
  const dRef = useRef(null);
  const nRef = useRef(null);
  useEffect(() => { ans.current = { d: dVal, n: nVal }; }, [dVal, nVal]);

  const submit = useCallback(() => onSubmit(ans.current.d, ans.current.n), [onSubmit]);

  // Validate + shake on bad input
  const trySubmit = () => {
    const dNum = parseFloat(ans.current.d.replace(",", "."));
    const nNum = parseInt(ans.current.n);
    const dBad = ans.current.d.trim() === "" || isNaN(dNum);
    const nBad = ans.current.n.trim() === "" || isNaN(nNum) || ![0,1,2].includes(nNum);
    if (dBad) { setDError(true); setTimeout(() => setDError(false), 400); }
    if (nBad) { setNError(true); setTimeout(() => setNError(false), 400); }
    if (!dBad && !nBad) submit();
  };

  useEffect(() => {
    const id = setInterval(() => setTime(t => {
      if (t <= 1) { clearInterval(id); submit(); return 0; }
      return t - 1;
    }), 1000);
    return () => clearInterval(id);
  }, [submit]);

  // Keyboard: Tab focuses next input
  const handleKeyDown = (e, isLast) => {
    if (e.key === "Enter") { e.preventDefault(); trySubmit(); }
    if (e.key === "Tab" && isLast) { e.preventDefault(); dRef.current?.focus(); }
  };

  return (
    <div className="flex flex-col gap-5">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 className="text-[20px] font-bold" style={{ color: "var(--foreground)" }}>Exercise {idx} / {total}</h2>
          <p className="text-[12px] mt-0.5" style={{ color: "var(--muted)" }}>Compute Δ then count the solutions</p>
        </div>
        <div className="rounded-2xl p-2 shadow-sm shrink-0 border"
          style={{ background: "var(--surface)", borderColor: "var(--border)" }}>
          <TimerRing timeLeft={time} />
        </div>
      </div>

      <div className="h-1.5 rounded-full overflow-hidden" style={{ background: "var(--border)" }}>
        <div className="h-full rounded-full transition-[width] duration-500"
          style={{ width: `${((idx - 1) / total) * 100}%`, background: "var(--accent)" }} />
      </div>

      <div className="rounded-2xl px-6 py-6 border" style={{ background: "#fef2f2", borderColor: "#fecaca" }}>
        <p className="text-[10px] font-bold uppercase tracking-[0.15em] mb-4" style={{ color: "#fca5a5" }}>Solve</p>
        <div className="flex justify-center py-2 overflow-x-auto">
          <KTex tex={toLatex(a, b, c)} block />
        </div>
        <div className="mt-4 flex gap-2">
          <span className="text-[11px] px-2.5 py-1 rounded-full border" style={{ background: "white", borderColor: "#fecaca", color: "#71717a" }}>Type {typ}</span>
          <span className="text-[11px] px-2.5 py-1 rounded-full border" style={{ background: "white", borderColor: "#fecaca", color: "#71717a" }}>1 pt total</span>
        </div>
      </div>

      <div className="rounded-2xl border p-6 flex flex-col gap-3" style={{ background: "var(--surface)", borderColor: "var(--border)" }}>
        <p className="text-[13px] font-semibold mb-1" style={{ color: "var(--foreground)" }}>Your answers</p>
        {[
          { label: "Discriminant", katex: "\\Delta", pts: "0.5 pt", val: dVal, set: setDVal, ph: "e.g. −3.25", error: dError, ref: dRef, isLast: false },
          { label: "Number of solutions (0, 1 or 2)", pts: "0.5 pt", val: nVal, set: setNVal, ph: "0, 1 or 2", error: nError, ref: nRef, isLast: true },
        ].map(({ label, katex: ktx, pts, val, set, ph, error, ref, isLast }) => (
          <label key={label} className="flex items-center gap-3 rounded-xl px-4 py-3 cursor-text border"
            style={{ background: "var(--surface-2)", borderColor: error ? "#f87171" : "var(--border-2)" }}>
            <span className="flex-1 text-[13px] flex items-center gap-1 select-none" style={{ color: "var(--foreground)" }}>
              {label}{ktx && <KTex tex={ktx} />} ?
            </span>
            <span className="text-[10px] border rounded-full px-2 py-0.5 shrink-0"
              style={{ color: "var(--muted)", borderColor: "var(--border)" }}>{pts}</span>
            <input ref={ref} value={val}
              onChange={e => set(e.target.value)}
              onKeyDown={e => handleKeyDown(e, isLast)}
              placeholder={ph}
              className={`w-32 h-9 text-center rounded-lg border text-[13px] outline-none transition ${error ? "shake" : ""}`}
              style={{
                background: "var(--surface)",
                borderColor: error ? "#f87171" : "var(--border)",
                color: "var(--foreground)",
              }} />
          </label>
        ))}
      </div>

      <div className="flex justify-end gap-2.5">
        <button onClick={onSkip}
          className="h-10 px-4 rounded-xl border text-[13px] font-medium flex items-center gap-1.5 transition"
          style={{ background: "var(--surface)", borderColor: "var(--border)", color: "var(--muted)" }}>
          <SkipForward size={14} /> Skip
        </button>
        <button onClick={trySubmit}
          className="h-10 px-5 rounded-xl text-white text-[13px] font-bold flex items-center gap-2 transition-all active:scale-[0.97]"
          style={{ background: "var(--accent)" }}>
          Submit <ArrowRight size={14} />
        </button>
      </div>
    </div>
  );
}

// ── Correction ────────────────────────────────────────────────────────────────
function CorrectionScreen({ exercise, exScore, runningScore, exerciseNum, remaining, onNext, isLast }) {
  const { a, b, c, delta } = exercise;
  const nsol = countSolutions(delta);
  const sols = computeSolutions(a, b, c, delta);

  const badgeStyle = exScore === 1
    ? { background: "#f0fdf4", borderColor: "#bbf7d0", color: "#15803d" }
    : exScore === 0.5
    ? { background: "#fffbeb", borderColor: "#fde68a", color: "#b45309" }
    : { background: "#fef2f2", borderColor: "#fecaca", color: "#b91c1c" };
  const BadgeIcon = exScore === 1 ? Check : exScore === 0.5 ? Minus : X;

  return (
    <div className="flex flex-col gap-5">
      <div>
        <div className="flex items-center justify-between">
          <h2 className="text-[20px] font-bold" style={{ color: "var(--foreground)" }}>Exercise {exerciseNum} · Correction</h2>
          <span className="inline-flex items-center gap-1.5 text-[12px] font-bold px-3 py-1.5 rounded-full border"
            style={badgeStyle}>
            <BadgeIcon size={12} /> {exScore} / 1 pt
          </span>
        </div>
        <div className="mt-4 h-px" style={{ background: "var(--border)" }} />
      </div>

      <div className="rounded-2xl px-6 py-6 border" style={{ background: "#fef2f2", borderColor: "#fecaca" }}>
        <p className="text-[10px] font-bold uppercase tracking-[0.15em] mb-4" style={{ color: "#fca5a5" }}>Equation</p>
        <div className="flex justify-center overflow-x-auto">
          <KTex tex={toLatex(a, b, c)} block />
        </div>
      </div>

      <div className="rounded-2xl border p-6" style={{ background: "var(--surface)", borderColor: "var(--border)" }}>
        <p className="text-[11px] font-bold uppercase tracking-widest mb-4" style={{ color: "var(--muted)" }}>Solution</p>
        <div className="flex flex-col gap-2">
          {[
            { label: "Discriminant", ktex: "\\Delta =", value: String(fmt4(delta)) },
            { label: "Number of solutions", value: String(nsol) },
            ...(nsol === 1 ? [{ label: "Solution", value: `x₀ = ${sols[0]}`, green: true }] : []),
            ...(nsol === 2 ? [
              { label: "Solutions", value: `x₁ = ${sols[0]}`, green: true },
              { label: "",          value: `x₂ = ${sols[1]}`, green: true },
            ] : []),
          ].map(({ label, ktex, value, green }, i) => (
            <div key={i} className="flex items-center gap-4 rounded-xl px-4 py-3 border"
              style={{ background: "var(--surface-2)", borderColor: "var(--border-2)" }}>
              <span className="text-[12px] w-44 shrink-0 flex items-center gap-1" style={{ color: "var(--muted)" }}>
                {label}{ktex && <KTex tex={ktex} />}
              </span>
              <span className="font-mono text-[13px] font-semibold" style={{ color: green ? "#16a34a" : "var(--foreground)" }}>
                {value}
              </span>
            </div>
          ))}
        </div>
      </div>

      <p className="text-[12px] flex items-center gap-1.5" style={{ color: "var(--muted)" }}>
        <Clock size={12} />
        Running total: <span className="font-semibold" style={{ color: "var(--foreground)" }}>{runningScore}</span>
        · {remaining} exercise{remaining !== 1 ? "s" : ""} remaining
      </p>

      <div className="flex justify-end">
        <button onClick={onNext}
          className="h-10 px-5 rounded-xl text-white text-[13px] font-bold flex items-center gap-2 transition-all active:scale-[0.97]"
          style={{ background: "var(--accent)" }}>
          {isLast ? "See Final Score" : "Next Exercise"} <ArrowRight size={14} />
        </button>
      </div>
    </div>
  );
}

// ── Summary ───────────────────────────────────────────────────────────────────
function SummaryScreen({ score, total, onRestart }) {
  const pct = total > 0 ? (score / total) * 100 : 0;
  const { verdict, color } =
    pct >= 80 ? { verdict: "Excellent!",      color: "#16a34a" } :
    pct >= 50 ? { verdict: "Good effort!",     color: "#d97706" } :
                { verdict: "Keep practicing!", color: "#dc2626" };

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-[22px] font-bold" style={{ color: "var(--foreground)" }}>Quiz Complete</h1>
        <p className="text-[13px] mt-0.5" style={{ color: "var(--muted)" }}>Here&apos;s how you did</p>
        <div className="mt-4 h-px" style={{ background: "var(--border)" }} />
      </div>

      <div className="flex flex-col items-center gap-4 py-2">
        <ScoreRing score={score} total={total} />
        <p className="text-[22px] font-bold" style={{ color }}>{verdict}</p>
      </div>

      <div className="rounded-2xl border p-6 flex flex-col gap-2" style={{ background: "var(--surface)", borderColor: "var(--border)" }}>
        {[["Total score", `${score} / ${total}`], ["Percentage", `${pct.toFixed(1)} %`], ["Exercises done", String(total)]].map(([l, v]) => (
          <div key={l} className="flex items-center justify-between rounded-xl px-4 py-3 border"
            style={{ background: "var(--surface-2)", borderColor: "var(--border-2)" }}>
            <span className="text-[13px]" style={{ color: "var(--muted)" }}>{l}</span>
            <span className="text-[13px] font-bold" style={{ color: "var(--foreground)" }}>{v}</span>
          </div>
        ))}
      </div>

      <div className="flex justify-end gap-2.5">
        <button onClick={onRestart}
          className="h-10 px-4 rounded-xl border text-[13px] font-medium transition"
          style={{ background: "var(--surface)", borderColor: "var(--border)", color: "var(--muted)" }}>
          Back to Intro
        </button>
        <button onClick={onRestart}
          className="h-10 px-5 rounded-xl text-white text-[13px] font-bold flex items-center gap-2 transition-all active:scale-[0.97]"
          style={{ background: "var(--accent)" }}>
          <RotateCcw size={14} /> New Quiz
        </button>
      </div>
    </div>
  );
}

// ── Root ──────────────────────────────────────────────────────────────────────
export default function Home() {
  const [screen,      setScreen]      = useState("intro");
  const [exercises,   setExercises]   = useState([]);
  const [currentIdx,  setCurrentIdx]  = useState(0);
  const [scores,      setScores]      = useState({});
  const [lastScore,   setLastScore]   = useState(0);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [reviewIdx,   setReviewIdx]   = useState(null); // null = not reviewing
  const [dark, toggleDark] = useDarkMode();

  const totalScore = Object.values(scores).reduce((s, v) => s + v, 0);

  const handleStart = (n) => {
    setExercises(generateExercises(n));
    setCurrentIdx(0); setScores({}); setReviewIdx(null); setScreen("quiz");
  };
  const handleSubmit = (d, n) => {
    const pts = scoreAnswer(exercises[currentIdx], d, n);
    setScores(s => ({ ...s, [currentIdx]: pts }));
    setLastScore(pts); setReviewIdx(null); setScreen("correction");
  };
  const handleSkip = () => {
    setScores(s => ({ ...s, [currentIdx]: 0 }));
    setLastScore(0); setReviewIdx(null); setScreen("correction");
  };
  const handleNext = () => {
    const next = currentIdx + 1;
    if (next >= exercises.length) {
      saveStats(Math.round(totalScore * 100) / 100, exercises.length);
      setScreen("summary");
    } else { setCurrentIdx(next); setReviewIdx(null); setScreen("quiz"); }
  };
  const handleRestart = () => { setScreen("intro"); setExercises([]); setCurrentIdx(0); setScores({}); setReviewIdx(null); };

  // Review mode: show correction for a past exercise
  const handleReview = (i) => {
    setReviewIdx(i);
    setSidebarOpen(false);
  };

  const ex = exercises[currentIdx];
  const reviewEx = reviewIdx !== null ? exercises[reviewIdx] : null;

  return (
    <div className="flex h-screen" style={{ background: "var(--background)" }}>
      <Sidebar
        screen={screen}
        exercises={exercises}
        currentIdx={currentIdx}
        scores={scores}
        open={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        onReview={handleReview}
        dark={dark}
        toggleDark={toggleDark}
      />

      <div className="flex flex-col flex-1 min-w-0 h-full">
        {/* Mobile top bar */}
        <header className="md:hidden flex items-center gap-3 px-4 py-3 border-b shrink-0"
          style={{ background: "var(--surface)", borderColor: "var(--border)" }}>
          <button onClick={() => setSidebarOpen(true)}
            className="w-9 h-9 flex items-center justify-center rounded-xl transition"
            style={{ color: "var(--muted)" }} aria-label="Open menu">
            <Menu size={20} />
          </button>
          <span className="text-[13px] font-bold tracking-wide" style={{ color: "var(--foreground)" }}>MESIM</span>
        </header>

        <main className="flex-1 h-full overflow-y-auto">
          <div className="px-8 py-10">
            {/* Review overlay banner */}
            {reviewEx && (
              <div className="mb-6 flex items-center justify-between px-4 py-3 rounded-xl border"
                style={{ background: "var(--surface)", borderColor: "var(--border)" }}>
                <span className="text-[13px] font-semibold" style={{ color: "var(--foreground)" }}>
                  Reviewing exercise {reviewIdx + 1}
                </span>
                <button onClick={() => setReviewIdx(null)}
                  className="text-[12px] font-medium px-3 py-1.5 rounded-lg border transition"
                  style={{ color: "var(--muted)", borderColor: "var(--border)" }}>
                  Back
                </button>
              </div>
            )}

            {reviewEx ? (
              <CorrectionScreen
                exercise={reviewEx}
                exScore={scores[reviewIdx]}
                runningScore={Math.round(totalScore * 100) / 100}
                exerciseNum={reviewIdx + 1}
                remaining={0}
                onNext={() => setReviewIdx(null)}
                isLast={false}
              />
            ) : (
              <>
                {screen === "intro"      && <IntroScreen onStart={handleStart} />}
                {screen === "quiz"       && ex && <QuizScreen key={currentIdx} exercise={ex} idx={currentIdx + 1} total={exercises.length} onSubmit={handleSubmit} onSkip={handleSkip} />}
                {screen === "correction" && ex && <CorrectionScreen exercise={ex} exScore={lastScore} runningScore={Math.round(totalScore * 100) / 100} exerciseNum={currentIdx + 1} remaining={exercises.length - currentIdx - 1} onNext={handleNext} isLast={currentIdx + 1 >= exercises.length} />}
                {screen === "summary"    && <SummaryScreen score={Math.round(totalScore * 100) / 100} total={exercises.length} onRestart={handleRestart} />}
              </>
            )}
          </div>
        </main>
      </div>
    </div>
  );
}
