import dash_bootstrap_components as dbc
import dash_html_components as html
import numpy as np
import pandas as pd
import dash_core_components as dcc
import dash_table
from dash.dependencies import Input, Output
columns = ['chance_of_playing_next_round', 'chance_of_playing_this_round',
       'element_type', 'ep_next', 'ep_this', 'first_name', 'form',
       'now_cost', 'points_per_game', 'second_name',
       'selected_by_percent', 'total_points',
       'transfers_in', 'transfers_out', 'value_form', 'value_season',
       'web_name', 'influence', 'creativity', 'threat', 'ict_index',
       'team_name',
        'stats',
       'team_h_difficulty', 'team_a_difficulty',  'team_a_name',
       'team_h_name', 'team_a_strength', 'team_h_strength', 'diff']
def page():
    pag = html.Div(children=[
        dcc.Input(
            placeholder='Enter your team number',
            type='text',
            id='input-on-submit',
            value=''
        ),
        html.Button('Submit', id='submit-val', n_clicks=0),
        html.Div(id='container-button-basic',
                children='Enter a value and press submit'),
        dash_table.DataTable(
            id='team_data',
            columns=[{"name": i, "id": i} for i in columns],       
            style_header={'backgroundColor': 'rgb(30, 30, 30)'},
            style_cell={
                'backgroundColor': 'rgb(50, 50, 50)',
                'color': 'white'
            },
            )
    ])
    return pag