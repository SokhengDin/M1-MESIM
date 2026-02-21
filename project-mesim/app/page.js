"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import Image from "next/image";
import katex from "katex";
import {
  Compass, PenLine, Trophy, ArrowRight, RotateCcw,
  SkipForward, Check, X, Minus, LayoutList, Clock, Menu,
} from "lucide-react";
import {
  generateExercises, countSolutions, computeSolutions, scoreAnswer, fmt4,
} from "@/lib/mesim";

// ── KaTeX ─────────────────────────────────────────────────────────────────────
function KTex({ tex, block = false, className = "" }) {
  const html = katex.renderToString(tex, { throwOnError: false, displayMode: block });
  const Tag = block ? "div" : "span";
  return (
    <Tag
      className={className}
      dangerouslySetInnerHTML={{ __html: html }}
    />
  );
}

/** Build LaTeX string for ax²+bx+c=0 */
function toLatex(a, b, c) {
  a = fmt4(a); b = fmt4(b); c = fmt4(c);
  const parts = [];
  const push = (coef, v, first = false) => {
    if (coef === 0) return;
    const abs = Math.abs(coef);
    const sign = coef < 0 ? "-" : "+";
    const mag = abs === 1 && v ? "" : String(abs);
    parts.push(first
      ? (coef < 0 ? `-${mag}${v}` : `${mag}${v}`)
      : `${sign} ${mag}${v}`);
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
        <circle cx="32" cy="32" r={r} fill="none" stroke="#e4e4e7" strokeWidth="5" />
        <circle cx="32" cy="32" r={r} fill="none" stroke={color} strokeWidth="5"
          strokeDasharray={`${Math.max(0, frac * circ)} ${circ}`} strokeLinecap="round"
          style={{ transition: "stroke-dasharray 0.9s linear, stroke 0.4s" }} />
      </svg>
      <span className="relative text-[11px] font-bold tabular-nums text-zinc-700">
        {m}:{String(s).padStart(2, "0")}
      </span>
    </div>
  );
}

// ── Score ring ────────────────────────────────────────────────────────────────
function ScoreRing({ score, total }) {
  const r = 54, circ = 2 * Math.PI * r;
  const pct = total > 0 ? score / total : 0;
  const color = pct >= 0.8 ? "#16a34a" : pct >= 0.5 ? "#d97706" : "#dc2626";
  return (
    <div className="relative flex items-center justify-center w-36 h-36">
      <svg className="absolute inset-0 -rotate-90" viewBox="0 0 144 144">
        <circle cx="72" cy="72" r={r} fill="none" stroke="#e4e4e7" strokeWidth="10" />
        <circle cx="72" cy="72" r={r} fill="none" stroke={color} strokeWidth="10"
          strokeDasharray={`${pct * circ} ${circ}`} strokeLinecap="round" />
      </svg>
      <div className="relative text-center leading-tight">
        <p className="text-2xl font-bold text-zinc-900">{score}/{total}</p>
        <p className="text-sm text-zinc-400">{Math.round(pct * 100)}%</p>
      </div>
    </div>
  );
}

