import customtkinter as ctk
import numpy as np
import math
import tkinter as tk
import os, io

# ─── ZINC LIGHT PALETTE ──────────────────────────────────────────────────────
# Background: zinc-50/100  |  Surface: white  |  Muted: zinc-200/300
# Text: zinc-900/700       |  Border: zinc-200 |  Accent: ENSIIE red

BG        = "#f4f4f5"   # zinc-100  — window background
SURFACE   = "#ffffff"   # white     — cards
SURFACE2  = "#fafafa"   # zinc-50   — inner frames
BORDER    = "#e4e4e7"   # zinc-200
MUTED_BG  = "#e4e4e7"   # zinc-200  — pills, muted
TEXT      = "#18181b"   # zinc-900
TEXT_MED  = "#52525b"   # zinc-600
TEXT_LOW  = "#a1a1aa"   # zinc-400
SIDEBAR   = "#ffffff"   # white     — sidebar background
SB_BORDER = "#e4e4e7"   # zinc-200  — sidebar right border
SB_TEXT   = "#18181b"   # zinc-900  — sidebar text
SB_MUTED  = "#71717a"   # zinc-500  — inactive nav
SB_ACTIVE = "#f4f4f5"   # zinc-100  — active nav bg highlight

ACCENT    = "#e11d48"   # rose-600 — ENSIIE red
ACCENT_H  = "#be123c"   # rose-700 — hover
ACCENT_LT = "#fff1f2"   # rose-50  — tint bg

SUCCESS   = "#16a34a"   # green-600
SUCCESS_BG= "#f0fdf4"   # green-50
WARNING   = "#d97706"   # amber-600
WARNING_BG= "#fffbeb"
DANGER    = "#dc2626"   # red-600
DANGER_BG = "#fef2f2"

# ─── HELPER: discrete inverse-CDF sampler ────────────────────────────────────
def generate_discrete_sample(values, probs, N=1):
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

def format_equation(a, b, c):
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
    return fmt(a, "x²", first=True) + fmt(b, "x") + fmt(c, "") + " = 0"

# ─── EXERCISE GENERATORS ─────────────────────────────────────────────────────
def generate_discrete_case1():
    E       = [i for i in range(-9, 10) if i != 0]
    E_small = [1, 2, 3]
    pe = [1/len(E)] * len(E)
    ps = [1/len(E_small)] * len(E_small)
    a = generate_discrete_sample(E, pe)
    b = generate_discrete_sample(E, pe)
    e = generate_discrete_sample(E_small, ps)
    c = (b**2 + e) / (4 * a)
    return a, b, c, b**2 - 4*a*c

def generate_discrete_case2():
    E  = [i for i in range(-9, 10) if i != 0]
    Ep = list(range(1, 10))
    pe = [1/len(E)] * len(E)
    pl = [1/2, 1/36, 1/36, 1/6, 1/36, 1/36, 1/36, 1/36, 1/6]
    e   = generate_discrete_sample(E, pe)
    ell = generate_discrete_sample(Ep, pl)
    x0  = e / math.sqrt(ell)
    a, b, c = 1, -2*x0, x0**2
    return a, b, c, b**2 - 4*a*c

def generate_discrete_case3():
    E       = [i for i in range(-9, 10) if i != 0]
    Ep      = list(range(1, 10))
    E_small = [i for i in range(-3, 4) if i != 0]
    pe  = [1/len(E)] * len(E)
    pEp = [1/len(Ep)] * len(Ep)
    pEs = [1/len(E_small)] * len(E_small)
    pZ  = [1/2 if i == 1 else 1/(2*17) for i in E]
    if generate_discrete_sample([1, 2], [1/2, 1/2]) == 1:
        h  = generate_discrete_sample(E, pe)
        k  = generate_discrete_sample(E, pe)
        ll = generate_discrete_sample(E, pZ)
        x1, x2 = h/ll, k/ll
    else:
        h = generate_discrete_sample(E, pe)
        l = generate_discrete_sample(E_small, pEs)
        e = generate_discrete_sample(Ep, pEp)
        p = generate_discrete_sample(Ep, pEp)
        x1 = (-h - e*math.sqrt(p)) / l
        x2 = (-h + e*math.sqrt(p)) / l
    a, b, c = 1, -(x1+x2), x1*x2
    return a, b, c, b**2 - 4*a*c

