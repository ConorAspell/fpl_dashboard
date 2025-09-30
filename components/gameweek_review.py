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
                    'position': 'relative',
                    'width': '100%',
                    'height': '700px',
                    'background': 'url(https://upload.wikimedia.org/wikipedia/commons/thumb/9/91/Football_pitch_v2.svg/2560px-Football_pitch_v2.svg.png) no-repeat center center',
                    'background-size': '95% 100%',
                    'margin': '20px 0'
                },
                children=[
                    # Home team positions (left side)
                    html.Div(id="home-gk", style={
                        'position': 'absolute',
                        'left': '6%',
                        'top': '50%',
                        'transform': 'translate(-50%, -50%)',
                        'textAlign': 'center'
                    }),
                    html.Div(id="home-def", style={
                        'position': 'absolute',
                        'left': '22%',
                        'top': '50%',
                        'transform': 'translate(-50%, -50%)',
                        'textAlign': 'center'
                    }),
                    html.Div(id="home-mid", style={
                        'position': 'absolute',
                        'left': '38%',
                        'top': '50%',
                        'transform': 'translate(-50%, -50%)',
                        'textAlign': 'center'
                    }),
                    html.Div(id="home-fwd", style={
                        'position': 'absolute',
                        'left': '47%',
                        'top': '50%',
                        'transform': 'translate(-50%, -50%)',
                        'textAlign': 'center'
                    }),
                    # Away team positions (right side)
                    html.Div(id="away-fwd", style={
                        'position': 'absolute',
                        'left': '53%',
                        'top': '50%',
                        'transform': 'translate(-50%, -50%)',
                        'textAlign': 'center'
                    }),
                    html.Div(id="away-mid", style={
                        'position': 'absolute',
                        'left': '62%',
                        'top': '50%',
                        'transform': 'translate(-50%, -50%)',
                        'textAlign': 'center'
                    }),
                    html.Div(id="away-def", style={
                        'position': 'absolute',
                        'left': '78%',
                        'top': '50%',
                        'transform': 'translate(-50%, -50%)',
                        'textAlign': 'center'
                    }),
                    html.Div(id="away-gk", style={
                        'position': 'absolute',
                        'left': '94%',
                        'top': '50%',
                        'transform': 'translate(-50%, -50%)',
                        'textAlign': 'center'
                    })
                ]
            ),
            # Substitutes section below the pitch
            html.Div(
                style={
                    'marginTop': '20px',
                    'padding': '20px',
                    'backgroundColor': 'rgba(0, 0, 0, 0.8)',
                    'borderRadius': '10px'
                },
                children=[
                    html.H4("Substitutes", style={'color': 'white', 'textAlign': 'center', 'marginBottom': '15px'}),
                    html.Div(id="all-subs", style={'display': 'flex', 'justifyContent': 'center', 'flexWrap': 'wrap', 'gap': '15px'})
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