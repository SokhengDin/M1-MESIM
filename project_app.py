import customtkinter as ctk
import numpy as np
import math
import tkinter as tk
import os, io, json

# ─── PALETTE (light / dark mirrors the web CSS variables) ────────────────────
_LIGHT = dict(
    BG       = "#f4f4f5",   # --background
    FG       = "#18181b",   # --foreground
    SURFACE  = "#ffffff",   # --surface
    SURFACE2 = "#f4f4f5",   # --surface-2
    BORDER   = "#e4e4e7",   # --border
    BORDER2  = "#f1f1f1",   # --border-2
    MUTED    = "#a1a1aa",   # --muted
    ACCENT   = "#e11d48",   # --accent
    ACCENT_H = "#be123c",
    ACCENT_LT= "#fff1f2",
    SIDEBAR  = "#ffffff",
    SB_MUTED = "#71717a",
    SB_ACTIVE= "#f4f4f5",
    TEXT_MED = "#52525b",
    TEXT_LOW = "#a1a1aa",
    MUTED_BG = "#e4e4e7",
)
_DARK = dict(
    BG       = "#18181b",
    FG       = "#f4f4f5",
    SURFACE  = "#27272a",
    SURFACE2 = "#3f3f46",
    BORDER   = "#3f3f46",
    BORDER2  = "#52525b",
    MUTED    = "#71717a",
    ACCENT   = "#fb7185",
    ACCENT_H = "#f43f5e",
    ACCENT_LT= "#2d1219",
    SIDEBAR  = "#27272a",
    SB_MUTED = "#71717a",
    SB_ACTIVE= "#3f3f46",
    TEXT_MED = "#a1a1aa",
    TEXT_LOW = "#71717a",
    MUTED_BG = "#3f3f46",
)

SUCCESS    = "#16a34a"
SUCCESS_BG_L = "#f0fdf4"
SUCCESS_BG_D = "#14532d"
WARNING    = "#d97706"
WARNING_BG_L = "#fffbeb"
WARNING_BG_D = "#451a03"
DANGER     = "#dc2626"
DANGER_BG_L  = "#fef2f2"
DANGER_BG_D  = "#450a0a"

# ─── STATS PERSISTENCE ───────────────────────────────────────────────────────
STATS_PATH = os.path.expanduser("~/.mesim_stats.json")

def load_stats():
    try:
        with open(STATS_PATH) as f:
            return json.load(f)
    except Exception:
        return {"sessions": 0, "total_score": 0.0, "total_exercises": 0, "best_pct": 0.0}

def save_stats(score, total):
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
    return fmt(a, "x\u00b2", first=True) + fmt(b, "x") + fmt(c, "") + " = 0"

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
    def __init__(self, master, app, **kw):
        self._app = app
        kw.setdefault("fg_color", app.c("SURFACE"))
        kw.setdefault("corner_radius", 14)
        kw.setdefault("border_width", 1)
        kw.setdefault("border_color", app.c("BORDER"))
        super().__init__(master, **kw)

class TintCard(ctk.CTkFrame):
    def __init__(self, master, app, **kw):
        kw.setdefault("fg_color", app.c("ACCENT_LT"))
        kw.setdefault("corner_radius", 14)
        kw.setdefault("border_width", 1)
        kw.setdefault("border_color", "#fecdd3" if not app.dark_mode else "#7f1d1d")
        super().__init__(master, **kw)

class PrimaryBtn(ctk.CTkButton):
    def __init__(self, master, app, **kw):
        kw.setdefault("fg_color", app.c("ACCENT"))
        kw.setdefault("hover_color", app.c("ACCENT_H"))
        kw.setdefault("text_color", "#ffffff")
        kw.setdefault("corner_radius", 10)
        kw.setdefault("font", ctk.CTkFont(size=14, weight="bold"))
        kw.setdefault("height", 44)
        super().__init__(master, **kw)

class SecondaryBtn(ctk.CTkButton):
    def __init__(self, master, app, **kw):
        kw.setdefault("fg_color", app.c("SURFACE"))
        kw.setdefault("hover_color", app.c("MUTED_BG"))
        kw.setdefault("text_color", app.c("TEXT_MED"))
        kw.setdefault("border_width", 1)
        kw.setdefault("border_color", app.c("BORDER"))
        kw.setdefault("corner_radius", 10)
        kw.setdefault("font", ctk.CTkFont(size=14))
        kw.setdefault("height", 44)
        super().__init__(master, **kw)

class ModernEntry(ctk.CTkEntry):
    def __init__(self, master, app, **kw):
        self._app = app
        kw.setdefault("fg_color", app.c("SURFACE"))
        kw.setdefault("border_color", app.c("BORDER"))
        kw.setdefault("border_width", 1)
        kw.setdefault("text_color", app.c("FG"))
        kw.setdefault("placeholder_text_color", app.c("TEXT_LOW"))
        kw.setdefault("corner_radius", 10)
        kw.setdefault("font", ctk.CTkFont(size=15))
        kw.setdefault("height", 44)
        super().__init__(master, **kw)

    def flash_error(self):
        """Flash red border for invalid input feedback."""
        orig = self._app.c("BORDER")
        self.configure(border_color=DANGER)
        self.after(600, lambda: self.configure(border_color=orig))

