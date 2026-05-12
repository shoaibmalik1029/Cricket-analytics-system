from data_adapter import load_local_cricket_data

player_innings, team_batting, team_bowling, team_results = load_local_cricket_data()

print("team_batting columns:", list(team_batting.columns))
print("team_batting shape:", team_batting.shape)
print("\nteam_bowling columns:", list(team_bowling.columns))
print("team_bowling shape:", team_bowling.shape)
print("\nteam_results columns:", list(team_results.columns))
print("team_results shape:", team_results.shape)

# Try the merge
team_bowling_clean = team_bowling.drop(columns=['matches_played'], errors='ignore')
merged = team_batting.merge(team_bowling_clean, on=["format", "country"], how="outer")
print("\nAfter first merge - columns:", list(merged.columns))
print("Merged shape:", merged.shape)

results = (
    team_results.groupby(["format", "country"], dropna=False)
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
print("\nResults columns:", list(results.columns))
print("Results shape:", results.shape)

merged2 = merged.merge(results, on=["format", "country"], how="left")
print("\nAfter second merge - columns:", list(merged2.columns))
print("Merged2 shape:", merged2.shape)
print("\nFirst row of merged2:")
print(merged2.iloc[0] if len(merged2) > 0 else "Empty")
