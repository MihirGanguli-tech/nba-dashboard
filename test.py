from nba_api.stats.endpoints import LeagueDashLineups

lineups = LeagueDashLineups(season='2025-26', group_quantity=5, timeout=60)
df = lineups.get_data_frames()[0]
print(df.columns.tolist())
print(df.head(2))
