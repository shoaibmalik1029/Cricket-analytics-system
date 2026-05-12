from dataclasses import dataclass
from pathlib import Path
import warnings

import joblib
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")


# Use project data directory instead of external Downloads folder
import os
BASE_DIR = Path(__file__).parent.parent  # Get cricket_analysis folder
DATA_DIR = BASE_DIR / "data" / "final"  # Fallback to project data
CACHE_DIR = BASE_DIR / ".cricket_cache"
CACHE_VERSION = "statsguru-v3"
ACCEPTED_CACHE_VERSIONS = {"statsguru-v2", "statsguru-v3"}
RECENT_DATA_DIR = BASE_DIR / "data" / "normalized_recent"
FINAL_DATA_DIR = BASE_DIR / "data" / "final"

DATA_SOURCES = {
    "ODI": {
        "player_files": [
            DATA_DIR / "Men ODI Player Innings Stats - 20th Century.csv",
            DATA_DIR / "Men ODI Player Innings Stats - 21st Century.csv",
        ],
        "team_batting_file": DATA_DIR / "Men ODI Team Batting Stats.csv",
        "team_bowling_file": DATA_DIR / "Men ODI Team Bowling Stats.csv",
        "result_files": [
            DATA_DIR / "Men ODI Team Match Results - 20th Century.csv",
            DATA_DIR / "Men ODI Team Match Results - 21st Century.csv",
        ],
    },
    "T20I": {
        "player_files": [DATA_DIR / "Men T20I Player Innings Stats - 21st Century.csv"],
        "team_batting_file": DATA_DIR / "Men T20I Team Batting Stats.csv",
        "team_bowling_file": DATA_DIR / "Men T20I Team Bowling Stats.csv",
        "result_files": [DATA_DIR / "Men T20I Team Match Results - 21st Century.csv"],
    },
    "Test": {
        "player_files": [
            DATA_DIR / "Men Test Player Innings Stats - 19th Century.csv",
            DATA_DIR / "Men Test Player Innings Stats - 20th Century.csv",
            DATA_DIR / "Men Test Player Innings Stats - 21st Century.csv",
        ],
        "team_batting_file": DATA_DIR / "Men Test Team Batting Stats.csv",
        "team_bowling_file": DATA_DIR / "Men Test Team Bowling Stats.csv",
        "result_files": [
            DATA_DIR / "Men Test Team Match Results - 19th Century.csv",
            DATA_DIR / "Men Test Team Match Results - 20th Century.csv",
            DATA_DIR / "Men Test Team Match Results - 21st Century.csv",
        ],
    },
}


def clean_text(value):
    if pd.isna(value):
        return ""
    return str(value).strip()


def normalize_name(text):
    text = clean_text(text).lower()
    for ch in [".", ",", "-", "_", "'"]:
        text = text.replace(ch, " ")
    return " ".join(text.split())


def to_numeric(series):
    return pd.to_numeric(series, errors="coerce")


def read_statsguru_csv(path, usecols=None):
    chunks = pd.read_csv(
        path,
        encoding="utf-8-sig",
        usecols=usecols,
        dtype=str,
        chunksize=5000,
    )
    return pd.concat(chunks, ignore_index=True)


def overs_to_balls(overs_value):
    if pd.isna(overs_value):
        return np.nan
    text = str(overs_value).strip()
    if not text or text.lower() == "nan":
        return np.nan
    if "." in text:
        whole, frac = text.split(".", 1)
        try:
            return int(whole) * 6 + int(frac[:1])
        except ValueError:
            return np.nan
    try:
        return int(float(text)) * 6
    except ValueError:
        return np.nan


def balls_to_overs(balls):
    if pd.isna(balls):
        return np.nan
    balls = int(balls)
    return f"{balls // 6}.{balls % 6}"


def parse_opposition(text):
    value = clean_text(text)
    if value.lower().startswith("v "):
        return value[2:].strip()
    return value


def parse_match_opponent(match_text, country):
    parts = [clean_text(part) for part in clean_text(match_text).split(" v ")]
    if len(parts) != 2:
        return ""
    if parts[0] == country:
        return parts[1]
    if parts[1] == country:
        return parts[0]
    return parts[1]


def safe_divide(num, den):
    if den in [0, 0.0] or pd.isna(den):
        return np.nan
    return num / den


def clamp(value, low, high):
    return max(low, min(high, value))


def date_label(value):
    return value.isoformat() if hasattr(value, "isoformat") else str(value)


def scalar_or_none(value):
    if pd.isna(value):
        return None
    try:
        if isinstance(value, (np.floating, float)):
            return round(float(value), 4)
        if isinstance(value, (np.integer, int)):
            return int(value)
    except Exception:
        return value
    return value


def compute_streak(values):
    streak = 0
    streak_type = "N/A"
    for value in values:
        if value == 1:
            if streak_type in ["N/A", "W"]:
                streak += 1
                streak_type = "W"
            else:
                break
        elif value == 0:
            if streak_type in ["N/A", "L"]:
                streak += 1
                streak_type = "L"
            else:
                break
    return f"{streak_type}{streak}" if streak else "N/A"


@dataclass
class DatasetSummary:
    formats: list
    total_player_rows: int
    total_result_rows: int
    total_players: int
    total_teams: int
    date_range: str
    min_year: int | None
    max_year: int | None


