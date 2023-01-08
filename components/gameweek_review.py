from dash import dcc, html
import dash_bootstrap_components as dbc
from dash import dash_table
import pandas as pd
import plotly.express as px

from build import get

position_points = {
    'Goalkeeper': {
        'goal': 6,
        'assist': 3,
        'clean_sheet': 4,
    },
    'Defender': {
        'goal': 5,
        'assist': 3,
        'clean_sheet': 4,
    },
    'Midfielder': {
        'goal': 4,
        'assist': 3,
        'clean_sheet': 1,
    },
    'Forward': {
        'goal': 4,
        'assist': 3,
        'clean_sheet': 0,
    }
}
gameweek=18
fixture_id = 179


def gameweek_review(player_df, teams_df, fixture_df):
    teams=dict(zip(teams_df.id, teams_df.name))
    fixtures = get('https://fantasy.premierleague.com/api/fixtures/?event='+str(gameweek))
    fixture = next(fixture for fixture in fixtures if fixture['id'] == fixture_id)
    away_players = []
    home_players = []
    for player in fixture['stats'][-1]['a']:
        history = get("https://fantasy.premierleague.com/api/element-summary/"+str(player['element'])+"/")
        his = next(f for f in history['history'] if f['fixture'] == fixture_id)
        away_players.append(his)
    for player in fixture['stats'][-1]['h']:
        history = get("https://fantasy.premierleague.com/api/element-summary/"+str(player['element'])+"/")
        his = next(f for f in history['history'] if f['fixture'] == fixture_id)
        home_players.append(his)


    away_df = pd.DataFrame(away_players)
    home_df = pd.DataFrame(home_players)
    away_df['team_a_name'] = away_df['team_a'].map(teams)
    home_df['team_h_name'] = home_df['team_h'].map(teams)
    layout = html.Div(
        children=[html.Div([
            dcc.Dropdown([192, 193], id='gameweek-drop-down',placeholder="Select Gameweek"),
            dcc.Dropdown([192, 193], id='game-drop-down', placeholder="Select Fixture"),
                    dash_table.DataTable(
                    id='home-table',
                    columns=[{"name": i, "id": i} for i in home_df.columns],
                    data=home_df.to_dict('records')
            )]),
            html.Div([
                    dash_table.DataTable(
                    id='away-table',
                    columns=[{"name": i, "id": i} for i in away_df.columns],
                    data=away_df.to_dict('records')
            )]
        )]
    )
    return layout
