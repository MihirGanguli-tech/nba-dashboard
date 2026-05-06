import streamlit as st
import pandas as pd
from db.connection import get_connection


conn = get_connection()
cursor = conn.cursor()
cursor.execute("SELECT team_id, team_name FROM teams")
teams = cursor.fetchall()
conn.close()

team_dict = {}
#mapping team name to team id
for team in teams:
    team_dict[team[1]] = team[0]

team_names = list(team_dict.keys())

selected_team = st.selectbox("Select a team", team_names)

selected_team_id = team_dict[selected_team]

conn = get_connection()
cursor = conn.cursor()
cursor.execute("SELECT group_name, gp, min, pts, reb, ast, plus_minus FROM lineups WHERE team_id = %s ORDER BY plus_minus DESC;", (selected_team_id,))
results = cursor.fetchall()
conn.close()

df = pd.DataFrame(results, columns=['Lineup', 'Games Played', 'MIN', 'PTS', 'REB', 'AST', 'Plus/Minus'])

st.subheader(f"{selected_team} Lineups")
st.dataframe(df, use_container_width=True)