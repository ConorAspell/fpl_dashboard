from dash import html, dcc, Dash
import dash_table
import requests
from dash.dependencies import Input, Output

def change_recommender():

# Create the text box for inputting the user's Fantasy Premier League ID
    content = html.Div([
        dcc.Input(id='fpl-id', type='text', value=''),
        dash_table.DataTable(
            id='team-table',
            style_cell={
                'textAlign': 'center'
            },
            style_data_conditional=[
                {
                    'if': {'column_id': 'name'},
                    'textAlign': 'left'
                },
                {
                    'if': {'column_id': 'cost'},
                    'format': '{:,}',
                    'fontSize': 14
                }
            ]
        )
    ])

    return content


