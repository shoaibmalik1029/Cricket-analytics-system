import logging
from functools import lru_cache
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from fastapi.middleware.cors import CORSMiddleware

from backend.cricket import CricketAnalyticsEngine


logger = logging.getLogger("elite-cricket-api")
logging.basicConfig(level=logging.INFO)
BASE_DIR = Path(__file__).resolve().parent.parent
FINAL_DATA_DIR = BASE_DIR / "data" / "final"
CACHE_DIR = BASE_DIR / ".cricket_cache"


def clean_value(value: Any):
    if isinstance(value, (np.floating, float)):
        if np.isnan(value):
            return None
        return round(float(value), 4)
    if isinstance(value, (np.integer, int)):
        return int(value)
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if pd.isna(value):
        return None
    return value


def records(df: pd.DataFrame, limit: int | None = None):
    if df is None:
        return []
    if limit is not None:
        df = df.head(limit)
    rows = []
    for item in df.to_dict(orient="records"):
        rows.append({key: clean_value(val) for key, val in item.items()})
    return rows


@lru_cache(maxsize=1)
def get_engine():
    return CricketAnalyticsEngine()


app = FastAPI(title="Cricket Analytics API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class PredictionRequest(BaseModel):
    format: str
    team_a: str
    team_b: str
    venue_mode: str = "Neutral"
    year: int | None = None


class NaturalLanguageQueryRequest(BaseModel):
    query: str
    format: str = "ODI"


class ScoredMatchRequest(BaseModel):
    teamA: str
    teamB: str
    battingTeam: str | None = None
    bowlingTeam: str | None = None
    format: str = Field(default="ODI")
    ground: str = Field(default="Local Ground")
    matchDate: str | None = None
    innings: list[dict[str, Any]] = Field(default_factory=list)


class MetaResponse(BaseModel):
    formats: list[str]
    total_player_rows: int
    total_result_rows: int
    total_players: int
    total_teams: int
    date_range: str
    min_year: int | None = None
    max_year: int | None = None


class ListResponse(BaseModel):
    items: list[dict[str, Any]]


class PlayerListResponse(ListResponse):
    countries: list[str]


class TeamListResponse(ListResponse):
    teams: list[str]


@app.get("/health")
def health():
    return {"status": "ok"}


@app.on_event("startup")
def warm_engine():
    get_engine()


@app.get("/meta", response_model=MetaResponse)
@app.get("/api/meta", response_model=MetaResponse)
def meta():
    engine = get_engine()
    summary = engine.dataset_summary
    return {
        "formats": summary.formats,
        "total_player_rows": summary.total_player_rows,
        "total_result_rows": summary.total_result_rows,
        "total_players": summary.total_players,
        "total_teams": summary.total_teams,
        "date_range": summary.date_range,
        "min_year": summary.min_year,
        "max_year": summary.max_year,
    }


@app.get("/dashboard")
def dashboard():
    engine = get_engine()
    top_teams = engine.team_summary.sort_values("win_rate", ascending=False).head(8)
    top_batters = engine.player_summary.sort_values("runs", ascending=False).head(8)
    top_bowlers = engine.player_summary.sort_values("wickets", ascending=False).head(8)
    batting_velocity = (
        engine.team_summary.groupby("format")["batting_runs_per_over"].mean().reset_index().rename(columns={"batting_runs_per_over": "value"})
    )
    win_rate_by_format = (
        engine.team_summary.groupby("format")["win_rate"].mean().reset_index().rename(columns={"win_rate": "value"})
    )
    return {
        "summary": meta(),
        "top_teams": records(top_teams),
        "top_batters": records(top_batters),
        "top_bowlers": records(top_bowlers),
        "batting_velocity": records(batting_velocity),
        "average_win_rate_by_format": records(win_rate_by_format),
        "prediction_sample": engine.predict_match("ODI", "India", "Australia", "Neutral")
        if "India" in engine.get_teams("ODI") and "Australia" in engine.get_teams("ODI")
        else None,
    }


@app.get("/predict/options")
@app.get("/api/predict/options")
def predict_options(format: str = Query("ODI")):
    engine = get_engine()
    return {
        "formats": engine.get_formats(),
        "teams": engine.get_teams(format),
        "venue_modes": ["Home", "Away", "Neutral"],
        **engine.get_date_bounds(),
    }


@app.post("/predict")
@app.post("/api/predict")
def predict(payload: PredictionRequest):
    engine = get_engine()
    result = engine.predict_match(
        match_format=payload.format,
        team_a=payload.team_a,
        team_b=payload.team_b,
        venue_mode=payload.venue_mode,
        year=payload.year,
    )
    if result is None:
        raise HTTPException(status_code=404, detail="Prediction could not be generated for the supplied teams/format.")
    return result


@app.get("/teams", response_model=TeamListResponse)
@app.get("/api/teams", response_model=TeamListResponse)
def teams(
    format: str = Query("All"),
    query: str = Query(""),
):
    engine = get_engine()
    result = engine.search_teams(query=query, match_format=format)
    return {
        "items": records(result, limit=100),
        "teams": engine.get_teams(format if format != "All" else None),
    }


@app.get("/teams/{team_name}")
@app.get("/api/teams/{team_name}")
def team_profile(team_name: str, format: str = Query("All")):
    engine = get_engine()
    report = engine.get_team_profile(team_name, match_format=format)
    if not report:
        raise HTTPException(status_code=404, detail="Team not found")
    return {
        "profile": records(report["profile"]),
        "against": records(report["against"], limit=20),
        "home_away": records(report["home_away"], limit=20),
        "by_ground": records(report["by_ground"], limit=20),
        "top_batters": records(report["top_batters"], limit=10),
        "top_bowlers": records(report["top_bowlers"], limit=10),
        "recent": records(report["recent"], limit=15),
        "notes": report["notes"],
    }


@app.get("/players", response_model=PlayerListResponse)
@app.get("/api/players", response_model=PlayerListResponse)
def players(
    format: str = Query("All"),
    country: str = Query("All"),
    query: str = Query(""),
):
    engine = get_engine()
    result = engine.search_players(query=query, match_format=format, country=country)
    teams = engine.get_teams(format if format != "All" else None)
    return {
        "items": records(result, limit=200),
        "countries": teams,
    }


@app.get("/players/{player_name}")
@app.get("/api/players/{player_name}")
def player_profile(player_name: str, format: str = Query("All")):
    engine = get_engine()
    report = engine.get_player_profile(player_name, match_format=format)
    if not report:
        raise HTTPException(status_code=404, detail="Player not found")
    return {
        "profile": {key: clean_value(val) for key, val in report["profile"].items()},
        "career_by_format": records(report["career_by_format"]),
        "against": records(report["against"], limit=20),
        "by_ground": records(report["by_ground"], limit=20),
        "by_year": records(report["by_year"], limit=50),
        "recent": records(report["recent"], limit=15),
    }


@app.get("/analysis/head-to-head")
@app.get("/api/analysis/head-to-head")
@app.get("/api/matchup")
def head_to_head(
    format: str = Query("ODI"),
    team_a: str = Query(...),
    team_b: str = Query(...),
):
    engine = get_engine()
    report = engine.get_head_to_head_analysis(format, team_a, team_b)
    if not report:
        raise HTTPException(status_code=404, detail="Head-to-head analysis could not be generated for the supplied teams.")
    return {
        **report,
        "model_prediction": report["model_prediction"],
        "venue_split": records(report["venue_split"]),
        "recent_meetings": records(report["recent_meetings"], limit=10),
    }


@app.get("/analysis/team-form")
@app.get("/api/analysis/team-form")
def team_form(
    team: str = Query(...),
    format: str = Query("ODI"),
    window: int = Query(8, ge=3, le=20),
):
    engine = get_engine()
    report = engine.get_team_form(team, format, window)
    if not report:
        raise HTTPException(status_code=404, detail="Team form could not be generated.")
    return {
        **report,
        "recent_matches": records(report["recent_matches"], limit=window),
    }


@app.get("/analysis/player-form")
@app.get("/api/analysis/player-form")
def player_form(
    player: str = Query(...),
    format: str = Query("ODI"),
    window: int = Query(8, ge=3, le=20),
):
    engine = get_engine()
    report = engine.get_player_form(player, format, window)
    if not report:
        raise HTTPException(status_code=404, detail="Player form could not be generated.")
    return {
        **report,
        "recent_innings": records(report["recent_innings"], limit=window),
    }


@app.get("/analysis/player-comparison")
@app.get("/api/analysis/player-comparison")
@app.get("/api/compare")
def player_comparison(
    player_a: str = Query(...),
    player_b: str = Query(...),
    format: str = Query("All"),
):
    engine = get_engine()
    report = engine.compare_players(player_a, player_b, format)
    if not report:
        raise HTTPException(status_code=404, detail="Player comparison could not be generated.")
    return report


@app.get("/analysis/opposition-report")
@app.get("/api/analysis/opposition-report")
def opposition_report(
    format: str = Query("ODI"),
    team: str = Query(...),
    opponent: str = Query(...),
):
    engine = get_engine()
    report = engine.get_opposition_report(format, team, opponent)
    if not report:
        raise HTTPException(status_code=404, detail="Opposition analysis report could not be generated.")
    return {
        **report,
        "threat_batters": records(report["threat_batters"], limit=5),
        "threat_bowlers": records(report["threat_bowlers"], limit=5),
    }


@app.get("/analysis/upset")
@app.get("/api/analysis/upset")
def upset_detector(
    format: str = Query("ODI"),
    team_a: str = Query(...),
    team_b: str = Query(...),
):
    engine = get_engine()
    report = engine.detect_upset(format, team_a, team_b)
    if not report:
        raise HTTPException(status_code=404, detail="Upset probability could not be generated.")
    return report


@app.post("/query")
@app.post("/api/query")
def natural_language_query(payload: NaturalLanguageQueryRequest):
    engine = get_engine()
    return engine.query_natural_language(payload.query, payload.format)


@app.post("/scorer/matches")
@app.post("/api/scorer/matches")
def save_scored_match(payload: ScoredMatchRequest):
    if not payload.innings:
        raise HTTPException(status_code=400, detail="No innings found to save.")

    player_rows, team_rows = scored_match_to_dataset_rows(payload)
    if not player_rows or not team_rows:
        raise HTTPException(status_code=400, detail="The scorecard is incomplete and could not be converted.")

    append_rows_to_final_dataset(
        FINAL_DATA_DIR / "player_innings_1877_2025.csv",
        FINAL_DATA_DIR / "player_innings_1877_2025.parquet",
        pd.DataFrame(player_rows),
    )
    append_rows_to_final_dataset(
        FINAL_DATA_DIR / "team_results_1877_2025.csv",
        FINAL_DATA_DIR / "team_results_1877_2025.parquet",
        pd.DataFrame(team_rows),
    )

    clear_engine_cache()
    get_engine.cache_clear()
    return {
        "status": "saved",
        "player_rows": len(player_rows),
        "team_rows": len(team_rows),
        "message": "Scored match saved into the final analytics dataset.",
    }


def append_rows_to_final_dataset(csv_path: Path, parquet_path: Path, new_rows: pd.DataFrame):
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    existing_cols = pd.read_csv(csv_path, nrows=0).columns.tolist() if csv_path.exists() else new_rows.columns.tolist()
    for col in existing_cols:
        if col not in new_rows.columns:
            new_rows[col] = None
    new_rows = new_rows[existing_cols]

    if parquet_path.exists():
        existing = pd.read_parquet(parquet_path)
        if "date" in existing.columns:
            existing["date"] = pd.to_datetime(existing["date"], errors="coerce")
        for col in existing.columns:
            if col not in new_rows.columns:
                new_rows[col] = None
        for col in new_rows.columns:
            if col not in existing.columns:
                existing[col] = None
        aligned_rows = align_rows_to_existing_dtypes(new_rows[existing.columns].copy(), existing)
        merged = pd.concat([existing, aligned_rows], ignore_index=True)
        merged.to_parquet(parquet_path, index=False)
    else:
        new_rows.to_parquet(parquet_path, index=False)

    if csv_path.exists():
        new_rows.to_csv(csv_path, mode="a", header=False, index=False)
    else:
        new_rows.to_csv(csv_path, index=False)


def align_rows_to_existing_dtypes(new_rows: pd.DataFrame, existing: pd.DataFrame) -> pd.DataFrame:
    for col in existing.columns:
        if col not in new_rows.columns:
            continue
        if col == "date" or pd.api.types.is_datetime64_any_dtype(existing[col]):
            new_rows[col] = pd.to_datetime(new_rows[col], errors="coerce")
        elif pd.api.types.is_integer_dtype(existing[col]):
            new_rows[col] = pd.to_numeric(new_rows[col], errors="coerce").fillna(0).astype(existing[col].dtype)
        elif pd.api.types.is_float_dtype(existing[col]):
            new_rows[col] = pd.to_numeric(new_rows[col], errors="coerce").fillna(0.0).astype(existing[col].dtype)
        elif pd.api.types.is_bool_dtype(existing[col]):
            new_rows[col] = new_rows[col].fillna(False).astype(bool)
        else:
            new_rows[col] = new_rows[col].fillna("").astype(str)
    return new_rows


def clear_engine_cache():
    for path in CACHE_DIR.glob("*"):
        if path.is_file():
            try:
                path.unlink()
            except OSError:
                logger.warning("Could not remove cache file %s", path)


def scored_match_to_dataset_rows(payload: ScoredMatchRequest):
    match_date = pd.to_datetime(payload.matchDate or pd.Timestamp.today().date(), errors="coerce")
    if pd.isna(match_date):
        match_date = pd.Timestamp.today().normalize()
    match_date_text = match_date.date().isoformat()
    month = match_date.strftime("%b")
    year = int(match_date.year)
    period = f"{month} {year}"
    match_name = f"{payload.teamA} v {payload.teamB}"
    innings = payload.innings
    scores = {inning.get("battingTeam"): int(inning.get("totalRuns") or 0) for inning in innings}
    winner = None
    tied = False
    if len(scores) >= 2 and payload.teamA in scores and payload.teamB in scores:
        if scores[payload.teamA] > scores[payload.teamB]:
            winner = payload.teamA
        elif scores[payload.teamB] > scores[payload.teamA]:
            winner = payload.teamB
        else:
            tied = True

    player_rows = []
    for inning in innings:
        batting_team = inning.get("battingTeam") or ""
        bowling_team = inning.get("bowlingTeam") or (payload.teamB if batting_team == payload.teamA else payload.teamA)
        batters = inning.get("batters") or {}
        bowlers = inning.get("bowlers") or {}
        inning_number = int(inning.get("inningsNumber") or 1)

        for player, stats in batters.items():
            runs = int(stats.get("runs") or 0)
            balls = int(stats.get("balls") or 0)
            out = bool(stats.get("out"))
            player_rows.append({
                "player": player,
                "country": batting_team,
                "format": payload.format,
                "runs": runs,
                "runs_text": f"{runs}{'' if out else '*'}",
                "balls_faced": balls,
                "fours": int(stats.get("fours") or 0),
                "sixes": int(stats.get("sixes") or 0),
                "batted_flag": 1 if balls or runs or out else 0,
                "not_out_flag": 0 if out else 1,
                "outs": 1 if out else 0,
                "fifty_flag": 1 if 50 <= runs < 100 else 0,
                "hundred_flag": 1 if runs >= 100 else 0,
                "minutes": 0,
                "innings_number": inning_number,
                "opposition": bowling_team,
                "ground": payload.ground,
                "date": match_date_text,
                "overs_bowled": 0.0,
                "bowled_flag": 0,
                "maidens": 0,
                "runs_conceded": 0,
                "wickets": 0,
                "economy_rate": 0.0,
                "bowling_strike_rate": 0.0,
                "batting_strike_rate": round((runs * 100 / balls), 2) if balls else 0.0,
                "four_wicket_flag": 0,
                "five_wicket_flag": 0,
                "ten_wicket_flag": 0,
                "balls_bowled": 0,
            })

        for player, stats in bowlers.items():
            balls = int(stats.get("balls") or 0)
            runs_conceded = int(stats.get("runs") or 0)
            wickets = int(stats.get("wickets") or 0)
            player_rows.append({
                "player": player,
                "country": bowling_team,
                "format": payload.format,
                "runs": 0,
                "runs_text": "0*",
                "balls_faced": 0,
                "fours": 0,
                "sixes": 0,
                "batted_flag": 0,
                "not_out_flag": 1,
                "outs": 0,
                "fifty_flag": 0,
                "hundred_flag": 0,
                "minutes": 0,
                "innings_number": inning_number,
                "opposition": batting_team,
                "ground": payload.ground,
                "date": match_date_text,
                "overs_bowled": balls_to_overs_float(balls),
                "bowled_flag": 1 if balls else 0,
                "maidens": int(stats.get("maidens") or 0),
                "runs_conceded": runs_conceded,
                "wickets": wickets,
                "economy_rate": round((runs_conceded * 6 / balls), 2) if balls else 0.0,
                "bowling_strike_rate": round((balls / wickets), 2) if wickets else 0.0,
                "batting_strike_rate": 0.0,
                "four_wicket_flag": 1 if wickets >= 4 else 0,
                "five_wicket_flag": 1 if wickets >= 5 else 0,
                "ten_wicket_flag": 1 if wickets >= 10 else 0,
                "balls_bowled": balls,
            })

    team_rows = []
    for team, opponent in [(payload.teamA, payload.teamB), (payload.teamB, payload.teamA)]:
        if tied:
            result = "Tied"
        elif winner is None:
            result = "No Result"
        else:
            result = "Won" if winner == team else "Lost"
        margin = build_margin(team, opponent, scores, winner, tied)
        team_rows.append({
            "country": team,
            "format": payload.format,
            "match": match_name,
            "opponent": opponent,
            "result": result,
            "margin": margin,
            "date": match_date_text,
            "ground": payload.ground,
            "home_away": "Neutral",
            "matches": 1,
            "won_flag": 1 if result == "Won" else 0,
            "lost_flag": 1 if result == "Lost" else 0,
            "tied_flag": 1 if result == "Tied" else 0,
            "no_result_flag": 1 if result == "No Result" else 0,
            "month": month,
            "year": year,
            "period": period,
        })
    return player_rows, team_rows


def balls_to_overs_float(balls: int) -> float:
    return float(f"{balls // 6}.{balls % 6}")


def build_margin(team: str, opponent: str, scores: dict[str, int], winner: str | None, tied: bool) -> str:
    if tied:
        return "Scores level"
    if winner is None or team not in scores or opponent not in scores:
        return ""
    run_margin = abs(scores.get(team, 0) - scores.get(opponent, 0))
    return f"{run_margin} runs"
