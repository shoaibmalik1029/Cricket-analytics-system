import tkinter as tk
from tkinter import ttk


class CricketAnalyticsGUI_H2H(tk.Frame):
    def __init__(self, parent, engine, palette, fonts):
        super().__init__(parent, bg=palette["page"])
        self.engine = engine
        self.palette = palette
        self.fonts = fonts
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self._build_page()
    
    def _build_page(self):
        content = tk.Frame(self, bg=self.palette["page"])
        content.grid(row=0, column=0, sticky="nsew")
        content.grid_columnconfigure(0, weight=1)
        content.grid_rowconfigure(1, weight=1)

        controls = tk.Frame(content, bg=self.palette["page"])
        controls.grid(row=0, column=0, sticky="ew", pady=(0, 16))
        tk.Label(controls, text="Format", bg=self.palette["page"], fg=self.palette["ink"], font=("Segoe UI Semibold", 10)).pack(side="left")
        h2h_format_var = tk.StringVar(value="ODI")
        h2h_format_combo = ttk.Combobox(controls, textvariable=h2h_format_var, values=self.engine.get_formats(), width=10, state="readonly")
        h2h_format_combo.pack(side="left", padx=(8, 16))
        
        tk.Label(controls, text="Team A", bg=self.palette["page"], fg=self.palette["ink"], font=("Segoe UI Semibold", 10)).pack(side="left")
        h2h_team_a_var = tk.StringVar()
        h2h_team_a_combo = ttk.Combobox(controls, textvariable=h2h_team_a_var, values=self.engine.get_teams(), width=18, state="readonly")
        h2h_team_a_combo.pack(side="left", padx=(8, 16))
        
        tk.Label(controls, text="Team B", bg=self.palette["page"], fg=self.palette["ink"], font=("Segoe UI Semibold", 10)).pack(side="left")
        h2h_team_b_var = tk.StringVar()
        h2h_team_b_combo = ttk.Combobox(controls, textvariable=h2h_team_b_var, values=self.engine.get_teams(), width=18, state="readonly")
        h2h_team_b_combo.pack(side="left", padx=(8, 16))
        
        h2h_results_text = tk.Text(self, wrap="word", bd=0, relief="flat", bg=self.palette["card"], fg=self.palette["ink"], font=self.fonts["body"])
        
        def run_h2h():
            try:
                team_a = h2h_team_a_var.get().strip()
                team_b = h2h_team_b_var.get().strip()
                fmt = h2h_format_var.get()
                if not team_a or not team_b:
                    return
                analysis = self.engine.get_head_to_head_analysis(fmt, team_a, team_b)
                if analysis:
                    self._display_h2h_results(h2h_results_text, analysis)
            except Exception:
                pass
        
        tk.Button(
            controls,
            text="Analyze",
            command=run_h2h,
            bg=self.palette["nav"],
            fg="white",
            bd=0,
            padx=18,
            pady=10,
            font=("Segoe UI Semibold", 10),
        ).pack(side="left", padx=(8, 0))

        h2h_results_text.grid(row=1, column=0, sticky="nsew", padx=16, pady=16)

    def _display_h2h_results(self, widget, analysis):
        widget.config(state="normal")
        widget.delete("1.0", tk.END)
        text = f"""HEAD-TO-HEAD ANALYSIS: {analysis['team_a']} vs {analysis['team_b']}

Format: {analysis['format']}
Overall Matches: {analysis['matches']}
{analysis['team_a']} Wins: {analysis['team_a_wins']}
{analysis['team_b']} Wins: {analysis['team_b_wins']}
{analysis['team_a']} Win Rate: {analysis['team_a_win_rate']:.1f}%

Recent Trend (Last 10):
{analysis['team_a']} Recent Wins: {analysis['recent_last_10_team_a_wins']}

Psychological Edge: {analysis['psychological_edge']}

Recent Meetings:
"""
        for _, row in analysis["recent_meetings"].head(5).iterrows():
            text += f"\n{row['date']} - {row['ground']} - {row['result']} ({row['margin']})"
        
        if analysis["model_prediction"]:
            pred = analysis["model_prediction"]
            text += f"\n\nMODEL PREDICTION (Neutral Venue):\nPredicted Winner: {pred['winner']}\n{pred['team_a']} Win Probability: {pred['team_a_win_probability']:.1f}%\n{pred['team_b']} Win Probability: {pred['team_b_win_probability']:.1f}%"
        
        widget.insert("1.0", text)
        widget.config(state="disabled")


