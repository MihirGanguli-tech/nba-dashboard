from nba_api.stats.static import players

all_players = players.get_players()
print(all_players[0])
