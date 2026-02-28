import math
import os
import io
import tkinter as tk
import customtkinter as ctk

from generators import (
    generate_exercise,
    format_equation,
    load_stats,
    save_stats,
)

# Semantic colours shared between palette-agnostic widgets
SUCCESS = "#16a34a"   # green-600
WARNING = "#d97706"   # amber-600
DANGER  = "#dc2626"   # red-600

# ─── PALETTE (mirrors the web CSS variables exactly) ─────────────────────────
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

SUCCESS_BG_L = "#f0fdf4"
SUCCESS_BG_D = "#14532d"
WARNING_BG_L = "#fffbeb"
WARNING_BG_D = "#451a03"
DANGER_BG_L  = "#fef2f2"
DANGER_BG_D  = "#450a0a"

# ─── REUSABLE WIDGETS ────────────────────────────────────────────────────────

class Card(ctk.CTkFrame):
    """White card with a subtle border — matches web <Card>."""
    def __init__(self, master, app, **kw):
        kw.setdefault("fg_color",     app.c("SURFACE"))
        kw.setdefault("corner_radius", 14)
        kw.setdefault("border_width",  1)
        kw.setdefault("border_color",  app.c("BORDER"))
        super().__init__(master, **kw)


class TintCard(ctk.CTkFrame):
    """Accent-tinted card (rose-50 / dark rose) — matches web <TintCard>."""
    def __init__(self, master, app, **kw):
        kw.setdefault("fg_color",     app.c("ACCENT_LT"))
        kw.setdefault("corner_radius", 14)
        kw.setdefault("border_width",  1)
        kw.setdefault("border_color",  "#fecdd3" if not app.dark_mode else "#7f1d1d")
        super().__init__(master, **kw)


class PrimaryBtn(ctk.CTkButton):
    """Rose filled button."""
    def __init__(self, master, app, **kw):
        kw.setdefault("fg_color",    app.c("ACCENT"))
        kw.setdefault("hover_color", app.c("ACCENT_H"))
        kw.setdefault("text_color",  "#ffffff")
        kw.setdefault("corner_radius", 10)
        kw.setdefault("font",   ctk.CTkFont(size=14, weight="bold"))
        kw.setdefault("height", 44)
        super().__init__(master, **kw)


class SecondaryBtn(ctk.CTkButton):
    """Outlined ghost button."""
    def __init__(self, master, app, **kw):
        kw.setdefault("fg_color",    app.c("SURFACE"))
        kw.setdefault("hover_color", app.c("MUTED_BG"))
        kw.setdefault("text_color",  app.c("TEXT_MED"))
        kw.setdefault("border_width", 1)
        kw.setdefault("border_color", app.c("BORDER"))
        kw.setdefault("corner_radius", 10)
        kw.setdefault("font",   ctk.CTkFont(size=14))
        kw.setdefault("height", 44)
        super().__init__(master, **kw)


class ModernEntry(ctk.CTkEntry):
    """Text entry that can flash its border red on validation error."""
    def __init__(self, master, app, **kw):
        self._app = app
        kw.setdefault("fg_color",              app.c("SURFACE"))
        kw.setdefault("border_color",          app.c("BORDER"))
        kw.setdefault("border_width",          1)
        kw.setdefault("text_color",            app.c("FG"))
        kw.setdefault("placeholder_text_color", app.c("TEXT_LOW"))
        kw.setdefault("corner_radius",         10)
        kw.setdefault("font",   ctk.CTkFont(size=15))
        kw.setdefault("height", 44)
        super().__init__(master, **kw)

    def flash_error(self):
        orig = self._app.c("BORDER")
        self.configure(border_color=DANGER)
        self.after(600, lambda: self.configure(border_color=orig))


