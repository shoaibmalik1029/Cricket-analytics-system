from __future__ import annotations

import csv
from pathlib import Path


DATA_DIR = Path(r"c:\Users\HP\Downloads\archive (12)\Cricket statsguru-data")
RECENT_DIR = Path("data/normalized_recent")
OUTPUT_DIR = Path("data/final")

ARCHIVE_PLAYER_FILES = {
    "ODI": [
        DATA_DIR / "Men ODI Player Innings Stats - 20th Century.csv",
        DATA_DIR / "Men ODI Player Innings Stats - 21st Century.csv",
    ],
    "T20I": [DATA_DIR / "Men T20I Player Innings Stats - 21st Century.csv"],
    "Test": [
        DATA_DIR / "Men Test Player Innings Stats - 19th Century.csv",
        DATA_DIR / "Men Test Player Innings Stats - 20th Century.csv",
        DATA_DIR / "Men Test Player Innings Stats - 21st Century.csv",
    ],
}

ARCHIVE_RESULT_FILES = {
    "ODI": [
        DATA_DIR / "Men ODI Team Match Results - 20th Century.csv",
        DATA_DIR / "Men ODI Team Match Results - 21st Century.csv",
    ],
    "T20I": [DATA_DIR / "Men T20I Team Match Results - 21st Century.csv"],
    "Test": [
        DATA_DIR / "Men Test Team Match Results - 19th Century.csv",
        DATA_DIR / "Men Test Team Match Results - 20th Century.csv",
        DATA_DIR / "Men Test Team Match Results - 21st Century.csv",
    ],
}


PLAYER_FIELDS = [
    "player",
    "country",
    "format",
    "runs",
    "runs_text",
    "balls_faced",
    "fours",
    "sixes",
    "batted_flag",
    "not_out_flag",
    "outs",
    "fifty_flag",
    "hundred_flag",
    "minutes",
    "innings_number",
    "opposition",
    "ground",
    "date",
    "overs_bowled",
    "bowled_flag",
    "maidens",
    "runs_conceded",
    "wickets",
    "economy_rate",
    "bowling_strike_rate",
    "batting_strike_rate",
    "four_wicket_flag",
    "five_wicket_flag",
    "ten_wicket_flag",
    "balls_bowled",
]

RESULT_FIELDS = [
    "country",
    "format",
    "match",
    "opponent",
    "result",
    "margin",
    "date",
    "ground",
    "home_away",
    "matches",
    "won_flag",
    "lost_flag",
    "tied_flag",
    "no_result_flag",
    "month",
    "year",
    "period",
]


def clean(value: str | None) -> str:
    if value is None:
        return ""
    return str(value).replace("\ufeff", "").strip()


def as_int(value: str | None) -> int:
    value = clean(value)
    if not value:
        return 0
    try:
        return int(float(value))
    except ValueError:
        return 0


def as_float(value: str | None) -> float:
    value = clean(value)
    if not value:
        return 0.0
    try:
        return float(value)
    except ValueError:
        return 0.0


def overs_to_balls(value: str | None) -> int:
    text = clean(value)
    if not text:
        return 0
    if "." in text:
        whole, frac = text.split(".", 1)
        return as_int(whole) * 6 + as_int(frac[:1])
    return as_int(text) * 6


def normalize_opposition(value: str | None) -> str:
    text = clean(value)
    return text[2:].strip() if text.lower().startswith("v ") else text


def parse_match_opponent(match_text: str, country: str) -> str:
    parts = [clean(part) for part in clean(match_text).split(" v ")]
    if len(parts) != 2:
        return ""
    if parts[0] == country:
        return parts[1]
    if parts[1] == country:
        return parts[0]
    return parts[1]


