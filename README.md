# NBA Analytics Dashboard

A  NBA analytics platform built with Streamlit, providing  lineup analysis and shot quality breakdowns for the 2025-26 NBA season.

🔗 **Live app:** (https://m2ocj8vtrzzsfvf8rcww5n.streamlit.app/team_lineup_browser)

May take a while to load, on Streamlit's free tier the link shuts down after 7 days of inactivity and reboots when the URL is visited.


## Overview
 Ingests play-by-play shot data and team/lineup statistics directly from the NBA's stats API, stores them in a cloud Postgres database, and displays them through an interactive Streamlit dashboard.

**Current pages:**
- **Team Lineup Browser** — explore real 5-man lineups by team, ranked by plus/minus
- **Shot Quality Analyzer** — interactive shot charts with court rendering, zone efficiency tables, and shot type breakdowns for any team or player


## Tech Stack

| Layer | Tools |
|---|---|
| Frontend | Streamlit, Plotly |
| Backend / ETL | Python, pandas, nba_api |
| Database | PostgreSQL (Neon, cloud-hosted) |
| DB Driver | psycopg2 (`execute_batch` for bulk inserts) |
| Scheduling | Windows Task Scheduler |


---

## Architecture

```
nba_api (stats.nba.com)
        │
        ▼
  db/pipeline.py   -> PostgreSQL (Neon)
   - load_teams
   - load_players
   - load_player_season_stats
   - load_lineups
   - load_lineup_players
   - load_shot_data (ON CONFLICT DO NOTHING — incremental)
        │
        ▼
   Streamlit app (app.py + pages/)
   - reads from db/connection.py
   - renders interactive Plotly visualizations
```

**Daily refresh:** `refresh.bat` runs `pipeline.py` using Windows Task Scheduler every night. Shot data is inserted incrementally (`ON CONFLICT DO NOTHING`) so only new games are added, but tables teams, players, lineups, season stats are wiped clean and refreshed in full each run.

---

## Database Schema

| Table | Description |
|---|---|
| `teams` | Team ID and name |
| `players` | Player roster info (team, position, height, weight, age) |
| `player_season_stats` | Per-season aggregate stats (pts, reb, ast, fg_pct, etc.) |
| `lineups` | 5-man lineup combinations with aggregate stats per team |
| `lineup_players` | Join table mapping lineups to individual players |
| `shots` | Individual shot attempts with location (loc_x/loc_y), zone, distance, and outcome |

---

## Design Decisions

**Why PostgreSQL on Neon instead of local MySQL**
The project started on local MySQL, but a cloud-hosted database was needed to deploy the dashboard on Streamlit Cloud without requiring users to run a local server. Neon's free Postgres tier covered the size of the database. The migration required converting `AUTO_INCREMENT` → `SERIAL`, dropping MySQL-specific foreign key syntax, and switching the driver from `mysql-connector-python` to `psycopg2`.

**Why `execute_batch` over `executemany` or row-by-row inserts**

Row-by-row inserts required a separate network round trip to Neon for each of the 113,000 rows. execute_batch groups rows into batches of 5,000, reducing 113,000 round trips to around 23 and cutting total insert time from 20+ minutes to under 2 minutes.

**Why `ON CONFLICT DO NOTHING` for shots instead of fully truncating and reloading on every refresh**
Re-pulling and re-inserting all season shot data daily is wasteful because only new games need to be added. The `shots` table's primary key (`game_id`, `game_event_id`) makes each shot uniquely identifiable, so `ON CONFLICT DO NOTHING` allows the pipeline to safely re-run daily and only insert new rows. Reference tables (teams, players, lineups, season stats) are small enough that a full refresh does not significantly impact the load time and makes it easy to update rosters and lineups from trades or free agent signings.

**Why GitHub Actions was abandoned for the daily refresh**

Originally I planned the daily pipeline to run through Github Actions so that the pipeline was not depended on my computer. However, `stats.nba.com` appears to actively block cloud infrastructure IP ranges, causing consistent read timeouts. The pipeline remains on local Windows Task Scheduler.




## Project Structure

```
nba_dashboard/
├── data/
├── db/
│   ├── nba_schema.sql
│   ├── connection.py
│   └── pipeline.py
├── models/
│   └── shot_model.py
├── pages/
│   ├── 1_team_lineup_browser.py
│   ├── 2_shot_quality_analyzer.py
├── app.py
├── refresh.bat
├── requirements.txt
└── .env
```
