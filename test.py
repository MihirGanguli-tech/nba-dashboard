from nba_api.stats.endpoints import LeagueDashPlayerStats

stats = LeagueDashPlayerStats(season='2025-26')
df = stats.get_data_frames()[0]
print(df.columns.tolist())

print(df.head(2))
