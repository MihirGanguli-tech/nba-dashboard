import sys
import os
#was having trouble, file was not running from project root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import time
import pandas as pd

from db.connection import get_connection
from nba_api.stats.static import teams
from nba_api.stats.endpoints import CommonTeamRoster
from nba_api.stats.endpoints import LeagueDashPlayerStats



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
    conn = get_connection()
    cursor = conn.cursor()

    all_teams = teams.get_teams()

    for team in all_teams:

        team_id = team['id']
        #list of dataframes containing team rosters
        roster = CommonTeamRoster(team_id=team_id, season='2025-26', timeout = 60)
        time.sleep(2)
        df = roster.get_data_frames()[0]
        #make all column names lowercase to match sql database
        df.columns = df.columns.str.lower()
        #only the columns needed for insertion into database
        df = df[['teamid', 'player', 'player_id', 'num', 'position', 'height', 'weight', 'age']]

        df.columns = df.columns.str.lower()

        df = df[['player_id', 'teamid', 'player', 'num', 'position', 'height', 'weight', 'age']]

    for _, row in df.iterrows():
        cursor.execute("""
            INSERT INTO players (player_id, team_id, player, num, position, height, weight, age)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
            row['player_id'],
            row['teamid'],
            row['player'],
            row['num'] if pd.notna(row['num']) else None,
            row['position'] if pd.notna(row['position']) else None,
            row['height'] if pd.notna(row['height']) else None,
            row['weight'] if pd.notna(row['weight']) else None,
            row['age'] if pd.notna(row['age']) else None
        ))

    conn.commit()
    conn.close()
    print("All players loaded")

        





def load_player_season_stats():

    conn = get_connection()
    cursor = conn.cursor()

    all_player_stats = LeagueDashPlayerStats(season = '2025-26', timeout=60)
    df = all_player_stats.get_data_frames()[0]

    df.columns = df.columns.str.lower()
    df = df[['player_id', 'gp', 'min', 'pts', 'reb', 'ast', 'stl', 'blk', 'fg_pct', 'fg3_pct', 'ft_pct', 'plus_minus']]
    #hardcode a season column
    df['season'] = '2025-26'
    for _, row in df.iterrows():
        cursor.execute("""
        INSERT INTO player_season_stats (player_id, gp, min, pts, reb, ast, stl, blk, fg_pct, fg3_pct, ft_pct, plus_minus, season)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,(
            row['player_id'],
            row['gp'],
            row['min'],
            row['pts'],
            row['reb'],
            row['ast'],
            row['stl'],
            row['blk'],
            row['fg_pct'],
            row['fg3_pct'],
            row['ft_pct'],
            row['plus_minus'],
            row['season']

        ))
    
    conn.commit()
    conn.close()
    print("All player stats loaded")






def load_lineups():
    pass
def load_lineup_players():
    pass
def load_shots():
    pass




def main():
    clear_tables()
    load_teams()
    load_players()
    load_player_season_stats()
    #load_lineups()
    #load_lineup_players()
    #load_shots()

if __name__ == "__main__":
    main()