class CricketAnalyticsGUI_Upset(tk.Frame):
    def __init__(self, parent, engine, palette, fonts):
        super().__init__(parent, bg=palette["page"])
        self.engine = engine
        self.palette = palette
        self.fonts = fonts
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self._build_page()
    
    def _build_page(self):
        content = tk.Frame(self, bg=self.palette["page"])
        content.grid(row=0, column=0, sticky="nsew")
        content.grid_columnconfigure(0, weight=1)
        content.grid_rowconfigure(1, weight=1)

        controls = tk.Frame(content, bg=self.palette["page"])
        controls.grid(row=0, column=0, sticky="ew", pady=(0, 16))
        tk.Label(controls, text="Format", bg=self.palette["page"], fg=self.palette["ink"], font=("Segoe UI Semibold", 10)).pack(side="left")
        upset_format_var = tk.StringVar(value="ODI")
        upset_format_combo = ttk.Combobox(controls, textvariable=upset_format_var, values=self.engine.get_formats(), width=10, state="readonly")
        upset_format_combo.pack(side="left", padx=(8, 16))
        
        tk.Label(controls, text="Favorite Team", bg=self.palette["page"], fg=self.palette["ink"], font=("Segoe UI Semibold", 10)).pack(side="left")
        upset_fav_var = tk.StringVar()
        upset_fav_combo = ttk.Combobox(controls, textvariable=upset_fav_var, values=self.engine.get_teams(), width=18, state="readonly")
        upset_fav_combo.pack(side="left", padx=(8, 16))
        
        tk.Label(controls, text="Underdog Team", bg=self.palette["page"], fg=self.palette["ink"], font=("Segoe UI Semibold", 10)).pack(side="left")
        upset_dog_var = tk.StringVar()
        upset_dog_combo = ttk.Combobox(controls, textvariable=upset_dog_var, values=self.engine.get_teams(), width=18, state="readonly")
        upset_dog_combo.pack(side="left", padx=(8, 16))
        
        upset_results_text = tk.Text(self, wrap="word", bd=0, relief="flat", bg=self.palette["card"], fg=self.palette["ink"], font=self.fonts["body"])
        
        def run_upset():
            try:
                fav = upset_fav_var.get().strip()
                dog = upset_dog_var.get().strip()
                fmt = upset_format_var.get()
                if not fav or not dog:
                    return
                analysis = self.engine.detect_upset(fmt, fav, dog)
                if analysis:
                    self._display_upset_results(upset_results_text, analysis)
            except Exception:
                pass
        
        tk.Button(
            controls,
            text="Analyze",
            command=run_upset,
            bg=self.palette["nav"],
            fg="white",
            bd=0,
            padx=18,
            pady=10,
            font=("Segoe UI Semibold", 10),
        ).pack(side="left", padx=(8, 0))

        upset_results_text.grid(row=1, column=0, sticky="nsew", padx=16, pady=16)

    def _display_upset_results(self, widget, analysis):
        widget.config(state="normal")
        widget.delete("1.0", tk.END)
        
        color_indicator = "[LOW]" if analysis['upset_probability'] < 33 else "[MODERATE]" if analysis['upset_probability'] < 66 else "[HIGH]"
        
        text = f"""UPSET DETECTION ANALYSIS - {analysis['format']}

Favorite: {analysis['favorite']}
Underdog: {analysis['underdog']}

Favorite Win Probability: {analysis['favorite_win_probability']:.1f}%
Upset Probability: {analysis['upset_probability']:.1f}% {color_indicator}

Analysis: {analysis['reason']}

Interpretation:
"""
        if analysis['upset_probability'] < 25:
            text += "The favorite is heavily favored. Upset potential is very low."
        elif analysis['upset_probability'] < 45:
            text += "The favorite is favored, but upset is possible. Watch recent form changes."
        elif analysis['upset_probability'] < 65:
            text += "This is a competitive matchup. Upset odds are moderate to good."
        else:
            text += "Strong upset potential. The underdog has viable pathways to victory."
        
        widget.insert("1.0", text)
        widget.config(state="disabled")