// ── Sidebar ───────────────────────────────────────────────────────────────────
function Sidebar({ screen, exercises, currentIdx, scores, open, onClose }) {
  const isQuiz = screen === "quiz" || screen === "correction";
  const navItems = [
    { key: "intro",   Icon: Compass,     label: "Introduction" },
    { key: "quiz",    Icon: PenLine,     label: "Exercises"    },
    { key: "summary", Icon: Trophy,      label: "Results"      },
  ];

  return (
    <>
      {/* Mobile backdrop — only rendered when open on small screens */}
      {open && (
        <div
          className="fixed inset-0 z-40 bg-black/40 md:hidden"
          onClick={onClose}
        />
      )}

      <aside
        className="sidebar-nav fixed inset-y-0 left-0 z-50 flex flex-col bg-white border-r border-zinc-200 w-60 shrink-0 h-full overflow-y-auto transition-transform duration-200"
        style={{ transform: open ? "translateX(0)" : "translateX(-100%)" }}
      >
        {/* Logo */}
        <div className="flex flex-col items-center pt-8 pb-1 px-4">
          <Image src="/logo.svg" alt="ENSIIE" width={138} height={55} className="object-contain" priority />
          <span className="mt-2 text-[10px] font-bold tracking-[0.2em] text-zinc-400 uppercase">MESIM</span>
        </div>

        <div className="mx-4 my-4 h-px bg-zinc-100" />

        {/* Main nav */}
        <nav className="flex flex-col gap-1 px-3">
          {navItems.map(({ key, Icon, label }) => {
            const active = key === "quiz" ? isQuiz : screen === key;
            return (
              <div key={key} onClick={onClose} className={`flex items-center gap-2.5 px-3 py-2.5 rounded-xl select-none
                transition-all cursor-default ${active ? "bg-zinc-100 text-zinc-900" : "text-zinc-400 hover:bg-zinc-50"}`}>
                <Icon size={15} className={active ? "text-rose-600" : ""} />
                <span className={`text-[13px] ${active ? "font-semibold" : ""}`}>{label}</span>
              </div>
            );
          })}
        </nav>

        {/* Exercise navigator */}
        {exercises.length > 0 && (
          <>
            <div className="mx-4 my-4 h-px bg-zinc-100" />
            <div className="px-4 flex-1 overflow-y-auto">
              <div className="flex items-center gap-1.5 mb-3">
                <LayoutList size={13} className="text-zinc-400" />
                <span className="text-[11px] font-bold uppercase tracking-widest text-zinc-400">Questions</span>
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

                  const cls = {
                    current: "bg-rose-600 border-rose-600 text-white ring-2 ring-rose-200",
                    correct: "bg-green-50 border-green-200 text-green-600",
                    partial: "bg-amber-50 border-amber-200 text-amber-600",
                    wrong:   "bg-red-50   border-red-200   text-red-500",
                    pending: "bg-zinc-50  border-zinc-200  text-zinc-400",
                  }[state];

                  return (
                    <div key={i} title={`Exercise ${i + 1}`}
                      className={`w-7 h-7 rounded-full border flex items-center justify-center text-[11px] font-bold ${cls}`}>
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
                  { cls: "bg-green-50 border-green-200 text-green-600", Icon: Check,  label: "Correct" },
                  { cls: "bg-amber-50 border-amber-200 text-amber-600", Icon: Minus,  label: "Partial" },
                  { cls: "bg-red-50   border-red-200   text-red-500",   Icon: X,      label: "Wrong"   },
                  { cls: "bg-zinc-50  border-zinc-200  text-zinc-400",  Icon: null,   label: "Pending" },
                ].map(({ cls, Icon: I, label }) => (
                  <div key={label} className="flex items-center gap-2">
                    <div className={`w-4 h-4 rounded-full border flex items-center justify-center ${cls}`}>
                      {I && <I size={9} />}
                    </div>
                    <span className="text-[10px] text-zinc-400">{label}</span>
                  </div>
                ))}
              </div>
            </div>
          </>
        )}

        <div className="mt-auto px-4 pb-6">
          <div className="h-px bg-zinc-100 mb-4" />
          <p className="text-[10px] text-zinc-300 text-center tracking-wide">ENSIIE · MESIM · 2026</p>
        </div>
      </aside>
    </>
  );
}