class TimerArc(tk.Canvas):
    """Circular countdown arc."""
    def __init__(self, master, app, size=76, **kw):
        self._app = app
        bg = app.c("SURFACE")
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
                        outline=self._app.c("MUTED_BG"), width=5, style="arc")
        color = SUCCESS if fraction > 0.4 else WARNING if fraction > 0.15 else DANGER
        self.create_arc(p, p, s-p, s-p, start=90, extent=-(360*fraction),
                        outline=color, width=5, style="arc")
        self.create_text(s//2, s//2, text=label,
                         fill=self._app.c("FG"), font=("Helvetica", 10, "bold"))

# ─── MAIN APP ────────────────────────────────────────────────────────────────
class ProjectMESIMApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("MESIM · Quadratic Equation Trainer")
        self.geometry("960x680")
        self.minsize(800, 580)
        self.resizable(True, True)

        self.dark_mode = False
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")
        self.configure(fg_color=self.c("BG"))

        self.exercises      = []
        self.current_ex     = 0
        self.score          = 0.0
        self.timer_running  = False
        self.time_left      = 0
        self.TIMER_MAX      = 120
        # Dot buttons for exercise navigator: list of (canvas, idx)
        self._dot_widgets   = []

        self._build_sidebar()
        self._build_main()
        self.show_intro()

    def c(self, key):
        """Return the current palette colour for the given key."""
        pal = _DARK if self.dark_mode else _LIGHT
        return pal.get(key, "#ff00ff")

    def _success_bg(self): return SUCCESS_BG_D if self.dark_mode else SUCCESS_BG_L
    def _warning_bg(self): return WARNING_BG_D if self.dark_mode else WARNING_BG_L
    def _danger_bg(self):  return DANGER_BG_D  if self.dark_mode else DANGER_BG_L

    # ── Dark-mode toggle ─────────────────────────────────────────────────────
    def toggle_dark(self):
        self.dark_mode = not self.dark_mode
        mode = "dark" if self.dark_mode else "light"
        ctk.set_appearance_mode(mode)
        self._dark_btn.configure(text="☀" if self.dark_mode else "☾")
        # Rebuild whole UI to pick up new colours
        current = self._current_screen
        self.configure(fg_color=self.c("BG"))
        self._rebuild_sidebar()
        if   current == "intro":    self.show_intro()
        elif current == "quiz":     self.show_exercise()
        elif current == "score":    self.show_summary()

    # ── Sidebar ──────────────────────────────────────────────────────────────
    def _build_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=228, fg_color=self.c("SIDEBAR"),
                                    corner_radius=0,
                                    border_width=1, border_color=self.c("BORDER"))
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        self._fill_sidebar()

    def _rebuild_sidebar(self):
        self.sidebar.destroy()
        self._build_sidebar()

    def _fill_sidebar(self):
        # ── Logo area
        logo_top = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        logo_top.pack(pady=(28, 0), padx=20)
        self._load_logo(logo_top)

        # App name
        ctk.CTkLabel(self.sidebar, text="MESIM",
                     font=ctk.CTkFont(size=11, weight="bold"),
                     text_color=self.c("SB_MUTED")).pack(pady=(6, 0))

        # Divider
        ctk.CTkFrame(self.sidebar, height=1, fg_color=self.c("BORDER")).pack(
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
                                    text_color=self.c("SB_MUTED"))
            icon_lbl.pack(side="left")
            text_lbl = ctk.CTkLabel(row, text=label,
                                    font=ctk.CTkFont(size=13),
                                    text_color=self.c("SB_MUTED"), anchor="w")
            text_lbl.pack(side="left", padx=(6, 0))
            self.nav_items[key] = (btn_frame, icon_lbl, text_lbl)

        # ── Exercise navigator dots (shown when quiz is active) ───────────
        self._dots_section = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self._dots_section.pack(fill="x", padx=16, pady=(4, 0))
        self._dots_label = ctk.CTkLabel(self._dots_section,
                                        text="Exercises",
                                        font=ctk.CTkFont(size=10, weight="bold"),
                                        text_color=self.c("TEXT_LOW"))
        self._dots_label.pack(anchor="w", pady=(0, 6))
        self._dots_grid = ctk.CTkFrame(self._dots_section, fg_color="transparent")
        self._dots_grid.pack(anchor="w")
        # Start hidden
        self._dots_section.pack_forget()

        # ── Dark-mode toggle (bottom of sidebar) ─────────────────────────
        bottom_row = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        bottom_row.pack(side="bottom", fill="x", padx=16, pady=18)

        self._dark_btn = ctk.CTkButton(
            bottom_row,
            text="☾" if not self.dark_mode else "☀",
            width=36, height=36,
            corner_radius=8,
            fg_color=self.c("SURFACE2"),
            hover_color=self.c("BORDER"),
            text_color=self.c("FG"),
            font=ctk.CTkFont(size=15),
            command=self.toggle_dark
        )
        self._dark_btn.pack(side="right")

        ctk.CTkLabel(bottom_row, text="ENSIIE · 2026",
                     font=ctk.CTkFont(size=10),
                     text_color=self.c("TEXT_LOW")).pack(side="left")

    def _load_logo(self, parent):
        try:
            import cairosvg
            from PIL import Image
            svg_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logo.svg")
            png_bytes = cairosvg.svg2png(url=svg_path, output_width=150, output_height=60)
            pil_img = Image.open(io.BytesIO(png_bytes))
            self._logo_img = ctk.CTkImage(
                light_image=pil_img, dark_image=pil_img, size=(150, 60))
            ctk.CTkLabel(parent, image=self._logo_img, text="").pack()
        except Exception:
            ctk.CTkLabel(parent, text="MESIM",
                         font=ctk.CTkFont(size=22, weight="bold"),
                         text_color=self.c("ACCENT")).pack()

    def _set_nav(self, active_key):
        self._current_screen = active_key
        for key, (frame, icon_lbl, text_lbl) in self.nav_items.items():
            if key == active_key:
                frame.configure(fg_color=self.c("SB_ACTIVE"))
                icon_lbl.configure(text_color=self.c("ACCENT"))
                text_lbl.configure(text_color=self.c("FG"),
                                   font=ctk.CTkFont(size=13, weight="bold"))
            else:
                frame.configure(fg_color="transparent")
                icon_lbl.configure(text_color=self.c("SB_MUTED"))
                text_lbl.configure(text_color=self.c("SB_MUTED"),
                                   font=ctk.CTkFont(size=13))

    def _update_dots(self, results):
        """Redraw exercise navigator dots from results list.

        results: list of None (pending), float ex_score (done)
        """
        # Rebuild grid
        for w in self._dots_grid.winfo_children():
            w.destroy()

        n = len(results)
        if n == 0:
            self._dots_section.pack_forget()
            return

        self._dots_section.pack(fill="x", padx=16, pady=(4, 0))

        cols = min(n, 7)
        for i, r in enumerate(results):
            col = i % cols
            row = i // cols

            if r is None:
                # Pending
                bg    = self.c("BORDER")
                fg    = self.c("MUTED")
                label = str(i + 1)
            elif r == 1.0:
                bg    = self._success_bg()
                fg    = SUCCESS
                label = "✓"
            elif r == 0.5:
                bg    = self._warning_bg()
                fg    = WARNING
                label = "½"
            else:
                bg    = self._danger_bg()
                fg    = DANGER
                label = "✕"

            is_current = (i == len([x for x in results if x is not None]))

            dot = tk.Canvas(self._dots_grid, width=28, height=28,
                            bg=self.c("SIDEBAR"), highlightthickness=0)
            dot.grid(row=row, column=col, padx=2, pady=2)
            dot.create_oval(2, 2, 26, 26, fill=bg, outline=self.c("ACCENT") if is_current else bg)
            dot.create_text(14, 14, text=label, fill=fg,
                            font=("Helvetica", 9, "bold"))

    # ── Main content area ─────────────────────────────────────────────────────
    def _build_main(self):
        self.main = ctk.CTkFrame(self, fg_color=self.c("BG"), corner_radius=0)
        self.main.pack(side="left", fill="both", expand=True)

    def clear(self):
        self.timer_running = False
        for w in self.main.winfo_children():
            w.destroy()

    def _page_title(self, parent, title, subtitle=""):
        ctk.CTkLabel(parent, text=title,
                     font=ctk.CTkFont(size=26, weight="bold"),
                     text_color=self.c("FG")).pack(anchor="w")
        if subtitle:
            ctk.CTkLabel(parent, text=subtitle,
                         font=ctk.CTkFont(size=13),
                         text_color=self.c("TEXT_MED")).pack(anchor="w", pady=(2, 0))
        ctk.CTkFrame(parent, height=1, fg_color=self.c("BORDER")).pack(
            fill="x", pady=(14, 20))

    def _pill(self, parent, text, fg, text_color):
        f = ctk.CTkFrame(parent, fg_color=fg, corner_radius=20)
        f.pack(side="left", padx=(0, 8))
        ctk.CTkLabel(f, text=text, font=ctk.CTkFont(size=11),
                     text_color=text_color).pack(padx=12, pady=5)

    # ═════════════════════════════════════════════════════════════════════════
    # SCREEN 1 — INTRODUCTION
    # ═════════════════════════════════════════════════════════════════════════
    def show_intro(self):
        self.clear()
        self._current_screen = "intro"
        self._set_nav("intro")
        self._dots_section.pack_forget()

        scroll = ctk.CTkScrollableFrame(self.main, fg_color="transparent",
                                        scrollbar_button_color=self.c("MUTED_BG"),
                                        scrollbar_button_hover_color=self.c("BORDER"))
        scroll.pack(fill="both", expand=True, padx=36, pady=28)

        self._page_title(scroll, "Quadratic Equation Trainer",
                         "Learn to solve ax\u00b2 + bx + c = 0 step by step")

        # ── Session stats bar ──────────────────────────────────────────────
        stats = load_stats()
        if stats["sessions"] > 0:
            stats_card = ctk.CTkFrame(scroll, fg_color=self.c("SURFACE"),
                                      corner_radius=12,
                                      border_width=1, border_color=self.c("BORDER"))
            stats_card.pack(fill="x", pady=(0, 18))
            sc_inner = ctk.CTkFrame(stats_card, fg_color="transparent")
            sc_inner.pack(fill="x", padx=20, pady=14)

            ctk.CTkLabel(sc_inner, text="Your stats",
                         font=ctk.CTkFont(size=12, weight="bold"),
                         text_color=self.c("TEXT_LOW")).pack(anchor="w", pady=(0, 10))

            stat_row = ctk.CTkFrame(sc_inner, fg_color="transparent")
            stat_row.pack(fill="x")

            avg = (stats["total_score"] / stats["total_exercises"] * 100
                   if stats["total_exercises"] else 0)

            for label in [
                f"{stats['sessions']} session{'s' if stats['sessions'] != 1 else ''}",
                f"{stats['total_exercises']} exercises",
                f"{avg:.0f}% avg",
                f"{stats['best_pct']:.0f}% best",
            ]:
                chip = ctk.CTkFrame(stat_row, fg_color=self.c("SURFACE2"),
                                    corner_radius=8)
                chip.pack(side="left", padx=(0, 8))
                ctk.CTkLabel(chip, text=label,
                             font=ctk.CTkFont(size=12, weight="bold"),
                             text_color=self.c("FG")).pack(padx=12, pady=6)

        # ── Theory block ──────────────────────────────────────────────────
        theory = Card(scroll, self)
        theory.pack(fill="x", pady=(0, 18))

        t_inner = ctk.CTkFrame(theory, fg_color="transparent")
        t_inner.pack(padx=24, pady=20, fill="x")

        # Big formula badge
        badge = ctk.CTkFrame(t_inner, fg_color=self.c("ACCENT_LT"), corner_radius=10,
                             border_width=1,
                             border_color="#fecdd3" if not self.dark_mode else "#7f1d1d")
        badge.pack(fill="x", pady=(0, 16))
        ctk.CTkLabel(badge,
                     text="ax\u00b2 + bx + c = 0",
                     font=ctk.CTkFont(size=20, weight="bold", family="Courier"),
                     text_color=self.c("ACCENT")).pack(pady=14)

        # Discriminant
        ctk.CTkLabel(t_inner, text="Discriminant",
                     font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=self.c("TEXT_LOW")).pack(anchor="w")
        ctk.CTkLabel(t_inner, text="\u0394  =  b\u00b2 \u2212 4ac",
                     font=ctk.CTkFont(size=16, weight="bold", family="Courier"),
                     text_color=self.c("FG")).pack(anchor="w", pady=(2, 14))

        # Three cases
        cases = [
            ("\u0394 < 0", "No real solution",
             DANGER,  self._danger_bg()),
            ("\u0394 = 0", "One solution:   x = \u2212b / (2a)",
             WARNING, self._warning_bg()),
            ("\u0394 > 0", "Two solutions:   x\u2081, x\u2082 = (\u2212b \u00b1 \u221a\u0394) / (2a)",
             SUCCESS, self._success_bg()),
        ]
        for disc, desc, col, bg in cases:
            row = ctk.CTkFrame(t_inner, fg_color=bg, corner_radius=10)
            row.pack(fill="x", pady=4)
            inner = ctk.CTkFrame(row, fg_color="transparent")
            inner.pack(fill="x", padx=16, pady=10)
            ctk.CTkLabel(inner, text=disc,
                         font=ctk.CTkFont(size=13, weight="bold", family="Courier"),
                         text_color=col, width=60, anchor="w").pack(side="left")
            ctk.CTkLabel(inner, text="\u2192",
                         font=ctk.CTkFont(size=13),
                         text_color=self.c("TEXT_LOW")).pack(side="left", padx=8)
            ctk.CTkLabel(inner, text=desc,
                         font=ctk.CTkFont(size=13),
                         text_color=self.c("FG"), anchor="w").pack(side="left")

        # ── Config card ───────────────────────────────────────────────────
        cfg = Card(scroll, self)
        cfg.pack(fill="x", pady=(0, 18))
        cfg_inner = ctk.CTkFrame(cfg, fg_color="transparent")
        cfg_inner.pack(padx=24, pady=20, fill="x")

        ctk.CTkLabel(cfg_inner, text="Configure your session",
                     font=ctk.CTkFont(size=15, weight="bold"),
                     text_color=self.c("FG")).pack(anchor="w", pady=(0, 4))
        ctk.CTkLabel(cfg_inner, text="Choose how many exercises to generate",
                     font=ctk.CTkFont(size=12),
                     text_color=self.c("TEXT_LOW")).pack(anchor="w", pady=(0, 14))

        row = ctk.CTkFrame(cfg_inner, fg_color="transparent")
        row.pack(anchor="w")
        self.num_entry = ModernEntry(row, self, width=100, justify="center",
                                    placeholder_text="5")
        self.num_entry.insert(0, "5")
        self.num_entry.pack(side="left", padx=(0, 12))
        self.num_entry.bind("<Return>", lambda _: self.start_quiz())
        PrimaryBtn(row, self, text="Start Quiz  \u2192", width=160,
                   command=self.start_quiz).pack(side="left")

        # ── Type distribution pills ───────────────────────────────────────
        pill_row = ctk.CTkFrame(scroll, fg_color="transparent")
        pill_row.pack(anchor="w", pady=(0, 10))
        self._pill(pill_row, "Type 1 · \u0394 < 0 · 33%",
                   fg=self._danger_bg(),  text_color=DANGER)
        self._pill(pill_row, "Type 2 · \u0394 = 0 · 33%",
                   fg=self._warning_bg(), text_color=WARNING)
        self._pill(pill_row, "Type 3 · \u0394 > 0 · 33%",
                   fg=self._success_bg(), text_color=SUCCESS)

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
            if hasattr(self, "num_entry"):
                self.num_entry.flash_error()
            return
        self.exercises    = [generate_exercise() for _ in range(n)]
        self.current_ex   = 0
        self.score        = 0.0
        self._ex_results  = [None] * n   # track per-exercise scores
        self.show_exercise()

    def show_exercise(self):
        self.clear()
        self._current_screen = "quiz"
        self._set_nav("quiz")
        self.timer_running = True
        self.time_left     = self.TIMER_MAX

        # Update navigator dots
        self._update_dots(self._ex_results)

        a, b, c, delta, typ = self.exercises[self.current_ex]
        delta = round(delta, 4)
        total = len(self.exercises)
        idx   = self.current_ex + 1

        outer = ctk.CTkFrame(self.main, fg_color="transparent")
        outer.pack(fill="both", expand=True, padx=36, pady=28)

        # ── Top bar ───────────────────────────────────────────────────────
        topbar = ctk.CTkFrame(outer, fg_color="transparent")
        topbar.pack(fill="x", pady=(0, 10))

        left = ctk.CTkFrame(topbar, fg_color="transparent")
        left.pack(side="left", fill="y")
        ctk.CTkLabel(left, text=f"Exercise {idx} / {total}",
                     font=ctk.CTkFont(size=18, weight="bold"),
                     text_color=self.c("FG")).pack(anchor="w")
        ctk.CTkLabel(left, text="Compute \u0394 and count the solutions",
                     font=ctk.CTkFont(size=12),
                     text_color=self.c("TEXT_LOW")).pack(anchor="w")

        timer_wrap = ctk.CTkFrame(topbar, fg_color=self.c("SURFACE"),
                                  corner_radius=12,
                                  border_width=1, border_color=self.c("BORDER"))
        timer_wrap.pack(side="right")
        self.timer_arc = TimerArc(timer_wrap, self, size=72)
        self.timer_arc.pack(padx=8, pady=8)
        self.run_timer()

        # Progress bar
        pbar = ctk.CTkProgressBar(outer, height=5,
                                   fg_color=self.c("MUTED_BG"),
                                   progress_color=self.c("ACCENT"),
                                   corner_radius=3)
        pbar.set((idx - 1) / total)
        pbar.pack(fill="x", pady=(0, 18))

        # ── Equation tint card ────────────────────────────────────────────
        eq_card = TintCard(outer, self)
        eq_card.pack(fill="x", pady=(0, 14))
        eq_in = ctk.CTkFrame(eq_card, fg_color="transparent")
        eq_in.pack(padx=24, pady=18, fill="x")

        row_eq = ctk.CTkFrame(eq_in, fg_color="transparent")
        row_eq.pack(fill="x")
        ctk.CTkLabel(row_eq, text="Solve:",
                     font=ctk.CTkFont(size=12),
                     text_color=self.c("TEXT_MED")).pack(side="left", padx=(0, 12))
        ctk.CTkLabel(row_eq,
                     text=format_equation(a, b, c),
                     font=ctk.CTkFont(size=24, weight="bold", family="Courier"),
                     text_color=self.c("ACCENT")).pack(side="left")

        pt_badge = ctk.CTkFrame(eq_in, fg_color=self.c("MUTED_BG"), corner_radius=20)
        pt_badge.pack(anchor="w", pady=(10, 0))
        ctk.CTkLabel(pt_badge, text=f"  Type {typ}  ·  1 point  ",
                     font=ctk.CTkFont(size=11),
                     text_color=self.c("TEXT_MED")).pack(padx=4, pady=4)

        # ── Answer inputs ─────────────────────────────────────────────────
        ans_card = Card(outer, self)
        ans_card.pack(fill="x", pady=(0, 18))
        ans_in = ctk.CTkFrame(ans_card, fg_color="transparent")
        ans_in.pack(padx=24, pady=20, fill="x")

        ctk.CTkLabel(ans_in, text="Your answers",
                     font=ctk.CTkFont(size=14, weight="bold"),
                     text_color=self.c("FG")).pack(anchor="w", pady=(0, 14))

        entries = []
        for q_text, attr, ph, pts in [
            ("What is the discriminant  \u0394 ?", "delta_entry", "e.g.  \u22123.25", "0.5 pt"),
            ("Number of real solutions (0, 1, or 2) ?", "nsol_entry", "0, 1 or 2", "0.5 pt"),
        ]:
            q_row = ctk.CTkFrame(ans_in, fg_color=self.c("SURFACE2"), corner_radius=10)
            q_row.pack(fill="x", pady=5)
            q_inner = ctk.CTkFrame(q_row, fg_color="transparent")
            q_inner.pack(fill="x", padx=16, pady=12)

            ctk.CTkLabel(q_inner, text=q_text,
                         font=ctk.CTkFont(size=13),
                         text_color=self.c("FG"), anchor="w").pack(
                         side="left", expand=True, fill="x")
            pts_lbl = ctk.CTkFrame(q_inner, fg_color=self.c("MUTED_BG"), corner_radius=20)
            pts_lbl.pack(side="left", padx=(8, 12))
            ctk.CTkLabel(pts_lbl, text=pts,
                         font=ctk.CTkFont(size=10),
                         text_color=self.c("TEXT_MED")).pack(padx=8, pady=3)

            entry = ModernEntry(q_inner, self, width=150, placeholder_text=ph)
            entry.pack(side="left")
            setattr(self, attr, entry)
            entries.append(entry)

        # Tab cycles between fields; Enter submits
        def _tab_to_next(_, nxt):
            nxt.focus_set()
            return "break"

        entries[0].bind("<Tab>",    lambda _: _tab_to_next(_, entries[1]))
        entries[1].bind("<Tab>",    lambda _: _tab_to_next(_, entries[0]))
        entries[0].bind("<Return>", lambda _: self.try_submit())
        entries[1].bind("<Return>", lambda _: self.try_submit())

        # ── Buttons ───────────────────────────────────────────────────────
        btn_row = ctk.CTkFrame(outer, fg_color="transparent")
        btn_row.pack(fill="x")
        PrimaryBtn(btn_row, self, text="Submit Answer", width=180,
                   command=self.try_submit).pack(side="right")
        SecondaryBtn(btn_row, self, text="Skip", width=110,
                     command=self._skip).pack(side="right", padx=(0, 10))

        # Focus first entry
        entries[0].focus_set()

    def try_submit(self):
        """Validate entries then submit; flash red border on bad input."""
        d_val = self.delta_entry.get().strip().replace(",", ".")
        n_val = self.nsol_entry.get().strip()
        err = False
        try:
            float(d_val)
        except ValueError:
            self.delta_entry.flash_error()
            err = True
        try:
            v = int(n_val)
            assert v in (0, 1, 2)
        except Exception:
            self.nsol_entry.flash_error()
            err = True
        if not err:
            self.check_answer()

    def _skip(self):
        self.timer_running = False
        a, b, c, delta, _ = self.exercises[self.current_ex]
        delta = round(delta, 4)
        nsol = 0 if delta < 0 else (1 if abs(delta) < 1e-9 else 2)
        self._ex_results[self.current_ex] = 0.0
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
            self.try_submit()

    def check_answer(self):
        self.timer_running = False
        a, b, c, delta, _ = self.exercises[self.current_ex]
        delta = round(delta, 4)
        correct_nsol = 0 if delta < 0 else (1 if abs(delta) < 1e-9 else 2)

        ex_score = 0.0
        try:
            if abs(float(self.delta_entry.get().replace(",", ".")) - delta) < 0.01:
                ex_score += 0.5
        except Exception:
            pass
        try:
            if int(self.nsol_entry.get()) == correct_nsol:
                ex_score += 0.5
        except Exception:
            pass

        self.score += ex_score
        self._ex_results[self.current_ex] = ex_score
        self.show_correction(a, b, c, delta, correct_nsol, ex_score)

    # ═════════════════════════════════════════════════════════════════════════
    # SCREEN 3 — CORRECTION
    # ═════════════════════════════════════════════════════════════════════════
    def show_correction(self, a, b, c, delta, correct_nsol, ex_score):
        self.clear()
        self._current_screen = "quiz"
        self._set_nav("quiz")

        # Update dots now that this exercise is scored
        self._update_dots(self._ex_results)

        scroll = ctk.CTkScrollableFrame(self.main, fg_color="transparent",
                                        scrollbar_button_color=self.c("MUTED_BG"))
        scroll.pack(fill="both", expand=True, padx=36, pady=28)

        # ── Header row ────────────────────────────────────────────────────
        hdr = ctk.CTkFrame(scroll, fg_color="transparent")
        hdr.pack(fill="x", pady=(0, 4))

        ctk.CTkLabel(hdr,
                     text=f"Exercise {self.current_ex + 1}  ·  Correction",
                     font=ctk.CTkFont(size=22, weight="bold"),
                     text_color=self.c("FG")).pack(side="left")

        if   ex_score == 1.0: sc_bg, sc_fg = self._success_bg(), SUCCESS
        elif ex_score == 0.5: sc_bg, sc_fg = self._warning_bg(), WARNING
        else:                 sc_bg, sc_fg = self._danger_bg(),  DANGER
        sb = ctk.CTkFrame(hdr, fg_color=sc_bg, corner_radius=20,
                          border_width=1, border_color=sc_fg)
        sb.pack(side="right")
        ctk.CTkLabel(sb, text=f"  {ex_score} / 1 pt  ",
                     font=ctk.CTkFont(size=13, weight="bold"),
                     text_color=sc_fg).pack(padx=6, pady=6)

        ctk.CTkFrame(scroll, height=1, fg_color=self.c("BORDER")).pack(
            fill="x", pady=(8, 18))

        # ── Equation display ──────────────────────────────────────────────
        eq_card = TintCard(scroll, self)
        eq_card.pack(fill="x", pady=(0, 12))
        ctk.CTkLabel(eq_card,
                     text=format_equation(a, b, c),
                     font=ctk.CTkFont(size=22, weight="bold", family="Courier"),
                     text_color=self.c("ACCENT")).pack(padx=24, pady=18)

        # ── Results card ──────────────────────────────────────────────────
        res_card = Card(scroll, self)
        res_card.pack(fill="x", pady=(0, 12))
        res_in = ctk.CTkFrame(res_card, fg_color="transparent")
        res_in.pack(padx=24, pady=18, fill="x")

        ctk.CTkLabel(res_in, text="Step-by-step solution",
                     font=ctk.CTkFont(size=13, weight="bold"),
                     text_color=self.c("TEXT_LOW")).pack(anchor="w", pady=(0, 12))

        def result_row(label, value, val_color=None):
            if val_color is None: val_color = self.c("FG")
            r = ctk.CTkFrame(res_in, fg_color=self.c("SURFACE2"), corner_radius=8)
            r.pack(fill="x", pady=3)
            ri = ctk.CTkFrame(r, fg_color="transparent")
            ri.pack(fill="x", padx=14, pady=9)
            ctk.CTkLabel(ri, text=label, font=ctk.CTkFont(size=13),
                         text_color=self.c("TEXT_MED"), anchor="w",
                         width=200).pack(side="left")
            ctk.CTkLabel(ri, text=value,
                         font=ctk.CTkFont(size=13, weight="bold", family="Courier"),
                         text_color=val_color).pack(side="left")

        result_row("Discriminant  \u0394 =", str(delta))
        result_row("Number of solutions:", str(correct_nsol))

        if correct_nsol == 1:
            x0 = round(-b / (2*a), 6)
            result_row("Solution:", f"x\u2080 = {x0}", SUCCESS)
        elif correct_nsol == 2:
            sq = math.sqrt(abs(delta))
            x1 = round((-b - sq) / (2*a), 6)
            x2 = round((-b + sq) / (2*a), 6)
            result_row("Solutions:", f"x\u2081 = {x1}", SUCCESS)
            result_row("",           f"x\u2082 = {x2}", SUCCESS)

        # Running total
        self.current_ex += 1
        remaining = len(self.exercises) - self.current_ex
        ctk.CTkLabel(scroll,
                     text=f"Running total: {round(self.score, 2)} / {self.current_ex}"
                          f"   ·   {remaining} exercise{'s' if remaining != 1 else ''} remaining",
                     font=ctk.CTkFont(size=12),
                     text_color=self.c("TEXT_LOW")).pack(anchor="w", pady=(6, 18))

        # Buttons
        btn_row = ctk.CTkFrame(scroll, fg_color="transparent")
        btn_row.pack(fill="x")
        if self.current_ex < len(self.exercises):
            PrimaryBtn(btn_row, self, text="Next Exercise  \u2192", width=190,
                       command=self.show_exercise).pack(side="right")
        else:
            PrimaryBtn(btn_row, self, text="See Final Score  \u2192", width=210,
                       command=self._finish_quiz).pack(side="right")

    def _finish_quiz(self):
        save_stats(self.score, len(self.exercises))
        self.show_summary()

    # ═════════════════════════════════════════════════════════════════════════
    # SCREEN 4 — SUMMARY
    # ═════════════════════════════════════════════════════════════════════════
    def show_summary(self):
        self.clear()
        self._current_screen = "score"
        self._set_nav("score")

        # Keep dots visible (read-only) in summary
        self._update_dots(self._ex_results if hasattr(self, "_ex_results") else [])

        outer = ctk.CTkFrame(self.main, fg_color="transparent")
        outer.pack(fill="both", expand=True, padx=48, pady=36)

        self._page_title(outer, "Quiz Complete", "Here's how you did")

        total = len(self.exercises)
        score = round(self.score, 2)
        pct   = (score / total * 100) if total else 0

        ring_color = SUCCESS if pct >= 80 else WARNING if pct >= 50 else DANGER

        # ── Animated score ring ───────────────────────────────────────────
        RING_SIZE = 170
        ring_canvas = tk.Canvas(outer, width=RING_SIZE, height=RING_SIZE,
                                bg=self.c("BG"), highlightthickness=0)
        ring_canvas.pack(pady=(0, 20))

        p = 14
        target_extent = -(360 * score / total) if total else 0

        # Draw static track
        ring_canvas.create_oval(p, p, RING_SIZE-p, RING_SIZE-p,
                                outline=self.c("MUTED_BG"), width=12)
        # Arc tag so we can delete/redraw only the arc
        ring_canvas.create_arc(p, p, RING_SIZE-p, RING_SIZE-p,
                               start=90, extent=0,
                               outline=ring_color, width=12, style="arc",
                               tags="arc")
        # Text labels
        ring_canvas.create_text(RING_SIZE//2, 76,
                                text=f"{score}/{total}",
                                fill=self.c("FG"),
                                font=("Helvetica", 22, "bold"), tags="score_text")
        ring_canvas.create_text(RING_SIZE//2, 104,
                                text=f"{pct:.0f}%",
                                fill=self.c("TEXT_MED"),
                                font=("Helvetica", 13), tags="pct_text")

        # Animate the arc from 0 → target_extent over ~900 ms (60 steps)
        STEPS = 60
        def _animate(step):
            frac = step / STEPS
            # ease-out cubic
            ease = 1 - (1 - frac) ** 3
            current_ext = target_extent * ease
            ring_canvas.delete("arc")
            ring_canvas.create_arc(p, p, RING_SIZE-p, RING_SIZE-p,
                                   start=90, extent=current_ext,
                                   outline=ring_color, width=12, style="arc",
                                   tags="arc")
            if step < STEPS:
                self.after(15, lambda: _animate(step + 1))

        self.after(100, lambda: _animate(0))

        # Verdict
        if pct >= 80:   verdict, v_col = "Excellent!", SUCCESS
        elif pct >= 50: verdict, v_col = "Good effort!", WARNING
        else:           verdict, v_col = "Keep practicing!", DANGER

        ctk.CTkLabel(outer, text=verdict,
                     font=ctk.CTkFont(size=24, weight="bold"),
                     text_color=v_col).pack(pady=(0, 20))

        # ── Stats card ────────────────────────────────────────────────────
        sc = Card(outer, self)
        sc.pack(fill="x", pady=(0, 24))
        sc_in = ctk.CTkFrame(sc, fg_color="transparent")
        sc_in.pack(padx=24, pady=18, fill="x")

        for label, value in [
            ("Total score",    f"{score} / {total}"),
            ("Percentage",     f"{pct:.1f} %"),
            ("Exercises done", str(total)),
        ]:
            r = ctk.CTkFrame(sc_in, fg_color=self.c("SURFACE2"), corner_radius=8)
            r.pack(fill="x", pady=4)
            ri = ctk.CTkFrame(r, fg_color="transparent")
            ri.pack(fill="x", padx=16, pady=10)
            ctk.CTkLabel(ri, text=label, font=ctk.CTkFont(size=13),
                         text_color=self.c("TEXT_MED"), anchor="w").pack(side="left")
            ctk.CTkLabel(ri, text=value,
                         font=ctk.CTkFont(size=14, weight="bold"),
                         text_color=self.c("FG"), anchor="e").pack(side="right")

        # ── Buttons ───────────────────────────────────────────────────────
        btn_row = ctk.CTkFrame(outer, fg_color="transparent")
        btn_row.pack(fill="x")
        PrimaryBtn(btn_row, self, text="New Quiz", width=150,
                   command=self.show_intro).pack(side="right")
        SecondaryBtn(btn_row, self, text="Back to Intro", width=160,
                     command=self.show_intro).pack(side="right", padx=(0, 10))


if __name__ == "__main__":
    app = ProjectMESIMApp()
    app.mainloop()