class TimerArc(tk.Canvas):
    """Circular countdown arc drawn on a plain tk.Canvas."""
    def __init__(self, master, app, size=76, **kw):
        self._app = app
        super().__init__(master, width=size, height=size,
                         bg=app.c("SURFACE"), highlightthickness=0, **kw)
        self.size = size
        self._draw(1.0, "2:00")

    def update_timer(self, fraction, label):
        self.delete("all")
        self._draw(fraction, label)

    def _draw(self, fraction, label):
        s, p = self.size, 8
        # track ring
        self.create_arc(p, p, s-p, s-p, start=90, extent=360,
                        outline=self._app.c("MUTED_BG"), width=5, style="arc")
        # countdown ring
        color = SUCCESS if fraction > 0.4 else WARNING if fraction > 0.15 else DANGER
        self.create_arc(p, p, s-p, s-p, start=90, extent=-(360 * fraction),
                        outline=color, width=5, style="arc")
        self.create_text(s // 2, s // 2, text=label,
                         fill=self._app.c("FG"), font=("Helvetica", 10, "bold"))


# ─── MAIN APPLICATION ────────────────────────────────────────────────────────

class ProjectMESIMApp(ctk.CTk):
    """Root window — owns all screens and sidebar."""

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
        self._ex_results    = []
        self._current_screen = "intro"

        self._build_sidebar()
        self._build_main()
        self.show_intro()

    # ── Palette helper ────────────────────────────────────────────────────────
    def c(self, key: str) -> str:
        return (_DARK if self.dark_mode else _LIGHT).get(key, "#ff00ff")

    def _success_bg(self): return SUCCESS_BG_D if self.dark_mode else SUCCESS_BG_L
    def _warning_bg(self): return WARNING_BG_D if self.dark_mode else WARNING_BG_L
    def _danger_bg(self):  return DANGER_BG_D  if self.dark_mode else DANGER_BG_L

    # ── Sidebar ───────────────────────────────────────────────────────────────
    def _build_sidebar(self):
        self.sidebar = ctk.CTkFrame(
            self, width=228,
            fg_color=self.c("SIDEBAR"), corner_radius=0,
            border_width=1, border_color=self.c("BORDER"),
        )
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        self._fill_sidebar()

    def _rebuild_sidebar(self):
        self.sidebar.destroy()
        self._build_sidebar()

    def _fill_sidebar(self):
        # Logo
        logo_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        logo_frame.pack(pady=(28, 0), padx=20)
        self._load_logo(logo_frame)

        ctk.CTkLabel(self.sidebar, text="MESIM",
                     font=ctk.CTkFont(size=11, weight="bold"),
                     text_color=self.c("SB_MUTED")).pack(pady=(6, 0))

        # Divider
        ctk.CTkFrame(self.sidebar, height=1,
                     fg_color=self.c("BORDER")).pack(fill="x", padx=20, pady=20)

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

        # Exercise navigator dot grid
        self._dots_section = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self._dots_section.pack(fill="x", padx=16, pady=(4, 0))
        ctk.CTkLabel(self._dots_section, text="Exercises",
                     font=ctk.CTkFont(size=10, weight="bold"),
                     text_color=self.c("TEXT_LOW")).pack(anchor="w", pady=(0, 6))
        self._dots_grid = ctk.CTkFrame(self._dots_section, fg_color="transparent")
        self._dots_grid.pack(anchor="w")
        self._dots_section.pack_forget()   # hidden until quiz starts

        # Footer
        ctk.CTkLabel(self.sidebar, text="ENSIIE · 2026",
                     font=ctk.CTkFont(size=10),
                     text_color=self.c("TEXT_LOW")).pack(side="bottom", pady=18)

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

    def _set_nav(self, active_key: str):
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
        """Redraw the exercise navigator dots.

        results: list where each entry is None (pending) or a float score.
        """
        for w in self._dots_grid.winfo_children():
            w.destroy()

        if not results:
            self._dots_section.pack_forget()
            return

        self._dots_section.pack(fill="x", padx=16, pady=(4, 0))
        done_count = sum(1 for r in results if r is not None)
        cols = min(len(results), 7)

        for i, r in enumerate(results):
            if r is None:
                bg, fg, lbl = self.c("BORDER"), self.c("MUTED"), str(i + 1)
            elif r == 1.0:
                bg, fg, lbl = self._success_bg(), SUCCESS, "✓"
            elif r == 0.5:
                bg, fg, lbl = self._warning_bg(), WARNING, "½"
            else:
                bg, fg, lbl = self._danger_bg(), DANGER, "✕"

            is_current = (i == done_count)
            dot = tk.Canvas(self._dots_grid, width=28, height=28,
                            bg=self.c("SIDEBAR"), highlightthickness=0)
            dot.grid(row=i // cols, column=i % cols, padx=2, pady=2)
            dot.create_oval(2, 2, 26, 26,
                            fill=bg,
                            outline=self.c("ACCENT") if is_current else bg)
            dot.create_text(14, 14, text=lbl, fill=fg,
                            font=("Helvetica", 9, "bold"))

    # ── Main content area ─────────────────────────────────────────────────────
    def _build_main(self):
        self.main = ctk.CTkFrame(self, fg_color=self.c("BG"), corner_radius=0)
        self.main.pack(side="left", fill="both", expand=True)

    def clear(self):
        self.timer_running = False
        for w in self.main.winfo_children():
            w.destroy()

    def _page_title(self, parent, title: str, subtitle: str = ""):
        ctk.CTkLabel(parent, text=title,
                     font=ctk.CTkFont(size=26, weight="bold"),
                     text_color=self.c("FG")).pack(anchor="w")
        if subtitle:
            ctk.CTkLabel(parent, text=subtitle,
                         font=ctk.CTkFont(size=13),
                         text_color=self.c("TEXT_MED")).pack(anchor="w", pady=(2, 0))
        ctk.CTkFrame(parent, height=1,
                     fg_color=self.c("BORDER")).pack(fill="x", pady=(14, 20))

    def _pill(self, parent, text: str, fg: str, text_color: str):
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
        self._dots_section.pack_forget()

        scroll = ctk.CTkScrollableFrame(
            self.main, fg_color="transparent",
            scrollbar_button_color=self.c("MUTED_BG"),
            scrollbar_button_hover_color=self.c("BORDER"),
        )
        scroll.pack(fill="both", expand=True, padx=36, pady=28)

        self._page_title(scroll, "Quadratic Equation Trainer",
                         "Learn to solve ax\u00b2 + bx + c = 0 step by step")

        # ── Session stats bar ─────────────────────────────────────────────
        stats = load_stats()
        if stats["sessions"] > 0:
            sc = ctk.CTkFrame(scroll, fg_color=self.c("SURFACE"),
                              corner_radius=12, border_width=1,
                              border_color=self.c("BORDER"))
            sc.pack(fill="x", pady=(0, 18))
            sc_inner = ctk.CTkFrame(sc, fg_color="transparent")
            sc_inner.pack(fill="x", padx=20, pady=14)
            ctk.CTkLabel(sc_inner, text="Your stats",
                         font=ctk.CTkFont(size=12, weight="bold"),
                         text_color=self.c("TEXT_LOW")).pack(anchor="w", pady=(0, 10))
            row = ctk.CTkFrame(sc_inner, fg_color="transparent")
            row.pack(fill="x")
            avg = (stats["total_score"] / stats["total_exercises"] * 100
                   if stats["total_exercises"] else 0)
            for label in [
                f"{stats['sessions']} session{'s' if stats['sessions'] != 1 else ''}",
                f"{stats['total_exercises']} exercises",
                f"{avg:.0f}% avg",
                f"{stats['best_pct']:.0f}% best",
            ]:
                chip = ctk.CTkFrame(row, fg_color=self.c("SURFACE2"), corner_radius=8)
                chip.pack(side="left", padx=(0, 8))
                ctk.CTkLabel(chip, text=label,
                             font=ctk.CTkFont(size=12, weight="bold"),
                             text_color=self.c("FG")).pack(padx=12, pady=6)

        # ── Theory card ───────────────────────────────────────────────────
        theory = Card(scroll, self)
        theory.pack(fill="x", pady=(0, 18))
        t_inner = ctk.CTkFrame(theory, fg_color="transparent")
        t_inner.pack(padx=24, pady=20, fill="x")

        badge = ctk.CTkFrame(t_inner, fg_color=self.c("ACCENT_LT"), corner_radius=10,
                             border_width=1,
                             border_color="#fecdd3" if not self.dark_mode else "#7f1d1d")
        badge.pack(fill="x", pady=(0, 16))
        ctk.CTkLabel(badge, text="ax\u00b2 + bx + c = 0",
                     font=ctk.CTkFont(size=20, weight="bold", family="Courier"),
                     text_color=self.c("ACCENT")).pack(pady=14)

        ctk.CTkLabel(t_inner, text="Discriminant",
                     font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=self.c("TEXT_LOW")).pack(anchor="w")
        ctk.CTkLabel(t_inner, text="\u0394  =  b\u00b2 \u2212 4ac",
                     font=ctk.CTkFont(size=16, weight="bold", family="Courier"),
                     text_color=self.c("FG")).pack(anchor="w", pady=(2, 14))

        for disc, desc, col, bg in [
            ("\u0394 < 0", "No real solution",
             DANGER,  self._danger_bg()),
            ("\u0394 = 0", "One solution:   x = \u2212b / (2a)",
             WARNING, self._warning_bg()),
            ("\u0394 > 0", "Two solutions:   x\u2081, x\u2082 = (\u2212b \u00b1 \u221a\u0394) / (2a)",
             SUCCESS, self._success_bg()),
        ]:
            r = ctk.CTkFrame(t_inner, fg_color=bg, corner_radius=10)
            r.pack(fill="x", pady=4)
            ri = ctk.CTkFrame(r, fg_color="transparent")
            ri.pack(fill="x", padx=16, pady=10)
            ctk.CTkLabel(ri, text=disc,
                         font=ctk.CTkFont(size=13, weight="bold", family="Courier"),
                         text_color=col, width=60, anchor="w").pack(side="left")
            ctk.CTkLabel(ri, text="\u2192",
                         font=ctk.CTkFont(size=13),
                         text_color=self.c("TEXT_LOW")).pack(side="left", padx=8)
            ctk.CTkLabel(ri, text=desc,
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
        self._pill(pill_row, "Type 1 · \u0394 < 0 · 20%",
                   fg=self._danger_bg(),  text_color=DANGER)
        self._pill(pill_row, "Type 2 · \u0394 = 0 · 40%",
                   fg=self._warning_bg(), text_color=WARNING)
        self._pill(pill_row, "Type 3 · \u0394 > 0 · 40%",
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
            self.num_entry.flash_error()
            return
        self.exercises   = [generate_exercise() for _ in range(n)]
        self.current_ex  = 0
        self.score       = 0.0
        self._ex_results = [None] * n
        self.show_exercise()

    def show_exercise(self):
        self.clear()
        self._set_nav("quiz")
        self.timer_running = True
        self.time_left     = self.TIMER_MAX
        self._update_dots(self._ex_results)

        a, b, c, delta, typ = self.exercises[self.current_ex]
        delta = round(delta, 4)
        total = len(self.exercises)
        idx   = self.current_ex + 1

        outer = ctk.CTkFrame(self.main, fg_color="transparent")
        outer.pack(fill="both", expand=True, padx=36, pady=28)

        # Top bar
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
                                  corner_radius=12, border_width=1,
                                  border_color=self.c("BORDER"))
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

        # Equation card
        eq_card = TintCard(outer, self)
        eq_card.pack(fill="x", pady=(0, 14))
        eq_in = ctk.CTkFrame(eq_card, fg_color="transparent")
        eq_in.pack(padx=24, pady=18, fill="x")
        eq_row = ctk.CTkFrame(eq_in, fg_color="transparent")
        eq_row.pack(fill="x")
        ctk.CTkLabel(eq_row, text="Solve:",
                     font=ctk.CTkFont(size=12),
                     text_color=self.c("TEXT_MED")).pack(side="left", padx=(0, 12))
        ctk.CTkLabel(eq_row, text=format_equation(a, b, c),
                     font=ctk.CTkFont(size=24, weight="bold", family="Courier"),
                     text_color=self.c("ACCENT")).pack(side="left")
        badge = ctk.CTkFrame(eq_in, fg_color=self.c("MUTED_BG"), corner_radius=20)
        badge.pack(anchor="w", pady=(10, 0))
        ctk.CTkLabel(badge, text=f"  Type {typ}  ·  1 point  ",
                     font=ctk.CTkFont(size=11),
                     text_color=self.c("TEXT_MED")).pack(padx=4, pady=4)

        # Answer inputs
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
            ctk.CTkLabel(q_inner, text=q_text, font=ctk.CTkFont(size=13),
                         text_color=self.c("FG"), anchor="w").pack(
                         side="left", expand=True, fill="x")
            pts_f = ctk.CTkFrame(q_inner, fg_color=self.c("MUTED_BG"), corner_radius=20)
            pts_f.pack(side="left", padx=(8, 12))
            ctk.CTkLabel(pts_f, text=pts, font=ctk.CTkFont(size=10),
                         text_color=self.c("TEXT_MED")).pack(padx=8, pady=3)
            entry = ModernEntry(q_inner, self, width=150, placeholder_text=ph)
            entry.pack(side="left")
            setattr(self, attr, entry)
            entries.append(entry)

        # Keyboard navigation
        def _tab_to(_, nxt):
            nxt.focus_set()
            return "break"

        entries[0].bind("<Tab>",    lambda _: _tab_to(_, entries[1]))
        entries[1].bind("<Tab>",    lambda _: _tab_to(_, entries[0]))
        entries[0].bind("<Return>", lambda _: self.try_submit())
        entries[1].bind("<Return>", lambda _: self.try_submit())

        # Action buttons
        btn_row = ctk.CTkFrame(outer, fg_color="transparent")
        btn_row.pack(fill="x")
        PrimaryBtn(btn_row, self, text="Submit Answer", width=180,
                   command=self.try_submit).pack(side="right")
        SecondaryBtn(btn_row, self, text="Skip", width=110,
                     command=self._skip).pack(side="right", padx=(0, 10))

        entries[0].focus_set()

    def try_submit(self):
        """Validate inputs; flash red on errors, submit if all valid."""
        d_val = self.delta_entry.get().strip().replace(",", ".")
        n_val = self.nsol_entry.get().strip()
        err   = False
        try:
            float(d_val)
        except ValueError:
            self.delta_entry.flash_error()
            err = True
        try:
            assert int(n_val) in (0, 1, 2)
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
        frac = self.time_left / self.TIMER_MAX
        mins = self.time_left // 60
        secs = self.time_left % 60
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
        self._set_nav("quiz")
        self._update_dots(self._ex_results)

        scroll = ctk.CTkScrollableFrame(self.main, fg_color="transparent",
                                        scrollbar_button_color=self.c("MUTED_BG"))
        scroll.pack(fill="both", expand=True, padx=36, pady=28)

        # Header
        hdr = ctk.CTkFrame(scroll, fg_color="transparent")
        hdr.pack(fill="x", pady=(0, 4))
        ctk.CTkLabel(hdr, text=f"Exercise {self.current_ex + 1}  ·  Correction",
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

        # Equation
        eq_card = TintCard(scroll, self)
        eq_card.pack(fill="x", pady=(0, 12))
        ctk.CTkLabel(eq_card, text=format_equation(a, b, c),
                     font=ctk.CTkFont(size=22, weight="bold", family="Courier"),
                     text_color=self.c("ACCENT")).pack(padx=24, pady=18)

        # Step-by-step results
        res_card = Card(scroll, self)
        res_card.pack(fill="x", pady=(0, 12))
        res_in = ctk.CTkFrame(res_card, fg_color="transparent")
        res_in.pack(padx=24, pady=18, fill="x")
        ctk.CTkLabel(res_in, text="Step-by-step solution",
                     font=ctk.CTkFont(size=13, weight="bold"),
                     text_color=self.c("TEXT_LOW")).pack(anchor="w", pady=(0, 12))

        def result_row(label, value, val_color=None):
            color = val_color or self.c("FG")
            r = ctk.CTkFrame(res_in, fg_color=self.c("SURFACE2"), corner_radius=8)
            r.pack(fill="x", pady=3)
            ri = ctk.CTkFrame(r, fg_color="transparent")
            ri.pack(fill="x", padx=14, pady=9)
            ctk.CTkLabel(ri, text=label, font=ctk.CTkFont(size=13),
                         text_color=self.c("TEXT_MED"), anchor="w",
                         width=200).pack(side="left")
            ctk.CTkLabel(ri, text=value,
                         font=ctk.CTkFont(size=13, weight="bold", family="Courier"),
                         text_color=color).pack(side="left")

        result_row("Discriminant  \u0394 =", str(delta))
        result_row("Number of solutions:", str(correct_nsol))
        if correct_nsol == 1:
            x0 = round(-b / (2 * a), 6)
            result_row("Solution:", f"x\u2080 = {x0}", SUCCESS)
        elif correct_nsol == 2:
            sq = math.sqrt(abs(delta))
            x1 = round((-b - sq) / (2 * a), 6)
            x2 = round((-b + sq) / (2 * a), 6)
            result_row("Solutions:", f"x\u2081 = {x1}", SUCCESS)
            result_row("",           f"x\u2082 = {x2}", SUCCESS)

        self.current_ex += 1
        remaining = len(self.exercises) - self.current_ex
        ctk.CTkLabel(scroll,
                     text=f"Running total: {round(self.score, 2)} / {self.current_ex}"
                          f"   ·   {remaining} exercise{'s' if remaining != 1 else ''} remaining",
                     font=ctk.CTkFont(size=12),
                     text_color=self.c("TEXT_LOW")).pack(anchor="w", pady=(6, 18))

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
        self._set_nav("score")
        self._update_dots(self._ex_results)

        outer = ctk.CTkFrame(self.main, fg_color="transparent")
        outer.pack(fill="both", expand=True, padx=48, pady=36)

        self._page_title(outer, "Quiz Complete", "Here's how you did")

        total = len(self.exercises)
        score = round(self.score, 2)
        pct   = (score / total * 100) if total else 0
        ring_color = SUCCESS if pct >= 80 else WARNING if pct >= 50 else DANGER

        # Animated score ring
        RS = 170
        ring_canvas = tk.Canvas(outer, width=RS, height=RS,
                                bg=self.c("BG"), highlightthickness=0)
        ring_canvas.pack(pady=(0, 20))
        p = 14
        target_extent = -(360 * score / total) if total else 0

        ring_canvas.create_oval(p, p, RS-p, RS-p,
                                outline=self.c("MUTED_BG"), width=12)
        ring_canvas.create_arc(p, p, RS-p, RS-p, start=90, extent=0,
                               outline=ring_color, width=12, style="arc", tags="arc")
        ring_canvas.create_text(RS//2, 76, text=f"{score}/{total}",
                                fill=self.c("FG"),
                                font=("Helvetica", 22, "bold"))
        ring_canvas.create_text(RS//2, 104, text=f"{pct:.0f}%",
                                fill=self.c("TEXT_MED"), font=("Helvetica", 13))

        STEPS = 60
        def _animate(step):
            ease = 1 - (1 - step / STEPS) ** 3
            ring_canvas.delete("arc")
            ring_canvas.create_arc(p, p, RS-p, RS-p,
                                   start=90, extent=target_extent * ease,
                                   outline=ring_color, width=12, style="arc",
                                   tags="arc")
            if step < STEPS:
                self.after(15, lambda: _animate(step + 1))

        self.after(100, lambda: _animate(0))

        if pct >= 80:   verdict, v_col = "Excellent!", SUCCESS
        elif pct >= 50: verdict, v_col = "Good effort!", WARNING
        else:           verdict, v_col = "Keep practicing!", DANGER
        ctk.CTkLabel(outer, text=verdict,
                     font=ctk.CTkFont(size=24, weight="bold"),
                     text_color=v_col).pack(pady=(0, 20))

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

        btn_row = ctk.CTkFrame(outer, fg_color="transparent")
        btn_row.pack(fill="x")
        PrimaryBtn(btn_row, self, text="New Quiz", width=150,
                   command=self.show_intro).pack(side="right")
        SecondaryBtn(btn_row, self, text="Back to Intro", width=160,
                     command=self.show_intro).pack(side="right", padx=(0, 10))
