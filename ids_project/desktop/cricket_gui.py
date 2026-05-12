import math
import tkinter as tk
from tkinter import ttk
from tkinter import font as tkFont

import pandas as pd

from backend.cricket import CricketAnalyticsEngine
from desktop.gui_extensions import CricketAnalyticsGUI_H2H, CricketAnalyticsGUI_Upset, CricketAnalyticsGUI_Form



class CricketAnalyticsGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Elite Cricket Professional Suite")
        self.root.geometry("1520x940")
        self.root.minsize(1280, 800)
        self.root.configure(bg="#f2efe9")

        self.engine = CricketAnalyticsEngine()
        self.current_page = "dashboard"
        self.sidebar_buttons = {}
        self.page_frames = {}

        self.search_var = tk.StringVar()
        self.player_format_var = tk.StringVar(value="ODI")
        self.player_country_var = tk.StringVar(value="All")
        self.player_query_var = tk.StringVar()
        self.player_select_var = tk.StringVar()
        self.team_format_var = tk.StringVar(value="ODI")
        self.team_query_var = tk.StringVar()
        self.team_select_var = tk.StringVar()
        self.settings_sync_var = tk.BooleanVar(value=True)
        self.settings_model_var = tk.BooleanVar(value=True)
        self.settings_overlay_var = tk.BooleanVar(value=False)
        self.alert_critical_var = tk.BooleanVar(value=True)
        self.alert_roster_var = tk.BooleanVar(value=True)
        self.alert_reports_var = tk.BooleanVar(value=False)
        self.alert_milestone_var = tk.BooleanVar(value=True)

        self.palette = {
            "nav": "#143452",
            "nav_alt": "#0f2b44",
            "nav_active": "#2c6a63",
            "page": "#f4f0ea",
            "card": "#ffffff",
            "mint": "#e7f5ef",
            "mint_soft": "#eef9f3",
            "teal": "#8fd0c8",
            "teal_dark": "#326963",
            "ink": "#0f2440",
            "muted": "#698091",
            "line": "#d7ddd8",
            "gold": "#e8ab49",
            "gold_soft": "#f7edd9",
            "danger": "#c6514d",
        }

        self.fonts = {
            "title": tkFont.Font(family="Segoe UI Semibold", size=18),
            "page_title": tkFont.Font(family="Segoe UI Semibold", size=24),
            "section": tkFont.Font(family="Segoe UI Semibold", size=11),
            "kpi": tkFont.Font(family="Segoe UI Semibold", size=28),
            "body": tkFont.Font(family="Segoe UI", size=10),
            "small": tkFont.Font(family="Segoe UI", size=9),
            "mono": tkFont.Font(family="Consolas", size=10),
        }

        self._configure_style()
        self._build_shell()
        self._build_pages()
        self._show_page("dashboard")

    def _configure_style(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure(
            "Elite.Treeview",
            background="#ffffff",
            fieldbackground="#ffffff",
            foreground=self.palette["ink"],
            rowheight=32,
            borderwidth=0,
            font=("Segoe UI", 10),
        )
        style.configure(
            "Elite.Treeview.Heading",
            background=self.palette["nav"],
            foreground="white",
            font=("Segoe UI Semibold", 10),
            relief="flat",
        )
        style.map("Elite.Treeview", background=[("selected", "#d8f0eb")], foreground=[("selected", self.palette["ink"])])

    def _build_shell(self):
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=1)

        self.sidebar = tk.Frame(self.root, bg=self.palette["nav"], width=300)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)
        self.sidebar.grid_rowconfigure(7, weight=1)

        self.main_shell = tk.Frame(self.root, bg=self.palette["page"])
        self.main_shell.grid(row=0, column=1, sticky="nsew")
        self.main_shell.grid_rowconfigure(1, weight=1)
        self.main_shell.grid_columnconfigure(0, weight=1)

        self._build_sidebar()
        self._build_topbar()

        self.page_container = tk.Frame(self.main_shell, bg=self.palette["page"])
        self.page_container.grid(row=1, column=0, sticky="nsew", padx=22, pady=(14, 20))
        self.page_container.grid_rowconfigure(0, weight=1)
        self.page_container.grid_columnconfigure(0, weight=1)

    def _build_sidebar(self):
        brand = tk.Frame(self.sidebar, bg=self.palette["nav"])
        brand.grid(row=0, column=0, sticky="ew", padx=22, pady=(22, 18))
        logo = tk.Canvas(brand, width=40, height=40, bg="#3c716a", highlightthickness=0)
        logo.create_rectangle(0, 0, 40, 40, fill="#3c716a", outline="")
        logo.create_text(20, 20, text="C", fill="white", font=("Segoe UI Semibold", 18))
        logo.grid(row=0, column=0, rowspan=2, sticky="w")
        tk.Label(brand, text="ELITE CRICKET", bg=self.palette["nav"], fg="white", font=("Segoe UI Semibold", 18)).grid(
            row=0, column=1, sticky="w", padx=(12, 0)
        )
        tk.Label(
            brand,
            text="PROFESSIONAL SUITE",
            bg=self.palette["nav"],
            fg="#9fb1c1",
            font=("Segoe UI", 9),
        ).grid(row=1, column=1, sticky="w", padx=(12, 0))

        items = [
            ("dashboard", "Dashboard"),
            ("live", "Live Scoring"),
            ("teams", "Teams"),
            ("players", "Players"),
            ("h2h", "Head-to-Head"),
            ("upset", "Upset Detector"),
            ("form", "Team Form"),
            ("settings", "Settings"),
        ]
        for idx, (key, label) in enumerate(items, start=1):
            btn = tk.Button(
                self.sidebar,
                text=label,
                bd=0,
                relief="flat",
                anchor="w",
                padx=22,
                pady=16,
                font=("Segoe UI", 11),
                bg=self.palette["nav"],
                fg="#d8e2ec",
                activebackground=self.palette["nav_active"],
                activeforeground="white",
                command=lambda page=key: self._show_page(page),
            )
            btn.grid(row=idx, column=0, sticky="ew", padx=10, pady=4)
            self.sidebar_buttons[key] = btn

        status = tk.Frame(self.sidebar, bg=self.palette["nav_alt"], padx=16, pady=16)
        status.grid(row=8, column=0, sticky="ew", padx=18, pady=(0, 18))
        tk.Label(status, text="SYSTEM STATUS", bg=self.palette["nav_alt"], fg="#9fb1c1", font=("Segoe UI", 9)).pack(anchor="w")
        tk.Label(status, text="Cloud Sync Active", bg=self.palette["nav_alt"], fg="white", font=("Segoe UI Semibold", 11)).pack(
            anchor="w", pady=(10, 0)
        )
        tk.Label(
            status,
            text=f"{self.engine.dataset_summary.total_players} players loaded across ODI, T20I and Test data.",
            wraplength=220,
            justify="left",
            bg=self.palette["nav_alt"],
            fg="#c7d2dc",
            font=("Segoe UI", 9),
        ).pack(anchor="w", pady=(6, 0))

    def _build_topbar(self):
        topbar = tk.Frame(self.main_shell, bg=self.palette["card"], height=74, bd=1, relief="solid")
        topbar.grid(row=0, column=0, sticky="ew")
        topbar.grid_propagate(False)
        topbar.grid_columnconfigure(1, weight=1)

        self.breadcrumb_label = tk.Label(
            topbar,
            text="Dashboard",
            bg=self.palette["card"],
            fg=self.palette["ink"],
            font=("Segoe UI Semibold", 20),
        )
        self.breadcrumb_label.grid(row=0, column=0, sticky="w", padx=(28, 20), pady=18)

        search_box = tk.Frame(topbar, bg="#fbfaf7", bd=1, relief="solid")
        search_box.grid(row=0, column=1, sticky="ew", padx=8, pady=16)
        search_box.grid_columnconfigure(1, weight=1)
        tk.Label(search_box, text="Search analytics...", bg="#fbfaf7", fg="#9aa9b5", font=("Segoe UI", 10)).grid(
            row=0, column=0, sticky="w", padx=(14, 10), pady=10
        )
        entry = tk.Entry(
            search_box,
            textvariable=self.search_var,
            bd=0,
            relief="flat",
            font=("Segoe UI", 11),
            fg=self.palette["ink"],
            bg="#fbfaf7",
        )
        entry.grid(row=0, column=1, sticky="ew", padx=(0, 14), pady=10)
        entry.bind("<Return>", lambda _event: self._run_global_search())

        profile = tk.Frame(topbar, bg=self.palette["card"])
        profile.grid(row=0, column=2, sticky="e", padx=(16, 24))
        tk.Label(profile, text="Marcus V.", bg=self.palette["card"], fg=self.palette["ink"], font=("Segoe UI Semibold", 11)).pack(
            anchor="e"
        )
        tk.Label(profile, text="Lead Analyst", bg=self.palette["card"], fg=self.palette["muted"], font=("Segoe UI", 9)).pack(
            anchor="e"
        )

    def _build_pages(self):
        self.page_frames["dashboard"] = self._build_dashboard_page()
        self.page_frames["live"] = self._build_live_page()
        self.page_frames["teams"] = self._build_teams_page()
        self.page_frames["players"] = self._build_players_page()
        self.page_frames["h2h"] = CricketAnalyticsGUI_H2H(self.page_container, self.engine, self.palette, self.fonts)
        self.page_frames["upset"] = CricketAnalyticsGUI_Upset(self.page_container, self.engine, self.palette, self.fonts)
        self.page_frames["form"] = CricketAnalyticsGUI_Form(self.page_container, self.engine, self.palette, self.fonts)
        self.page_frames["settings"] = self._build_settings_page()

        for frame in self.page_frames.values():
            frame.grid(row=0, column=0, sticky="nsew")

    def _new_page(self):
        page = tk.Frame(self.page_container, bg=self.palette["page"])
        page.grid_rowconfigure(0, weight=1)
        page.grid_columnconfigure(0, weight=1)

        canvas = tk.Canvas(page, bg=self.palette["page"], highlightthickness=0, bd=0)
        vscroll = ttk.Scrollbar(page, orient="vertical", command=canvas.yview)
        inner = tk.Frame(canvas, bg=self.palette["page"])

        canvas.configure(yscrollcommand=vscroll.set)
        canvas.grid(row=0, column=0, sticky="nsew")
        vscroll.grid(row=0, column=1, sticky="ns")

        window_id = canvas.create_window((0, 0), window=inner, anchor="nw")

        def sync_scroll_region(_event=None):
            canvas.configure(scrollregion=canvas.bbox("all"))

        def fit_inner_width(event):
            canvas.itemconfigure(window_id, width=event.width)

        inner.bind("<Configure>", sync_scroll_region)
        canvas.bind("<Configure>", fit_inner_width)
        self._bind_mousewheel(canvas)

        page.scroll_canvas = canvas
        page.inner = inner
        return page

    def _bind_mousewheel(self, widget):
        def _wheel(event):
            if event.delta:
                widget.yview_scroll(int(-event.delta / 120), "units")
            elif getattr(event, "num", None) == 4:
                widget.yview_scroll(-1, "units")
            elif getattr(event, "num", None) == 5:
                widget.yview_scroll(1, "units")

        widget.bind("<MouseWheel>", _wheel)
        widget.bind("<Button-4>", _wheel)
        widget.bind("<Button-5>", _wheel)

    def _show_page(self, page_key):
        self.current_page = page_key
        title_map = {
            "dashboard": "Match Center",
            "live": "Live Scoring Console",
            "teams": "Squad Analytics",
            "players": "Player Intelligence",
            "h2h": "Head-to-Head Predictor",
            "upset": "Upset Detector",
            "form": "Team Form Analyzer",
            "settings": "Account Settings",
        }
        self.breadcrumb_label.config(text=title_map.get(page_key, "Elite Cricket"))
        for key, btn in self.sidebar_buttons.items():
            btn.configure(bg=self.palette["nav_active"] if key == page_key else self.palette["nav"])
        if hasattr(self.page_frames[page_key], 'scroll_canvas'):
            self.page_frames[page_key].scroll_canvas.yview_moveto(0)
        self.page_frames[page_key].tkraise()

    def _card(self, parent, title=None, subtitle=None, bg=None, padx=18, pady=18):
        frame = tk.Frame(parent, bg=bg or self.palette["card"], bd=1, relief="solid", highlightthickness=0)
        if title:
            head = tk.Frame(frame, bg=bg or self.palette["card"])
            head.pack(fill="x", padx=padx, pady=(pady, 8))
            tk.Label(head, text=title.upper(), bg=bg or self.palette["card"], fg=self.palette["ink"], font=self.fonts["section"]).pack(
                anchor="w"
            )
            if subtitle:
                tk.Label(
                    head,
                    text=subtitle,
                    bg=bg or self.palette["card"],
                    fg=self.palette["muted"],
                    font=self.fonts["small"],
                ).pack(anchor="w", pady=(4, 0))
        return frame

    def _metric_card(self, parent, title, value, accent=None, note=None):
        card = self._card(parent, bg=self.palette["card"])
        tk.Label(card, text=title.upper(), bg=self.palette["card"], fg=self.palette["muted"], font=self.fonts["small"]).pack(
            anchor="w", padx=18, pady=(16, 6)
        )
        tk.Label(card, text=value, bg=self.palette["card"], fg=self.palette["ink"], font=("Segoe UI Semibold", 24)).pack(
            anchor="w", padx=18
        )
        if note:
            tk.Label(card, text=note, bg=self.palette["card"], fg=accent or self.palette["teal_dark"], font=("Segoe UI", 10)).pack(
                anchor="w", padx=18, pady=(8, 16)
            )
        else:
            tk.Frame(card, bg=accent or self.palette["teal"], height=4).pack(fill="x", padx=18, pady=(14, 16))
        return card

    def _build_dashboard_page(self):
        page = self._new_page()
        content = tk.Frame(page.inner, bg=self.palette["page"])
        content.grid(row=0, column=0, sticky="nsew")
        content.grid_columnconfigure(0, weight=3)
        content.grid_columnconfigure(1, weight=1)
        content.grid_rowconfigure(1, weight=1)
        content.grid_rowconfigure(2, weight=1)

        summary = self.engine.dataset_summary
        top_strip = tk.Frame(content, bg=self.palette["page"])
        top_strip.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 16))
        top_strip.grid_columnconfigure((0, 1, 2, 3), weight=1)
        metrics = [
            ("Formats", ", ".join(summary.formats), self.palette["teal_dark"]),
            ("Players", f"{summary.total_players}", self.palette["teal_dark"]),
            ("Teams", f"{summary.total_teams}", self.palette["gold"]),
            ("Date Range", summary.date_range, self.palette["teal"]),
        ]
        for col, (title, value, accent) in enumerate(metrics):
            card = self._metric_card(top_strip, title, value, accent=accent)
            card.grid(row=0, column=col, sticky="nsew", padx=(0 if col == 0 else 8, 0), pady=0)

        center = self._card(
            content,
            title="Live Now",
            subtitle="International analytics snapshot based on the loaded ODI, T20I and Test datasets",
            bg=self.palette["mint_soft"],
        )
        center.grid(row=1, column=0, sticky="nsew", padx=(0, 12), pady=(0, 12))
        center_body = tk.Frame(center, bg=self.palette["mint_soft"])
        center_body.pack(fill="both", expand=True, padx=22, pady=(8, 22))
        center_body.grid_columnconfigure((0, 1, 2), weight=1)

        top_team = self.engine.team_summary.sort_values("win_rate", ascending=False).iloc[0]
        tk.Label(
            center_body,
            text=f"{top_team['country']} LEADS",
            bg=self.palette["mint_soft"],
            fg=self.palette["muted"],
            font=("Segoe UI", 12),
        ).grid(row=0, column=0, sticky="w")
        tk.Label(
            center_body,
            text=f"{top_team['win_rate']:.1f}% Win Rate",
            bg=self.palette["mint_soft"],
            fg=self.palette["ink"],
            font=("Segoe UI Semibold", 42),
        ).grid(row=1, column=0, sticky="w", pady=(12, 0))
        tk.Label(
            center_body,
            text=f"Format: {top_team['format']}   Matches: {int(top_team['matches_played'])}",
            bg=self.palette["mint_soft"],
            fg=self.palette["muted"],
            font=("Segoe UI", 12),
        ).grid(row=2, column=0, sticky="w", pady=(8, 0))

        top_player = self.engine.player_summary.sort_values("all_round_impact", ascending=False).iloc[0]
        stat_box = tk.Frame(center_body, bg=self.palette["mint"], bd=1, relief="solid")
        stat_box.grid(row=0, column=2, rowspan=3, sticky="nsew", padx=(16, 0))
        tk.Label(stat_box, text="Top Impact Player", bg=self.palette["mint"], fg=self.palette["muted"], font=self.fonts["small"]).pack(
            anchor="w", padx=16, pady=(16, 6)
        )
        tk.Label(stat_box, text=top_player["player"], bg=self.palette["mint"], fg=self.palette["ink"], font=("Segoe UI Semibold", 20)).pack(
            anchor="w", padx=16
        )
        tk.Label(
            stat_box,
            text=f"{top_player['country']} • {top_player['format']} • {top_player['role']}",
            bg=self.palette["mint"],
            fg=self.palette["muted"],
            font=("Segoe UI", 10),
        ).pack(anchor="w", padx=16, pady=(4, 14))
        tk.Label(
            stat_box,
            text=f"Runs {int(top_player['runs'])}   Wickets {int(top_player['wickets'])}",
            bg=self.palette["mint"],
            fg=self.palette["ink"],
            font=("Segoe UI", 12),
        ).pack(anchor="w", padx=16)
        tk.Label(
            stat_box,
            text=f"Bat Avg {self._fmt(top_player['batting_average'])}   SR {self._fmt(top_player['strike_rate'])}",
            bg=self.palette["mint"],
            fg=self.palette["ink"],
            font=("Segoe UI", 12),
        ).pack(anchor="w", padx=16, pady=(6, 18))

        prob = self._card(content, title="Win Probability", subtitle="Current model-free momentum view from historical team win rates")
        prob.grid(row=1, column=1, sticky="nsew", pady=(0, 12))
        box = tk.Frame(prob, bg=self.palette["card"])
        box.pack(fill="both", expand=True, padx=18, pady=(8, 18))
        team_a = self.engine.team_summary.sort_values("win_rate", ascending=False).iloc[0]
        team_b = self.engine.team_summary.sort_values("win_rate", ascending=False).iloc[1]
        total = team_a["win_rate"] + team_b["win_rate"]
        left_share = team_a["win_rate"] / total if total else 0.5
        tk.Label(box, text=f"{team_a['country']} vs {team_b['country']}", bg=self.palette["card"], fg=self.palette["muted"], font=("Segoe UI", 11)).pack(
            anchor="w", pady=(6, 18)
        )
        bar = tk.Canvas(box, bg=self.palette["card"], height=28, highlightthickness=0)
        bar.pack(fill="x")
        bar.create_rectangle(0, 6, 360, 22, fill="#dfe9e5", outline="")
        bar.create_rectangle(0, 6, int(360 * left_share), 22, fill=self.palette["nav"], outline="")
        bar.create_rectangle(int(360 * left_share), 6, 360, 22, fill=self.palette["teal_dark"], outline="")
        tk.Label(
            box,
            text=f"{team_a['country']} ({team_a['win_rate']:.1f}%)    {team_b['country']} ({team_b['win_rate']:.1f}%)",
            bg=self.palette["card"],
            fg=self.palette["ink"],
            font=("Segoe UI Semibold", 11),
        ).pack(anchor="w", pady=(12, 18))
        tk.Label(
            box,
            text="Historical match results currently favor the first side, but format and venue splits should still be checked in the Teams screen.",
            wraplength=320,
            justify="left",
            bg=self.palette["card"],
            fg=self.palette["muted"],
            font=("Segoe UI", 10),
        ).pack(anchor="w")

        table_card = self._card(content, title="Top Batters", subtitle="Highest run aggregates across the international dataset")
        table_card.grid(row=2, column=0, sticky="nsew", padx=(0, 12))
        self._build_table(
            table_card,
            self.engine.player_summary.sort_values("runs", ascending=False).head(12),
            columns=[
                ("player", 180),
                ("country", 100),
                ("format", 70),
                ("runs", 90),
                ("batting_average", 110),
                ("strike_rate", 100),
            ],
        )

        chart_card = self._card(content, title="Scoring Velocity", subtitle="Format-level batting tempo comparison")
        chart_card.grid(row=2, column=1, sticky="nsew")
        canvas = tk.Canvas(chart_card, bg=self.palette["card"], highlightthickness=0, height=280)
        canvas.pack(fill="both", expand=True, padx=16, pady=16)
        self._draw_format_velocity_chart(canvas)
        return page

    def _build_live_page(self):
        page = self._new_page()
        content = tk.Frame(page.inner, bg=self.palette["page"])
        content.grid(row=0, column=0, sticky="nsew")
        content.grid_columnconfigure(0, weight=3)
        content.grid_columnconfigure(1, weight=2)
        content.grid_rowconfigure(1, weight=1)
        content.grid_rowconfigure(2, weight=1)

        header = self._card(content, bg=self.palette["nav"], title=None)
        header.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 16))
        inner = tk.Frame(header, bg=self.palette["nav"])
        inner.pack(fill="x", padx=24, pady=20)
        tk.Label(inner, text="MATCH DAY 3 | INNINGS 1", bg=self.palette["nav"], fg="#c8d8e3", font=("Segoe UI", 13)).pack(anchor="w")
        tk.Label(inner, text="ENG VS AUS • ASHES SERIES", bg=self.palette["nav"], fg="white", font=("Segoe UI Semibold", 18)).pack(
            anchor="w", pady=(8, 0)
        )
        tk.Label(inner, text="185/6   Overs: 42.4   CRR: 4.33", bg=self.palette["nav"], fg="#dce6ef", font=("Segoe UI", 14)).pack(
            anchor="w", pady=(6, 0)
        )

        scoring = self._card(content, title="Scoring Console", subtitle="Interactive-looking panel for a more professional live dashboard feel")
        scoring.grid(row=1, column=0, sticky="nsew", padx=(0, 12), pady=(0, 12))
        grid = tk.Frame(scoring, bg=self.palette["card"])
        grid.pack(fill="both", expand=True, padx=18, pady=(8, 18))
        for r in range(2):
            grid.grid_rowconfigure(r, weight=1)
        for c in range(6):
            grid.grid_columnconfigure(c, weight=1)
        labels = [("0", "Dot Ball"), ("1", "Single"), ("2", "Double"), ("3", "Triple"), ("4", "Boundary"), ("6", "Maximum")]
        for col, (num, text) in enumerate(labels):
            tile = tk.Frame(grid, bg="#356764", bd=0)
            tile.grid(row=0, column=col, sticky="nsew", padx=8, pady=8)
            tk.Label(tile, text=num, bg="#356764", fg="white", font=("Segoe UI Semibold", 22)).pack(expand=True, pady=(18, 0))
            tk.Label(tile, text=text.upper(), bg="#356764", fg="#d2e7e2", font=("Segoe UI", 10)).pack(pady=(0, 18))
        lower = [("Wide", "+1 Extra", self.palette["nav"]), ("No Ball", "+1 Extra", self.palette["nav"]), ("Bye / LB", "Leg Bye", self.palette["nav"]), ("Wicket", "Dismissal", self.palette["gold"])]
        for col, (num, text, color) in enumerate(lower):
            tile = tk.Frame(grid, bg=color, bd=0)
            tile.grid(row=1, column=col * 6 // 4, columnspan=6 // 4, sticky="nsew", padx=8, pady=8)
            fg = self.palette["ink"] if color == self.palette["gold"] else "white"
            subfg = "#6f4e15" if color == self.palette["gold"] else "#d2e7e2"
            tk.Label(tile, text=num.upper(), bg=color, fg=fg, font=("Segoe UI Semibold", 16)).pack(expand=True, pady=(16, 0))
            tk.Label(tile, text=text.upper(), bg=color, fg=subfg, font=("Segoe UI", 9)).pack(pady=(0, 16))

        momentum = self._card(content, title="Over-By-Over Progress", subtitle="Prototype momentum chart")
        momentum.grid(row=1, column=1, sticky="nsew", pady=(0, 12))
        canvas = tk.Canvas(momentum, bg=self.palette["card"], highlightthickness=0, height=320)
        canvas.pack(fill="both", expand=True, padx=16, pady=16)
        self._draw_over_progress(canvas)

        wagon = self._card(content, title="Wagon Wheel", subtitle="Field-side directional summary")
        wagon.grid(row=2, column=0, sticky="nsew", padx=(0, 12))
        wagon_canvas = tk.Canvas(wagon, bg=self.palette["card"], highlightthickness=0, height=260)
        wagon_canvas.pack(fill="both", expand=True, padx=16, pady=16)
        self._draw_wagon_wheel(wagon_canvas)

        recent = self._card(content, title="Current Over", subtitle="Ball-by-ball strip")
        recent.grid(row=2, column=1, sticky="nsew")
        strip = tk.Frame(recent, bg=self.palette["card"])
        strip.pack(fill="both", expand=True, padx=16, pady=18)
        tk.Label(strip, text="42.4", bg=self.palette["card"], fg=self.palette["ink"], font=("Segoe UI Semibold", 28)).pack(anchor="w")
        tk.Label(strip, text="Last 5 balls", bg=self.palette["card"], fg=self.palette["muted"], font=("Segoe UI", 10)).pack(anchor="w", pady=(0, 16))
        balls = [("1", "#8fd0c8"), ("2", self.palette["nav"]), ("4", "#8fd0c8"), ("6", "#8fd0c8"), ("W", self.palette["gold"])]
        row = tk.Frame(strip, bg=self.palette["card"])
        row.pack(anchor="w")
        for val, color in balls:
            chip = tk.Label(row, text=val, bg=color, fg=self.palette["ink"], width=4, height=2, font=("Segoe UI Semibold", 14))
            chip.pack(side="left", padx=(0, 10))
        return page

    def _build_teams_page(self):
        page = self._new_page()
        content = tk.Frame(page.inner, bg=self.palette["page"])
        content.grid(row=0, column=0, sticky="nsew")
        content.grid_columnconfigure(0, weight=4)
        content.grid_columnconfigure(1, weight=2)
        content.grid_rowconfigure(1, weight=1)

        controls = tk.Frame(content, bg=self.palette["page"])
        controls.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 16))
        tk.Label(controls, text="Format", bg=self.palette["page"], fg=self.palette["ink"], font=("Segoe UI Semibold", 10)).pack(side="left")
        team_format_combo = ttk.Combobox(controls, textvariable=self.team_format_var, values=self.engine.get_formats(), width=10, state="readonly")
        team_format_combo.pack(side="left", padx=(8, 16))
        team_format_combo.bind("<<ComboboxSelected>>", lambda _event: self._refresh_team_select_options())
        tk.Label(controls, text="Team List", bg=self.palette["page"], fg=self.palette["ink"], font=("Segoe UI Semibold", 10)).pack(side="left")
        self.team_select_combo = ttk.Combobox(controls, textvariable=self.team_select_var, width=22, state="readonly")
        self.team_select_combo.pack(side="left", padx=(8, 16))
        self.team_select_combo.bind("<<ComboboxSelected>>", lambda _event: self._select_team_from_dropdown())
        tk.Label(controls, text="Search Team", bg=self.palette["page"], fg=self.palette["ink"], font=("Segoe UI Semibold", 10)).pack(side="left")
        tk.Entry(controls, textvariable=self.team_query_var, font=("Segoe UI", 11), width=28, bd=1, relief="solid").pack(
            side="left", padx=(8, 10)
        )
        tk.Button(
            controls,
            text="Apply Filter",
            command=self._refresh_teams_page,
            bg=self.palette["nav"],
            fg="white",
            bd=0,
            padx=18,
            pady=10,
            font=("Segoe UI Semibold", 10),
        ).pack(side="left")

        roster = self._card(content, title="Squad Analytics", subtitle="Country comparison table with format filters")
        roster.grid(row=1, column=0, sticky="nsew", padx=(0, 12))
        roster.grid_rowconfigure(1, weight=1)
        roster.grid_columnconfigure(0, weight=1)

        top_metrics = tk.Frame(roster, bg=self.palette["card"])
        top_metrics.pack(fill="x", padx=18, pady=(8, 12))
        top_metrics.grid_columnconfigure((0, 1, 2, 3), weight=1)
        self.team_metric_labels = []
        for idx, label in enumerate(["Average Win %", "Top Bat Avg", "Top Bowl Econ", "Loaded Teams"]):
            card = self._metric_card(top_metrics, label, "--", accent=self.palette["teal"])
            card.grid(row=0, column=idx, sticky="nsew", padx=(0 if idx == 0 else 8, 0))
            self.team_metric_labels.append(card)

        self.team_tree = self._build_table(
            roster,
            pd.DataFrame(),
            columns=[
                ("country", 140),
                ("matches_played", 90),
                ("wins", 70),
                ("losses", 70),
                ("win_rate", 90),
                ("batting_average", 95),
                ("batting_runs_per_over", 95),
                ("bowling_average", 95),
            ],
            return_tree=True,
        )
        self.team_tree.bind("<<TreeviewSelect>>", lambda _event: self._update_team_side_panel())

        side = tk.Frame(content, bg=self.palette["page"])
        side.grid(row=1, column=1, sticky="nsew")
        side.grid_rowconfigure((0, 1, 2), weight=1)
        side.grid_columnconfigure(0, weight=1)

        self.team_overview_card = self._card(side, title="Team Overview", subtitle="Select a team from the table to view details")
        self.team_overview_card.grid(row=0, column=0, sticky="nsew", pady=(0, 12))
        self.team_overview_text = tk.Text(
            self.team_overview_card,
            height=10,
            wrap="word",
            bd=0,
            relief="flat",
            bg=self.palette["card"],
            fg=self.palette["ink"],
            font=self.fonts["body"],
        )
        self.team_overview_text.pack(fill="both", expand=True, padx=16, pady=16)

        self.team_top_players = self._card(side, title="Top Players", subtitle="Best batting and bowling names in the selected format")
        self.team_top_players.grid(row=1, column=0, sticky="nsew", pady=(0, 12))
        self.team_top_players_text = tk.Text(
            self.team_top_players,
            wrap="word",
            bd=0,
            relief="flat",
            bg=self.palette["card"],
            fg=self.palette["ink"],
            font=self.fonts["body"],
        )
        self.team_top_players_text.pack(fill="both", expand=True, padx=16, pady=16)

        self.team_recent = self._card(side, title="Recent Results", subtitle="Latest match history")
        self.team_recent.grid(row=2, column=0, sticky="nsew")
        self.team_recent_text = tk.Text(
            self.team_recent,
            wrap="word",
            bd=0,
            relief="flat",
            bg=self.palette["card"],
            fg=self.palette["ink"],
            font=self.fonts["body"],
        )
        self.team_recent_text.pack(fill="both", expand=True, padx=16, pady=16)

        self._refresh_team_select_options()
        self._refresh_teams_page()
        return page

    def _build_players_page(self):
        page = self._new_page()
        content = tk.Frame(page.inner, bg=self.palette["page"])
        content.grid(row=0, column=0, sticky="nsew")
        content.grid_columnconfigure(0, weight=4)
        content.grid_columnconfigure(1, weight=2)
        content.grid_rowconfigure(1, weight=1)

        controls = tk.Frame(content, bg=self.palette["page"])
        controls.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 16))
        tk.Label(controls, text="Format", bg=self.palette["page"], fg=self.palette["ink"], font=("Segoe UI Semibold", 10)).pack(side="left")
        player_format_combo = ttk.Combobox(
            controls,
            textvariable=self.player_format_var,
            values=self.engine.get_formats(),
            width=10,
            state="readonly",
        )
        player_format_combo.pack(side="left", padx=(8, 16))
        player_format_combo.bind("<<ComboboxSelected>>", lambda _event: self._on_player_filter_change())
        tk.Label(controls, text="Country", bg=self.palette["page"], fg=self.palette["ink"], font=("Segoe UI Semibold", 10)).pack(side="left")
        self.player_country_combo = ttk.Combobox(controls, textvariable=self.player_country_var, width=18, state="readonly")
        self.player_country_combo.pack(side="left", padx=(8, 16))
        self.player_country_combo.bind("<<ComboboxSelected>>", lambda _event: self._on_player_filter_change())
        tk.Label(controls, text="Player List", bg=self.palette["page"], fg=self.palette["ink"], font=("Segoe UI Semibold", 10)).pack(side="left")
        self.player_select_combo = ttk.Combobox(controls, textvariable=self.player_select_var, width=28, state="readonly")
        self.player_select_combo.pack(side="left", padx=(8, 16))
        self.player_select_combo.bind("<<ComboboxSelected>>", lambda _event: self._select_player_from_dropdown())
        tk.Label(controls, text="Search Player", bg=self.palette["page"], fg=self.palette["ink"], font=("Segoe UI Semibold", 10)).pack(
            side="left"
        )
        tk.Entry(controls, textvariable=self.player_query_var, font=("Segoe UI", 11), width=28, bd=1, relief="solid").pack(
            side="left", padx=(8, 10)
        )
        tk.Button(
            controls,
            text="Analyze",
            command=self._refresh_players_page,
            bg=self.palette["nav"],
            fg="white",
            bd=0,
            padx=18,
            pady=10,
            font=("Segoe UI Semibold", 10),
        ).pack(side="left")

        self._refresh_player_country_options()
        self._refresh_player_select_options()

        left = tk.Frame(content, bg=self.palette["page"])
        left.grid(row=1, column=0, sticky="nsew", padx=(0, 12))
        left.grid_columnconfigure((0, 1, 2), weight=1)
        left.grid_rowconfigure(2, weight=1)

        self.player_hero = self._card(left, title="Player Snapshot", subtitle="Select a player to populate this panel", bg=self.palette["card"])
        self.player_hero.grid(row=0, column=0, columnspan=3, sticky="ew", pady=(0, 12))
        self.player_hero_text = tk.Text(
            self.player_hero,
            height=8,
            wrap="word",
            bd=0,
            relief="flat",
            bg=self.palette["card"],
            fg=self.palette["ink"],
            font=self.fonts["body"],
        )
        self.player_hero_text.pack(fill="both", expand=True, padx=16, pady=16)

        self.player_format_cards = []
        for idx in range(3):
            card = self._metric_card(left, "Format", "--", accent=[self.palette["nav"], "#1777aa", "#1c9d95"][idx])
            card.grid(row=1, column=idx, sticky="nsew", padx=(0 if idx == 0 else 8, 0), pady=(0, 12))
            self.player_format_cards.append(card)

        self.player_tree_holder = self._card(left, title="Player Results", subtitle="Responsive table with key batting and bowling metrics")
        self.player_tree_holder.grid(row=2, column=0, columnspan=3, sticky="nsew")
        self.player_tree = self._build_table(
            self.player_tree_holder,
            pd.DataFrame(),
            columns=[
                ("player", 170),
                ("country", 100),
                ("role", 100),
                ("runs", 90),
                ("wickets", 80),
                ("batting_average", 100),
                ("strike_rate", 90),
                ("economy_rate", 90),
            ],
            return_tree=True,
        )
        self.player_tree.bind("<<TreeviewSelect>>", lambda _event: self._update_player_side_panel())

        right = tk.Frame(content, bg=self.palette["page"])
        right.grid(row=1, column=1, sticky="nsew")
        right.grid_rowconfigure((0, 1, 2), weight=1)
        right.grid_columnconfigure(0, weight=1)

        self.player_form_card = self._card(right, title="Recent Form", subtitle="Last innings trend")
        self.player_form_card.grid(row=0, column=0, sticky="nsew", pady=(0, 12))
        self.player_form_canvas = tk.Canvas(self.player_form_card, bg=self.palette["card"], highlightthickness=0, height=220)
        self.player_form_canvas.pack(fill="both", expand=True, padx=16, pady=16)

        self.player_against_card = self._card(right, title="Against Opponents", subtitle="Quick opposition breakdown")
        self.player_against_card.grid(row=1, column=0, sticky="nsew", pady=(0, 12))
        self.player_against_text = tk.Text(
            self.player_against_card,
            wrap="word",
            bd=0,
            relief="flat",
            bg=self.palette["card"],
            fg=self.palette["ink"],
            font=self.fonts["body"],
        )
        self.player_against_text.pack(fill="both", expand=True, padx=16, pady=16)

        self.player_recent_card = self._card(right, title="Match History", subtitle="Recent innings details")
        self.player_recent_card.grid(row=2, column=0, sticky="nsew")
        self.player_recent_text = tk.Text(
            self.player_recent_card,
            wrap="word",
            bd=0,
            relief="flat",
            bg=self.palette["card"],
            fg=self.palette["ink"],
            font=self.fonts["body"],
        )
        self.player_recent_text.pack(fill="both", expand=True, padx=16, pady=16)

        self._refresh_players_page()
        return page

    def _build_settings_page(self):
        page = self._new_page()
        content = tk.Frame(page.inner, bg=self.palette["page"])
        content.grid(row=0, column=0, sticky="nsew")
        content.grid_columnconfigure(0, weight=2)
        content.grid_columnconfigure(1, weight=1)
        content.grid_rowconfigure(1, weight=1)
        content.grid_rowconfigure(2, weight=1)

        title = tk.Frame(content, bg=self.palette["page"])
        title.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 16))
        tk.Label(title, text="Account Settings", bg=self.palette["page"], fg=self.palette["ink"], font=self.fonts["page_title"]).pack(
            anchor="w"
        )
        tk.Label(
            title,
            text="Manage your professional profile and application preferences.",
            bg=self.palette["page"],
            fg=self.palette["muted"],
            font=("Segoe UI", 12),
        ).pack(anchor="w", pady=(6, 0))

        profile = self._card(content, title="User Profile", subtitle="Analyst identity and preferred operating settings", bg=self.palette["mint_soft"])
        profile.grid(row=1, column=0, sticky="nsew", padx=(0, 12), pady=(0, 12))
        form = tk.Frame(profile, bg=self.palette["mint_soft"])
        form.pack(fill="both", expand=True, padx=18, pady=18)
        form.grid_columnconfigure((1, 3), weight=1)
        avatar = tk.Canvas(form, width=130, height=130, bg="#17344f", highlightthickness=0)
        avatar.create_oval(28, 18, 102, 92, fill="#dce8f0", outline="")
        avatar.create_rectangle(36, 76, 94, 118, fill="#dce8f0", outline="")
        avatar.grid(row=0, column=0, rowspan=3, sticky="nw", padx=(0, 18))
        self._labeled_entry(form, "FULL NAME", "Marcus V.", 0, 1)
        self._labeled_entry(form, "PROFESSIONAL ROLE", "Lead Analyst", 0, 3)
        self._labeled_entry(form, "EMAIL ADDRESS", "m.v@elite-cricket.pro", 1, 1, columnspan=3)

        display = self._card(content, title="Display", subtitle="Visual mode and density", bg=self.palette["mint_soft"])
        display.grid(row=1, column=1, sticky="nsew", pady=(0, 12))
        disp = tk.Frame(display, bg=self.palette["mint_soft"])
        disp.pack(fill="both", expand=True, padx=18, pady=18)
        tk.Label(disp, text="THEME MODE", bg=self.palette["mint_soft"], fg=self.palette["muted"], font=self.fonts["small"]).pack(anchor="w")
        row = tk.Frame(disp, bg=self.palette["mint_soft"])
        row.pack(fill="x", pady=(8, 18))
        for text, active in [("LIGHT", True), ("DARK", False)]:
            tk.Label(
                row,
                text=text,
                bg=self.palette["nav"] if active else "#f8fbf8",
                fg="white" if active else self.palette["ink"],
                width=16,
                pady=10,
                bd=1,
                relief="solid",
                font=("Segoe UI Semibold", 10),
            ).pack(side="left", padx=(0, 10))
        tk.Label(disp, text="INTERFACE DENSITY", bg=self.palette["mint_soft"], fg=self.palette["muted"], font=self.fonts["small"]).pack(anchor="w")
        tk.Label(disp, text="Standard", bg="#f8fbf8", fg=self.palette["ink"], bd=1, relief="solid", padx=12, pady=12).pack(
            fill="x", pady=(8, 18)
        )
        tk.Label(disp, text="UNITS", bg=self.palette["mint_soft"], fg=self.palette["muted"], font=self.fonts["small"]).pack(anchor="w")
        units = tk.Frame(disp, bg=self.palette["mint_soft"])
        units.pack(fill="x", pady=(8, 0))
        tk.Label(units, text="Metric", bg=self.palette["nav"], fg="white", width=14, pady=10, font=("Segoe UI Semibold", 10)).pack(
            side="left"
        )
        tk.Label(units, text="Imperial", bg="#f8fbf8", fg=self.palette["ink"], width=14, pady=10, font=("Segoe UI Semibold", 10)).pack(
            side="left", padx=(10, 0)
        )

        logic = self._card(content, title="Analytics Logic", subtitle="Engine feature flags", bg=self.palette["mint_soft"])
        logic.grid(row=2, column=0, sticky="nsew", padx=(0, 12))
        logic_body = tk.Frame(logic, bg=self.palette["mint_soft"])
        logic_body.pack(fill="both", expand=True, padx=18, pady=18)
        self._toggle_row(logic_body, "Real-time Data Sync", self.settings_sync_var)
        self._toggle_row(logic_body, "Advanced Win Probability Models", self.settings_model_var)
        self._toggle_row(logic_body, "Predictive Fielding Overlays", self.settings_overlay_var)

        alerts = self._card(content, title="Alerts & Notifications", subtitle="Operational event selection", bg=self.palette["mint_soft"])
        alerts.grid(row=2, column=1, sticky="nsew")
        alert_body = tk.Frame(alerts, bg=self.palette["mint_soft"])
        alert_body.pack(fill="both", expand=True, padx=18, pady=18)
        self._check_row(alert_body, "Critical Match Alerts", self.alert_critical_var)
        self._check_row(alert_body, "Roster & Squad Changes", self.alert_roster_var)
        self._check_row(alert_body, "Automated System Reports", self.alert_reports_var)
        self._check_row(alert_body, "Player Milestone Pings", self.alert_milestone_var)
        return page

    def _labeled_entry(self, parent, label, value, row, column, columnspan=1):
        tk.Label(parent, text=label, bg=parent["bg"], fg=self.palette["muted"], font=self.fonts["small"]).grid(
            row=row, column=column, sticky="w", pady=(0, 6), padx=(0, 12)
        )
        tk.Label(
            parent,
            text=value,
            bg="#f8fbf8",
            fg=self.palette["ink"],
            bd=1,
            relief="solid",
            anchor="w",
            padx=14,
            pady=12,
            font=("Segoe UI", 11),
        ).grid(row=row + 1, column=column, columnspan=columnspan, sticky="ew", padx=(0, 12), pady=(0, 16))

    def _toggle_row(self, parent, label, variable):
        row = tk.Frame(parent, bg=parent["bg"])
        row.pack(fill="x", pady=10)
        tk.Label(row, text=label, bg=parent["bg"], fg=self.palette["ink"], font=("Segoe UI", 12)).pack(side="left")
        indicator = tk.Label(
            row,
            text="ON" if variable.get() else "OFF",
            bg=self.palette["nav"] if variable.get() else "#c9d0d9",
            fg="white",
            width=6,
            pady=4,
            font=("Segoe UI Semibold", 10),
        )
        indicator.pack(side="right")

    def _check_row(self, parent, label, variable):
        row = tk.Frame(parent, bg=parent["bg"])
        row.pack(fill="x", pady=10)
        tk.Checkbutton(
            row,
            text=label,
            variable=variable,
            bg=parent["bg"],
            fg=self.palette["ink"],
            activebackground=parent["bg"],
            anchor="w",
            font=("Segoe UI", 12),
        ).pack(side="left")

    def _build_table(self, parent, df, columns, return_tree=False):
        holder = tk.Frame(parent, bg=self.palette["card"])
        holder.pack(fill="both", expand=True, padx=16, pady=16)
        tree = ttk.Treeview(holder, columns=[name for name, _ in columns], show="headings", style="Elite.Treeview")
        yscroll = ttk.Scrollbar(holder, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=yscroll.set)
        for name, width in columns:
            tree.heading(name, text=name.replace("_", " ").title())
            tree.column(name, width=width, anchor="w")
        tree.grid(row=0, column=0, sticky="nsew")
        yscroll.grid(row=0, column=1, sticky="ns")
        holder.grid_rowconfigure(0, weight=1)
        holder.grid_columnconfigure(0, weight=1)
        self._populate_tree(tree, df, [name for name, _ in columns])
        if return_tree:
            return tree
        return tree

    def _populate_tree(self, tree, df, columns):
        for item in tree.get_children():
            tree.delete(item)
        if df is None or df.empty:
            return
        for idx, (_, row) in enumerate(df.iterrows()):
            values = []
            for col in columns:
                val = row.get(col, "")
                if isinstance(val, float):
                    if math.isnan(val):
                        val = ""
                    else:
                        val = f"{val:.2f}"
                values.append(val)
            tree.insert("", "end", iid=str(idx), values=values)

    def _draw_format_velocity_chart(self, canvas):
        canvas.delete("all")
        width = max(canvas.winfo_width(), 380)
        height = max(canvas.winfo_height(), 260)
        margin = 34
        canvas.create_line(margin, height - margin, width - margin, height - margin, fill="#d2d9d3", width=2)
        canvas.create_line(margin, margin, margin, height - margin, fill="#d2d9d3", width=2)
        data = self.engine.team_summary.groupby("format")["batting_runs_per_over"].mean().reindex(self.engine.get_formats())
        max_val = data.max() if len(data) else 8
        colors = [self.palette["teal"], self.palette["gold"], self.palette["nav"]]
        step = (width - margin * 2) / max(len(data), 1)
        for idx, (fmt, val) in enumerate(data.items()):
            x0 = margin + idx * step + 30
            x1 = x0 + 70
            y1 = height - margin
            y0 = y1 - ((val / max_val) * (height - margin * 2))
            canvas.create_rectangle(x0, y0, x1, y1, fill=colors[idx % len(colors)], outline="")
            canvas.create_text((x0 + x1) / 2, y0 - 12, text=f"{val:.2f}", fill=self.palette["ink"], font=("Segoe UI", 10))
            canvas.create_text((x0 + x1) / 2, height - 14, text=fmt, fill=self.palette["muted"], font=("Segoe UI", 10))

    def _draw_over_progress(self, canvas):
        canvas.delete("all")
        width = max(canvas.winfo_width(), 420)
        height = max(canvas.winfo_height(), 280)
        values = [3, 5, 4, 8, 6, 5, 3, 7, 5]
        max_val = max(values)
        gap = 12
        bar_w = (width - 80 - gap * (len(values) - 1)) / len(values)
        for idx, val in enumerate(values):
            x0 = 40 + idx * (bar_w + gap)
            x1 = x0 + bar_w
            y1 = height - 40
            y0 = y1 - (val / max_val) * (height - 90)
            color = self.palette["teal_dark"] if idx == len(values) - 1 else self.palette["mint"]
            canvas.create_rectangle(x0, y0, x1, y1, fill=color, outline="")
            canvas.create_text((x0 + x1) / 2, height - 20, text=f"OVR {34 + idx}", fill=self.palette["muted"], font=("Segoe UI", 9))
        canvas.create_text(width - 54, 28, text="LIVE", fill=self.palette["ink"], font=("Segoe UI Semibold", 10))

    def _draw_wagon_wheel(self, canvas):
        canvas.delete("all")
        width = max(canvas.winfo_width(), 260)
        height = max(canvas.winfo_height(), 220)
        cx = width / 2
        cy = height / 2 + 20
        radius = min(width, height) * 0.34
        canvas.create_oval(cx - radius, cy - radius, cx + radius, cy + radius, outline="#d3ded8", width=2)
        for angle, color in [(40, self.palette["teal"]), (95, "#c8d0d9"), (140, self.palette["teal"]), (220, self.palette["nav"]), (315, self.palette["nav"])]:
            rad = math.radians(angle)
            x = cx + radius * 0.95 * math.cos(rad)
            y = cy - radius * 0.95 * math.sin(rad)
            canvas.create_line(cx, cy, x, y, fill=color, width=4)
        canvas.create_text(cx, cy - radius - 12, text="OFF", fill=self.palette["ink"], font=("Segoe UI Semibold", 10))
        canvas.create_text(cx, cy + radius + 12, text="LEG", fill=self.palette["ink"], font=("Segoe UI Semibold", 10))

    def _draw_player_form(self, canvas, runs):
        canvas.delete("all")
        width = max(canvas.winfo_width(), 360)
        height = max(canvas.winfo_height(), 220)
        if not runs:
            canvas.create_text(width / 2, height / 2, text="No recent innings to plot", fill=self.palette["muted"], font=("Segoe UI", 12))
            return
        max_run = max(runs) if max(runs) else 1
        gap = 12
        bar_w = (width - 60 - gap * (len(runs) - 1)) / len(runs)
        for idx, val in enumerate(runs):
            x0 = 30 + idx * (bar_w + gap)
            x1 = x0 + bar_w
            y1 = height - 28
            y0 = y1 - (val / max_run) * (height - 60)
            canvas.create_rectangle(x0, y0, x1, y1, fill=self.palette["teal"], outline="")
            canvas.create_text((x0 + x1) / 2, y0 - 10, text=str(int(val)), fill=self.palette["ink"], font=("Segoe UI", 9))

    def _refresh_player_country_options(self):
        teams = ["All"] + self.engine.get_teams(self.player_format_var.get())
        self.player_country_combo["values"] = teams
        if self.player_country_var.get() not in teams:
            self.player_country_var.set("All")

    def _refresh_player_select_options(self):
        options_df = self.engine.search_players("", self.player_format_var.get(), self.player_country_var.get())
        values = [f"{row['player']} [{row['country']}]" for _, row in options_df.head(300).iterrows()]
        self.player_select_combo["values"] = values
        if self.player_select_var.get() not in values:
            self.player_select_var.set(values[0] if values else "")

    def _refresh_team_select_options(self):
        options_df = self.engine.search_teams("", self.team_format_var.get())
        values = [row["country"] for _, row in options_df.iterrows()]
        self.team_select_combo["values"] = values
        if self.team_select_var.get() not in values:
            self.team_select_var.set(values[0] if values else "")

    def _on_player_filter_change(self):
        self._refresh_player_country_options()
        self._refresh_player_select_options()
        self._refresh_players_page()

    def _select_player_from_dropdown(self):
        selected = self.player_select_var.get().strip()
        if not selected:
            return
        player_name = selected.split(" [")[0].strip()
        self.player_query_var.set(player_name)
        self._refresh_players_page()

    def _select_team_from_dropdown(self):
        selected = self.team_select_var.get().strip()
        if not selected:
            return
        self.team_query_var.set(selected)
        self._refresh_teams_page()

    def _refresh_players_page(self):
        self._refresh_player_country_options()
        self._refresh_player_select_options()
        self.player_df = self.engine.search_players(
            self.player_query_var.get(),
            self.player_format_var.get(),
            self.player_country_var.get(),
        )
        self._populate_tree(
            self.player_tree,
            self.player_df,
            ["player", "country", "role", "runs", "wickets", "batting_average", "strike_rate", "economy_rate"],
        )
        if not self.player_df.empty:
            self.player_select_var.set(f"{self.player_df.iloc[0]['player']} [{self.player_df.iloc[0]['country']}]")
            self.player_tree.selection_set("0")
            self._update_player_side_panel()

    def _update_player_side_panel(self):
        selection = self.player_tree.selection()
        if not selection or self.player_df.empty:
            return
        row = self.player_df.iloc[int(selection[0])]
        report = self.engine.get_player_profile(row["player"], self.player_format_var.get())
        if not report:
            return
        profile = report["profile"]
        hero = (
            f"{profile['player']}\n"
            f"{profile['country']} • {profile['format']} • {profile['role']}\n\n"
            f"Runs: {int(profile['runs'])}   Bat Avg: {self._fmt(profile['batting_average'])}   SR: {self._fmt(profile['strike_rate'])}\n"
            f"Wickets: {int(profile['wickets'])}   Bowl Avg: {self._fmt(profile['bowling_average'])}   Econ: {self._fmt(profile['economy_rate'])}\n"
            f"100s: {int(profile['hundreds'])}   50s: {int(profile['fifties'])}   5WI: {int(profile['five_wicket_hauls'])}"
        )
        self._set_text(self.player_hero_text, hero)

        for widget in self.player_format_cards:
            for child in widget.winfo_children():
                child.destroy()
        career = report["career_by_format"].copy()
        colors = [self.palette["nav"], "#1777aa", "#1c9d95"]
        for idx, (_, fmt_row) in enumerate(career.head(3).iterrows()):
            widget = self.player_format_cards[idx]
            widget.configure(bg=self.palette["card"])
            tk.Label(widget, text=f"{fmt_row['format']} FORMAT", bg=self.palette["card"], fg=self.palette["muted"], font=self.fonts["small"]).pack(
                anchor="w", padx=18, pady=(16, 6)
            )
            tk.Label(widget, text=f"Runs {int(fmt_row['runs'])}", bg=self.palette["card"], fg=self.palette["ink"], font=("Segoe UI Semibold", 20)).pack(
                anchor="w", padx=18
            )
            tk.Label(
                widget,
                text=f"Avg {self._fmt(fmt_row['batting_average'])}   SR {self._fmt(fmt_row['strike_rate'])}",
                bg=self.palette["card"],
                fg=self.palette["teal_dark"],
                font=("Segoe UI", 11),
            ).pack(anchor="w", padx=18, pady=(6, 6))
            tk.Label(
                widget,
                text=f"Wkts {int(fmt_row['wickets'])}   Econ {self._fmt(fmt_row['economy_rate'])}",
                bg=self.palette["card"],
                fg=self.palette["muted"],
                font=("Segoe UI", 10),
            ).pack(anchor="w", padx=18, pady=(0, 12))
            tk.Frame(widget, bg=colors[idx], height=4).pack(fill="x", padx=18, pady=(0, 16))

        against = report["against"].head(8)[["opposition", "runs", "wickets", "batting_average", "strike_rate"]]
        self._set_text(self.player_against_text, against.to_string(index=False))

        recent = report["recent"].head(8)
        self._set_text(self.player_recent_text, recent.to_string(index=False))
        recent_runs = recent["runs"].fillna(0).tolist()[::-1]
        self._draw_player_form(self.player_form_canvas, recent_runs)

    def _refresh_teams_page(self):
        self._refresh_team_select_options()
        self.team_df = self.engine.search_teams(self.team_query_var.get(), self.team_format_var.get())
        self._populate_tree(
            self.team_tree,
            self.team_df,
            ["country", "matches_played", "wins", "losses", "win_rate", "batting_average", "batting_runs_per_over", "bowling_average"],
        )
        if not self.team_df.empty:
            avg_win = self.team_df["win_rate"].mean()
            top_bat = self.team_df["batting_average"].max()
            top_bowl = self.team_df["bowling_runs_per_over"].min()
            metrics = [
                ("Average Win %", f"{avg_win:.1f}%", self.palette["teal_dark"]),
                ("Top Bat Avg", f"{top_bat:.2f}", self.palette["teal"]),
                ("Top Bowl Econ", f"{top_bowl:.2f}", self.palette["gold"]),
                ("Loaded Teams", str(len(self.team_df)), self.palette["nav"]),
            ]
            for card, (title, value, accent) in zip(self.team_metric_labels, metrics):
                for child in card.winfo_children():
                    child.destroy()
                tk.Label(card, text=title.upper(), bg=self.palette["card"], fg=self.palette["muted"], font=self.fonts["small"]).pack(
                    anchor="w", padx=18, pady=(16, 6)
                )
                tk.Label(card, text=value, bg=self.palette["card"], fg=self.palette["ink"], font=("Segoe UI Semibold", 24)).pack(
                    anchor="w", padx=18
                )
                tk.Frame(card, bg=accent, height=4).pack(fill="x", padx=18, pady=(14, 16))
            self.team_select_var.set(self.team_df.iloc[0]["country"])
            self.team_tree.selection_set("0")
            self._update_team_side_panel()

    def _update_team_side_panel(self):
        selection = self.team_tree.selection()
        if not selection or self.team_df.empty:
            return
        row = self.team_df.iloc[int(selection[0])]
        report = self.engine.get_team_profile(row["country"], self.team_format_var.get())
        if not report:
            return
        profile = report["profile"].head(3)
        overview = profile[
            ["format", "matches_played", "wins", "losses", "win_rate", "batting_average", "bowling_average"]
        ].to_string(index=False)
        self._set_text(self.team_overview_text, overview)

        bat = report["top_batters"].head(5)[["player", "runs", "batting_average", "strike_rate"]].to_string(index=False)
        bowl = report["top_bowlers"].head(5)[["player", "wickets", "bowling_average", "economy_rate"]].to_string(index=False)
        self._set_text(self.team_top_players_text, "Top Batters\n\n" + bat + "\n\nTop Bowlers\n\n" + bowl)
        self._set_text(self.team_recent_text, report["recent"].head(8).to_string(index=False))

    def _set_text(self, widget, text):
        widget.config(state="normal")
        widget.delete("1.0", tk.END)
        widget.insert("1.0", text)
        widget.config(state="disabled")

    def _run_global_search(self):
        query = self.search_var.get().strip()
        if not query:
            return
        players = self.engine.search_players(query, self.player_format_var.get(), "All")
        if not players.empty:
            self._show_page("players")
            self.player_query_var.set(query)
            self._refresh_players_page()
            return
        teams = self.engine.search_teams(query, self.team_format_var.get())
        if not teams.empty:
            self._show_page("teams")
            self.team_query_var.set(query)
            self._refresh_teams_page()

    def _fmt(self, value):
        try:
            if pd.isna(value):
                return "N/A"
            return f"{float(value):.2f}"
        except Exception:
            return "N/A"


def main():
    root = tk.Tk()
    CricketAnalyticsGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