class CricketAnalyticsEngine:
    def __init__(self):
        self.formats = list(DATA_SOURCES.keys())
        if self._load_cache():
            self._append_recent_extension()
            self._optimize_loaded_frames()
            self._build_indexes()
            self._train_match_model()
            self._save_cache()
            return
        self._load_all_data()
        self._append_recent_extension()
        self._optimize_loaded_frames()
        self._build_indexes()
        self._train_match_model()
        self._save_cache()

    def _all_source_files(self):
        merged_player_parquet = FINAL_DATA_DIR / "player_innings_1877_2025.parquet"
        merged_results_parquet = FINAL_DATA_DIR / "team_results_1877_2025.parquet"
        if merged_player_parquet.exists() and merged_results_parquet.exists():
            return [merged_player_parquet, merged_results_parquet]
        merged_player = FINAL_DATA_DIR / "player_innings_1877_2025.csv"
        merged_results = FINAL_DATA_DIR / "team_results_1877_2025.csv"
        if merged_player.exists() and merged_results.exists():
            return [merged_player, merged_results]
        files = []
        for config in DATA_SOURCES.values():
            files.extend(config["player_files"])
            files.append(config["team_batting_file"])
            files.append(config["team_bowling_file"])
            files.extend(config["result_files"])
        return files

    def _cache_is_valid(self):
        meta_file = CACHE_DIR / "meta.joblib"
        if not meta_file.exists():
            return False
        try:
            meta = joblib.load(meta_file)
            if meta.get("cache_version") not in ACCEPTED_CACHE_VERSIONS:
                return False
        except Exception:
            return False
        cache_time = meta_file.stat().st_mtime
        for path in self._all_source_files():
            if path.exists() and path.stat().st_mtime > cache_time:
                return False
        for path in self._recent_extension_files():
            if path.exists() and path.stat().st_mtime > cache_time:
                return False
        return True

    def _recent_extension_files(self):
        return [
            RECENT_DATA_DIR / "player_innings_recent.csv",
            RECENT_DATA_DIR / "team_results_recent.csv",
            RECENT_DATA_DIR / "team_batting_recent.csv",
            RECENT_DATA_DIR / "team_bowling_recent.csv",
        ]

    def _load_cache(self):
        if not self._cache_is_valid():
            return False
        try:
            self.player_innings = pd.read_parquet(CACHE_DIR / "player_innings.parquet")
            self.team_batting = pd.read_parquet(CACHE_DIR / "team_batting.parquet")
            self.team_bowling = pd.read_parquet(CACHE_DIR / "team_bowling.parquet")
            self.team_results = pd.read_parquet(CACHE_DIR / "team_results.parquet")
            self.player_summary = pd.read_parquet(CACHE_DIR / "player_summary.parquet")
            self.team_summary = pd.read_parquet(CACHE_DIR / "team_summary.parquet")
            meta = joblib.load(CACHE_DIR / "meta.joblib")
            self.dataset_summary = meta["dataset_summary"]
            self.available_teams = meta["available_teams"]
            self.available_players = meta["available_players"]
            self.team_strength_lookup = meta["team_strength_lookup"]
            self.model_features = meta["model_features"]
            self.match_model = meta.get("match_model", {})
            return True
        except Exception as exc:
            print(f"Cache load failed: {exc}")
            return False

    def _save_cache(self):
        try:
            CACHE_DIR.mkdir(parents=True, exist_ok=True)
            self.player_innings.to_parquet(CACHE_DIR / "player_innings.parquet", index=False)
            self.team_batting.to_parquet(CACHE_DIR / "team_batting.parquet", index=False)
            self.team_bowling.to_parquet(CACHE_DIR / "team_bowling.parquet", index=False)
            self.team_results.to_parquet(CACHE_DIR / "team_results.parquet", index=False)
            self.player_summary.to_parquet(CACHE_DIR / "player_summary.parquet", index=False)
            self.team_summary.to_parquet(CACHE_DIR / "team_summary.parquet", index=False)
            joblib.dump(
                {
                    "dataset_summary": self.dataset_summary,
                    "available_teams": self.available_teams,
                    "available_players": self.available_players,
                    "team_strength_lookup": self.team_strength_lookup,
                    "model_features": self.model_features,
                    "match_model": self.match_model,
                    "cache_version": CACHE_VERSION,
                },
                CACHE_DIR / "meta.joblib",
            )
        except Exception:
            pass

    def _append_recent_extension(self):
        if (FINAL_DATA_DIR / "player_innings_1877_2025.parquet").exists() and (FINAL_DATA_DIR / "team_results_1877_2025.parquet").exists():
            return
        extension_files = self._recent_extension_files()
        if not all(path.exists() for path in extension_files):
            return

        player_recent = pd.read_csv(extension_files[0], parse_dates=["date"])
        result_recent = pd.read_csv(extension_files[1], parse_dates=["date"])
        batting_recent = pd.read_csv(extension_files[2])
        bowling_recent = pd.read_csv(extension_files[3])

        if hasattr(self, "player_innings") and not player_recent.empty:
            current_max = self.player_innings["date"].max() if not self.player_innings.empty else pd.NaT
            recent_min = player_recent["date"].min()
            if pd.notna(current_max) and pd.notna(recent_min) and current_max >= recent_min:
                player_recent = player_recent[player_recent["date"] > current_max]
                result_recent = result_recent[result_recent["date"] > current_max]

        if player_recent.empty and result_recent.empty:
            return

        if not player_recent.empty:
            self.player_innings = pd.concat([self.player_innings, player_recent], ignore_index=True)
        if not batting_recent.empty:
            self.team_batting = pd.concat([self.team_batting, batting_recent], ignore_index=True)
        if not bowling_recent.empty:
            self.team_bowling = pd.concat([self.team_bowling, bowling_recent], ignore_index=True)
        if not result_recent.empty:
            self.team_results = pd.concat([self.team_results, result_recent], ignore_index=True)

        player_dates = self.player_innings.get("date", pd.Series(dtype="datetime64[ns]"))
        result_dates = self.team_results.get("date", pd.Series(dtype="datetime64[ns]"))
        all_dates = pd.concat([player_dates.dropna(), result_dates.dropna()], ignore_index=True)
        date_range = self.dataset_summary.date_range if hasattr(self, "dataset_summary") else "Unknown"
        min_year = self.dataset_summary.min_year if hasattr(self, "dataset_summary") else None
        max_year = self.dataset_summary.max_year if hasattr(self, "dataset_summary") else None
        if not all_dates.empty:
            date_range = f"{date_label(all_dates.min())} to {date_label(all_dates.max())}"
            min_year = int(all_dates.min().year)
            max_year = int(all_dates.max().year)

        self.dataset_summary = DatasetSummary(
            formats=self.formats,
            total_player_rows=len(self.player_innings),
            total_result_rows=len(self.team_results),
            total_players=self.player_innings.get("player", pd.Series(dtype=object)).nunique(),
            total_teams=self.team_results.get("country", pd.Series(dtype=object)).nunique(),
            date_range=date_range,
            min_year=min_year,
            max_year=max_year,
        )

    def _optimize_loaded_frames(self):
        return

    def _load_all_data(self):
        merged_player_parquet = FINAL_DATA_DIR / "player_innings_1877_2025.parquet"
        merged_results_parquet = FINAL_DATA_DIR / "team_results_1877_2025.parquet"
        merged_player = FINAL_DATA_DIR / "player_innings_1877_2025.csv"
        merged_results = FINAL_DATA_DIR / "team_results_1877_2025.csv"
        if merged_player_parquet.exists() and merged_results_parquet.exists():
            self.player_innings = pd.read_parquet(merged_player_parquet, dtype_backend="pyarrow")
            self.team_results = pd.read_parquet(merged_results_parquet, dtype_backend="pyarrow")
            self.team_batting = pd.DataFrame()
            self.team_bowling = pd.DataFrame()
        elif merged_player.exists() and merged_results.exists():
            self.player_innings = pd.read_csv(merged_player, parse_dates=["date"])
            self.team_results = pd.read_csv(merged_results, parse_dates=["date"])
            self.team_batting = pd.DataFrame()
            self.team_bowling = pd.DataFrame()
        else:
            player_frames = []
            team_batting_frames = []
            team_bowling_frames = []
            result_frames = []

            for match_format, paths in DATA_SOURCES.items():
                player_frames.append(self._load_player_format(match_format, paths["player_files"]))
                team_batting_frames.append(self._load_team_batting_format(match_format, paths["team_batting_file"]))
                team_bowling_frames.append(self._load_team_bowling_format(match_format, paths["team_bowling_file"]))
                result_frames.append(self._load_results_format(match_format, paths["result_files"]))

            self.player_innings = pd.concat(player_frames, ignore_index=True) if player_frames else pd.DataFrame()
            self.team_batting = pd.concat(team_batting_frames, ignore_index=True) if team_batting_frames else pd.DataFrame()
            self.team_bowling = pd.concat(team_bowling_frames, ignore_index=True) if team_bowling_frames else pd.DataFrame()
            self.team_results = pd.concat(result_frames, ignore_index=True) if result_frames else pd.DataFrame()

        player_dates = self.player_innings.get("date", pd.Series(dtype="datetime64[ns]"))
        result_dates = self.team_results.get("date", pd.Series(dtype="datetime64[ns]"))
        all_dates = pd.concat([player_dates.dropna(), result_dates.dropna()], ignore_index=True)
        date_range = "Unknown"
        min_year = None
        max_year = None
        if not all_dates.empty:
            date_range = f"{date_label(all_dates.min())} to {date_label(all_dates.max())}"
            min_year = int(all_dates.min().year)
            max_year = int(all_dates.max().year)

        self.dataset_summary = DatasetSummary(
            formats=self.formats,
            total_player_rows=len(self.player_innings),
            total_result_rows=len(self.team_results),
            total_players=self.player_innings.get("player", pd.Series()).nunique() if len(self.player_innings) > 0 else 0,
            total_teams=self.team_results.get("country", pd.Series()).nunique() if len(self.team_results) > 0 else 0,
            date_range=date_range,
            min_year=min_year,
            max_year=max_year,
        )

    def _load_player_format(self, match_format, files):
        player_usecols = [
            "Innings Player",
            "Innings Runs Scored",
            "Innings Runs Scored Num",
            "Innings Minutes Batted",
            "Innings Batted Flag",
            "Innings Not Out Flag",
            "Innings Balls Faced",
            "Innings Boundary Fours",
            "Innings Boundary Sixes",
            "Innings Batting Strike Rate",
            "Innings Number",
            "Opposition",
            "Ground",
            "Innings Date",
            "Country",
            "50's",
            "100's",
            "Innings Overs Bowled",
            "Innings Bowled Flag",
            "Innings Maidens Bowled",
            "Innings Runs Conceded",
            "Innings Wickets Taken",
            "4 Wickets",
            "5 Wickets",
            "10 Wickets",
            "Innings Economy Rate",
        ]
        frames = []
        for file_path in files:
            df = read_statsguru_csv(file_path, usecols=player_usecols)
            df["format"] = match_format
            frames.append(df)
        df = pd.concat(frames, ignore_index=True)
        df.columns = [str(col).replace("\ufeff", "") for col in df.columns]

        rename_map = {
            "Innings Player": "player",
            "Innings Runs Scored": "runs_text",
            "Innings Runs Scored Num": "runs",
            "Innings Minutes Batted": "minutes",
            "Innings Batted Flag": "batted_flag",
            "Innings Not Out Flag": "not_out_flag",
            "Innings Balls Faced": "balls_faced",
            "Innings Boundary Fours": "fours",
            "Innings Boundary Sixes": "sixes",
            "Innings Batting Strike Rate": "batting_strike_rate",
            "Innings Number": "innings_number",
            "Opposition": "opposition",
            "Ground": "ground",
            "Innings Date": "date",
            "Country": "country",
            "50's": "fifty_flag",
            "100's": "hundred_flag",
            "Innings Overs Bowled": "overs_bowled",
            "Innings Bowled Flag": "bowled_flag",
            "Innings Maidens Bowled": "maidens",
            "Innings Runs Conceded": "runs_conceded",
            "Innings Wickets Taken": "wickets",
            "4 Wickets": "four_wicket_flag",
            "5 Wickets": "five_wicket_flag",
            "10 Wickets": "ten_wicket_flag",
            "Innings Economy Rate": "economy_rate",
        }
        df = df.rename(columns=rename_map)

        numeric_cols = [
            "runs",
            "minutes",
            "batted_flag",
            "not_out_flag",
            "balls_faced",
            "fours",
            "sixes",
            "batting_strike_rate",
            "innings_number",
            "fifty_flag",
            "hundred_flag",
            "overs_bowled",
            "bowled_flag",
            "maidens",
            "runs_conceded",
            "wickets",
            "four_wicket_flag",
            "five_wicket_flag",
            "ten_wicket_flag",
            "economy_rate",
        ]
        for col in numeric_cols:
            df[col] = to_numeric(df[col]) if col in df.columns else np.nan

        df["player"] = df["player"].map(clean_text)
        df["country"] = df["country"].map(clean_text)
        df["opposition"] = df["opposition"].map(parse_opposition)
        df["ground"] = df["ground"].map(clean_text)
        df["date"] = pd.to_datetime(df["date"], format="%Y/%m/%d", errors="coerce")
        df["balls_bowled"] = df["overs_bowled"].apply(overs_to_balls)
        df["outs"] = np.where(df["batted_flag"].fillna(0) == 1, 1 - df["not_out_flag"].fillna(0), 0)
        df["batted_flag"] = df["batted_flag"].fillna(0).astype(int)
        df["bowled_flag"] = df["bowled_flag"].fillna(0).astype(int)
        df["not_out_flag"] = df["not_out_flag"].fillna(0).astype(int)
        df["fifty_flag"] = df["fifty_flag"].fillna(0).astype(int)
        df["hundred_flag"] = df["hundred_flag"].fillna(0).astype(int)
        df["four_wicket_flag"] = df["four_wicket_flag"].fillna(0).astype(int)
        df["five_wicket_flag"] = df["five_wicket_flag"].fillna(0).astype(int)
        df["ten_wicket_flag"] = df["ten_wicket_flag"].fillna(0).astype(int)
        df["batting_score"] = df["runs"].fillna(0) + df["fifty_flag"] * 15 + df["hundred_flag"] * 35
        df["bowling_score"] = df["wickets"].fillna(0) * 20 + df["four_wicket_flag"] * 25 + df["five_wicket_flag"] * 35
        return df

    def _load_team_batting_format(self, match_format, file_path):
        df = read_statsguru_csv(file_path)
        df.columns = [str(col).replace("\ufeff", "") for col in df.columns]
        df["format"] = match_format
        df = df.rename(
            columns={
                "Country": "country",
                "Team Matches Played": "matches_played",
                "Matches Won": "matches_won",
                "Matches Lost": "matches_lost",
                "Matches Tied": "matches_tied",
                "Matches With No Result": "matches_no_result",
                "Win/Loss Ratio": "win_loss_ratio",
                "Avg Runs Per Wicket Batting": "batting_average",
                "Avg Runs Per Six Balls Batting": "batting_runs_per_over",
                "Number Of Team Innings Batting": "innings_batted",
                "Highest Team Score Batting": "highest_team_score",
                "Lowest Completed Score Batting": "lowest_completed_score",
            }
        )
        df["country"] = df["country"].map(clean_text)
        for col in df.columns:
            if col not in ["country", "format"]:
                df[col] = to_numeric(df[col])
        return df

    def _load_team_bowling_format(self, match_format, file_path):
        df = read_statsguru_csv(file_path)
        df.columns = [str(col).replace("\ufeff", "") for col in df.columns]
        df["format"] = match_format
        df = df.rename(
            columns={
                "Country": "country",
                "Avg Runs Per Wicket Bowling": "bowling_average",
                "Avg Runs Per Six Balls Bowling": "bowling_runs_per_over",
                "Number Of Team Innings Bowling": "innings_bowled",
                "Highest Team Score Bowling": "highest_score_conceded",
                "Lowest Completed Score Bowling": "lowest_completed_score_conceded",
            }
        )
        df["country"] = df["country"].map(clean_text)
        for col in df.columns:
            if col not in ["country", "format"]:
                df[col] = to_numeric(df[col])
        return df

    def _load_results_format(self, match_format, files):
        frames = []
        for file_path in files:
            df = read_statsguru_csv(file_path)
            df["format"] = match_format
            frames.append(df)
        df = pd.concat(frames, ignore_index=True)
        df.columns = [str(col).replace("\ufeff", "") for col in df.columns]
        df = df.rename(
            columns={
                "Result": "result",
                "Margin": "margin",
                "Match": "match",
                "Home/Away": "home_away",
                "Ground": "ground",
                "Match Date": "date",
                "Match Month": "month",
                "Match Year": "year",
                "Match Period": "period",
                "Matches": "matches",
                "Country": "country",
            }
        )
        df["country"] = df["country"].map(clean_text)
        df["ground"] = df["ground"].map(clean_text)
        df["match"] = df["match"].map(clean_text)
        df["home_away"] = df["home_away"].map(clean_text)
        df["result"] = df["result"].map(clean_text)
        df["date"] = pd.to_datetime(df["date"], format="%Y/%m/%d", errors="coerce")
        df["opponent"] = df.apply(lambda row: parse_match_opponent(row["match"], row["country"]), axis=1)
        df["won_flag"] = (df["result"] == "Won").astype(int)
        df["lost_flag"] = (df["result"] == "Lost").astype(int)
        df["tied_flag"] = (df["result"] == "Tied").astype(int)
        df["no_result_flag"] = df["result"].isin(["No Result", "Abandoned", "Drawn"]).astype(int)
        return df

    def _build_indexes(self):
        self.player_innings_indices_by_player = self.player_innings.groupby("player", dropna=False, observed=True).indices
        self.team_results_indices_by_country = self.team_results.groupby("country", dropna=False, observed=True).indices
        self.player_summary = self._build_player_summary()
        self.team_summary = self._build_team_summary()
        self.available_teams = sorted(self.team_summary["country"].dropna().astype(str).unique().tolist())
        self.available_players = sorted(self.player_summary["player"].dropna().astype(str).unique().tolist())
        self.team_strength_lookup = self.team_summary.set_index(["format", "country"]).to_dict("index")

    def _build_player_summary(self):
        grouped = (
            self.player_innings.groupby(["format", "country", "player"], dropna=False)
            .agg(
                batting_innings=("batted_flag", "sum"),
                runs=("runs", "sum"),
                outs=("outs", "sum"),
                balls_faced=("balls_faced", "sum"),
                fours=("fours", "sum"),
                sixes=("sixes", "sum"),
                fifties=("fifty_flag", "sum"),
                hundreds=("hundred_flag", "sum"),
                highest_score=("runs", "max"),
                bowling_innings=("bowled_flag", "sum"),
                balls_bowled=("balls_bowled", "sum"),
                maidens=("maidens", "sum"),
                runs_conceded=("runs_conceded", "sum"),
                wickets=("wickets", "sum"),
                four_wicket_hauls=("four_wicket_flag", "sum"),
                five_wicket_hauls=("five_wicket_flag", "sum"),
                first_match=("date", "min"),
                last_match=("date", "max"),
            )
            .reset_index()
        )
        grouped["batting_average"] = grouped.apply(lambda row: safe_divide(row["runs"], row["outs"]), axis=1)
        grouped["strike_rate"] = grouped.apply(lambda row: safe_divide(row["runs"] * 100, row["balls_faced"]), axis=1)
        grouped["bowling_average"] = grouped.apply(lambda row: safe_divide(row["runs_conceded"], row["wickets"]), axis=1)
        grouped["economy_rate"] = grouped.apply(lambda row: safe_divide(row["runs_conceded"] * 6, row["balls_bowled"]), axis=1)
        grouped["bowling_strike_rate"] = grouped.apply(lambda row: safe_divide(row["balls_bowled"], row["wickets"]), axis=1)
        grouped["boundary_runs"] = grouped["fours"].fillna(0) * 4 + grouped["sixes"].fillna(0) * 6
        grouped["boundary_percent"] = grouped.apply(lambda row: safe_divide(row["boundary_runs"] * 100, row["runs"]), axis=1)
        grouped["batting_impact"] = (
            grouped["runs"].fillna(0)
            + grouped["hundreds"].fillna(0) * 50
            + grouped["fifties"].fillna(0) * 20
        )
        grouped["bowling_impact"] = (
            grouped["wickets"].fillna(0) * 25
            + grouped["five_wicket_hauls"].fillna(0) * 40
            + grouped["four_wicket_hauls"].fillna(0) * 20
        )
        grouped["all_round_impact"] = grouped["batting_impact"] + grouped["bowling_impact"]
        grouped["role"] = grouped.apply(self._infer_role, axis=1)
        return grouped.sort_values(["format", "all_round_impact"], ascending=[True, False])

    def _infer_role(self, row):
        batting = row["batting_innings"] > 0 and row["runs"] >= 200
        bowling = row["bowling_innings"] > 0 and row["wickets"] >= 10
        if batting and bowling:
            return "All-Rounder"
        if bowling:
            return "Bowler"
        if batting:
            return "Batter"
        return "Utility"

    def _build_team_summary(self):
        batting_rows = self.player_innings[self.player_innings["batted_flag"].fillna(0) == 1].copy()
        bowling_rows = self.player_innings[self.player_innings["bowled_flag"].fillna(0) == 1].copy()

        batting_innings = (
            batting_rows.groupby(["format", "country", "date", "ground", "innings_number", "opposition"], dropna=False)
            .agg(
                team_runs=("runs", "sum"),
                team_balls=("balls_faced", "sum"),
                team_outs=("outs", "sum"),
            )
            .reset_index()
        )
        batting_summary = (
            batting_innings.groupby(["format", "country"], dropna=False)
            .agg(
                innings_batted=("team_runs", "count"),
                runs_scored=("team_runs", "sum"),
                balls_faced=("team_balls", "sum"),
                wickets_lost=("team_outs", "sum"),
                highest_team_score=("team_runs", "max"),
                lowest_completed_score=("team_runs", "min"),
            )
            .reset_index()
        )
        batting_summary["batting_average"] = batting_summary.apply(
            lambda row: safe_divide(row["runs_scored"], row["wickets_lost"]), axis=1
        )
        batting_summary["batting_runs_per_over"] = batting_summary.apply(
            lambda row: safe_divide(row["runs_scored"] * 6, row["balls_faced"]), axis=1
        )

        bowling_summary = (
            bowling_rows.groupby(["format", "country"], dropna=False)
            .agg(
                innings_bowled=("bowled_flag", "sum"),
                balls_bowled=("balls_bowled", "sum"),
                runs_conceded=("runs_conceded", "sum"),
                wickets=("wickets", "sum"),
                highest_score_conceded=("runs_conceded", "max"),
                lowest_completed_score_conceded=("runs_conceded", "min"),
            )
            .reset_index()
        )
        bowling_summary["bowling_average"] = bowling_summary.apply(
            lambda row: safe_divide(row["runs_conceded"], row["wickets"]), axis=1
        )
        bowling_summary["bowling_runs_per_over"] = bowling_summary.apply(
            lambda row: safe_divide(row["runs_conceded"] * 6, row["balls_bowled"]), axis=1
        )

        merged = batting_summary.merge(
            bowling_summary[
                [
                    "format",
                    "country",
                    "innings_bowled",
                    "highest_score_conceded",
                    "lowest_completed_score_conceded",
                    "bowling_average",
                    "bowling_runs_per_over",
                ]
            ],
            on=["format", "country"],
            how="outer",
        )
        results = (
            self.team_results.groupby(["format", "country"], dropna=False)
            .agg(
                matches_from_results=("matches", "sum"),
                wins=("won_flag", "sum"),
                losses=("lost_flag", "sum"),
                ties=("tied_flag", "sum"),
                no_results=("no_result_flag", "sum"),
                first_match=("date", "min"),
                last_match=("date", "max"),
            )
            .reset_index()
        )
        merged = merged.merge(results, on=["format", "country"], how="left")
        merged["matches_played"] = merged["matches_from_results"]
        merged["win_rate"] = merged.apply(lambda row: safe_divide(row["wins"] * 100, row["matches_played"]), axis=1)
        merged["loss_rate"] = merged.apply(lambda row: safe_divide(row["losses"] * 100, row["matches_played"]), axis=1)
        return merged.sort_values(["format", "win_rate"], ascending=[True, False])

    def _head_to_head_rate(self, match_format, team_name, opponent):
        subset = self.team_results[
            (self.team_results["format"] == match_format)
            & (self.team_results["country"] == team_name)
            & (self.team_results["opponent"] == opponent)
        ]
        if subset.empty:
            return 50.0
        return float(subset["won_flag"].mean() * 100)

    def _train_match_model(self):
        self.model_features = [
            "win_rate",
            "batting_average",
            "batting_runs_per_over",
            "bowling_average",
            "bowling_runs_per_over",
            "highest_team_score",
            "lowest_completed_score",
            "head_to_head_win_rate",
        ]
        self.match_model = {
            "trained_on_rows": int(len(self.team_results)),
            "formats": self.formats,
        }

    def predict_match(self, match_format, team_a, team_b, venue_mode="Neutral", year=None):
        own_key = (match_format, team_a)
        opp_key = (match_format, team_b)
        own_stats = self.team_strength_lookup.get(own_key)
        opp_stats = self.team_strength_lookup.get(opp_key)
        if own_stats is None or opp_stats is None:
            return None

        normalized_mode = venue_mode.title()
        if normalized_mode not in ["Home", "Away", "Neutral"]:
            normalized_mode = "Neutral"
        h2h = self._head_to_head_rate(match_format, team_a, team_b)
        win_rate_edge = (own_stats.get("win_rate", 50.0) - opp_stats.get("win_rate", 50.0)) * 0.35
        batting_edge = (own_stats.get("batting_average", 0.0) - opp_stats.get("batting_average", 0.0)) * 0.20
        scoring_edge = (own_stats.get("batting_runs_per_over", 0.0) - opp_stats.get("batting_runs_per_over", 0.0)) * 6.0
        bowling_edge = (opp_stats.get("bowling_average", 0.0) - own_stats.get("bowling_average", 0.0)) * 0.18
        economy_edge = (opp_stats.get("bowling_runs_per_over", 0.0) - own_stats.get("bowling_runs_per_over", 0.0)) * 8.0
        h2h_edge = (h2h - 50.0) * 0.25
        venue_edge = 0.0
        if normalized_mode == "Home":
            venue_edge = 4.0
        elif normalized_mode == "Away":
            venue_edge = -4.0
        probability = clamp(
            0.5 + (win_rate_edge + batting_edge + scoring_edge + bowling_edge + economy_edge + h2h_edge + venue_edge) / 100,
            0.05,
            0.95,
        )
        winner = team_a if probability >= 0.5 else team_b
        loser = team_b if winner == team_a else team_a
        return {
            "format": match_format,
            "team_a": team_a,
            "team_b": team_b,
            "venue_mode": normalized_mode,
            "winner": winner,
            "loser": loser,
            "team_a_win_probability": round(probability * 100, 2),
            "team_b_win_probability": round((1 - probability) * 100, 2),
            "head_to_head_team_a": round(h2h, 2),
            "team_a_strength": {
                "win_rate": scalar_or_none(own_stats.get("win_rate")),
                "batting_average": scalar_or_none(own_stats.get("batting_average")),
                "batting_runs_per_over": scalar_or_none(own_stats.get("batting_runs_per_over")),
                "bowling_average": scalar_or_none(own_stats.get("bowling_average")),
                "bowling_runs_per_over": scalar_or_none(own_stats.get("bowling_runs_per_over")),
            },
            "team_b_strength": {
                "win_rate": scalar_or_none(opp_stats.get("win_rate")),
                "batting_average": scalar_or_none(opp_stats.get("batting_average")),
                "batting_runs_per_over": scalar_or_none(opp_stats.get("batting_runs_per_over")),
                "bowling_average": scalar_or_none(opp_stats.get("bowling_average")),
                "bowling_runs_per_over": scalar_or_none(opp_stats.get("bowling_runs_per_over")),
            },
        }

    def get_formats(self):
        return self.formats

    def get_date_bounds(self):
        return {
            "min_year": self.dataset_summary.min_year,
            "max_year": self.dataset_summary.max_year,
        }

    def get_teams(self, match_format=None):
        df = self.team_summary
        if match_format and match_format != "All":
            df = df[df["format"] == match_format]
        return sorted(df["country"].dropna().unique().tolist())

    def search_players(self, query="", match_format="All", country="All"):
        df = self.player_summary.copy()
        if match_format != "All":
            df = df[df["format"] == match_format]
        if country != "All":
            df = df[df["country"] == country]
        query = normalize_name(query)
        if query:
            tokens = [token for token in query.split() if token]
            player_norm = df["player"].map(normalize_name)
            country_norm = df["country"].map(normalize_name)
            mask = player_norm.str.contains(query, na=False) | country_norm.str.contains(query, na=False)
            if tokens:
                token_mask = False
                for token in tokens:
                    token_mask = token_mask | player_norm.str.contains(token, na=False) | country_norm.str.contains(token, na=False)
                mask = mask | token_mask
            df = df[mask]
        return df.sort_values(["all_round_impact", "runs", "wickets"], ascending=[False, False, False]).head(200)

    def search_teams(self, query="", match_format="All"):
        df = self.team_summary.copy()
        if match_format != "All":
            df = df[df["format"] == match_format]
        query = clean_text(query).lower()
        if query:
            df = df[df["country"].str.lower().str.contains(query, na=False)]
        return df.sort_values(["win_rate", "matches_played"], ascending=[False, False]).head(100)

    def get_player_profile(self, player_name, match_format="All"):
        summary = self.player_summary[self.player_summary["player"] == player_name].copy()
        if match_format != "All":
            summary = summary[summary["format"] == match_format]
        if summary.empty:
            return None

        innings_idx = self.player_innings_indices_by_player.get(player_name, [])
        innings = self.player_innings.loc[innings_idx].copy()
        if match_format != "All":
            innings = innings[innings["format"] == match_format]

        profile = summary.sort_values("all_round_impact", ascending=False).iloc[0].to_dict()

        against = (
            innings.groupby(["format", "country", "opposition"], dropna=False)
            .agg(
                innings=("batted_flag", "sum"),
                runs=("runs", "sum"),
                outs=("outs", "sum"),
                balls=("balls_faced", "sum"),
                wickets=("wickets", "sum"),
                runs_conceded=("runs_conceded", "sum"),
                bowling_balls=("balls_bowled", "sum"),
                fifties=("fifty_flag", "sum"),
                hundreds=("hundred_flag", "sum"),
            )
            .reset_index()
        )
        against["batting_average"] = against.apply(lambda row: safe_divide(row["runs"], row["outs"]), axis=1)
        against["strike_rate"] = against.apply(lambda row: safe_divide(row["runs"] * 100, row["balls"]), axis=1)
        against["bowling_average"] = against.apply(lambda row: safe_divide(row["runs_conceded"], row["wickets"]), axis=1)
        against["economy_rate"] = against.apply(lambda row: safe_divide(row["runs_conceded"] * 6, row["bowling_balls"]), axis=1)
        against = against.sort_values(["innings", "runs", "wickets"], ascending=[False, False, False])

        by_ground = (
            innings.groupby(["format", "ground"], dropna=False)
            .agg(
                innings=("batted_flag", "sum"),
                runs=("runs", "sum"),
                wickets=("wickets", "sum"),
            )
            .reset_index()
            .sort_values(["innings", "runs"], ascending=[False, False])
        )

        by_year = (
            innings.assign(year=innings["date"].dt.year)
            .groupby(["format", "year"], dropna=False)
            .agg(
                innings=("batted_flag", "sum"),
                runs=("runs", "sum"),
                wickets=("wickets", "sum"),
                hundreds=("hundred_flag", "sum"),
                five_wicket_hauls=("five_wicket_flag", "sum"),
            )
            .reset_index()
            .sort_values(["format", "year"])
        )

        recent = innings.sort_values("date", ascending=False).head(15).copy()
        recent["date"] = recent["date"].astype(str)

        return {
            "profile": profile,
            "career_by_format": summary.sort_values("format"),
            "against": against,
            "by_ground": by_ground,
            "by_year": by_year,
            "recent": recent[
                [
                    "format",
                    "date",
                    "country",
                    "opposition",
                    "ground",
                    "runs",
                    "balls_faced",
                    "batting_strike_rate",
                    "wickets",
                    "runs_conceded",
                    "economy_rate",
                ]
            ],
        }

    def get_team_profile(self, team_name, match_format="All"):
        summary = self.team_summary[self.team_summary["country"] == team_name].copy()
        if match_format != "All":
            summary = summary[summary["format"] == match_format]
        if summary.empty:
            return None

        results_idx = self.team_results_indices_by_country.get(team_name, [])
        results = self.team_results.loc[results_idx].copy()
        if match_format != "All":
            results = results[results["format"] == match_format]

        top_players = self.player_summary[self.player_summary["country"] == team_name].copy()
        if match_format != "All":
            top_players = top_players[top_players["format"] == match_format]

        against = (
            results.groupby(["format", "opponent"], dropna=False)
            .agg(matches=("matches", "sum"), wins=("won_flag", "sum"), losses=("lost_flag", "sum"), ties=("tied_flag", "sum"))
            .reset_index()
        )
        against["win_rate"] = against.apply(lambda row: safe_divide(row["wins"] * 100, row["matches"]), axis=1)
        against = against.sort_values(["matches", "win_rate"], ascending=[False, False])

        home_away = (
            results.groupby(["format", "home_away"], dropna=False)
            .agg(matches=("matches", "sum"), wins=("won_flag", "sum"), losses=("lost_flag", "sum"))
            .reset_index()
        )
        home_away["win_rate"] = home_away.apply(lambda row: safe_divide(row["wins"] * 100, row["matches"]), axis=1)

        by_ground = (
            results.groupby(["format", "ground"], dropna=False)
            .agg(matches=("matches", "sum"), wins=("won_flag", "sum"), losses=("lost_flag", "sum"))
            .reset_index()
        )
        by_ground["win_rate"] = by_ground.apply(lambda row: safe_divide(row["wins"] * 100, row["matches"]), axis=1)
        by_ground = by_ground.sort_values(["matches", "win_rate"], ascending=[False, False])

        recent = results.sort_values("date", ascending=False).head(15).copy()
        recent["date"] = recent["date"].astype(str)

        return {
            "profile": summary.sort_values("format"),
            "against": against,
            "home_away": home_away,
            "by_ground": by_ground,
            "top_batters": top_players.sort_values(["runs", "batting_average"], ascending=[False, False]).head(10),
            "top_bowlers": top_players.sort_values(["wickets", "bowling_average"], ascending=[False, True]).head(10),
            "recent": recent[["format", "date", "opponent", "result", "margin", "home_away", "ground"]],
            "notes": [
                "This dataset includes team results, team batting summary, team bowling summary, and player innings records.",
                "Toss-based analysis is not available in these Statsguru files because toss fields are not present.",
            ],
        }

    def get_team_form(self, team_name, match_format="All", window=10):
        results_idx = self.team_results_indices_by_country.get(team_name, [])
        results = self.team_results.loc[results_idx].copy()
        if match_format != "All":
            results = results[results["format"] == match_format]
        if results.empty:
            return None

        recent = results.sort_values("date", ascending=False).head(window).copy()
        weighted = np.linspace(window, 1, len(recent))
        weighted_wins = recent["won_flag"].fillna(0).to_numpy()
        weighted_losses = recent["lost_flag"].fillna(0).to_numpy()
        momentum = safe_divide(np.dot(weighted_wins, weighted) * 100, weighted.sum())
        volatility = recent["won_flag"].fillna(0).std() * 100 if len(recent) > 1 else 0.0
        recent["date"] = recent["date"].astype(str)
        recent["performance_label"] = np.where(recent["won_flag"] == 1, "Win", np.where(recent["lost_flag"] == 1, "Loss", "Other"))

        return {
            "team": team_name,
            "format": match_format,
            "window": window,
            "matches": len(recent),
            "wins": int(recent["won_flag"].sum()),
            "losses": int(recent["lost_flag"].sum()),
            "win_rate": scalar_or_none(recent["won_flag"].mean() * 100),
            "momentum_score": scalar_or_none(momentum),
            "volatility_index": scalar_or_none(volatility),
            "current_streak": compute_streak(recent["won_flag"].fillna(0).astype(int).tolist()),
            "recent_matches": recent[["date", "opponent", "result", "margin", "home_away", "ground", "performance_label"]],
        }

    def get_player_form(self, player_name, match_format="All", window=10):
        innings_idx = self.player_innings_indices_by_player.get(player_name, [])
        innings = self.player_innings.loc[innings_idx].copy()
        if match_format != "All":
            innings = innings[innings["format"] == match_format]
        if innings.empty:
            return None

        recent = innings.sort_values("date", ascending=False).head(window).copy()
        recent["impact_score"] = (
            recent["runs"].fillna(0)
            + recent["wickets"].fillna(0) * 25
            + recent["fifty_flag"].fillna(0) * 15
            + recent["hundred_flag"].fillna(0) * 30
        )
        volatility = recent["impact_score"].std() if len(recent) > 1 else 0.0
        recent["date"] = recent["date"].astype(str)
        return {
            "player": player_name,
            "format": match_format,
            "window": window,
            "innings": len(recent),
            "average_runs": scalar_or_none(recent["runs"].mean()),
            "average_wickets": scalar_or_none(recent["wickets"].mean()),
            "average_impact": scalar_or_none(recent["impact_score"].mean()),
            "volatility_index": scalar_or_none(volatility),
            "recent_innings": recent[
                ["date", "country", "opposition", "ground", "runs", "balls_faced", "wickets", "impact_score"]
            ],
        }

    def get_head_to_head_analysis(self, match_format, team_a, team_b):
        subset = self.team_results[
            (self.team_results["format"] == match_format)
            & (self.team_results["country"] == team_a)
            & (self.team_results["opponent"] == team_b)
        ].copy()
        if subset.empty:
            return None

        recent = subset.sort_values("date", ascending=False).head(10).copy()
        overall_matches = len(subset)
        team_a_wins = int(subset["won_flag"].sum())
        team_b_wins = int(subset["lost_flag"].sum())
        recent_team_a_wins = int(recent["won_flag"].sum())
        predicted = self.predict_match(match_format, team_a, team_b, "Neutral")
        edge = "Balanced"
        if recent_team_a_wins >= 7:
            edge = f"{team_a} have a strong recent psychological edge"
        elif recent_team_a_wins <= 3:
            edge = f"{team_b} have a strong recent psychological edge"
        elif team_a_wins > team_b_wins:
            edge = f"{team_a} hold a slight historical edge"
        elif team_b_wins > team_a_wins:
            edge = f"{team_b} hold a slight historical edge"

        venue_split = (
            subset.groupby("home_away", dropna=False)
            .agg(matches=("matches", "sum"), wins=("won_flag", "sum"), losses=("lost_flag", "sum"))
            .reset_index()
        )
        venue_split["win_rate"] = venue_split.apply(lambda row: safe_divide(row["wins"] * 100, row["matches"]), axis=1)
        recent["date"] = recent["date"].astype(str)
        return {
            "format": match_format,
            "team_a": team_a,
            "team_b": team_b,
            "matches": overall_matches,
            "team_a_wins": team_a_wins,
            "team_b_wins": team_b_wins,
            "team_a_win_rate": scalar_or_none(safe_divide(team_a_wins * 100, overall_matches)),
            "recent_last_10_team_a_wins": recent_team_a_wins,
            "psychological_edge": edge,
            "model_prediction": predicted,
            "venue_split": venue_split,
            "recent_meetings": recent[["date", "ground", "home_away", "result", "margin"]],
        }

    def compare_players(self, player_a, player_b, match_format="All"):
        profile_a = self.get_player_profile(player_a, match_format)
        profile_b = self.get_player_profile(player_b, match_format)
        if not profile_a or not profile_b:
            return None

        a = profile_a["profile"]
        b = profile_b["profile"]
        metrics = [
            "runs",
            "batting_average",
            "strike_rate",
            "wickets",
            "bowling_average",
            "economy_rate",
            "all_round_impact",
        ]
        comparison_rows = []
        for metric in metrics:
            a_val = scalar_or_none(a.get(metric))
            b_val = scalar_or_none(b.get(metric))
            if metric in ["bowling_average", "economy_rate"]:
                winner = player_a if (a_val is not None and b_val is not None and a_val < b_val) else player_b
            else:
                winner = player_a if (a_val or 0) >= (b_val or 0) else player_b
            comparison_rows.append({"metric": metric, "player_a": a_val, "player_b": b_val, "leader": winner})

        form_a = self.get_player_form(player_a, match_format, window=8)
        form_b = self.get_player_form(player_b, match_format, window=8)
        return {
            "format": match_format,
            "player_a": {"name": player_a, **{key: scalar_or_none(val) for key, val in a.items() if key in metrics or key in ["country", "role"]}},
            "player_b": {"name": player_b, **{key: scalar_or_none(val) for key, val in b.items() if key in metrics or key in ["country", "role"]}},
            "comparison": comparison_rows,
            "form_snapshot": {
                "player_a_average_impact": form_a["average_impact"] if form_a else None,
                "player_b_average_impact": form_b["average_impact"] if form_b else None,
            },
        }

    def get_opposition_report(self, match_format, team_name, opponent):
        h2h = self.get_head_to_head_analysis(match_format, team_name, opponent)
        team_form = self.get_team_form(team_name, match_format, window=8)
        opponent_form = self.get_team_form(opponent, match_format, window=8)
        if not h2h or not team_form or not opponent_form:
            return None

        opponent_players = self.player_innings[
            (self.player_innings["format"] == match_format)
            & (self.player_innings["country"] == opponent)
            & (self.player_innings["opposition"] == team_name)
        ].copy()
        top_batters = (
            opponent_players.groupby("player", dropna=False)
            .agg(innings=("batted_flag", "sum"), runs=("runs", "sum"), average_runs=("runs", "mean"))
            .reset_index()
            .sort_values(["runs", "average_runs"], ascending=[False, False])
            .head(5)
        )
        top_bowlers = (
            opponent_players.groupby("player", dropna=False)
            .agg(innings=("bowled_flag", "sum"), wickets=("wickets", "sum"), economy_rate=("economy_rate", "mean"))
            .reset_index()
            .sort_values(["wickets", "economy_rate"], ascending=[False, True])
            .head(5)
        )
        vulnerabilities = []
        if (h2h["team_a_win_rate"] or 0) < 45:
            vulnerabilities.append(f"{team_name} trail this matchup historically.")
        if (team_form["momentum_score"] or 0) < (opponent_form["momentum_score"] or 0):
            vulnerabilities.append(f"{opponent} enter with stronger recent momentum.")
        if not vulnerabilities:
            vulnerabilities.append(f"{team_name} appear competitive on both history and recent form.")

        return {
            "format": match_format,
            "team": team_name,
            "opponent": opponent,
            "head_to_head": h2h,
            "team_form": team_form,
            "opponent_form": opponent_form,
            "threat_batters": top_batters,
            "threat_bowlers": top_bowlers,
            "vulnerabilities": vulnerabilities,
        }

    def detect_upset(self, match_format, team_a, team_b):
        prediction = self.predict_match(match_format, team_a, team_b, "Neutral")
        if prediction is None:
            return None
        team_a_form = self.get_team_form(team_a, match_format, window=8)
        team_b_form = self.get_team_form(team_b, match_format, window=8)
        if not team_a_form or not team_b_form:
            return None

        favorite = prediction["winner"]
        underdog = team_b if favorite == team_a else team_a
        favorite_prob = max(prediction["team_a_win_probability"], prediction["team_b_win_probability"])
        form_gap = abs((team_a_form["momentum_score"] or 0) - (team_b_form["momentum_score"] or 0))
        upset_score = max(0.0, min(100.0, 100 - favorite_prob + (25 - min(form_gap, 25))))
        return {
            "format": match_format,
            "favorite": favorite,
            "underdog": underdog,
            "favorite_win_probability": favorite_prob,
            "upset_probability": round(upset_score, 2),
            "reason": (
                f"{underdog} remain live because recent form is closer than the headline win probability suggests."
                if upset_score >= 45
                else f"The model sees a relatively stable matchup with limited underdog pressure."
            ),
        }

    def query_natural_language(self, query, match_format="ODI"):
        text = normalize_name(query)
        if not text:
            return {"intent": "unknown", "message": "Please enter a cricket question."}

        if "predict" in text and " vs " in text:
            raw = clean_text(query)
            parts = [part.strip(" ?") for part in raw.replace("Predict", "").replace("predict", "").split("vs")]
            if len(parts) == 2:
                prediction = self.predict_match(match_format, parts[0].strip(), parts[1].strip(), "Neutral")
                return {
                    "intent": "match_prediction",
                    "answer": prediction,
                    "message": f"Predicted winner: {prediction['winner']}" if prediction else "I could not find those teams in the selected format.",
                }

        if "compare" in text and " and " in text:
            raw = clean_text(query)
            parts = [part.strip(" ?") for part in raw.replace("Compare", "").replace("compare", "").split(" and ")]
            if len(parts) == 2:
                comparison = self.compare_players(parts[0].strip(), parts[1].strip(), match_format)
                return {
                    "intent": "player_comparison",
                    "answer": comparison,
                    "message": "Player comparison generated." if comparison else "I could not compare those players in the selected format.",
                }

        if "form" in text:
            for team in self.get_teams(match_format):
                if normalize_name(team) in text:
                    form = self.get_team_form(team, match_format, window=8)
                    return {
                        "intent": "team_form",
                        "answer": form,
                        "message": f"{team} recent win rate is {form['win_rate']}%." if form else "Form data unavailable.",
                    }

        if "best player" in text:
            summary = self.player_summary[self.player_summary["format"] == match_format].sort_values("all_round_impact", ascending=False).head(1)
            if not summary.empty:
                row = summary.iloc[0]
                return {
                    "intent": "best_player",
                    "answer": {"player": row["player"], "country": row["country"], "all_round_impact": scalar_or_none(row["all_round_impact"])},
                    "message": f"{row['player']} rates as the top all-round impact player in {match_format}.",
                }

        return {
            "intent": "unknown",
            "message": "Try queries like 'Predict India vs Australia', 'Compare Virat Kohli and Babar Azam', or 'Show Pakistan form'.",
        }


if __name__ == "__main__":
    engine = CricketAnalyticsEngine()
    print("Cricket Analytics Engine Ready")
    print(f"Formats: {', '.join(engine.dataset_summary.formats)}")
    print(f"Player innings rows: {engine.dataset_summary.total_player_rows}")
    print(f"Team result rows: {engine.dataset_summary.total_result_rows}")
    print(f"Players: {engine.dataset_summary.total_players}")
    print(f"Teams: {engine.dataset_summary.total_teams}")
    print(f"Date range: {engine.dataset_summary.date_range}")
