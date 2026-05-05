import sys
import os
#was having trouble, file was not running from project root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.connection import get_connection
from nba_api.stats.static import teams



def clear_tables():
    """
    Clear the tables by temporarily disabling foregin key checks. 
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
    cursor.execute("TRUNCATE TABLE shots")
    cursor.execute("TRUNCATE TABLE lineup_players")
    cursor.execute("TRUNCATE TABLE lineups")
    cursor.execute("TRUNCATE TABLE player_season_stats")
    cursor.execute("TRUNCATE TABLE players")
    cursor.execute("TRUNCATE TABLE teams")
    cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
    
    conn.commit()
    conn.close()
    print("Tables cleared")



def load_teams():

    conn = get_connection()
    cursor = conn.cursor()

    #retrieve list of teams from the API
    all_teams = teams.get_teams()

    for team in all_teams:

        team_id = team['id']
        team_name = team['full_name']

        cursor.execute(
        "INSERT INTO teams (team_id, team_name) VALUES (%s, %s)", (team_id, team_name)
        )

    conn.commit()
    conn.close()
    print("All teams loaded")



def load_players():
    pass
def load_player_season_stats():
    pass
def load_lineups():
    pass
def load_lineup_players():
    pass
def load_shots():
    pass




def main():
    clear_tables()
    load_teams()
    #load_players()
    #load_player_season_stats()
    #load_lineups()
    #load_lineup_players()
    #load_shots()

if __name__ == "__main__":
    main()