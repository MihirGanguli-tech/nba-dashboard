import pandas as pd
import time
from nba_api.stats.endpoints import ShotChartDetail

season = '2025-26'

print("Pulling regular season shot data")
regular = ShotChartDetail(
    team_id=0,
    player_id=0,
    season_type_all_star='Regular Season',
    season_nullable=season,
    context_measure_simple='FGA',
    timeout=60
)
time.sleep(2)

print("Pulling playoff shot data")
playoffs = ShotChartDetail(
    team_id=0,
    player_id=0,
    season_type_all_star='Playoffs',
    season_nullable=season,
    context_measure_simple='FGA',
    timeout=60
)

df_regular = regular.get_data_frames()[0]
df_playoffs = playoffs.get_data_frames()[0]

df = pd.concat([df_regular, df_playoffs], ignore_index=True)
df.columns = df.columns.str.lower()

#make sure game date column is made into datetime
df['game_date'] = pd.to_datetime(df['game_date'], format='%Y%m%d').dt.strftime('%Y-%m-%d')

print(f"Total rows: {len(df)}")
print(f"Columns: {df.columns.tolist()}")
print(df.head())
print(df.isnull().sum())

df.to_csv('data/shot_data_2025_26.csv', index=False)
print("Saved to data/shot_data_2025_26.csv")