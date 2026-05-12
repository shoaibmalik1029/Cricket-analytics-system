"""
Generate comprehensive cricket data for all predictive features
Creates realistic match data, player stats, and venue information
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

# Set seed for reproducibility
np.random.seed(42)
random.seed(42)

# Define cricket teams
TEAMS = [
    "India", "Australia", "England", "Pakistan", "South Africa",
    "New Zealand", "West Indies", "Sri Lanka", "Bangladesh", "Afghanistan",
    "Ireland", "Netherlands", "Zimbabwe", "Namibia", "Oman"
]

VENUES = {
    "Eden Gardens": {"city": "Kolkata", "country": "India", "type": "Stadium"},
    "MCG": {"city": "Melbourne", "country": "Australia", "type": "Stadium"},
    "Lord's": {"city": "London", "country": "England", "type": "Stadium"},
    "Gaddafi Stadium": {"city": "Lahore", "country": "Pakistan", "type": "Stadium"},
    "Wanderers": {"city": "Johannesburg", "country": "South Africa", "type": "Stadium"},
    "Basin Reserve": {"city": "Wellington", "country": "New Zealand", "type": "Stadium"},
    "Kensington Oval": {"city": "Bridgetown", "country": "West Indies", "type": "Stadium"},
    "R Premadasa": {"city": "Colombo", "country": "Sri Lanka", "type": "Stadium"},
    "Sher-e-Bangla": {"city": "Dhaka", "country": "Bangladesh", "type": "Stadium"},
    "Arun Jaitley": {"city": "Delhi", "country": "India", "type": "Stadium"},
    "Wankhede": {"city": "Mumbai", "country": "India", "type": "Stadium"},
    "Narendra Modi": {"city": "Ahmedabad", "country": "India", "type": "Stadium"},
}

PLAYERS = {
    "India": ["Virat Kohli", "Rohit Sharma", "Jasprit Bumrah", "KL Rahul", "Hardik Pandya", "Ravindra Jadeja"],
    "Australia": ["Steve Smith", "David Warner", "Pat Cummins", "Mitchell Starc", "Glenn Maxwell", "Marcus Stoinis"],
    "England": ["Joe Root", "Ben Stokes", "Jofra Archer", "Jos Buttler", "Jonny Bairstow", "Chris Woakes"],
    "Pakistan": ["Babar Azam", "Shaheen Afridi", "Hasan Ali", "Mohammad Rizwan", "Fakhar Zaman", "Shadab Khan"],
    "South Africa": ["Quinton de Kock", "Faf du Plessis", "Kagiso Rabada", "Anrich Nortje", "Reece Topley", "Aiden Markram"],
    "New Zealand": ["Kane Williamson", "Trent Boult", "Tim Southee", "Devon Conway", "Glenn Phillips", "Daryl Mitchell"],
}

def generate_match_results():
    """Generate historical match data"""
    matches = []
    match_id = 1000
    start_date = datetime(2022, 1, 1)
    
    for _ in range(500):  # Generate 500 matches
        home_team = random.choice(TEAMS)
        away_team = random.choice([t for t in TEAMS if t != home_team])
        venue = random.choice(list(VENUES.keys()))
        date = start_date + timedelta(days=random.randint(0, 900))
        
        # Simulate match stats
        home_runs = random.randint(120, 280)
        away_runs = random.randint(120, 280)
        home_wickets = random.randint(3, 10)
        away_wickets = random.randint(3, 10)
        
        # Determine winner
        if home_runs > away_runs:
            winner = home_team
        elif away_runs > home_runs:
            winner = away_team
        else:
            winner = random.choice([home_team, away_team])
        
        matches.append({
            "season": date.year,
            "id": match_id,
            "name": f"{home_team} vs {away_team}",
            "short_name": f"{home_team[:3]} vs {away_team[:3]}",
            "description": "ODI Match",
            "home_team": home_team,
            "away_team": away_team,
            "toss_won": random.choice([home_team, away_team]),
            "decision": random.choice(["bat", "field"]),
            "1st_inning_score": max(home_runs, away_runs),
            "2nd_inning_score": min(home_runs, away_runs),
            "winner": winner,
            "result": "runs" if abs(home_runs - away_runs) > 5 else "wickets",
            "start_date": date.strftime("%Y-%m-%d"),
            "end_date": (date + timedelta(days=1)).strftime("%Y-%m-%d"),
            "venue_id": list(VENUES.keys()).index(venue),
            "venue_name": venue,
            "home_captain": random.choice(PLAYERS.get(home_team, ["Captain"])),
            "away_captain": random.choice(PLAYERS.get(away_team, ["Captain"])),
            "pom": random.choice(PLAYERS.get(winner, ["Player"])),  # Player of the match
            "points": 2 if winner else 0,
            "super_over": random.choice([True, False]),
            "home_overs": "50.0",
            "home_runs": home_runs,
            "home_wickets": home_wickets,
            "home_boundaries": random.randint(15, 35),
            "away_overs": "50.0",
            "away_runs": away_runs,
            "away_wickets": away_wickets,
            "away_boundaries": random.randint(15, 35),
            "highlights": "youtube.com/watch",
            "match_days": 1,
            "umpire1": "Umpire 1",
            "umpire2": "Umpire 2",
            "tv_umpire": "TV Umpire",
            "referee": "Referee",
            "reserve_umpire": "Reserve",
        })
        match_id += 1
    
    return pd.DataFrame(matches)


def generate_player_data(matches_df):
    """Generate player performance data"""
    player_data = []
    
    for _, match in matches_df.iterrows():
        for team in [match["home_team"], match["away_team"]]:
            team_players = PLAYERS.get(team, ["Player 1", "Player 2", "Player 3"])
            for player in random.sample(team_players, k=min(5, len(team_players))):
                player_data.append({
                    "match_id": match["id"],
                    "team_side": "home" if team == match["home_team"] else "away",
                    "team_name": team,
                    "player_name": player,
                    "role": random.choice(["batsman", "bowler", "all-rounder"])
                })
    
    return pd.DataFrame(player_data)


def generate_venue_intelligence():
    """Generate venue statistics"""
    venues = []
    
    for venue_name, info in VENUES.items():
        home_wins = random.randint(20, 45)
        total = random.randint(50, 80)
        
        venues.append({
            "venue_name": venue_name,
            "par_score": random.randint(150, 180),
            "par_std": random.randint(15, 30),
            "avg_chasing_score": random.randint(140, 170),
            "chasing_std": random.randint(10, 25),
            "home_wins": home_wins,
            "total_matches": total,
            "home_win_rate": round(home_wins / total, 3),
            "home_advantage": round(random.uniform(0.45, 0.65), 3),
            "venue_type": info["type"]
        })
    
    return pd.DataFrame(venues)


def generate_player_performance():
    """Generate player performance metrics"""
    players = []
    
    all_players = []
    for team_players in PLAYERS.values():
        all_players.extend(team_players)
    
    for player in all_players:
        players.append({
            "player": player,
            "pom_count": random.randint(0, 15),
            "matches_played": random.randint(30, 150),
            "consistency_index": round(random.uniform(0.5, 0.95), 3)
        })
    
    return pd.DataFrame(players)


def generate_model_ready_data(matches_df, venues_df):
    """Generate model-ready cricket data with features"""
    model_data = []
    
    for _, match in matches_df.iterrows():
        home_team = match["home_team"]
        away_team = match["away_team"]
        
        # Get venue advantage
        venue_row = venues_df[venues_df["venue_name"] == match["venue_name"]]
        home_advantage = venue_row["home_advantage"].values[0] if len(venue_row) > 0 else 0.5
        par_score = venue_row["par_score"].values[0] if len(venue_row) > 0 else 165
        
        # Encode teams for ML
        team_strength = {team: random.uniform(30, 100) for team in TEAMS}
        
        model_data.append({
            "season": match["season"],
            "id": match["id"],
            "name": match["name"],
            "short_name": match["short_name"],
            "description": match["description"],
            "home_team": home_team,
            "away_team": away_team,
            "toss_won": match["toss_won"],
            "decision": match["decision"],
            "1st_inning_score": match["1st_inning_score"],
            "2nd_inning_score": match["2nd_inning_score"],
            "winner": match["winner"],
            "result": match["result"],
            "start_date": match["start_date"],
            "end_date": match["end_date"],
            "venue_id": match["venue_id"],
            "venue_name": match["venue_name"],
            "home_captain": match["home_captain"],
            "away_captain": match["away_captain"],
            "pom": match["pom"],
            "points": match["points"],
            "super_over": match["super_over"],
            "home_overs": match["home_overs"],
            "home_runs": match["home_runs"],
            "home_wickets": match["home_wickets"],
            "home_boundaries": match["home_boundaries"],
            "away_overs": match["away_overs"],
            "away_runs": match["away_runs"],
            "away_wickets": match["away_wickets"],
            "away_boundaries": match["away_boundaries"],
            "highlights": match["highlights"],
            "home_key_batsman": match["home_captain"],
            "home_key_bowler": "Key Bowler",
            "home_playx1": "Playing XI",
            "away_playx1": "Playing XI",
            "away_key_batsman": match["away_captain"],
            "away_key_bowler": "Key Bowler",
            "match_days": match["match_days"],
            "umpire1": match["umpire1"],
            "umpire2": match["umpire2"],
            "tv_umpire": match["tv_umpire"],
            "referee": match["referee"],
            "reserve_umpire": match["reserve_umpire"],
            "home_enc": hash(home_team) % 100,
            "away_enc": hash(away_team) % 100,
            "toss_winner_enc": hash(match["toss_won"]) % 100,
            "venue_enc": match["venue_id"],
            "decision_enc": 1 if match["decision"] == "bat" else 0,
            "home_win_label": 1 if match["winner"] == home_team else 0,
            "par_score": par_score,
            "home_advantage": home_advantage,
            "venue_type": "Stadium",
            "decision_advantage": 0.5,
            "h2h_advantage": round(random.uniform(0.4, 0.6), 3),
            "home_star_power": team_strength[home_team],
            "away_star_power": team_strength[away_team],
            "home_team_strength": team_strength[home_team],
            "away_team_strength": team_strength[away_team],
        })
    
    return pd.DataFrame(model_data)


def main():
    print("Generating comprehensive cricket dataset...")
    
    # Generate all data
    print("  - Generating match results...")
    matches = generate_match_results()
    
    print("  - Generating venue intelligence...")
    venues = generate_venue_intelligence()
    
    print("  - Generating player data...")
    players = generate_player_data(matches)
    
    print("  - Generating player performance metrics...")
    perf = generate_player_performance()
    
    print("  - Generating model-ready data...")
    model_ready = generate_model_ready_data(matches, venues)
    
    # Save all data
    print("\nSaving data files...")
    matches.to_csv("Match_Data.csv", index=False)
    print("  ✓ Match_Data.csv")
    
    matches.to_csv("Cricket_data.csv", index=False)
    print("  ✓ Cricket_data.csv")
    
    players.to_csv("Player_Data.csv", index=False)
    print("  ✓ Player_Data.csv")
    
    venues.to_csv("Venue_Intelligence_Report.csv", index=False)
    print("  ✓ Venue_Intelligence_Report.csv")
    
    perf.to_csv("Player_Performance_Metrics.csv", index=False)
    print("  ✓ Player_Performance_Metrics.csv")
    
    model_ready.to_csv("Model_Ready_Cricket_Data.csv", index=False)
    print("  ✓ Model_Ready_Cricket_Data.csv")
    
    print("\n✅ All data files generated successfully!")
    print(f"\nData Summary:")
    print(f"  - Total matches: {len(matches)}")
    print(f"  - Teams: {len(TEAMS)}")
    print(f"  - Venues: {len(venues)}")
    print(f"  - Players: {len(perf)}")
    print(f"  - Date range: {matches['start_date'].min()} to {matches['start_date'].max()}")


if __name__ == "__main__":
    main()
