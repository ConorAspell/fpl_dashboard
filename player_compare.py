from dash import dcc, html
import dash_bootstrap_components as dbc
from dash import dash_table
import pandas as pd

from build import get 

def player_compare(players_df, teams_df):

    positions_map = {1 : "Goalkeeper",
    2 : "Defender",
    3 : "Midfielder",
    4 : "Forward"}
    style_sheet = {"color": "black"}
    teams_map=dict(zip(teams_df.id, teams_df.name))
    players = players_df.web_name.unique()
    teams = players_df.team_name.unique()
    positions = players_df.element_type.unique()
    positions = [positions_map[x] for x in positions]
    content = html.Div(children=[
        dbc.Row([
            dbc.Col(dcc.Dropdown(players, ['Haaland'], id='multi-player-drop-down',  multi=True)),
        ]),
        dcc.Graph(id="cumulative-scoring-2"),
        dcc.Graph(id="price-2")
    ]
    )
    return content
