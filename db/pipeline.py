import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import time
import pandas as pd
from db.connection import get_connection
from nba_api.stats.static import teams
from nba_api.stats.endpoints import CommonTeamRoster
from nba_api.stats.endpoints import LeagueDashPlayerStats
from nba_api.stats.endpoints import LeagueDashLineups
from nba_api.stats.endpoints import ShotChartDetail
from psycopg2.extras import execute_batch



from nba_api.library.http import NBAStatsHTTP as _http
_http.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Referer': 'https://www.nba.com/',
    'Origin': 'https://www.nba.com',
    'x-nba-stats-origin': 'stats',
    'x-nba-stats-token': 'true',
})

season = '2025-26'
timeout_time = 120


def clear_tables():
    #empty all of the tables to avoid inserting duplicates
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("TRUNCATE TABLE shots, lineup_players, lineups, player_season_stats, players, teams RESTART IDENTITY CASCADE")
    conn.commit()
    conn.close()
    print("Tables cleared")


def load_teams():
    conn = get_connection()
    cursor = conn.cursor()

    all_teams = teams.get_teams()
    data = [(team['id'], team['full_name']) for team in all_teams]

    execute_batch(cursor,
        "INSERT INTO teams (team_id, team_name) VALUES (%s, %s)", data
    )

    conn.commit()
    conn.close()
    print("All teams loaded")


def load_players():
    conn = get_connection()
    cursor = conn.cursor()

    all_teams = teams.get_teams()
    all_rows = []

    for team in all_teams:
        team_id = team['id']
        roster = CommonTeamRoster(team_id=team_id, season=season, timeout=60)
        time.sleep(2)
        df = roster.get_data_frames()[0]
        df.columns = df.columns.str.lower()

        #fetching player names and stats for use if project is expanded
        df = df[['player_id', 'teamid', 'player', 'num', 'position', 'height', 'weight', 'age']]

        for _, row in df.iterrows():
            all_rows.append((
                row['player_id'],
                row['teamid'],
                row['player'],
                row['num'] if pd.notna(row['num']) else None,
                row['position'] if pd.notna(row['position']) else None,
                row['height'] if pd.notna(row['height']) else None,
                row['weight'] if pd.notna(row['weight']) else None,
                row['age'] if pd.notna(row['age']) else None
            ))

    execute_batch(cursor, """
        INSERT INTO players (player_id, team_id, player, num, position, height, weight, age)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, all_rows)

    conn.commit()
    conn.close()
    print("All players loaded")


def load_player_season_stats():
    conn = get_connection()
    cursor = conn.cursor()
    #fetching every players box stats from the api
    all_player_stats = LeagueDashPlayerStats(season=season, timeout=timeout_time)
    df = all_player_stats.get_data_frames()[0]

    df.columns = df.columns.str.lower()
    df = df[['player_id', 'gp', 'min', 'pts', 'reb', 'ast', 'stl', 'blk', 'fg_pct', 'fg3_pct', 'ft_pct', 'plus_minus']]
    df['season'] = season

    data = list(df.itertuples(index=False, name=None))

    execute_batch(cursor, """
        INSERT INTO player_season_stats (player_id, gp, min, pts, reb, ast, stl, blk, fg_pct, fg3_pct, ft_pct, plus_minus, season)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, data)

    conn.commit()
    conn.close()
    print("All player stats loaded")


def load_lineups():
    conn = get_connection()
    cursor = conn.cursor()
    #all lineup stats for each team, combinations of players
    all_lineup_stats = LeagueDashLineups(season=season, timeout=timeout_time)
    df = all_lineup_stats.get_data_frames()[0]
    df.columns = df.columns.str.lower()
    df = df[['group_id', 'group_name', 'team_id', 'gp', 'min', 'pts', 'ast', 'reb', 'stl', 'blk', 'plus_minus', 'fg_pct', 'fg3_pct']]

    data = list(df.itertuples(index=False, name=None))

    execute_batch(cursor, """
        INSERT INTO lineups (group_id, group_name, team_id, gp, min, pts, ast, reb, stl, blk, plus_minus, fg_pct, fg3_pct)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, data)

    conn.commit()
    conn.close()
    print("Lineups loaded")


def load_lineup_players():
    conn = get_connection()
    cursor = conn.cursor()

    all_lineup_stats = LeagueDashLineups(season=season, timeout=timeout_time)
    df = all_lineup_stats.get_data_frames()[0]
    df.columns = df.columns.str.lower()

    data = []
    for _, row in df.iterrows():
        group_id = row['group_id']
        player_ids = group_id.strip('-').split('-')
        for player_id in player_ids:
            data.append((group_id, player_id))

    execute_batch(cursor,
        "INSERT INTO lineup_players (group_id, player_id) VALUES (%s, %s)", data
    )

    conn.commit()
    conn.close()
    print("lineup_players loaded")


def load_shot_data():

    #fetching data for every single shot taken, reg season and playoff, location, type of shot, etc.
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
    df.columns = df.columns.str.lower()
    df['game_date'] = pd.to_datetime(df['game_date'], format='%Y%m%d').dt.strftime('%Y-%m-%d')

    cols = ['game_id', 'game_event_id', 'player_id', 'team_id', 'period',
            'minutes_remaining', 'seconds_remaining', 'action_type', 'shot_type',
            'shot_zone_basic', 'shot_zone_area', 'shot_zone_range', 'shot_distance',
            'loc_x', 'loc_y', 'shot_made_flag', 'game_date']

    data = [tuple(row) for row in df[cols].itertuples(index=False, name=None)]

    execute_batch(cursor, """
        INSERT INTO shots (game_id, game_event_id, player_id, team_id, period,
            minutes_remaining, seconds_remaining, action_type, shot_type,
            shot_zone_basic, shot_zone_area, shot_zone_range, shot_distance,
            loc_x, loc_y, shot_made_flag, game_date)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, data, page_size=5000)
    print(f"Inserted {len(data)} rows")

    conn.commit()
    conn.close()
    print("Shots loaded")


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