def write_archive_player_rows(writer):
    for match_format, files in ARCHIVE_PLAYER_FILES.items():
        for path in files:
            with path.open("r", newline="", encoding="utf-8-sig") as handle:
                reader = csv.DictReader(handle)
                for row in reader:
                    balls_bowled = overs_to_balls(row.get("Innings Overs Bowled"))
                    wickets = as_int(row.get("Innings Wickets Taken"))
                    writer.writerow(
                        {
                            "player": clean(row.get("Innings Player")),
                            "country": clean(row.get("Country")),
                            "format": match_format,
                            "runs": as_int(row.get("Innings Runs Scored Num")),
                            "runs_text": clean(row.get("Innings Runs Scored")),
                            "balls_faced": as_int(row.get("Innings Balls Faced")),
                            "fours": as_int(row.get("Innings Boundary Fours")),
                            "sixes": as_int(row.get("Innings Boundary Sixes")),
                            "batted_flag": as_int(row.get("Innings Batted Flag")),
                            "not_out_flag": as_int(row.get("Innings Not Out Flag")),
                            "outs": 1 - as_int(row.get("Innings Not Out Flag")) if as_int(row.get("Innings Batted Flag")) else 0,
                            "fifty_flag": as_int(row.get("50's")),
                            "hundred_flag": as_int(row.get("100's")),
                            "minutes": as_int(row.get("Innings Minutes Batted")),
                            "innings_number": as_int(row.get("Innings Number")),
                            "opposition": normalize_opposition(row.get("Opposition")),
                            "ground": clean(row.get("Ground")),
                            "date": clean(row.get("Innings Date")).replace("/", "-"),
                            "overs_bowled": as_float(row.get("Innings Overs Bowled")),
                            "bowled_flag": as_int(row.get("Innings Bowled Flag")),
                            "maidens": as_int(row.get("Innings Maidens Bowled")),
                            "runs_conceded": as_int(row.get("Innings Runs Conceded")),
                            "wickets": wickets,
                            "economy_rate": as_float(row.get("Innings Economy Rate")),
                            "bowling_strike_rate": round(balls_bowled / wickets, 4) if wickets else 0.0,
                            "batting_strike_rate": as_float(row.get("Innings Batting Strike Rate")),
                            "four_wicket_flag": as_int(row.get("4 Wickets")),
                            "five_wicket_flag": as_int(row.get("5 Wickets")),
                            "ten_wicket_flag": as_int(row.get("10 Wickets")),
                            "balls_bowled": balls_bowled,
                        }
                    )


def write_archive_result_rows(writer):
    for match_format, files in ARCHIVE_RESULT_FILES.items():
        for path in files:
            with path.open("r", newline="", encoding="utf-8-sig") as handle:
                reader = csv.DictReader(handle)
                for row in reader:
                    match = clean(row.get("Match"))
                    country = clean(row.get("Country"))
                    result = clean(row.get("Result"))
                    writer.writerow(
                        {
                            "country": country,
                            "format": match_format,
                            "match": match,
                            "opponent": parse_match_opponent(match, country),
                            "result": result,
                            "margin": clean(row.get("Margin")),
                            "date": clean(row.get("Match Date")).replace("/", "-"),
                            "ground": clean(row.get("Ground")),
                            "home_away": clean(row.get("Home/Away")),
                            "matches": as_int(row.get("Matches")) or 1,
                            "won_flag": 1 if result == "Won" else 0,
                            "lost_flag": 1 if result == "Lost" else 0,
                            "tied_flag": 1 if result == "Tied" else 0,
                            "no_result_flag": 1 if result in {"No Result", "Abandoned", "Drawn"} else 0,
                            "month": clean(row.get("Match Month")),
                            "year": as_int(row.get("Match Year")),
                            "period": clean(row.get("Match Period")),
                        }
                    )


def append_existing_rows(writer, path: Path):
    with path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            writer.writerow(row)


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    player_out = OUTPUT_DIR / "player_innings_1877_2025.csv"
    result_out = OUTPUT_DIR / "team_results_1877_2025.csv"

    with player_out.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=PLAYER_FIELDS)
        writer.writeheader()
        write_archive_player_rows(writer)
        append_existing_rows(writer, RECENT_DIR / "player_innings_recent.csv")

    with result_out.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=RESULT_FIELDS)
        writer.writeheader()
        write_archive_result_rows(writer)
        append_existing_rows(writer, RECENT_DIR / "team_results_recent.csv")

    print(f"Wrote merged files to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
