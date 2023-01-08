from dash import dcc, html
import dash_bootstrap_components as dbc
from dash import dash_table
import pandas as pd

from build import get 

columns = ['total_points', 'minutes',
       'goals_scored', 'assists', 'clean_sheets', 'goals_conceded',
       'own_goals', 'penalties_saved', 'penalties_missed', 'yellow_cards',
       'red_cards', 'saves', 'bonus', 'bps', 'influence', 'creativity',
       'threat', 'ict_index', 'starts', 'expected_goals', 'expected_assists',
       'expected_goal_involvements', 'expected_goals_conceded', 'value',
       'transfers_balance', 'selected', 'transfers_in', 'transfers_out']
cum_columns = [ 'value',
       'cum_sum', 'cum_minutes', 'cum_goals_scored', 'cum_assists',
       'cum_clean_sheets', 'cum_goals_conceded', 'cum_own_goals',
       'cum_penalties_saved', 'cum_penalties_missed', 'cum_yellow_cards',
       'cum_red_cards', 'cum_saves', 'cum_bonus', 'cum_bps', 'cum_influence',
       'cum_creativity', 'cum_threat', 'cum_ict_index', 'cum_starts',
       'cum_expected_goals', 'cum_expected_assists',
       'cum_expected_goal_involvements', 'cum_expected_goals_conceded',
       'cum_value', 'cum_transfers_balance', 'cum_selected',
       'cum_transfers_in', 'cum_transfers_out']

tabs_styles = {
    'height': '44px',
    'backgroundColor' : 'black'
}
tab_style = {
    'borderBottom': '1px solid #d6d6d6',
    'padding': '6px',
    'fontWeight': 'bold',
    'backgroundColor' : 'black',
    'color': 'white',
}

tab_selected_style = {
    'borderTop': '1px solid #d6d6d6',
    'borderBottom': '1px solid #d6d6d6',
    'backgroundColor': '#119DFF',
    'color': 'white',
    'padding': '6px'
}

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
        dcc.Store(id='session', storage_type='session'),
    dcc.Tabs([

        dcc.Tab(label='Sequential', style=tab_style, selected_style=tab_selected_style,
        children =[
        dbc.Row([
            dbc.Col(dcc.Dropdown(columns, ['total_points'], id='stat-drop-down')),
            dbc.Col(dcc.Dropdown(players, ['Haaland'], id='multi-player-drop-down',  multi=True)),
        ]),
        dcc.Graph(id="sequential-scoring"),
        dbc.Col(dcc.Dropdown(columns, ['total_points'], id='stat-drop-down')),
        dcc.Graph(id="player-price")
        ]
        ),
        dcc.Tab(label='Cumulative', style=tab_style, selected_style=tab_selected_style,
        children = [
        dbc.Row([
            dbc.Col(dcc.Dropdown(cum_columns, value=['cum_sum'], id='cum-stat-drop-down')),
            dbc.Col(dcc.Dropdown(players, ['Haaland'], id='multi-player-drop-down-2',  multi=True)),
        ]),
            dcc.Graph(id="cumulative-scoring-2"),
            dbc.Col(dcc.Dropdown(cum_columns, value=['value'], id='cum-stat-drop-down-2')),
            
            dcc.Graph(id="player-price-2")
    ])
    ]
    )
    ]
    )
    return content