def generate_exercise():
    E_set = [1, 2, 3]
    type_probs = [1/len(E_set)] * len(E_set)
    typ = generate_discrete_sample(E_set, type_probs)
    if   typ == 1: return (*generate_discrete_case1(), typ)
    elif typ == 2: return (*generate_discrete_case2(), typ)
    else:          return (*generate_discrete_case3(), typ)

# ─── REUSABLE WIDGETS ────────────────────────────────────────────────────────
class Card(ctk.CTkFrame):
    """White card with border shadow feel."""
    def __init__(self, master, **kw):
        kw.setdefault("fg_color", SURFACE)
        kw.setdefault("corner_radius", 14)
        kw.setdefault("border_width", 1)
        kw.setdefault("border_color", BORDER)
        super().__init__(master, **kw)

class TintCard(ctk.CTkFrame):
    """Lightly tinted accent card (e.g. rose-50 for equation)."""
    def __init__(self, master, tint=ACCENT_LT, **kw):
        kw.setdefault("fg_color", tint)
        kw.setdefault("corner_radius", 14)
        kw.setdefault("border_width", 1)
        kw.setdefault("border_color", "#fecdd3")  # rose-200
        super().__init__(master, **kw)

class PrimaryBtn(ctk.CTkButton):
    def __init__(self, master, **kw):
        kw.setdefault("fg_color", ACCENT)
        kw.setdefault("hover_color", ACCENT_H)
        kw.setdefault("text_color", "#ffffff")
        kw.setdefault("corner_radius", 10)
        kw.setdefault("font", ctk.CTkFont(size=14, weight="bold"))
        kw.setdefault("height", 44)
        super().__init__(master, **kw)

class SecondaryBtn(ctk.CTkButton):
    def __init__(self, master, **kw):
        kw.setdefault("fg_color", SURFACE)
        kw.setdefault("hover_color", MUTED_BG)
        kw.setdefault("text_color", TEXT_MED)
        kw.setdefault("border_width", 1)
        kw.setdefault("border_color", BORDER)
        kw.setdefault("corner_radius", 10)
        kw.setdefault("font", ctk.CTkFont(size=14))
        kw.setdefault("height", 44)
        super().__init__(master, **kw)

class ModernEntry(ctk.CTkEntry):
    def __init__(self, master, **kw):
        kw.setdefault("fg_color", SURFACE)
        kw.setdefault("border_color", BORDER)
        kw.setdefault("border_width", 1)
        kw.setdefault("text_color", TEXT)
        kw.setdefault("placeholder_text_color", TEXT_LOW)
        kw.setdefault("corner_radius", 10)
        kw.setdefault("font", ctk.CTkFont(size=15))
        kw.setdefault("height", 44)
        super().__init__(master, **kw)

class TimerArc(tk.Canvas):
    """Circular countdown arc."""
    def __init__(self, master, size=76, bg=SURFACE, **kw):
        super().__init__(master, width=size, height=size,
                         bg=bg, highlightthickness=0, **kw)
        self.size = size
        self._draw(1.0, "2:00")

    def update_timer(self, fraction, label):
        self.delete("all")
        self._draw(fraction, label)

    def _draw(self, fraction, label):
        s, p = self.size, 8
        self.create_arc(p, p, s-p, s-p, start=90, extent=360,
                        outline=MUTED_BG, width=5, style="arc")
        color = SUCCESS if fraction > 0.4 else WARNING if fraction > 0.15 else DANGER
        self.create_arc(p, p, s-p, s-p, start=90, extent=-(360*fraction),
                        outline=color, width=5, style="arc")
        self.create_text(s//2, s//2, text=label,
                         fill=TEXT, font=("Helvetica", 10, "bold"))

