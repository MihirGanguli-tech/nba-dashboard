import streamlit as st
import pandas as pd
import plotly.express as px
from db.connection import get_connection

st.set_page_config(page_title="Shot Quality Analyzer", layout="wide")
st.title("🏀 Shot Quality Analyzer")

mode = st.sidebar.radio("View by", ["Team", "Player"])


conn = get_connection()
cursor = conn.cursor()

#user can choose to see shot map for either a player or team
if mode  == "Team":
    cursor.execute("SELECT DISTINCT team_name FROM teams")
if mode == "Player":
    cursor.execute("SELECT DISTINCT player FROM players")

results = cursor.fetchall()
options = [row[0] for row in results]

#there is alot of players, instead of scrolling through all create a search bar
if mode == "Player":
    search = st.sidebar.text_input("Search player name")
    options_filtered = [p for p in options if search.lower() in p.lower()]
    selection = st.sidebar.selectbox("Select", options_filtered)
else:
    selection = st.sidebar.selectbox("Select", options)



if mode  == "Team":
    cursor.execute("""
    
    SELECT shot_zone_basic, shot_zone_area, shot_made_flag, loc_x, loc_y,action_type
    FROM shots
    INNER JOIN teams ON teams.team_id = shots.team_id
    WHERE teams.team_name = %s
    """, (selection,))
if mode == "Player":
     cursor.execute("""
    
    SELECT shot_zone_basic, shot_zone_area, shot_made_flag, loc_x, loc_y, action_type
    FROM shots
    INNER JOIN players ON players.player_id = shots.player_id
    WHERE players.player = %s
    """,(selection,) )
     
rows = cursor.fetchall()
df = pd.DataFrame(rows, columns=["zone_basic", "zone_area", "shot_made", "loc_x", "loc_y", "action_type"])
#group actions into smaller categories
df['action_type']= df['action_type'].apply(
    lambda x: 'Layup' if 'Layup' in x else
              'Dunk' if 'Dunk' in x else
              'Jump Shot' if ('Jump' in x and 'Floating' not in x) else
              'Floater' if 'Floating' in x else
              'Hook' if 'Hook' in x else
              'Other'
)
conn.close()


action_types = ["All"] + sorted(df["action_type"].unique().tolist())
selected_action = st.sidebar.selectbox("Shot Type", action_types)

if selected_action != "All":
    df = df[df["action_type"] == selected_action]


df_grouped_by_shotzone = df.groupby('zone_basic')['shot_made'].agg(
    FGA = 'count',
    FGM = 'sum',
    FG_PCT = 'mean'
)

df_grouped_by_shotzone["FG_PCT"] = (df_grouped_by_shotzone["FG_PCT"] * 100).round(1)
df_grouped_by_shotzone = df_grouped_by_shotzone.reset_index()

st.dataframe(
    df_grouped_by_shotzone,
    use_container_width=True
)

df_grouped_by_action = df.groupby('action_type')['shot_made'].count().reset_index()
df_grouped_by_action.columns = ['action_type', 'count']

fig_action = px.pie(
    df_grouped_by_action,
    values="count",
    names="action_type",
    title=f"Shot Distribution by Type — {selection}"
)

st.plotly_chart(fig_action, use_container_width=True)



df["shot_made"] = df["shot_made"].astype(str)

st.subheader("Zone Efficiency")

st.subheader("Shot Chart")

fig = px.scatter(
    df,
    x="loc_x",
    y="loc_y",
    color="shot_made",
    color_discrete_map={"1":"green", "0":"red"},
    title=f"Shot Chart — {selection}"
)



#chat gpt generated function to draw court markings, adjusted in the update_layout so that it is not stretched
def draw_court(fig):
    # Hoop
    fig.add_shape(type="circle", x0=-7.5, y0=-7.5, x1=7.5, y1=7.5, line_color="gray")
    # Backboard
    fig.add_shape(type="line", x0=-30, y0=-7.5, x1=30, y1=-7.5, line_color="gray")
    # Paint
    fig.add_shape(type="rect", x0=-80, y0=-47.5, x1=80, y1=142.5, line_color="gray")
    # Free throw circle
    fig.add_shape(type="circle", x0=-60, y0=77.5, x1=60, y1=197.5, line_color="gray")
    # Three point line
    fig.add_shape(type="line", x0=-220, y0=-47.5, x1=-220, y1=92.5, line_color="gray")
    fig.add_shape(type="line", x0=220, y0=-47.5, x1=220, y1=92.5, line_color="gray")
    fig.add_shape(type="path",
        path="M -220 92.5 Q 0 357.5 220 92.5",
        line_color="gray")
    return fig


fig = draw_court(fig)
fig.update_layout(
    yaxis_range=[-50, 400],
    xaxis_range=[-250, 250],
    yaxis=dict(visible=False),
    xaxis=dict(visible=False),
    height=1000,
    width = 1000,
    yaxis_scaleanchor="x",  # locks aspect ratio
    plot_bgcolor="white"
)

fig.update_traces(marker=dict(size=6))
st.plotly_chart(fig, use_container_width=True)

