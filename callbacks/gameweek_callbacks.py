import dash
from dash import html
import dash_bootstrap_components as dbc
import pandas as pd
from build import get
import json

def register_gameweek_callbacks(app, players_df, teams_df, all_history_df):
    """Register all gameweek-related callbacks"""
    
    @app.callback(
        [dash.dependencies.Output("home-gk", 'children'),
         dash.dependencies.Output("home-def", 'children'),
         dash.dependencies.Output("home-mid", 'children'),
         dash.dependencies.Output("home-fwd", 'children'),
         dash.dependencies.Output("away-fwd", 'children'),
         dash.dependencies.Output("away-mid", 'children'),
         dash.dependencies.Output("away-def", 'children'),
         dash.dependencies.Output("away-gk", 'children'),
         dash.dependencies.Output("all-subs", 'children'),
         dash.dependencies.Output('home-players-data', 'data'),
         dash.dependencies.Output('away-players-data', 'data'),
         dash.dependencies.Output('game-data', 'data')],
        [dash.dependencies.Input('gameweek-drop-down', 'value'),
         dash.dependencies.Input('game-drop-down', 'value')]
    )
    def update_gameweek_review(gameweek, fixture_title):
        
        fixture_id = int(fixture_title.split(" ")[0])
        teams=dict(zip(teams_df.id, teams_df.name))
        image_url_prefix = 'https://resources.premierleague.com/premierleague25/photos/players/110x140/'
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
        
        player_map = dict(zip(players_df.id_x, players_df.web_name))
        player_map_2 = dict(zip(players_df.id_x, players_df.element_type))
        game_df = pd.concat([away_df, home_df], ignore_index=True)
        game_df['web_name'] = game_df['element'].map(player_map)
        game_df['element_type'] = game_df['element'].map(player_map_2)
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

        home_gk_content = html.Div([
            html.Div([
                html.Img(
                    src=row.photo,
                    id={'type': 'player-image', 'player_id': row.element},
                    style={'border-radius': '100%', 'height': '50px', 'width': '50px'}
                ),
                html.P(row.total_points_y, style={"color": "white"})
            ]) for row in home_goalkeeper.itertuples()
        ], style={'textAlign': 'center'})

        home_def_content = html.Div([
            html.Div([
                html.Img(
                    src=row.photo,
                    id={'type': 'player-image', 'player_id': row.element},
                    style={'border-radius': '100%', 'height': '50px', 'width': '50px'}
                ),
                html.P(row.total_points_y, style={"color": "white"})
            ]) for row in home_defender.itertuples()
        ], style={'textAlign': 'center'})

        home_mid_content = html.Div([
            html.Div([
                html.Img(
                    src=row.photo,
                    id={'type': 'player-image', 'player_id': row.element},
                    style={'border-radius': '100%', 'height': '50px', 'width': '50px'}
                ),
                html.P(row.total_points_y, style={"color": "white"})
            ]) for row in home_midfielder.itertuples()
        ], style={'textAlign': 'center'})

        home_fwd_content = html.Div([
            html.Div([
                html.Img(
                    src=row.photo,
                    id={'type': 'player-image', 'player_id': row.element},
                    style={'border-radius': '100%', 'height': '50px', 'width': '50px'}
                ),
                html.P(row.total_points_y, style={"color": "white"})
            ]) for row in home_forward.itertuples()
        ], style={'textAlign': 'center'})

        away_fwd_content = html.Div([
            html.Div([
                html.Img(
                    src=row.photo,
                    id={'type': 'player-image', 'player_id': row.element},
                    style={'border-radius': '100%', 'height': '50px', 'width': '50px'}
                ),
                html.P(row.total_points_y, style={"color": "white"})
            ]) for row in away_forward.itertuples()
        ], style={'textAlign': 'center'})

        away_mid_content = html.Div([
            html.Div([
                html.Img(
                    src=row.photo,
                    id={'type': 'player-image', 'player_id': row.element},
                    style={'border-radius': '100%', 'height': '50px', 'width': '50px'}
                ),
                html.P(row.total_points_y, style={"color": "white"})
            ]) for row in away_midfielder.itertuples()
        ], style={'textAlign': 'center'})

        away_def_content = html.Div([
            html.Div([
                html.Img(
                    src=row.photo,
                    id={'type': 'player-image', 'player_id': row.element},
                    style={'border-radius': '100%', 'height': '50px', 'width': '50px'}
                ),
                html.P(row.total_points_y, style={"color": "white"})
            ]) for row in away_defender.itertuples()
        ], style={'textAlign': 'center'})

        away_gk_content = html.Div([
            html.Div([
                html.Img(
                    src=row.photo,
                    id={'type': 'player-image', 'player_id': row.element},
                    style={'border-radius': '100%', 'height': '50px', 'width': '50px'}
                ),
                html.P(row.total_points_y, style={"color": "white"})
            ]) for row in away_goalkeeper.itertuples()
        ], style={'textAlign': 'center'})

        home_sub_cards = []
        for i, row in home_players_subs.iterrows():
            card = html.Div(children=[
                html.Img(
                    src=row.photo,
                    id={'type': 'player-image', 'player_id': row.element},
                    style={'border-radius': '100%', 'height': '50px', 'width': '50px'}
                ),
                html.P(row.total_points_y, style={"color": "white", "margin": "5px 0"})
            ], style={'textAlign': 'center', 'margin': '5px'})
            home_sub_cards.append(card)

        away_sub_cards = []
        for i, row in away_players_subs.iterrows():
            card = html.Div(children=[
                html.Img(
                    src=row.photo,
                    id={'type': 'player-image', 'player_id': row.element},
                    style={'border-radius': '100%', 'height': '50px', 'width': '50px'}
                ),
                html.P(row.total_points_y, style={"color": "white", "margin": "5px 0"})
            ], style={'textAlign': 'center', 'margin': '5px'})
            away_sub_cards.append(card)

        all_subs_content = html.Div([
            html.Div([
                html.H6("Home Substitutes", style={'color': 'white', 'marginBottom': '10px', 'textAlign': 'center'}),
                html.Div(home_sub_cards, style={'display': 'flex', 'justifyContent': 'center', 'flexWrap': 'wrap', 'gap': '8px', 'minWidth': '400px'})
            ], style={'width': '48%', 'minWidth': '450px'}),
            html.Div([
                html.H6("Away Substitutes", style={'color': 'white', 'marginBottom': '10px', 'textAlign': 'center'}),
                html.Div(away_sub_cards, style={'display': 'flex', 'justifyContent': 'center', 'flexWrap': 'wrap', 'gap': '8px', 'minWidth': '400px'})
            ], style={'width': '48%', 'minWidth': '450px'})
        ], style={'display': 'flex', 'justifyContent': 'space-between', 'alignItems': 'flex-start', 'flexWrap': 'wrap'})

        return (home_gk_content, home_def_content, home_mid_content, home_fwd_content,
                away_fwd_content, away_mid_content, away_def_content, away_gk_content,
                all_subs_content,
                home_players_df.to_dict('records'), away_players_df.to_dict('records'),
                game_df.to_dict('records'))

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

    @app.callback(
        dash.dependencies.Output("player-stats-modal", "is_open"),
        dash.dependencies.Output("player-stats-content", "children"),
        dash.dependencies.Input({"type": "player-image", "player_id": dash.dependencies.ALL}, "n_clicks"),
        dash.dependencies.Input("close-modal", "n_clicks"),
        dash.dependencies.State("game-data", "data"),
        prevent_initial_call=True
    )
    def show_player_stats(n_clicks_images, n_clicks_close, game_data):
        ctx = dash.callback_context
        if not ctx.triggered:
            return False, ""
        trigger_id_str = ctx.triggered[0]['prop_id']
        if 'close-modal' in trigger_id_str:
            return False, ""
        # parse the player_id
        trigger_id = json.loads(trigger_id_str.split('.')[0])
        player_id = trigger_id['player_id']
        # find player data
        all_data = game_data or []
        player_data = next((p for p in all_data if p['element'] == player_id), None)
        if not player_data:
            return True, "Player data not found"
        # create content
        content = html.Div([
            html.H5(player_data.get('web_name', 'Unknown')),
            html.P(f"Total Points: {player_data.get('total_points', 0)}"),
            html.P(f"Minutes: {player_data.get('minutes', 0)}"),
            html.P(f"Goals: {player_data.get('goals_scored', 0)}"),
            html.P(f"Assists: {player_data.get('assists', 0)}"),
            html.P(f"Saves: {player_data.get('saves', 0)}"),
            html.P(f"Clean Sheets: {player_data.get('clean_sheets', 0)}"),
            html.P(f"Yellow Cards: {player_data.get('yellow_cards', 0)}"),
            html.P(f"Red Cards: {player_data.get('red_cards', 0)}"),
            html.P(f"Bonus: {player_data.get('bonus', 0)}"),
            html.P(f"Expected Goals: {player_data.get('expected_goals', 0)}"),
            html.P(f"Expected Assists: {player_data.get('expected_assists', 0)}"),
        ])
        return True, content