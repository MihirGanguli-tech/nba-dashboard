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
from nba_api.stats.endpoints import LeagueDashLineups
from nba_api.stats.endpoints import ShotChartDetail

season = '2025-26'

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
        roster = CommonTeamRoster(team_id=team_id, season=season, timeout = 60)
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

    all_player_stats = LeagueDashPlayerStats(season = season, timeout=60)
    df = all_player_stats.get_data_frames()[0]

    df.columns = df.columns.str.lower()
    df = df[['player_id', 'gp', 'min', 'pts', 'reb', 'ast', 'stl', 'blk', 'fg_pct', 'fg3_pct', 'ft_pct', 'plus_minus']]
    #hardcode a season column
    df['season'] = season
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

    conn = get_connection()
    cursor = conn.cursor()

    all_lineup_stats = LeagueDashLineups(season = season, timeout = 60)
    df = all_lineup_stats.get_data_frames()[0]
    df.columns = df.columns.str.lower()
    #keeping only what will be inserted into the table
    df = df[['group_id', 'group_name', 'team_id', 'gp', 'min', 'pts', 'ast', 'reb', 'stl', 'blk', 'plus_minus', 'fg_pct', 'fg3_pct']]
    for _, row in df.iterrows():
        cursor.execute("""
            INSERT INTO lineups (group_id, group_name, team_id, gp, min, pts, ast, reb, stl, blk, plus_minus, fg_pct, fg3_pct)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            row['group_id'],
            row['group_name'],
            row['team_id'],
            row['gp'],
            row['min'],
            row['pts'],
            row['ast'],
            row['reb'],
            row['stl'],
            row['blk'],
            row['plus_minus'],
            row['fg_pct'],
            row['fg3_pct']
        ))

    conn.commit()
    conn.close()
    print("Lineups loaded")





def load_lineup_players():

    conn = get_connection()
    cursor = conn.cursor()

    all_lineup_stats = LeagueDashLineups(season = season, timeout=60)
    df = all_lineup_stats.get_data_frames()[0]
    df.columns = df.columns.str.lower()

    for _, row in df.iterrows():

        group_id = row['group_id']
        #split into individual player ids
        player_ids = group_id.strip('-').split('-')

        for player_id in player_ids:
            cursor.execute("INSERT INTO lineup_players (group_id, player_id) VALUES (%s, %s)", (group_id, player_id))

    conn.commit()
    conn.close()
    print("lineup_players loaded")




def load_shot_data():

    conn = get_connection()
    cursor = conn.cursor()
    regular = ShotChartDetail(
        team_id=0,
        player_id=0,
        season_type_all_star='Regular Season',
        season_nullable=season,
        context_measure_simple='FGA',
        timeout=60
    )
    time.sleep(2)
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
    df.to_csv(f'data/shot_data_{season}.csv', index=False)

    df.columns = df.columns.str.lower()
    #SQL datetime format
    df['game_date'] = pd.to_datetime(df['game_date'], format='%Y%m%d').dt.strftime('%Y-%m-%d')

    for idx, row in df.iterrows():
        try:
            cursor.execute("""
            INSERT INTO shots (game_id, game_event_id, player_id, team_id, period,
                minutes_remaining, seconds_remaining, action_type, shot_type,
                shot_zone_basic, shot_zone_area, shot_zone_range, shot_distance,
                loc_x, loc_y, shot_made_flag, game_date)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            row['game_id'], row['game_event_id'], row['player_id'], row['team_id'],
            row['period'], row['minutes_remaining'], row['seconds_remaining'],
            row['action_type'], row['shot_type'], row['shot_zone_basic'],
            row['shot_zone_area'], row['shot_zone_range'], row['shot_distance'],
            row['loc_x'], row['loc_y'], row['shot_made_flag'], row['game_date']
        ))
        except Exception as e:
            print(f"Error on row {idx}: {e}")
            break

    conn.commit()
    conn.close()
    print("Shots loaded")
    print(f"CSV rows: {len(df)}")



    


def main():
    clear_tables()
    load_teams()
    load_players()
    load_player_season_stats()
    load_lineups()
    load_lineup_players()
    load_shot_data()

if __name__ == "__main__":
    main()