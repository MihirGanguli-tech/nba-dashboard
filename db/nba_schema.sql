CREATE DATABASE nba_dashboard;

\c nba_dashboard;

CREATE TABLE teams (
    team_id INT PRIMARY KEY,
    team_name VARCHAR(50) NOT NULL
);

CREATE TABLE players (
    player_id INT PRIMARY KEY,
    team_id INT NOT NULL,
    player VARCHAR(50) NOT NULL,
    num VARCHAR(3),
    position VARCHAR(5),
    height VARCHAR(5),
    weight INT,
    age INT,
    FOREIGN KEY (team_id) REFERENCES teams(team_id)
);

CREATE TABLE player_season_stats (
    player_id INT NOT NULL,
    season VARCHAR(10) NOT NULL,
    gp INT,
    min FLOAT,
    pts FLOAT,
    reb FLOAT,
    ast FLOAT,
    stl FLOAT,
    blk FLOAT,
    fg_pct FLOAT,
    fg3_pct FLOAT,
    ft_pct FLOAT,
    plus_minus FLOAT,
    PRIMARY KEY (player_id, season),
    FOREIGN KEY (player_id) REFERENCES players(player_id)
);

CREATE TABLE lineups (
    group_id VARCHAR(50) PRIMARY KEY,
    group_name VARCHAR(200) NOT NULL,
    team_id INT NOT NULL,
    gp INT,
    min FLOAT,
    pts FLOAT,
    ast FLOAT,
    reb FLOAT,
    stl FLOAT,
    blk FLOAT,
    plus_minus FLOAT,
    fg_pct FLOAT,
    fg3_pct FLOAT,
    FOREIGN KEY (team_id) REFERENCES teams(team_id)
);

CREATE TABLE lineup_players (
    player_id INT NOT NULL,
    group_id VARCHAR(50) NOT NULL,
    PRIMARY KEY (player_id, group_id),
    FOREIGN KEY (player_id) REFERENCES players(player_id),
    FOREIGN KEY (group_id) REFERENCES lineups(group_id)
);

CREATE TABLE shots (
    game_id VARCHAR(20) NOT NULL,
    game_event_id INT NOT NULL,
    player_id INT NOT NULL,
    team_id INT NOT NULL,
    period INT,
    minutes_remaining INT,
    seconds_remaining INT,
    action_type VARCHAR(50),
    shot_type VARCHAR(20),
    shot_zone_basic VARCHAR(50),
    shot_zone_area VARCHAR(50),
    shot_zone_range VARCHAR(50),
    shot_distance INT,
    loc_x INT,
    loc_y INT,
    shot_made_flag INT,
    game_date DATE,
    PRIMARY KEY (game_id, game_event_id),
    FOREIGN KEY (player_id) REFERENCES players(player_id),
    FOREIGN KEY (team_id) REFERENCES teams(team_id)
);

CREATE INDEX idx_shots_player ON shots(player_id);
CREATE INDEX idx_shots_game ON shots(game_id);
CREATE INDEX idx_lineups_team ON lineups(team_id);