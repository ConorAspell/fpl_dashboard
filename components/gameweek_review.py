from dash import dcc, html
import dash_bootstrap_components as dbc

def gameweek_review(players_df, teams_df, gameweek):
    layout = html.Div(
        children=[html.Div([

                dbc.Row([
                    dbc.Col(dcc.Dropdown(list(range(1, gameweek+1)),value=gameweek,id='gameweek-drop-down',placeholder="Select Gameweek")),
                    dbc.Col(dcc.Dropdown(id='game-drop-down', placeholder="Select Fixture"))
                ])
            ]),
            html.Div(style= {  
                        'verticalAlign':'middle',
                        'textAlign': 'center',
                        'background': 'url(https://upload.wikimedia.org/wikipedia/commons/thumb/9/91/Football_pitch_v2.svg/2560px-Football_pitch_v2.svg.png) no-repeat center center fixed',
                        'background-size': 'cover'}, children=[ 
                dbc.Row([
                    dbc.Col(width=6, id="home-team",  children=[                    
                        ]),
                    dbc.Col(width=6, id="away-team",  children=[
                        ])]),]
            ),
            html.Div(
                dbc.Col(id="home_subs")
            )])              
    return layout