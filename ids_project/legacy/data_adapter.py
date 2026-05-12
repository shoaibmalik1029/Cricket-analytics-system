"""
Data adapter to load local CSV files and transform them to cricket.py format
"""
import pandas as pd
import numpy as np
from pathlib import Path


def load_local_cricket_data():
    """Load local CSV files and return dataframes in cricket.py format"""
    
    # Load the generated CSV files
    match_data = pd.read_csv("Match_Data.csv")
    player_data = pd.read_csv("Player_Data.csv")
    
    # Transform match data into player innings format
    player_innings = transform_match_data_to_player_innings(match_data, player_data)
    
    # Transform match data into results format
    team_results = transform_match_data_to_results(match_data)
    
    # Create team batting and bowling stats
    team_batting = create_team_batting_stats(match_data)
    team_bowling = create_team_bowling_stats(match_data)
    
    return player_innings, team_batting, team_bowling, team_results


def transform_match_data_to_player_innings(match_data, player_data):
    """Transform match and player data into player innings format"""
    
    innings = []
    
    for _, match in match_data.iterrows():
        # Get players for this match
        match_players = player_data[player_data['match_id'] == match['id']]
        
        for _, player_row in match_players.iterrows():
            team = player_row['team_name']
            is_home = (team == match['home_team'])
            
            # Determine runs based on team performance
            if is_home:
                team_runs = match['home_runs']
                team_wickets = match['home_wickets']
                opposition = match['away_team']
            else:
                team_runs = match['away_runs']
                team_wickets = match['away_wickets']
                opposition = match['home_team']
            
            # Estimate individual player runs (distribute team runs among players)
            num_players = max(1, len(match_players[match_players['team_name'] == team]))
            player_runs = int(team_runs / num_players + np.random.randint(-20, 30))
            player_runs = max(0, player_runs)
            
            batted_flag = 1 if player_runs > 0 else (1 if np.random.random() > 0.5 else 0)
            not_out = 0 if batted_flag == 0 else (1 if team_wickets < 8 else 0)
            
            balls_faced = max(1, int(player_runs / max(0.5, np.random.uniform(0.8, 1.2))))
            minutes = balls_faced
            
            # Bowling simulation
            overs_bowled = np.random.uniform(5, 10)
            balls_bowled = int(overs_bowled * 6)
            
            fours = max(0, np.random.randint(0, int(balls_faced / 10) + 1))
            sixes = max(0, np.random.randint(0, int(balls_faced / 20) + 1))
            
            outs = 1 if (batted_flag == 1 and not_out == 0) else 0
            
            innings.append({
                'player': player_row['player_name'],
                'country': team,
                'format': 'ODI',
                'runs': player_runs,
                'runs_text': str(player_runs),
                'balls_faced': balls_faced,
                'fours': fours,
                'sixes': sixes,
                'batted_flag': batted_flag,
                'not_out_flag': not_out,
                'outs': outs,
                'fifty_flag': 1 if 50 <= player_runs < 100 else 0,
                'hundred_flag': 1 if player_runs >= 100 else 0,
                'minutes': minutes,
                'innings_number': 1,
                'opposition': opposition,
                'ground': match['venue_name'],
                'date': pd.to_datetime(match['start_date']),
                'overs_bowled': overs_bowled,
                'bowled_flag': 1 if np.random.random() > 0.6 else 0,
                'maidens': max(0, np.random.randint(0, 3)),
                'runs_conceded': np.random.randint(20, 50),
                'wickets': max(0, np.random.randint(0, 3)),
                'economy_rate': np.random.uniform(4, 8),
                'bowling_strike_rate': np.random.uniform(15, 35),
                'batting_strike_rate': (100 * player_runs / balls_faced) if balls_faced > 0 else 0,
                'four_wicket_flag': 0,
                'five_wicket_flag': 0,
                'ten_wicket_flag': 0,
                'balls_bowled': balls_bowled,
            })
    
    df = pd.DataFrame(innings)
    
    # Ensure all required columns exist with proper types
    required_cols = {
        'player': str,
        'country': str,
        'format': str,
        'runs': 'float64',
        'balls_faced': 'float64',
        'fours': 'float64',
        'sixes': 'float64',
        'batted_flag': 'float64',
        'not_out_flag': 'float64',
        'outs': 'float64',
        'fifty_flag': 'float64',
        'hundred_flag': 'float64',
        'minutes': 'float64',
        'innings_number': 'float64',
        'opposition': str,
        'ground': str,
        'date': 'datetime64[ns]',
        'overs_bowled': 'float64',
        'bowled_flag': 'float64',
        'maidens': 'float64',
        'runs_conceded': 'float64',
        'wickets': 'float64',
        'economy_rate': 'float64',
        'bowling_strike_rate': 'float64',
        'batting_strike_rate': 'float64',
        'four_wicket_flag': 'float64',
        'five_wicket_flag': 'float64',
        'ten_wicket_flag': 'float64',
        'balls_bowled': 'float64',
    }
    
    for col, dtype in required_cols.items():
        if col not in df.columns:
            if dtype == str:
                df[col] = ""
            else:
                df[col] = 0.0
        else:
            if dtype == 'float64':
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            elif dtype == 'datetime64[ns]':
                df[col] = pd.to_datetime(df[col], errors='coerce')
    
    return df