// ── Generation Details Modal ──────────────────────────────────────────────────
function GenerationDetails() {
  const [open, setOpen] = useState(false);
  const [tab,  setTab]  = useState(1); // 1 | 2 | 3 | "algo"

  const cases = {
    1: {
      label: "Type 1 — Δ < 0",
      color: "text-red-600",
      border: "border-red-200",
      bg: "bg-red-50",
      activeBg: "bg-red-600",
      rows: [
        { label: "Sets",    content: <><KTex tex="\mathbb{E} = \{-9,\ldots,-1,1,\ldots,9\}" />&ensp;<KTex tex="E_s = \{1,2,3\}" /></> },
        { label: "Sample",  content: <><KTex tex="a,b \sim \mathcal{U}(\mathbb{E})" />&ensp;<KTex tex="e \sim \mathcal{U}(E_s)" /></> },
        { label: "Compute", content: <KTex tex="c = \dfrac{b^2 + e}{4a}" /> },
        { label: "Result",  content: <><KTex tex="\Delta = b^2 - 4ac = -e < 0" />&ensp;— always negative</> },
        { label: "Why",     content: "By construction Δ = −e, and e ∈ {1,2,3}, so Δ is always strictly negative." },
      ],
    },
    2: {
      label: "Type 2 — Δ = 0",
      color: "text-amber-600",
      border: "border-amber-200",
      bg: "bg-amber-50",
      activeBg: "bg-amber-500",
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
      label: "Type 3 — Δ > 0",
      color: "text-green-600",
      border: "border-green-200",
      bg: "bg-green-50",
      activeBg: "bg-green-600",
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
      {/* Trigger button */}
      <button
        onClick={() => setOpen(true)}
        className="w-full flex items-center justify-between px-5 py-3.5 rounded-2xl
                   bg-white border border-zinc-200 hover:border-zinc-300 hover:bg-zinc-50
                   transition-all group"
      >
        <div className="flex items-center gap-2.5">
          <span className="text-[13px] font-semibold text-zinc-700">How exercises are generated</span>
          <span className="text-[10px] px-2 py-0.5 rounded-full bg-zinc-100 text-zinc-400 font-medium border border-zinc-200">
            Inverse-CDF method
          </span>
        </div>
        <svg className="w-4 h-4 text-zinc-400 group-hover:text-zinc-600 transition-colors"
          fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M13 16h-1v-4h-1m1-4h.01M12 2a10 10 0 110 20A10 10 0 0112 2z" />
        </svg>
      </button>

      {/* Modal backdrop + panel */}
      {open && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4 md:p-6"
          style={{ backgroundColor: "rgba(0,0,0,0.45)" }}
          onClick={() => setOpen(false)}
        >
          <div
            className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90dvh] flex flex-col overflow-hidden"
            onClick={e => e.stopPropagation()}
          >
            {/* Modal header */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-zinc-100 shrink-0">
              <div className="flex items-center gap-2.5">
                <span className="text-[15px] font-bold text-zinc-900">How exercises are generated</span>
                <span className="text-[10px] px-2 py-0.5 rounded-full bg-zinc-100 text-zinc-400 font-medium border border-zinc-200">
                  Inverse-CDF method
                </span>
              </div>
              <button onClick={() => setOpen(false)}
                className="w-7 h-7 rounded-full flex items-center justify-center text-zinc-400
                           hover:bg-zinc-100 hover:text-zinc-700 transition-colors">
                <svg fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2} className="w-4 h-4">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {/* Modal body — scrollable */}
            <div className="overflow-y-auto px-6 py-5">
              {/* Inverse-CDF core idea */}
              <div className="bg-zinc-50 border border-zinc-100 rounded-xl px-4 py-3 text-[12px] text-zinc-600 leading-relaxed mb-4">
                <span className="font-semibold text-zinc-800">Core idea — Inverse-CDF sampling:&ensp;</span>
                To sample from a discrete distribution with values <KTex tex="(a_1,\ldots,a_n)" /> and probabilities <KTex tex="(p_1,\ldots,p_n)" />,
                compute the CDF <KTex tex="F_k = p_1+\cdots+p_k" />, draw <KTex tex="U\sim\mathcal{U}(]0,1[)" />,
                then return <KTex tex="a_k" /> where <KTex tex="k = \min\{i : U \leq F_i\}" />.
              </div>

              {/* Single tabbed panel — 4 tabs */}
              <div className="rounded-xl border border-zinc-200 overflow-hidden">
                {/* Tab bar */}
                <div className="flex border-b border-zinc-200 bg-zinc-50">
                  {[1, 2, 3].map(t => (
                    <button key={t} onClick={() => setTab(t)}
                      className={`flex-1 py-2.5 text-[12px] font-semibold transition-all border-b-2
                        ${tab === t
                          ? `bg-white border-current ${cases[t].color}`
                          : `border-transparent text-zinc-400 hover:text-zinc-600 hover:bg-zinc-100`}`}>
                      Type {t}&ensp;
                      <span className={`text-[10px] font-normal ${tab === t ? cases[t].color : "text-zinc-300"}`}>
                        {t === 1 ? "Δ < 0" : t === 2 ? "Δ = 0" : "Δ > 0"}
                      </span>
                    </button>
                  ))}
                  <button onClick={() => setTab("algo")}
                    className={`flex-1 py-2.5 text-[12px] font-semibold transition-all border-b-2
                      ${tab === "algo"
                        ? "bg-white border-indigo-500 text-indigo-600"
                        : "border-transparent text-zinc-400 hover:text-zinc-600 hover:bg-zinc-100"}`}>
                    Algorithm
                  </button>
                </div>

                {/* Tab content — case rows */}
                {tab !== "algo" && c && (
                  <div>
                    <div className={`px-4 py-2 ${c.bg} border-b ${c.border}`}>
                      <span className={`text-[11px] font-bold uppercase tracking-widest ${c.color}`}>{c.label}</span>
                    </div>
                    <div className="divide-y divide-zinc-100">
                      {c.rows.map(({ label, content }) => (
                        <div key={label} className="flex gap-4 px-4 py-3 text-[12px] leading-relaxed bg-white">
                          <span className="w-20 shrink-0 font-semibold text-zinc-400 pt-0.5">{label}</span>
                          <span className="text-zinc-700 flex flex-wrap items-center gap-x-1.5 gap-y-1">{content}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Tab content — algorithm */}
                {tab === "algo" && (
                  <div>
                    <div className="bg-zinc-800 px-4 py-2.5">
                      <span className="text-[11px] font-bold uppercase tracking-widest text-zinc-400">Inverse-CDF Sampler</span>
                    </div>
                    <div className="grid grid-cols-2 divide-x divide-zinc-100 border-b border-zinc-100">
                      <div className="px-4 py-2.5 bg-zinc-50 text-[12px] flex items-center gap-2">
                        <span className="font-bold text-rose-500 shrink-0">Input</span>
                        <span className="text-zinc-500">values <KTex tex="(a_1,\ldots,a_n)" />, probs <KTex tex="(p_1,\ldots,p_n)" /></span>
                      </div>
                      <div className="px-4 py-2.5 bg-zinc-50 text-[12px] flex items-center gap-2">
                        <span className="font-bold text-indigo-500 shrink-0">Output</span>
                        <span className="text-zinc-500">sampled value <KTex tex="a_k" /></span>
                      </div>
                    </div>
                    <table className="w-full text-[12px]">
                      <tbody className="divide-y divide-zinc-100">
                        {[
                          { step: "1", keyword: null,     line: <span>Compute CDF:&ensp;<KTex tex="F_k \leftarrow p_1 + \cdots + p_k" />&ensp;for <KTex tex="k = 1, \ldots, n" /></span> },
                          { step: "2", keyword: null,     line: <span>Draw&ensp;<KTex tex="U \sim \mathcal{U}(]0,1[)" /></span> },
                          { step: "3", keyword: null,     line: <span>Set&ensp;<KTex tex="k \leftarrow 0" /></span> },
                          { step: "4", keyword: "while",  line: <span><KTex tex="U > F_k" />&ensp;<span className="text-zinc-400">and</span>&ensp;<KTex tex="k < n" />&ensp;<span className="text-indigo-500 font-semibold">do</span></span> },
                          { step: "",  keyword: null,     line: <KTex tex="k \leftarrow k + 1" />, indent: true },
                          { step: "5", keyword: "return", line: <KTex tex="a_k" /> },
                        ].map(({ step, keyword, line, indent }, i) => (
                          <tr key={i} className={indent ? "bg-zinc-50" : "bg-white"}>
                            <td className="w-8 px-4 py-2.5 text-zinc-300 font-mono text-center select-none">{step}</td>
                            <td className="px-2 py-2.5 w-16">
                              {keyword && <span className="text-indigo-500 font-semibold font-mono">{keyword}</span>}
                            </td>
                            <td className="px-2 py-2.5 text-zinc-700">
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

  return (
    <div className="flex flex-col gap-5">
      <div>
        <h1 className="text-[22px] font-bold text-zinc-900">Quadratic Equation Trainer</h1>
        <p className="text-[13px] text-zinc-400 mt-0.5">Practice solving ax² + bx + c = 0 step by step</p>
        <div className="mt-4 h-px bg-zinc-200" />
      </div>

      {/* Theory */}
      <div className="bg-white rounded-2xl border border-zinc-200 p-6 flex flex-col gap-5">
        <div className="bg-rose-50 border border-rose-100 rounded-xl py-5 flex justify-center overflow-x-auto">
          <KTex tex="ax^2 + bx + c = 0" block />
        </div>

        <div className="flex flex-col items-center gap-1">
          <span className="text-[11px] font-bold uppercase tracking-widest text-zinc-400">Discriminant</span>
          <KTex tex="\Delta = b^2 - 4ac" />
        </div>

        <div className="flex flex-col gap-2">
          {[
            { tex: "\\Delta < 0", desc: "No real solution",                         c: "text-red-600",   bg: "bg-red-50   border-red-100"   },
            { tex: "\\Delta = 0", desc: "One solution:  x = −b / (2a)",             c: "text-amber-600", bg: "bg-amber-50 border-amber-100" },
            { tex: "\\Delta > 0", desc: "Two solutions:  x₁,₂ = (−b ± √Δ) / (2a)", c: "text-green-600", bg: "bg-green-50 border-green-100" },
          ].map(({ tex, desc, c, bg }) => (
            <div key={tex} className={`flex items-center gap-4 rounded-xl border px-4 py-3 ${bg}`}>
              <span className={`font-bold w-16 shrink-0 ${c}`}><KTex tex={tex} /></span>
              <span className="text-zinc-300 text-sm">→</span>
              <span className="text-[13px] text-zinc-700">{desc}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Generation details */}
      <GenerationDetails />

      {/* Config */}
      <div className="bg-white rounded-2xl border border-zinc-200 p-6">
        <p className="text-[14px] font-semibold text-zinc-800 mb-1">Configure your session</p>
        <p className="text-[12px] text-zinc-400 mb-5">Each type has equal probability 1/3</p>
        <div className="flex items-center gap-3">
          <input type="number" min="1" max="100" value={count}
            onChange={e => setCount(e.target.value)}
            onKeyDown={e => e.key === "Enter" && go()}
            className="w-24 h-11 text-center rounded-xl border border-zinc-200 bg-zinc-50
                       text-zinc-900 text-[15px] font-semibold outline-none
                       focus:border-rose-400 focus:ring-2 focus:ring-rose-100 transition" />
          <button onClick={go}
            className="h-11 px-5 rounded-xl bg-rose-600 hover:bg-rose-700 active:scale-[0.97]
                       text-white text-[13px] font-bold flex items-center gap-2 transition-all">
            Start Quiz <ArrowRight size={15} />
          </button>
        </div>
      </div>

      <div className="flex gap-2 flex-wrap">
        {[
          { label: "Type 1 · Δ < 0 · 1/3", c: "text-red-600",   bg: "bg-red-50   border-red-100"   },
          { label: "Type 2 · Δ = 0 · 1/3", c: "text-amber-600", bg: "bg-amber-50 border-amber-100" },
          { label: "Type 3 · Δ > 0 · 1/3", c: "text-green-600", bg: "bg-green-50 border-green-100" },
        ].map(({ label, c, bg }) => (
          <span key={label} className={`text-[11px] px-3 py-1.5 rounded-full border font-medium ${c} ${bg}`}>
            {label}
          </span>
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
  const ans = useRef({ d: "", n: "" });
  useEffect(() => { ans.current = { d: dVal, n: nVal }; }, [dVal, nVal]);

  const submit = useCallback(() => onSubmit(ans.current.d, ans.current.n), [onSubmit]);

  useEffect(() => {
    const id = setInterval(() => setTime(t => {
      if (t <= 1) { clearInterval(id); submit(); return 0; }
      return t - 1;
    }), 1000);
    return () => clearInterval(id);
  }, [submit]);

  return (
    <div className="flex flex-col gap-5">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 className="text-[20px] font-bold text-zinc-900">Exercise {idx} / {total}</h2>
          <p className="text-[12px] text-zinc-400 mt-0.5">Compute Δ then count the solutions</p>
        </div>
        <div className="bg-white border border-zinc-200 rounded-2xl p-2 shadow-sm shrink-0">
          <TimerRing timeLeft={time} />
        </div>
      </div>

      <div className="h-1.5 bg-zinc-200 rounded-full overflow-hidden">
        <div className="h-full bg-rose-500 rounded-full transition-[width] duration-500"
          style={{ width: `${((idx - 1) / total) * 100}%` }} />
      </div>

      {/* Equation */}
      <div className="bg-rose-50 border border-rose-100 rounded-2xl px-6 py-6">
        <p className="text-[10px] font-bold uppercase tracking-[0.15em] text-rose-300 mb-4">Solve</p>
        <div className="flex justify-center py-2 overflow-x-auto">
          <KTex tex={toLatex(a, b, c)} block />
        </div>
        <div className="mt-4 flex gap-2">
          <span className="text-[11px] px-2.5 py-1 rounded-full bg-white border border-rose-100 text-zinc-500">Type {typ}</span>
          <span className="text-[11px] px-2.5 py-1 rounded-full bg-white border border-rose-100 text-zinc-500">1 pt total</span>
        </div>
      </div>

      {/* Inputs */}
      <div className="bg-white rounded-2xl border border-zinc-200 p-6 flex flex-col gap-3">
        <p className="text-[13px] font-semibold text-zinc-800 mb-1">Your answers</p>
        {[
          { label: "Discriminant", katex: "\\Delta", pts: "0.5 pt", val: dVal, set: setDVal, ph: "e.g. −3.25" },
          { label: "Number of solutions (0, 1 or 2)", pts: "0.5 pt", val: nVal, set: setNVal, ph: "0, 1 or 2" },
        ].map(({ label, katex: ktx, pts, val, set, ph }) => (
          <label key={label} className="flex items-center gap-3 bg-zinc-50 border border-zinc-100 rounded-xl px-4 py-3 cursor-text">
            <span className="flex-1 text-[13px] text-zinc-700 flex items-center gap-1 select-none">
              {label}{ktx && <KTex tex={ktx} />} ?
            </span>
            <span className="text-[10px] text-zinc-400 border border-zinc-200 rounded-full px-2 py-0.5 shrink-0">{pts}</span>
            <input value={val} onChange={e => set(e.target.value)} onKeyDown={e => e.key === "Enter" && submit()}
              placeholder={ph}
              className="w-32 h-9 text-center rounded-lg border border-zinc-200 bg-white text-zinc-900 text-[13px]
                         outline-none focus:border-rose-400 focus:ring-2 focus:ring-rose-100 transition" />
          </label>
        ))}
      </div>

      <div className="flex justify-end gap-2.5">
        <button onClick={onSkip}
          className="h-10 px-4 rounded-xl border border-zinc-200 bg-white hover:bg-zinc-50
                     text-zinc-500 text-[13px] font-medium flex items-center gap-1.5 transition">
          <SkipForward size={14} /> Skip
        </button>
        <button onClick={submit}
          className="h-10 px-5 rounded-xl bg-rose-600 hover:bg-rose-700 active:scale-[0.97]
                     text-white text-[13px] font-bold flex items-center gap-2 transition-all">
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

  const badge =
    exScore === 1   ? "bg-green-50 border-green-200 text-green-700" :
    exScore === 0.5 ? "bg-amber-50 border-amber-200 text-amber-700" :
                      "bg-red-50   border-red-200   text-red-700";
  const BadgeIcon = exScore === 1 ? Check : exScore === 0.5 ? Minus : X;

  return (
    <div className="flex flex-col gap-5">
      <div>
        <div className="flex items-center justify-between">
          <h2 className="text-[20px] font-bold text-zinc-900">Exercise {exerciseNum} · Correction</h2>
          <span className={`inline-flex items-center gap-1.5 text-[12px] font-bold px-3 py-1.5 rounded-full border ${badge}`}>
            <BadgeIcon size={12} /> {exScore} / 1 pt
          </span>
        </div>
        <div className="mt-4 h-px bg-zinc-200" />
      </div>

      <div className="bg-rose-50 border border-rose-100 rounded-2xl px-6 py-6">
        <p className="text-[10px] font-bold uppercase tracking-[0.15em] text-rose-300 mb-4">Equation</p>
        <div className="flex justify-center overflow-x-auto">
          <KTex tex={toLatex(a, b, c)} block />
        </div>
      </div>

      <div className="bg-white rounded-2xl border border-zinc-200 p-6">
        <p className="text-[11px] font-bold uppercase tracking-widest text-zinc-400 mb-4">Solution</p>
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
            <div key={i} className="flex items-center gap-4 bg-zinc-50 border border-zinc-100 rounded-xl px-4 py-3">
              <span className="text-[12px] text-zinc-500 w-44 shrink-0 flex items-center gap-1">
                {label}{ktex && <KTex tex={ktex} />}
              </span>
              <span className={`font-mono text-[13px] font-semibold ${green ? "text-green-600" : "text-zinc-800"}`}>
                {value}
              </span>
            </div>
          ))}
        </div>
      </div>

      <p className="text-[12px] text-zinc-400 flex items-center gap-1.5">
        <Clock size={12} />
        Running total: <span className="font-semibold text-zinc-600">{runningScore}</span>
        · {remaining} exercise{remaining !== 1 ? "s" : ""} remaining
      </p>

      <div className="flex justify-end">
        <button onClick={onNext}
          className="h-10 px-5 rounded-xl bg-rose-600 hover:bg-rose-700 active:scale-[0.97]
                     text-white text-[13px] font-bold flex items-center gap-2 transition-all">
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
    pct >= 80 ? { verdict: "Excellent!",       color: "text-green-600" } :
    pct >= 50 ? { verdict: "Good effort!",      color: "text-amber-600" } :
                { verdict: "Keep practicing!",  color: "text-red-600"   };

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-[22px] font-bold text-zinc-900">Quiz Complete</h1>
        <p className="text-[13px] text-zinc-400 mt-0.5">Here&apos;s how you did</p>
        <div className="mt-4 h-px bg-zinc-200" />
      </div>

      <div className="flex flex-col items-center gap-4 py-2">
        <ScoreRing score={score} total={total} />
        <p className={`text-[22px] font-bold ${color}`}>{verdict}</p>
      </div>

      <div className="bg-white rounded-2xl border border-zinc-200 p-6 flex flex-col gap-2">
        {[["Total score", `${score} / ${total}`], ["Percentage", `${pct.toFixed(1)} %`], ["Exercises done", String(total)]].map(([l, v]) => (
          <div key={l} className="flex items-center justify-between bg-zinc-50 border border-zinc-100 rounded-xl px-4 py-3">
            <span className="text-[13px] text-zinc-500">{l}</span>
            <span className="text-[13px] font-bold text-zinc-900">{v}</span>
          </div>
        ))}
      </div>

      <div className="flex justify-end gap-2.5">
        <button onClick={onRestart}
          className="h-10 px-4 rounded-xl border border-zinc-200 bg-white hover:bg-zinc-50
                     text-zinc-500 text-[13px] font-medium transition">
          Back to Intro
        </button>
        <button onClick={onRestart}
          className="h-10 px-5 rounded-xl bg-rose-600 hover:bg-rose-700 active:scale-[0.97]
                     text-white text-[13px] font-bold flex items-center gap-2 transition-all">
          <RotateCcw size={14} /> New Quiz
        </button>
      </div>
    </div>
  );
}

// ── Root ──────────────────────────────────────────────────────────────────────
export default function Home() {
  const [screen,      setScreen]     = useState("intro");
  const [exercises,   setExercises]  = useState([]);
  const [currentIdx,  setCurrentIdx] = useState(0);
  const [scores,      setScores]     = useState({});
  const [lastScore,   setLastScore]  = useState(0);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const totalScore = Object.values(scores).reduce((s, v) => s + v, 0);

  const handleStart   = (n) => { setExercises(generateExercises(n)); setCurrentIdx(0); setScores({}); setScreen("quiz"); };
  const handleSubmit  = (d, n) => {
    const pts = scoreAnswer(exercises[currentIdx], d, n);
    setScores(s => ({ ...s, [currentIdx]: pts }));
    setLastScore(pts);
    setScreen("correction");
  };
  const handleSkip    = () => { setScores(s => ({ ...s, [currentIdx]: 0 })); setLastScore(0); setScreen("correction"); };
  const handleNext    = () => {
    const next = currentIdx + 1;
    if (next >= exercises.length) setScreen("summary");
    else { setCurrentIdx(next); setScreen("quiz"); }
  };
  const handleRestart = () => { setScreen("intro"); setExercises([]); setCurrentIdx(0); setScores({}); };

  const ex = exercises[currentIdx];

  return (
    <div className="flex h-screen bg-zinc-100">
      <Sidebar
        screen={screen}
        exercises={exercises}
        currentIdx={currentIdx}
        scores={scores}
        open={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
      />

      <div className="flex flex-col flex-1 min-w-0 h-full">
        {/* Mobile-only top bar with hamburger */}
        <header className="md:hidden flex items-center gap-3 px-4 py-3 bg-white border-b border-zinc-200 shrink-0">
          <button
            onClick={() => setSidebarOpen(true)}
            className="w-9 h-9 flex items-center justify-center rounded-xl hover:bg-zinc-100 transition text-zinc-500"
            aria-label="Open menu"
          >
            <Menu size={20} />
          </button>
          <span className="text-[13px] font-bold text-zinc-700 tracking-wide">MESIM</span>
        </header>

        <main className="flex-1 h-full overflow-y-auto">
          <div className="px-8 py-10">
            {screen === "intro"      && <IntroScreen onStart={handleStart} />}
            {screen === "quiz"       && ex && <QuizScreen key={currentIdx} exercise={ex} idx={currentIdx + 1} total={exercises.length} onSubmit={handleSubmit} onSkip={handleSkip} />}
            {screen === "correction" && ex && <CorrectionScreen exercise={ex} exScore={lastScore} runningScore={Math.round(totalScore * 100) / 100} exerciseNum={currentIdx + 1} remaining={exercises.length - currentIdx - 1} onNext={handleNext} isLast={currentIdx + 1 >= exercises.length} />}
            {screen === "summary"    && <SummaryScreen score={Math.round(totalScore * 100) / 100} total={exercises.length} onRestart={handleRestart} />}
          </div>
        </main>
      </div>
    </div>
  );
}
