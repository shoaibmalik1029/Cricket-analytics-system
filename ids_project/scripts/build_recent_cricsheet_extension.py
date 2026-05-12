from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path


INPUT_FILES = {
    "Test": Path("data/cricsheet/tests_male_ball_by_ball.csv"),
    "ODI": Path("data/cricsheet/odis_male_ball_by_ball.csv"),
    "T20I": Path("data/cricsheet/t20s_male_ball_by_ball.csv"),
}

OUTPUT_DIR = Path("data/normalized_recent")
START_YEAR = 2021
END_YEAR = 2025


def as_int(value: str | None) -> int:
    if value in (None, "", "NA", "Unknown", "None", "nan"):
        return 0
    try:
        return int(float(value))
    except ValueError:
        return 0


def as_bool(value: str | None) -> bool:
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes"}


def clean(value: str | None) -> str:
    if value is None:
        return ""
    value = str(value).strip()
    return "" if value in {"NA", "Unknown", "None", "nan"} else value


def build_recent_extension():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    batting_stats = {}
    bowling_stats = {}
    maiden_tracker = defaultdict(lambda: {"balls": 0, "runs": 0})
    team_innings = {}
    match_meta = {}
    match_teams = defaultdict(set)

    for match_format, path in INPUT_FILES.items():
        if not path.exists():
            raise FileNotFoundError(f"Missing input file: {path}")

        with path.open("r", newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                year = as_int(row.get("year")) or as_int((row.get("date") or "")[:4])
                if year < START_YEAR or year > END_YEAR:
                    continue

                match_id = clean(row.get("match_id"))
                innings = as_int(row.get("innings"))
                batting_team = clean(row.get("batting_team"))
                bowling_team = clean(row.get("bowling_team"))
                batter = clean(row.get("batter"))
                bowler = clean(row.get("bowler"))
                date = clean(row.get("date"))
                venue = clean(row.get("venue"))
                result_type = clean(row.get("result_type")).lower()
                winner = clean(row.get("match_won_by"))

                match_teams[match_id].update([batting_team, bowling_team])
                if match_id not in match_meta:
                    match_meta[match_id] = {
                        "format": match_format,
                        "date": date,
                        "venue": venue,
                        "city": clean(row.get("city")),
                        "winner": winner,
                        "margin": clean(row.get("win_outcome")),
                        "result_type": result_type,
                        "toss_winner": clean(row.get("toss_winner")),
                        "toss_decision": clean(row.get("toss_decision")),
                    }

                team_key = (match_id, innings, batting_team)
                team_innings[team_key] = {
                    "match_id": match_id,
                    "format": match_format,
                    "innings": innings,
                    "batting_team": batting_team,
                    "bowling_team": bowling_team,
                    "date": date,
                    "venue": venue,
                    "team_runs": max(as_int(row.get("team_runs")), team_innings.get(team_key, {}).get("team_runs", 0)),
                    "team_balls": max(as_int(row.get("team_balls")), team_innings.get(team_key, {}).get("team_balls", 0)),
                    "team_wicket": max(as_int(row.get("team_wicket")), team_innings.get(team_key, {}).get("team_wicket", 0)),
                }

                batter_key = (match_id, innings, batting_team, batter)
                if batter_key not in batting_stats:
                    batting_stats[batter_key] = {
                        "player": batter,
                        "country": batting_team,
                        "format": match_format,
                        "runs": 0,
                        "balls_faced": 0,
                        "fours": 0,
                        "sixes": 0,
                        "dismissed": False,
                        "opposition": bowling_team,
                        "ground": venue,
                        "date": date,
                        "innings_number": innings,
                    }
                batting_stats[batter_key]["runs"] += as_int(row.get("runs_batter"))
                batting_stats[batter_key]["balls_faced"] = max(
                    batting_stats[batter_key]["balls_faced"], as_int(row.get("batter_balls"))
                )
                if as_int(row.get("runs_batter")) == 4 and not as_bool(row.get("runs_not_boundary")):
                    batting_stats[batter_key]["fours"] += 1
                if as_int(row.get("runs_batter")) == 6 and not as_bool(row.get("runs_not_boundary")):
                    batting_stats[batter_key]["sixes"] += 1
                if clean(row.get("player_out")) == batter:
                    batting_stats[batter_key]["dismissed"] = True

                if bowler:
                    bowler_key = (match_id, innings, bowling_team, bowler)
                    if bowler_key not in bowling_stats:
                        bowling_stats[bowler_key] = {
                            "player": bowler,
                            "country": bowling_team,
                            "format": match_format,
                            "balls_bowled": 0,
                            "maidens": 0,
                            "runs_conceded": 0,
                            "wickets": 0,
                            "opposition": batting_team,
                            "ground": venue,
                            "date": date,
                            "innings_number": innings,
                        }
                    valid_ball = as_int(row.get("valid_ball"))
                    bowling_stats[bowler_key]["balls_bowled"] += valid_ball
                    bowling_stats[bowler_key]["runs_conceded"] += as_int(row.get("runs_bowler"))
                    bowling_stats[bowler_key]["wickets"] = max(
                        bowling_stats[bowler_key]["wickets"], as_int(row.get("bowler_wicket"))
                    )

                    over_key = (match_id, innings, bowling_team, bowler, as_int(row.get("over")))
                    maiden_tracker[over_key]["balls"] += valid_ball
                    maiden_tracker[over_key]["runs"] += as_int(row.get("runs_bowler"))

    for over_key, over_data in maiden_tracker.items():
        if over_data["balls"] >= 6 and over_data["runs"] == 0:
            match_id, innings, bowling_team, bowler, _ = over_key
            bowler_key = (match_id, innings, bowling_team, bowler)
            if bowler_key in bowling_stats:
                bowling_stats[bowler_key]["maidens"] += 1

    player_rows = []
    for item in batting_stats.values():
        runs = item["runs"]
        balls = item["balls_faced"]
        outs = 1 if item["dismissed"] else 0
        player_rows.append(
            {
                "player": item["player"],
                "country": item["country"],
                "format": item["format"],
                "runs": runs,
                "runs_text": f"{runs}{'*' if not item['dismissed'] else ''}",
                "balls_faced": balls,
                "fours": item["fours"],
                "sixes": item["sixes"],
                "batted_flag": 1,
                "not_out_flag": 0 if item["dismissed"] else 1,
                "outs": outs,
                "fifty_flag": 1 if 50 <= runs < 100 else 0,
                "hundred_flag": 1 if runs >= 100 else 0,
                "minutes": balls,
                "innings_number": item["innings_number"],
                "opposition": item["opposition"],
                "ground": item["ground"],
                "date": item["date"],
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
            }
        )

    for item in bowling_stats.values():
        balls = item["balls_bowled"]
        wickets = item["wickets"]
        economy = round((item["runs_conceded"] * 6 / balls), 2) if balls else 0.0
        strike = round((balls / wickets), 2) if wickets else 0.0
        player_rows.append(
            {
                "player": item["player"],
                "country": item["country"],
                "format": item["format"],
                "runs": 0,
                "runs_text": "0",
                "balls_faced": 0,
                "fours": 0,
                "sixes": 0,
                "batted_flag": 0,
                "not_out_flag": 0,
                "outs": 0,
                "fifty_flag": 0,
                "hundred_flag": 0,
                "minutes": 0,
                "innings_number": item["innings_number"],
                "opposition": item["opposition"],
                "ground": item["ground"],
                "date": item["date"],
                "overs_bowled": round(balls / 6, 2),
                "bowled_flag": 1 if balls else 0,
                "maidens": item["maidens"],
                "runs_conceded": item["runs_conceded"],
                "wickets": wickets,
                "economy_rate": economy,
                "bowling_strike_rate": strike,
                "batting_strike_rate": 0.0,
                "four_wicket_flag": 1 if 4 <= wickets < 5 else 0,
                "five_wicket_flag": 1 if wickets >= 5 else 0,
                "ten_wicket_flag": 1 if wickets >= 10 else 0,
                "balls_bowled": balls,
            }
        )

    result_rows = []
    team_batting_rows = {}
    team_bowling_rows = {}

    for item in team_innings.values():
        bat_key = (item["format"], item["batting_team"])
        bowl_key = (item["format"], item["bowling_team"])
        bat_row = team_batting_rows.setdefault(
            bat_key,
            {
                "country": item["batting_team"],
                "format": item["format"],
                "matches_played": 0,
                "innings_batted": 0,
                "runs_scored": 0,
                "wickets_lost": 0,
                "balls_faced": 0,
                "highest_team_score": 0,
                "lowest_completed_score": None,
            },
        )
        bat_row["innings_batted"] += 1
        bat_row["runs_scored"] += item["team_runs"]
        bat_row["wickets_lost"] += item["team_wicket"]
        bat_row["balls_faced"] += item["team_balls"]
        bat_row["highest_team_score"] = max(bat_row["highest_team_score"], item["team_runs"])
        bat_row["lowest_completed_score"] = (
            item["team_runs"]
            if bat_row["lowest_completed_score"] is None
            else min(bat_row["lowest_completed_score"], item["team_runs"])
        )

        bowl_row = team_bowling_rows.setdefault(
            bowl_key,
            {
                "country": item["bowling_team"],
                "format": item["format"],
                "matches_played": 0,
                "innings_bowled": 0,
                "runs_conceded": 0,
                "wickets_taken": 0,
                "balls_bowled": 0,
                "highest_score_conceded": 0,
                "lowest_completed_score_conceded": None,
            },
        )
        bowl_row["innings_bowled"] += 1
        bowl_row["runs_conceded"] += item["team_runs"]
        bowl_row["wickets_taken"] += item["team_wicket"]
        bowl_row["balls_bowled"] += item["team_balls"]
        bowl_row["highest_score_conceded"] = max(bowl_row["highest_score_conceded"], item["team_runs"])
        bowl_row["lowest_completed_score_conceded"] = (
            item["team_runs"]
            if bowl_row["lowest_completed_score_conceded"] is None
            else min(bowl_row["lowest_completed_score_conceded"], item["team_runs"])
        )

    for match_id, meta in match_meta.items():
        teams = sorted(team for team in match_teams[match_id] if team)
        if len(teams) != 2:
            continue
        team_a, team_b = teams
        winner = meta["winner"]
        result_type = meta["result_type"]
        margin = meta["margin"] or result_type.title()
        for team in teams:
            opponent = team_b if team == team_a else team_a
            if winner and winner == team:
                result = "Won"
            elif result_type == "draw":
                result = "Drawn"
            elif result_type == "tie":
                result = "Tied"
            elif result_type in {"no result", "abandoned"}:
                result = "No Result"
            elif winner:
                result = "Lost"
            else:
                result = "No Result"

            result_rows.append(
                {
                    "country": team,
                    "format": meta["format"],
                    "match": f"{team_a} v {team_b}",
                    "opponent": opponent,
                    "result": result,
                    "margin": margin,
                    "date": meta["date"],
                    "ground": meta["venue"],
                    "home_away": "Neutral",
                    "matches": 1,
                    "won_flag": 1 if result == "Won" else 0,
                    "lost_flag": 1 if result == "Lost" else 0,
                    "tied_flag": 1 if result == "Tied" else 0,
                    "no_result_flag": 1 if result in {"No Result", "Drawn"} else 0,
                    "month": int(meta["date"][5:7]),
                    "year": int(meta["date"][:4]),
                    "period": meta["date"][:7],
                }
            )

            bat_key = (meta["format"], team)
            bowl_key = (meta["format"], team)
            if bat_key in team_batting_rows:
                team_batting_rows[bat_key]["matches_played"] += 1
            if bowl_key in team_bowling_rows:
                team_bowling_rows[bowl_key]["matches_played"] += 1

    batting_output = []
    for item in team_batting_rows.values():
        batting_output.append(
            {
                "country": item["country"],
                "format": item["format"],
                "matches_played": item["matches_played"],
                "innings_batted": item["innings_batted"],
                "runs_scored": item["runs_scored"],
                "average_runs": round(item["runs_scored"] / item["innings_batted"], 2) if item["innings_batted"] else 0.0,
                "batting_runs_per_over": round(item["runs_scored"] * 6 / item["balls_faced"], 4) if item["balls_faced"] else 0.0,
                "highest_team_score": item["highest_team_score"],
                "lowest_completed_score": item["lowest_completed_score"] or 0,
                "batting_average": round(item["runs_scored"] / item["wickets_lost"], 4) if item["wickets_lost"] else 0.0,
            }
        )

    bowling_output = []
    for item in team_bowling_rows.values():
        bowling_output.append(
            {
                "country": item["country"],
                "format": item["format"],
                "bowling_average": round(item["runs_conceded"] / item["wickets_taken"], 4) if item["wickets_taken"] else 0.0,
                "bowling_runs_per_over": round(item["runs_conceded"] * 6 / item["balls_bowled"], 4) if item["balls_bowled"] else 0.0,
                "innings_bowled": item["innings_bowled"],
                "highest_score_conceded": item["highest_score_conceded"],
                "lowest_completed_score_conceded": item["lowest_completed_score_conceded"] or 0,
                "matches_played": item["matches_played"],
                "format": item["format"],
                "country": item["country"],
            }
        )

    write_csv(OUTPUT_DIR / "player_innings_recent.csv", player_rows)
    write_csv(OUTPUT_DIR / "team_results_recent.csv", result_rows)
    write_csv(OUTPUT_DIR / "team_batting_recent.csv", batting_output)
    write_csv(OUTPUT_DIR / "team_bowling_recent.csv", bowling_output)
    print(f"Wrote recent extension for {START_YEAR}-{END_YEAR} to {OUTPUT_DIR}")


def write_csv(path: Path, rows: list[dict]):
    if not rows:
        raise ValueError(f"No rows available for {path.name}")
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    build_recent_extension()
