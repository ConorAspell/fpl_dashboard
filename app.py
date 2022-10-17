import dash
import dash_core_components as dcc
import dash_html_components as html
import numpy as np
import pandas as pd
import dash_bootstrap_components as dbc
from page import page
import requests
from build import get_data, get

df = pd.DataFrame()
players_df, fixtures_df, gameweek = get_data()
pag = page()

def Homepage():
    layout = html.Div([
    pag
    ])
    return layout

app = dash.Dash(__name__,suppress_callback_exceptions=True, external_stylesheets = [dbc.themes.CYBORG])
app.layout = Homepage()
server = app.server

@app.callback(
    dash.dependencies.Output('team_data', 'data'),
    [dash.dependencies.Input('submit-val', 'n_clicks')],
    [dash.dependencies.State('input-on-submit', 'value')],
    prevent_initial_call=True)
def update_output(n_clicks, value):
    if len(value) >= 6:
        team = get('https://fantasy.premierleague.com/api/entry/'+str(value)+'/event/'+str(gameweek-1) +'/picks/')
        players = [x['element'] for x in team['picks']]

        my_team = players_df.loc[players_df.id.isin(players)]
        potential_players = players_df.loc[~players_df.id.isin(players)]
        
        return my_team.to_dict("records")
    return []

if __name__ == '__main__':
    app.run_server(debug=True)