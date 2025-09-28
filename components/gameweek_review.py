from dash import dcc, html
import dash_bootstrap_components as dbc

def gameweek_review(players_df, teams_df, gameweek):
    layout = html.Div(
        children=[
            html.Div([
                dbc.Row([
                    dbc.Col(dcc.Dropdown(list(range(1, gameweek+1)), value=gameweek, id='gameweek-drop-down', placeholder="Select Gameweek")),
                    dbc.Col(dcc.Dropdown(id='game-drop-down', placeholder="Select Fixture"))
                ])
            ]),
            html.Div(
                style={
                    'verticalAlign': 'middle',
                    'textAlign': 'center',
                    'background': 'url(https://upload.wikimedia.org/wikipedia/commons/thumb/9/91/Football_pitch_v2.svg/2560px-Football_pitch_v2.svg.png) no-repeat center center fixed',
                    'background-size': 'cover'
                },
                children=[
                    dbc.Row([
                        dbc.Col(id="home-gk", width=1, style={'display': 'flex', 'flexDirection': 'column', 'justifyContent': 'center', 'alignItems': 'center'}),
                        dbc.Col(id="home-def", width=1, style={'display': 'flex', 'flexDirection': 'column', 'justifyContent': 'center', 'alignItems': 'center'}),
                        dbc.Col(id="home-mid", width=1, style={'display': 'flex', 'flexDirection': 'column', 'justifyContent': 'center', 'alignItems': 'center'}),
                        dbc.Col(id="home-fwd", width=1, style={'display': 'flex', 'flexDirection': 'column', 'justifyContent': 'center', 'alignItems': 'center'}),
                        dbc.Col(id="away-fwd", width=1, style={'display': 'flex', 'flexDirection': 'column', 'justifyContent': 'center', 'alignItems': 'center'}),
                        dbc.Col(id="away-mid", width=1, style={'display': 'flex', 'flexDirection': 'column', 'justifyContent': 'center', 'alignItems': 'center'}),
                        dbc.Col(id="away-def", width=1, style={'display': 'flex', 'flexDirection': 'column', 'justifyContent': 'center', 'alignItems': 'center'}),
                        dbc.Col(id="away-gk", width=1, style={'display': 'flex', 'flexDirection': 'column', 'justifyContent': 'center', 'alignItems': 'center'})
                    ], justify='center'),
                    dbc.Row(id="all-subs")
                ]
            ),
            dcc.Store(id='home-players-data'),
            dcc.Store(id='away-players-data'),
            dcc.Store(id='game-data'),
            dbc.Modal(
                id="player-stats-modal",
                is_open=False,
                children=[
                    dbc.ModalHeader("Player Stats"),
                    dbc.ModalBody(id="player-stats-content"),
                    dbc.ModalFooter(dbc.Button("Close", id="close-modal"))
                ]
            )
        ]
    )
    return layout