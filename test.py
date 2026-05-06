from nba_api.stats.endpoints import CommonTeamRoster

roster = CommonTeamRoster(team_id=1610612737, season='2025-26')
df =roster.get_data_frames()
print(df[0])

