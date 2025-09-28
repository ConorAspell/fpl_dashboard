import dash
from dash import html
import dash_bootstrap_components as dbc
import pandas as pd
from build import get

def register_gameweek_callbacks(app, players_df, teams_df, all_history_df):
    """Register all gameweek-related callbacks"""
    
    @app.callback(
        [dash.dependencies.Output("home-team", 'children')],
        [dash.dependencies.Output("away-team", 'children')],
        [dash.dependencies.State('gameweek-drop-down', 'value')],
        [dash.dependencies.Input('game-drop-down', 'value')]
    )
    def update_gameweek_review(gameweek, fixture_title):
        
        fixture_id = int(fixture_title.split(" ")[0])
        teams=dict(zip(teams_df.id, teams_df.name))
        image_url_prefix = 'https://resources.premierleague.com/premierleague/photos/players/110x140/p'
        fixtures = get('https://fantasy.premierleague.com/api/fixtures/?event='+str(gameweek))

        fixture = next(fixture for fixture in fixtures if fixture['id'] == fixture_id)
        away_ids = [x['element'] for x in fixture['stats'][-2]['a']]
        home_ids = [x['element'] for x in fixture['stats'][-2]['h']]
        away_players = []
        home_players = []
        for p_history in all_history_df:
            if p_history['id'] in away_ids:
                try:
                    game = next(x for x in p_history['history'] if x['fixture'] == fixture_id)
                except StopIteration:
                    print(f"Unable to find fixture {fixture_id} in player history.")
                    continue
                except Exception as e:
                    print(f"An error occurred while searching for fixture {fixture_id}: {str(e)}")
                    continue
                away_players.append(game)
            elif p_history['id'] in home_ids:
                try:
                    game = next(x for x in p_history['history'] if x['fixture'] == fixture_id)
                except StopIteration:
                    print(f"Unable to find fixture {fixture_id} in player history.")
                    continue
                except Exception as e:
                    print(f"An error occurred while searching for fixture {fixture_id}: {str(e)}")
                    continue
                home_players.append(game)

        team_map=dict(zip(players_df.team, players_df.team_name))
        f_df = pd.DataFrame(fixtures)
        f_df['team_a_name'] = f_df['team_a'].map(team_map)
        f_df['team_h_name'] = f_df['team_h'].map(team_map)
        f_df['fixture_title'] = f_df['id'].astype(str) + ": " + f_df['team_h_name'] + " v " + f_df['team_a_name']
        
        away_df = pd.DataFrame(away_players)
        home_df = pd.DataFrame(home_players)
        away_df['id_x'] = away_df['element']
        home_df['id_x'] = home_df['element']
        away_players_df = pd.merge(players_df, away_df, how='inner', on=["id_x"] )
        home_players_df = pd.merge(players_df, home_df, how='inner', on=["id_x"] )
        away_players_df['photo'] = image_url_prefix + away_players_df['photo'].str.slice(start=0, stop=-3) + 'png'
        home_players_df['photo'] = image_url_prefix + home_players_df['photo'].str.slice(start=0, stop=-3) + 'png'

        away_players_df = away_players_df.sort_values('minutes', ascending=False)
        away_players_df_starters = away_players_df.iloc[:11]
        away_players_subs = away_players_df.iloc[11:]

        home_players_df = home_players_df.sort_values('minutes', ascending=False)
        home_players_df_starters = home_players_df.iloc[:11]
        home_players_subs = home_players_df.iloc[11:]

        away_goalkeeper = away_players_df_starters.loc[away_players_df_starters.element_type==1]
        away_defender = away_players_df_starters.loc[away_players_df_starters.element_type==2]
        away_midfielder = away_players_df_starters.loc[away_players_df_starters.element_type==3]
        away_forward = away_players_df_starters.loc[away_players_df_starters.element_type==4]

        if away_forward.empty:
            row = away_midfielder.iloc[-1]
            away_forward = pd.DataFrame([row])
            away_midfielder = away_midfielder.drop(away_midfielder.index[-1])

        home_goalkeeper = home_players_df_starters.loc[home_players_df_starters.element_type==1]
        home_defender = home_players_df_starters.loc[home_players_df_starters.element_type==2]
        home_midfielder = home_players_df_starters.loc[home_players_df_starters.element_type==3]
        home_forward = home_players_df_starters.loc[home_players_df_starters.element_type==4]

        if home_forward.empty:
            row = home_midfielder.iloc[-1]
            home_forward = pd.DataFrame([row])
            home_midfielder = home_midfielder.drop(home_midfielder.index[-1])

        home_df_list = [home_goalkeeper, home_defender, home_midfielder, home_forward]
        away_df_list = [away_forward, away_midfielder, away_defender, away_goalkeeper]

        away_cards = []
        for df in away_df_list:
            card = dbc.Col(children=[
                
                html.Div([
                    html.Div([
                        html.Img(
                            src='{}'.format(row.photo), 
                            id={'type': 'player-image', 'index': i},
                            style={
                                'border-radius': '100%', 
                                'height': '40%', 
                                'width': '55%'
                            }      
                        ),
                        html.P('{}'.format(row.total_points_y), style={"color": "white"})
                    ])
                    for i, row in df.iterrows()
                ])],
                width=3, align='center'
            )
            away_cards.append(card)
        
        home_cards = []
        for df in home_df_list:
            card = dbc.Col(children=[
                
                    html.Div([
                        html.Div([
                            html.Img(
                                src='{}'.format(row.photo), 
                                id={'type': 'player-image', 'index': i},
                                style={
                                    'border-radius': '100%', 
                                    'height': '40%', 
                                    'width': '55%'
                                }      
                            ),
                            html.P('{}'.format(row.total_points_y), style={"color": "white"})
                        ])
                        for i, row in df.iterrows()
                    ])],
                width=3, align='center'
            )
            home_cards.append(card)

        home_sub_cards=[]

        for i, row in home_players_subs.iterrows():
            card = dbc.Col(children=[
                html.Img(
                    src='{}'.format(row.photo), 
                    id={'type': 'player-image', 'index': i},
                    style={
                        'border-radius': '100%', 
                        'height': '40%', 
                        'width': '55%'
                    }
                ),
                html.P('{}'.format(row.total_points_y), style={"color": "white"})
            ], width=3, align='center')
            home_sub_cards.append(card)
        
        away_sub_cards=[]

        for i, row in away_players_subs.iterrows():
            card = dbc.Col(children=[
                html.Img(
                    src='{}'.format(row.photo), 
                    id={'type': 'player-image', 'index': i},
                    style={
                        'border-radius': '100%', 
                        'height': '40%', 
                        'width': '55%'
                    }
                ),
                html.P('{}'.format(row.total_points_y), style={"color": "white"})
            ], width=3, align='center')
            away_sub_cards.append(card)

        return html.Div(children=[
                    dbc.Row(                                  
                            home_cards, justify='end'                                
                        ),
                        dbc.Row(
                        home_sub_cards
                        )]
        ), html.Div(children=[
                    dbc.Row(                                  
                            away_cards, justify='end'                                
                        ),
                        dbc.Row(
                        away_sub_cards
                        )]
        )

    @app.callback(
        [dash.dependencies.Output("game-drop-down", "options"),
        dash.dependencies.Output("game-drop-down", "value")],
        [dash.dependencies.Input("gameweek-drop-down", "value")],
    )
    def update_dropdown(gameweek):
        fixtures = get('https://fantasy.premierleague.com/api/fixtures/?event='+str(gameweek))
        team_map=dict(zip(teams_df.id, teams_df.name))
        f_df = pd.DataFrame(fixtures)
        f_df['team_a_name'] = f_df['team_a'].map(team_map)
        f_df['team_h_name'] = f_df['team_h'].map(team_map)
        f_df['fixture_title'] = f_df['id'].astype(str) + " - " + f_df['team_h_name'] + " v " + f_df['team_a_name']
        f_df = f_df.sort_values('id')
        f_df = f_df.loc[f_df.finished_provisional==True]
        options = [{'label': d['fixture_title'], 'value': d['fixture_title']} for d in f_df.to_dict('records')]
        return options, options[0]['value'] if options else None