def transform_match_data_to_results(match_data):
    """Transform match data into results format"""
    
    results = []
    
    for _, match in match_data.iterrows():
        for country in [match['home_team'], match['away_team']]:
            is_home = (country == match['home_team'])
            opponent = match['away_team'] if is_home else match['home_team']
            
            if is_home:
                team_runs = match['home_runs']
                opp_runs = match['away_runs']
            else:
                team_runs = match['away_runs']
                opp_runs = match['home_runs']
            
            # Determine result
            if match['winner'] == country:
                result = "Won"
                margin = abs(team_runs - opp_runs)
            else:
                result = "Lost"
                margin = abs(opp_runs - team_runs)
            
            match_str = f"{match['home_team']} v {match['away_team']}"
            
            results.append({
                'country': country,
                'format': 'ODI',
                'match': match_str,
                'opponent': opponent,
                'result': result,
                'margin': margin,
                'date': pd.to_datetime(match['start_date']),
                'ground': match['venue_name'],
                'home_away': 'Home' if is_home else 'Away',
                'matches': 1,
                'won_flag': 1 if result == 'Won' else 0,
                'lost_flag': 1 if result == 'Lost' else 0,
                'tied_flag': 0,
                'no_result_flag': 0,
                'month': pd.to_datetime(match['start_date']).month,
                'year': pd.to_datetime(match['start_date']).year,
                'period': 'Recent',
            })
    
    df = pd.DataFrame(results)
    
    # Ensure all required columns exist
    required_cols = {
        'country': str,
        'format': str,
        'match': str,
        'opponent': str,
        'result': str,
        'margin': 'float64',
        'date': 'datetime64[ns]',
        'ground': str,
        'home_away': str,
        'matches': 'float64',
        'won_flag': 'float64',
        'lost_flag': 'float64',
        'tied_flag': 'float64',
        'no_result_flag': 'float64',
        'month': 'float64',
        'year': 'float64',
        'period': str,
    }
    
    for col, dtype in required_cols.items():
        if col not in df.columns:
            if dtype == str:
                df[col] = ""
            else:
                df[col] = 0.0
        else:
            if dtype == 'float64':
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            elif dtype == 'datetime64[ns]':
                df[col] = pd.to_datetime(df[col], errors='coerce')
    
    return df


def create_team_batting_stats(match_data):
    """Create team batting statistics"""
    
    stats = []
    
    teams = set(match_data['home_team'].unique().tolist() + match_data['away_team'].unique().tolist())
    
    for team in teams:
        team_matches = match_data[
            (match_data['home_team'] == team) | (match_data['away_team'] == team)
        ]
        
        home_matches = match_data[match_data['home_team'] == team]
        away_matches = match_data[match_data['away_team'] == team]
        
        total_runs_home = home_matches['home_runs'].sum() if len(home_matches) > 0 else 0
        total_runs_away = away_matches['away_runs'].sum() if len(away_matches) > 0 else 0
        total_runs = total_runs_home + total_runs_away
        
        total_matches = len(team_matches)
        home_matches_count = len(home_matches)
        
        stats.append({
            'country': team,
            'format': 'ODI',
            'matches_played': total_matches,
            'innings_batted': total_matches,
            'runs_scored': total_runs,
            'average_runs': total_runs / max(1, total_matches),
            'batting_runs_per_over': total_runs / (total_matches * 50) if total_matches > 0 else 0,
            'highest_team_score': max(home_matches['home_runs'].max(), away_matches['away_runs'].max()) if len(team_matches) > 0 else 0,
            'lowest_completed_score': min(home_matches['home_runs'].min(), away_matches['away_runs'].min()) if len(team_matches) > 0 else 0,
            'batting_average': total_runs / max(1, total_matches * 10),
        })
    
    return pd.DataFrame(stats)


def create_team_bowling_stats(match_data):
    """Create team bowling statistics"""
    
    stats = []
    
    teams = set(match_data['home_team'].unique().tolist() + match_data['away_team'].unique().tolist())
    
    for team in teams:
        team_matches = match_data[
            (match_data['home_team'] == team) | (match_data['away_team'] == team)
        ]
        
        home_matches = match_data[match_data['home_team'] == team]
        away_matches = match_data[match_data['away_team'] == team]
        
        # Runs conceded
        runs_conceded_home = away_matches['away_runs'].sum() if len(away_matches) > 0 else 0
        runs_conceded_away = home_matches['home_runs'].sum() if len(home_matches) > 0 else 0
        total_runs_conceded = runs_conceded_home + runs_conceded_away
        
        # Wickets taken (estimated from opposition wickets)
        wickets_home = home_matches['away_wickets'].sum() if len(home_matches) > 0 else 0
        wickets_away = away_matches['home_wickets'].sum() if len(away_matches) > 0 else 0
        total_wickets = wickets_home + wickets_away
        
        total_matches = len(team_matches)
        
        stats.append({
            'country': team,
            'format': 'ODI',
            'bowling_average': total_runs_conceded / max(1, total_wickets),
            'bowling_runs_per_over': total_runs_conceded / (total_matches * 50) if total_matches > 0 else 0,
            'innings_bowled': total_matches,
            'highest_score_conceded': max(home_matches['away_runs'].max(), away_matches['home_runs'].max()) if len(team_matches) > 0 else 0,
            'lowest_completed_score_conceded': min(home_matches['away_runs'].min(), away_matches['home_runs'].min()) if len(team_matches) > 0 else 0,
            'matches_played': total_matches,  # Add this column to match team_batting
        })
    
    return pd.DataFrame(stats)