# ─── MAIN APP ────────────────────────────────────────────────────────────────
class ProjectMESIMApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("MESIM · Quadratic Equation Trainer")
        self.geometry("920x660")
        self.minsize(800, 580)
        self.resizable(True, True)

        # Force LIGHT mode so zinc-100 background actually shows as light
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")
        self.configure(fg_color=BG)

        self.exercises     = []
        self.current_ex    = 0
        self.score         = 0.0
        self.timer_running = False
        self.time_left     = 0
        self.TIMER_MAX     = 120

        self._build_sidebar()
        self._build_main()
        self.show_intro()

    # ── Sidebar ──────────────────────────────────────────────────────────────
    def _build_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=220, fg_color=SIDEBAR,
                                    corner_radius=0,
                                    border_width=1, border_color=SB_BORDER)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # ── Logo area
        logo_top = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        logo_top.pack(pady=(28, 0), padx=20)

        self._load_logo(logo_top)

        # App name below logo
        ctk.CTkLabel(self.sidebar, text="MESIM",
                     font=ctk.CTkFont(size=11, weight="bold"),
                     text_color=SB_MUTED).pack(pady=(6, 0))

        # Divider
        ctk.CTkFrame(self.sidebar, height=1, fg_color=BORDER).pack(
            fill="x", padx=20, pady=20)

        # Nav items
        self.nav_items = {}
        for key, icon, label in [
            ("intro", "⊙", "Introduction"),
            ("quiz",  "✏", "Exercises"),
            ("score", "◈", "Results"),
        ]:
            btn_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent",
                                     corner_radius=10)
            btn_frame.pack(fill="x", padx=12, pady=3)
            row = ctk.CTkFrame(btn_frame, fg_color="transparent")
            row.pack(fill="x", padx=10, pady=8)
            icon_lbl = ctk.CTkLabel(row, text=icon, width=24,
                                    font=ctk.CTkFont(size=15),
                                    text_color=SB_MUTED)
            icon_lbl.pack(side="left")
            text_lbl = ctk.CTkLabel(row, text=label,
                                    font=ctk.CTkFont(size=13),
                                    text_color=SB_MUTED, anchor="w")
            text_lbl.pack(side="left", padx=(6, 0))
            self.nav_items[key] = (btn_frame, icon_lbl, text_lbl)

        # Footer
        ctk.CTkLabel(self.sidebar, text="ENSIIE · 2026",
                     font=ctk.CTkFont(size=10),
                     text_color=TEXT_LOW).pack(side="bottom", pady=18)

    def _load_logo(self, parent):
        """Load logo.svg via cairosvg + Pillow, display in sidebar."""
        import cairosvg
        from PIL import Image
        svg_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logo.svg")
        png_bytes = cairosvg.svg2png(url=svg_path, output_width=150, output_height=60)
        pil_img = Image.open(io.BytesIO(png_bytes))
        self._logo_img = ctk.CTkImage(
            light_image=pil_img, dark_image=pil_img, size=(150, 60))
        ctk.CTkLabel(parent, image=self._logo_img, text="").pack()

    def _set_nav(self, active_key):
        for key, (frame, icon_lbl, text_lbl) in self.nav_items.items():
            if key == active_key:
                frame.configure(fg_color=SB_ACTIVE)
                icon_lbl.configure(text_color=ACCENT)
                text_lbl.configure(text_color=TEXT,
                                   font=ctk.CTkFont(size=13, weight="bold"))
            else:
                frame.configure(fg_color="transparent")
                icon_lbl.configure(text_color=SB_MUTED)
                text_lbl.configure(text_color=SB_MUTED,
                                   font=ctk.CTkFont(size=13))

    # ── Main content area ─────────────────────────────────────────────────────
    def _build_main(self):
        self.main = ctk.CTkFrame(self, fg_color=BG, corner_radius=0)
        self.main.pack(side="left", fill="both", expand=True)

    def clear(self):
        self.timer_running = False
        for w in self.main.winfo_children():
            w.destroy()

    def _page_title(self, parent, title, subtitle=""):
        ctk.CTkLabel(parent, text=title,
                     font=ctk.CTkFont(size=26, weight="bold"),
                     text_color=TEXT).pack(anchor="w")
        if subtitle:
            ctk.CTkLabel(parent, text=subtitle,
                         font=ctk.CTkFont(size=13),
                         text_color=TEXT_MED).pack(anchor="w", pady=(2, 0))
        ctk.CTkFrame(parent, height=1, fg_color=BORDER).pack(
            fill="x", pady=(14, 20))

    def _pill(self, parent, text, fg=MUTED_BG, text_color=TEXT_MED):
        f = ctk.CTkFrame(parent, fg_color=fg, corner_radius=20)
        f.pack(side="left", padx=(0, 8))
        ctk.CTkLabel(f, text=text, font=ctk.CTkFont(size=11),
                     text_color=text_color).pack(padx=12, pady=5)

    # ═════════════════════════════════════════════════════════════════════════
    # SCREEN 1 — INTRODUCTION
    # ═════════════════════════════════════════════════════════════════════════
    def show_intro(self):
        self.clear()
        self._set_nav("intro")

        scroll = ctk.CTkScrollableFrame(self.main, fg_color="transparent",
                                        scrollbar_button_color=MUTED_BG,
                                        scrollbar_button_hover_color=BORDER)
        scroll.pack(fill="both", expand=True, padx=36, pady=28)

        self._page_title(scroll, "Quadratic Equation Trainer",
                         "Learn to solve ax² + bx + c = 0 step by step")

        # ── Theory block ──────────────────────────────────────────────────
        theory = Card(scroll)
        theory.pack(fill="x", pady=(0, 18))

        t_inner = ctk.CTkFrame(theory, fg_color="transparent")
        t_inner.pack(padx=24, pady=20, fill="x")

        # Big formula badge
        badge = ctk.CTkFrame(t_inner, fg_color=ACCENT_LT, corner_radius=10,
                             border_width=1, border_color="#fecdd3")
        badge.pack(fill="x", pady=(0, 16))
        ctk.CTkLabel(badge,
                     text="ax² + bx + c = 0",
                     font=ctk.CTkFont(size=20, weight="bold", family="Courier"),
                     text_color=ACCENT).pack(pady=14)

        # Discriminant
        ctk.CTkLabel(t_inner, text="Discriminant",
                     font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=TEXT_LOW).pack(anchor="w")
        ctk.CTkLabel(t_inner, text="Δ  =  b² − 4ac",
                     font=ctk.CTkFont(size=16, weight="bold", family="Courier"),
                     text_color=TEXT).pack(anchor="w", pady=(2, 14))

        # Three cases
        cases = [
            ("Δ < 0", "No real solution",                    DANGER,  DANGER_BG),
            ("Δ = 0", "One solution:   x = −b / (2a)",       WARNING, WARNING_BG),
            ("Δ > 0", "Two solutions:   x₁, x₂ = (−b ± √Δ) / (2a)", SUCCESS, SUCCESS_BG),
        ]
        for disc, desc, col, bg in cases:
            row = ctk.CTkFrame(t_inner, fg_color=bg, corner_radius=10)
            row.pack(fill="x", pady=4)
            inner = ctk.CTkFrame(row, fg_color="transparent")
            inner.pack(fill="x", padx=16, pady=10)
            ctk.CTkLabel(inner, text=disc,
                         font=ctk.CTkFont(size=13, weight="bold", family="Courier"),
                         text_color=col, width=60, anchor="w").pack(side="left")
            ctk.CTkLabel(inner, text="→",
                         font=ctk.CTkFont(size=13),
                         text_color=TEXT_LOW).pack(side="left", padx=8)
            ctk.CTkLabel(inner, text=desc,
                         font=ctk.CTkFont(size=13),
                         text_color=TEXT, anchor="w").pack(side="left")

        # ── Config card ───────────────────────────────────────────────────
        cfg = Card(scroll)
        cfg.pack(fill="x", pady=(0, 18))
        cfg_inner = ctk.CTkFrame(cfg, fg_color="transparent")
        cfg_inner.pack(padx=24, pady=20, fill="x")

        ctk.CTkLabel(cfg_inner, text="Configure your session",
                     font=ctk.CTkFont(size=15, weight="bold"),
                     text_color=TEXT).pack(anchor="w", pady=(0, 4))
        ctk.CTkLabel(cfg_inner, text="Choose how many exercises to generate",
                     font=ctk.CTkFont(size=12),
                     text_color=TEXT_LOW).pack(anchor="w", pady=(0, 14))

        row = ctk.CTkFrame(cfg_inner, fg_color="transparent")
        row.pack(anchor="w")
        self.num_entry = ModernEntry(row, width=100, justify="center",
                                     placeholder_text="5")
        self.num_entry.insert(0, "5")
        self.num_entry.pack(side="left", padx=(0, 12))
        PrimaryBtn(row, text="Start Quiz  →", width=160,
                   command=self.start_quiz).pack(side="left")

        # ── Type distribution pills ───────────────────────────────────────
        pill_row = ctk.CTkFrame(scroll, fg_color="transparent")
        pill_row.pack(anchor="w", pady=(0, 10))
        self._pill(pill_row, "Type 1 · Δ < 0 · 33%",
                   fg=DANGER_BG,  text_color=DANGER)
        self._pill(pill_row, "Type 2 · Δ = 0 · 33%",
                   fg=WARNING_BG, text_color=WARNING)
        self._pill(pill_row, "Type 3 · Δ > 0 · 33%",
                   fg=SUCCESS_BG, text_color=SUCCESS)

    # ═════════════════════════════════════════════════════════════════════════
    # SCREEN 2 — EXERCISE
    # ═════════════════════════════════════════════════════════════════════════
    def start_quiz(self):
        try:
            n = int(self.num_entry.get())
            assert n > 0
        except Exception:
            self.num_entry.delete(0, "end")
            self.num_entry.insert(0, "5")
            return
        self.exercises  = [generate_exercise() for _ in range(n)]
        self.current_ex = 0
        self.score      = 0.0
        self.show_exercise()

    def show_exercise(self):
        self.clear()
        self._set_nav("quiz")
        self.timer_running = True
        self.time_left     = self.TIMER_MAX

        a, b, c, delta, typ = self.exercises[self.current_ex]
        delta = round(delta, 4)
        total = len(self.exercises)
        idx   = self.current_ex + 1

        outer = ctk.CTkFrame(self.main, fg_color="transparent")
        outer.pack(fill="both", expand=True, padx=36, pady=28)

        # ── Top bar ───────────────────────────────────────────────────────
        topbar = ctk.CTkFrame(outer, fg_color="transparent")
        topbar.pack(fill="x", pady=(0, 10))

        # Left: breadcrumb
        left = ctk.CTkFrame(topbar, fg_color="transparent")
        left.pack(side="left", fill="y")
        ctk.CTkLabel(left, text=f"Exercise {idx} / {total}",
                     font=ctk.CTkFont(size=18, weight="bold"),
                     text_color=TEXT).pack(anchor="w")
        ctk.CTkLabel(left, text="Compute Δ and count the solutions",
                     font=ctk.CTkFont(size=12),
                     text_color=TEXT_LOW).pack(anchor="w")

        # Right: timer
        timer_wrap = ctk.CTkFrame(topbar, fg_color=SURFACE,
                                  corner_radius=12,
                                  border_width=1, border_color=BORDER)
        timer_wrap.pack(side="right")
        self.timer_arc = TimerArc(timer_wrap, size=72, bg=SURFACE)
        self.timer_arc.pack(padx=8, pady=8)
        self.run_timer()

        # Progress bar
        pbar = ctk.CTkProgressBar(outer, height=5,
                                   fg_color=MUTED_BG,
                                   progress_color=ACCENT,
                                   corner_radius=3)
        pbar.set((idx - 1) / total)
        pbar.pack(fill="x", pady=(0, 18))

        # ── Equation tint card ────────────────────────────────────────────
        eq_card = TintCard(outer)
        eq_card.pack(fill="x", pady=(0, 14))
        eq_in = ctk.CTkFrame(eq_card, fg_color="transparent")
        eq_in.pack(padx=24, pady=18, fill="x")

        row_eq = ctk.CTkFrame(eq_in, fg_color="transparent")
        row_eq.pack(fill="x")
        ctk.CTkLabel(row_eq, text="Solve:",
                     font=ctk.CTkFont(size=12),
                     text_color=TEXT_MED).pack(side="left", padx=(0, 12))
        ctk.CTkLabel(row_eq,
                     text=format_equation(a, b, c),
                     font=ctk.CTkFont(size=24, weight="bold", family="Courier"),
                     text_color=ACCENT).pack(side="left")

        # Points badge
        pt_badge = ctk.CTkFrame(eq_in, fg_color=MUTED_BG, corner_radius=20)
        pt_badge.pack(anchor="w", pady=(10, 0))
        ctk.CTkLabel(pt_badge, text=f"  Type {typ}  ·  1 point  ",
                     font=ctk.CTkFont(size=11),
                     text_color=TEXT_MED).pack(padx=4, pady=4)

        # ── Answer inputs ─────────────────────────────────────────────────
        ans_card = Card(outer)
        ans_card.pack(fill="x", pady=(0, 18))
        ans_in = ctk.CTkFrame(ans_card, fg_color="transparent")
        ans_in.pack(padx=24, pady=20, fill="x")

        ctk.CTkLabel(ans_in, text="Your answers",
                     font=ctk.CTkFont(size=14, weight="bold"),
                     text_color=TEXT).pack(anchor="w", pady=(0, 14))

        for q_text, attr, ph, pts in [
            ("What is the discriminant  Δ ?", "delta_entry", "e.g.  −3.25", "0.5 pt"),
            ("Number of real solutions (0, 1, or 2) ?", "nsol_entry", "0, 1 or 2", "0.5 pt"),
        ]:
            q_row = ctk.CTkFrame(ans_in, fg_color=SURFACE2, corner_radius=10)
            q_row.pack(fill="x", pady=5)
            q_inner = ctk.CTkFrame(q_row, fg_color="transparent")
            q_inner.pack(fill="x", padx=16, pady=12)

            ctk.CTkLabel(q_inner, text=q_text,
                         font=ctk.CTkFont(size=13),
                         text_color=TEXT, anchor="w").pack(side="left", expand=True,
                                                           fill="x")
            pts_lbl = ctk.CTkFrame(q_inner, fg_color=MUTED_BG, corner_radius=20)
            pts_lbl.pack(side="left", padx=(8, 12))
            ctk.CTkLabel(pts_lbl, text=pts,
                         font=ctk.CTkFont(size=10),
                         text_color=TEXT_MED).pack(padx=8, pady=3)

            entry = ModernEntry(q_inner, width=150, placeholder_text=ph)
            entry.pack(side="left")
            setattr(self, attr, entry)

        # ── Buttons ───────────────────────────────────────────────────────
        btn_row = ctk.CTkFrame(outer, fg_color="transparent")
        btn_row.pack(fill="x")
        PrimaryBtn(btn_row, text="Submit Answer", width=180,
                   command=self.check_answer).pack(side="right")
        SecondaryBtn(btn_row, text="Skip", width=110,
                     command=self._skip).pack(side="right", padx=(0, 10))

    def _skip(self):
        self.timer_running = False
        a, b, c, delta, _ = self.exercises[self.current_ex]
        delta = round(delta, 4)
        nsol = 0 if delta < 0 else (1 if abs(delta) < 1e-9 else 2)
        self.show_correction(a, b, c, delta, nsol, 0.0)

    def run_timer(self):
        if not self.timer_running:
            return
        frac  = self.time_left / self.TIMER_MAX
        mins  = self.time_left // 60
        secs  = self.time_left % 60
        try:
            self.timer_arc.update_timer(frac, f"{mins}:{secs:02d}")
        except Exception:
            return
        if self.time_left > 0:
            self.time_left -= 1
            self.after(1000, self.run_timer)
        else:
            self.timer_running = False
            self.check_answer()

    def check_answer(self):
        self.timer_running = False
        a, b, c, delta, _ = self.exercises[self.current_ex]
        delta = round(delta, 4)
        correct_nsol = 0 if delta < 0 else (1 if abs(delta) < 1e-9 else 2)

        ex_score = 0.0
        try:
            if abs(float(self.delta_entry.get()) - delta) < 0.01:
                ex_score += 0.5
        except Exception:
            pass
        try:
            if int(self.nsol_entry.get()) == correct_nsol:
                ex_score += 0.5
        except Exception:
            pass

        self.score += ex_score
        self.show_correction(a, b, c, delta, correct_nsol, ex_score)

    # ═════════════════════════════════════════════════════════════════════════
    # SCREEN 3 — CORRECTION
    # ═════════════════════════════════════════════════════════════════════════
    def show_correction(self, a, b, c, delta, correct_nsol, ex_score):
        self.clear()
        self._set_nav("quiz")

        scroll = ctk.CTkScrollableFrame(self.main, fg_color="transparent",
                                        scrollbar_button_color=MUTED_BG)
        scroll.pack(fill="both", expand=True, padx=36, pady=28)

        # ── Header row ────────────────────────────────────────────────────
        hdr = ctk.CTkFrame(scroll, fg_color="transparent")
        hdr.pack(fill="x", pady=(0, 4))

        ctk.CTkLabel(hdr,
                     text=f"Exercise {self.current_ex + 1}  ·  Correction",
                     font=ctk.CTkFont(size=22, weight="bold"),
                     text_color=TEXT).pack(side="left")

        # Score badge
        if   ex_score == 1.0: sc_bg, sc_fg = SUCCESS_BG, SUCCESS
        elif ex_score == 0.5: sc_bg, sc_fg = WARNING_BG, WARNING
        else:                 sc_bg, sc_fg = DANGER_BG,  DANGER
        sb = ctk.CTkFrame(hdr, fg_color=sc_bg, corner_radius=20,
                          border_width=1, border_color=sc_fg)
        sb.pack(side="right")
        ctk.CTkLabel(sb, text=f"  {ex_score} / 1 pt  ",
                     font=ctk.CTkFont(size=13, weight="bold"),
                     text_color=sc_fg).pack(padx=6, pady=6)

        ctk.CTkFrame(scroll, height=1, fg_color=BORDER).pack(
            fill="x", pady=(8, 18))

        # ── Equation display ──────────────────────────────────────────────
        eq_card = TintCard(scroll)
        eq_card.pack(fill="x", pady=(0, 12))
        ctk.CTkLabel(eq_card,
                     text=format_equation(a, b, c),
                     font=ctk.CTkFont(size=22, weight="bold", family="Courier"),
                     text_color=ACCENT).pack(padx=24, pady=18)

        # ── Results card ──────────────────────────────────────────────────
        res_card = Card(scroll)
        res_card.pack(fill="x", pady=(0, 12))
        res_in = ctk.CTkFrame(res_card, fg_color="transparent")
        res_in.pack(padx=24, pady=18, fill="x")

        ctk.CTkLabel(res_in, text="Step-by-step solution",
                     font=ctk.CTkFont(size=13, weight="bold"),
                     text_color=TEXT_LOW).pack(anchor="w", pady=(0, 12))

        def result_row(label, value, val_color=TEXT):
            r = ctk.CTkFrame(res_in, fg_color=SURFACE2, corner_radius=8)
            r.pack(fill="x", pady=3)
            ri = ctk.CTkFrame(r, fg_color="transparent")
            ri.pack(fill="x", padx=14, pady=9)
            ctk.CTkLabel(ri, text=label, font=ctk.CTkFont(size=13),
                         text_color=TEXT_MED, anchor="w",
                         width=200).pack(side="left")
            ctk.CTkLabel(ri, text=value,
                         font=ctk.CTkFont(size=13, weight="bold", family="Courier"),
                         text_color=val_color).pack(side="left")

        result_row("Discriminant  Δ =", str(delta))
        result_row("Number of solutions:", str(correct_nsol))

        if correct_nsol == 1:
            x0 = round(-b / (2*a), 6)
            result_row("Solution:", f"x₀ = {x0}", SUCCESS)
        elif correct_nsol == 2:
            sq = math.sqrt(abs(delta))
            x1 = round((-b - sq) / (2*a), 6)
            x2 = round((-b + sq) / (2*a), 6)
            result_row("Solutions:", f"x₁ = {x1}", SUCCESS)
            result_row("",           f"x₂ = {x2}", SUCCESS)

        # Running total
        self.current_ex += 1
        remaining = len(self.exercises) - self.current_ex
        ctk.CTkLabel(scroll,
                     text=f"Running total: {round(self.score, 2)} / {self.current_ex}"
                          f"   ·   {remaining} exercise{'s' if remaining != 1 else ''} remaining",
                     font=ctk.CTkFont(size=12),
                     text_color=TEXT_LOW).pack(anchor="w", pady=(6, 18))

        # Buttons
        btn_row = ctk.CTkFrame(scroll, fg_color="transparent")
        btn_row.pack(fill="x")
        if self.current_ex < len(self.exercises):
            PrimaryBtn(btn_row, text="Next Exercise  →", width=190,
                       command=self.show_exercise).pack(side="right")
        else:
            PrimaryBtn(btn_row, text="See Final Score  →", width=210,
                       command=self.show_summary).pack(side="right")

    # ═════════════════════════════════════════════════════════════════════════
    # SCREEN 4 — SUMMARY
    # ═════════════════════════════════════════════════════════════════════════
    def show_summary(self):
        self.clear()
        self._set_nav("score")

        outer = ctk.CTkFrame(self.main, fg_color="transparent")
        outer.pack(fill="both", expand=True, padx=48, pady=36)

        self._page_title(outer, "Quiz Complete", "Here's how you did")

        total = len(self.exercises)
        score = round(self.score, 2)
        pct   = (score / total * 100) if total else 0

        # ── Score ring ────────────────────────────────────────────────────
        ring_color = SUCCESS if pct >= 80 else WARNING if pct >= 50 else DANGER

        ring_canvas = tk.Canvas(outer, width=170, height=170,
                                bg=BG, highlightthickness=0)
        ring_canvas.pack(pady=(0, 20))
        p = 14
        # track
        ring_canvas.create_oval(p, p, 170-p, 170-p,
                                outline=MUTED_BG, width=12)
        # fill
        extent = -(360 * score / total) if total else 0
        ring_canvas.create_arc(p, p, 170-p, 170-p,
                               start=90, extent=extent,
                               outline=ring_color, width=12, style="arc")
        ring_canvas.create_text(85, 76,
                                text=f"{score}/{total}",
                                fill=TEXT, font=("Helvetica", 22, "bold"))
        ring_canvas.create_text(85, 104,
                                text=f"{pct:.0f}%",
                                fill=TEXT_MED, font=("Helvetica", 13))

        # Verdict
        if pct >= 80:   verdict, v_col = "Excellent!", SUCCESS
        elif pct >= 50: verdict, v_col = "Good effort!", WARNING
        else:           verdict, v_col = "Keep practicing!", DANGER

        ctk.CTkLabel(outer, text=verdict,
                     font=ctk.CTkFont(size=24, weight="bold"),
                     text_color=v_col).pack(pady=(0, 20))

        # ── Stats card ────────────────────────────────────────────────────
        sc = Card(outer)
        sc.pack(fill="x", pady=(0, 24))
        sc_in = ctk.CTkFrame(sc, fg_color="transparent")
        sc_in.pack(padx=24, pady=18, fill="x")

        for label, value in [
            ("Total score",    f"{score} / {total}"),
            ("Percentage",     f"{pct:.1f} %"),
            ("Exercises done", str(total)),
        ]:
            r = ctk.CTkFrame(sc_in, fg_color=SURFACE2, corner_radius=8)
            r.pack(fill="x", pady=4)
            ri = ctk.CTkFrame(r, fg_color="transparent")
            ri.pack(fill="x", padx=16, pady=10)
            ctk.CTkLabel(ri, text=label, font=ctk.CTkFont(size=13),
                         text_color=TEXT_MED, anchor="w").pack(side="left")
            ctk.CTkLabel(ri, text=value,
                         font=ctk.CTkFont(size=14, weight="bold"),
                         text_color=TEXT, anchor="e").pack(side="right")

        # ── Buttons ───────────────────────────────────────────────────────
        btn_row = ctk.CTkFrame(outer, fg_color="transparent")
        btn_row.pack(fill="x")
        PrimaryBtn(btn_row, text="New Quiz", width=150,
                   command=self.show_intro).pack(side="right")
        SecondaryBtn(btn_row, text="Back to Intro", width=160,
                     command=self.show_intro).pack(side="right", padx=(0, 10))


if __name__ == "__main__":
    app = ProjectMESIMApp()
    app.mainloop()