class CricketAnalyticsGUI_Form(tk.Frame):
    def __init__(self, parent, engine, palette, fonts):
        super().__init__(parent, bg=palette["page"])
        self.engine = engine
        self.palette = palette
        self.fonts = fonts
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self._build_page()
    
    def _build_page(self):
        content = tk.Frame(self, bg=self.palette["page"])
        content.grid(row=0, column=0, sticky="nsew")
        content.grid_columnconfigure(0, weight=1)
        content.grid_rowconfigure(1, weight=1)

        controls = tk.Frame(content, bg=self.palette["page"])
        controls.grid(row=0, column=0, sticky="ew", pady=(0, 16))
        tk.Label(controls, text="Format", bg=self.palette["page"], fg=self.palette["ink"], font=("Segoe UI Semibold", 10)).pack(side="left")
        form_format_var = tk.StringVar(value="ODI")
        form_format_combo = ttk.Combobox(controls, textvariable=form_format_var, values=self.engine.get_formats(), width=10, state="readonly")
        form_format_combo.pack(side="left", padx=(8, 16))
        
        tk.Label(controls, text="Team", bg=self.palette["page"], fg=self.palette["ink"], font=("Segoe UI Semibold", 10)).pack(side="left")
        form_team_var = tk.StringVar()
        form_team_combo = ttk.Combobox(controls, textvariable=form_team_var, values=self.engine.get_teams(), width=22, state="readonly")
        form_team_combo.pack(side="left", padx=(8, 16))
        
        form_results_text = tk.Text(self, wrap="word", bd=0, relief="flat", bg=self.palette["card"], fg=self.palette["ink"], font=self.fonts["body"])
        
        def run_form():
            try:
                team = form_team_var.get().strip()
                fmt = form_format_var.get()
                if not team:
                    return
                form_data = self.engine.get_team_form(team, fmt, window=8)
                if form_data:
                    self._display_form_results(form_results_text, form_data)
            except Exception:
                pass
        
        tk.Button(
            controls,
            text="Analyze",
            command=run_form,
            bg=self.palette["nav"],
            fg="white",
            bd=0,
            padx=18,
            pady=10,
            font=("Segoe UI Semibold", 10),
        ).pack(side="left", padx=(8, 0))

        form_results_text.grid(row=1, column=0, sticky="nsew", padx=16, pady=16)

    def _display_form_results(self, widget, form_data):
        widget.config(state="normal")
        widget.delete("1.0", tk.END)
        
        momentum = form_data.get("momentum_score", 0) or 0
        momentum_indicator = "[HOT]" if momentum > 65 else "[IMPROVING]" if momentum > 50 else "[STEADY]" if momentum > 35 else "[STRUGGLING]"
        
        text = f"""TEAM FORM ANALYSIS - {form_data['team']} ({form_data['format']})

Analysis Period: Last {form_data['window']} Matches

Recent Results: {form_data['innings']} matches analyzed

Win Rate (Recent): {form_data['win_rate']:.1f}%
Average Runs: {form_data['avg_batting_runs']:.1f}
Momentum Score: {momentum:.1f}/100 {momentum_indicator}

Volatility: {form_data['volatility_score']:.1f}
(Higher = More inconsistent)

Key Insights:
"""
        if momentum > 65:
            text += "Team is in excellent form with strong momentum.\n"
        elif momentum > 50:
            text += "Team is improving and gaining confidence.\n"
        elif momentum > 35:
            text += "Team performance is stable.\n"
        else:
            text += "Team is going through a rough patch.\n"
        
        if form_data['volatility_score'] > 50:
            text += "Performance is highly inconsistent - unpredictable outcomes likely.\n"
        else:
            text += "Consistent performance pattern observed.\n"
        
        text += f"\nAverage Bowling Runs Conceded: {form_data['avg_bowling_runs']:.1f}\n"
        
        if form_data['recent_innings']:
            text += "\nRecent Match Results (Latest First):\n"
            for _, match in form_data['recent_innings'].head(8).iterrows():
                text += f"  {match['date']} - {match['opposition']} ({match['ground']}) - Runs: {match['runs']}\n"
        
        widget.insert("1.0", text)
        widget.config(state="disabled")
