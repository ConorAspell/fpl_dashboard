import dash
from dash import dcc, html
import pandas as pd
import dash_bootstrap_components as dbc
from build import get_data
from page import page
from components.navbar import Navbar
from flask_caching import Cache

# Import all callback modules
from callbacks.player_callbacks import register_player_callbacks
from callbacks.comparison_callbacks import register_comparison_callbacks
from callbacks.team_callbacks import register_team_callbacks
from callbacks.gameweek_callbacks import register_gameweek_callbacks
from callbacks.navigation_callbacks import register_navigation_callbacks

# Load data
df = pd.DataFrame()
bet_df, players_df, fixtures_df, gameweek, history, teams_df, all_history_df = get_data()
pag = page()

# Setup layout components
content = html.Div(id="page-content", children=[])
nav = Navbar()

def Homepage():
    layout = html.Div([
    dcc.Location(id="url"),
    nav,
    content
    ])
    return layout

# Initialize Dash app
app = dash.Dash(__name__, suppress_callback_exceptions=True, external_stylesheets=[dbc.themes.CYBORG])
app.title = 'FPL Data'
app._favicon = ("/home/conor-aspell/Documents/projects/fpl_dashboard/icon/favicon.ico")
app.layout = Homepage()
server = app.server
cache = Cache(app.server, config={'CACHE_TYPE': 'simple'})

# Register all callbacks
register_player_callbacks(app, players_df, cache)
register_comparison_callbacks(app, players_df, cache)
register_team_callbacks(app, players_df)
register_gameweek_callbacks(app, players_df, teams_df, all_history_df)
register_navigation_callbacks(app, players_df, teams_df, bet_df, gameweek)

if __name__ == '__main__':
    app.run_server(debug=True, host='0.0.0.0', port=8051)