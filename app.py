from turtle import title
import dash
from dash import dcc, html, ctx
import json
import numpy as np
import pandas as pd
import dash_bootstrap_components as dbc

from components.player_history import player_history
from page import page
import requests
from build import get_data, get, add_names, remove_names, add_seq_names
import plotly.express as px

from components.player_compare import player_compare
from components.upcoming_gameweek import upcoming
from components.team_change_recommender import change_recommender
from components.gameweek_review import gameweek_review

from dash.exceptions import PreventUpdate
from flask_caching import Cache

df = pd.DataFrame()
bet_df, players_df, fixtures_df, gameweek, history, teams_df, all_history_df = get_data()
pag = page()

from components.navbar import Navbar

columns = ['minutes',
       'goals_scored', 'assists', 'clean_sheets', 'goals_conceded',
       'own_goals', 'penalties_saved', 'penalties_missed', 'yellow_cards',
       'red_cards', 'saves', 'bonus', 'bps', 'influence', 'creativity',
       'threat', 'ict_index', 'starts', 'expected_goals', 'expected_assists',
       'expected_goal_involvements', 'expected_goals_conceded', 'value',
       'transfers_balance', 'selected', 'transfers_in', 'transfers_out']
content = html.Div(id="page-content", children=[])
nav = Navbar()
def Homepage():
    layout = html.Div([
    dcc.Location(id="url"),
    nav,
    content
    ])
    return layout

app = dash.Dash(__name__,suppress_callback_exceptions=True, external_stylesheets = [dbc.themes.CYBORG])
app.title = 'FPL Data'
app._favicon = ("C:\\Users\\lleps\\Documents\\projects-2022\\fpl_dashboard\\icon\\favicon.ico")
app.layout = Homepage()
server = app.server
cache = Cache(app.server, config={'CACHE_TYPE': 'simple'})

@app.callback(
    [dash.dependencies.Output("scatter-plot", "figure")], 
    [dash.dependencies.Output("price-scatter-plot", "figure")],
    [dash.dependencies.Output("cumulative-scoring", "figure")],
    [dash.dependencies.Input("player-drop-down", "value")]
    )
def update_scatter_chart(player_name):

    ctx_msg = json.dumps({
        'states': ctx.states,
        'triggered': ctx.triggered,
        'inputs': ctx.inputs
    }, indent=2)

    map=dict(zip(players_df.web_name, players_df.id))
    team_map=dict(zip(players_df.team, players_df.team_name))
    pid = map[player_name]
    history = get("https://fantasy.premierleague.com/api/element-summary/"+str(pid)+"/")
    history = pd.DataFrame(history['history'])
    history.opponent_team = history.opponent_team.map(team_map)

    history.loc[history['total_points'] < 3, "color" ] = 0
    history.loc[history['total_points'] >= 3, "color" ] = 1
    history.loc[history['total_points'] > 6, "color" ] = 2
    history.loc[history['total_points'] > 9, "color" ] = 3
    player_score = history.loc[history.element==map[player_name]]
    player_score['value'] = player_score['value']/10
    highest = max(max(player_score.total_points), 17)
    lowest = min(min(player_score.total_points), 0)

    hover = {'color' : False, 'opponent_team' : True}

    fig = px.scatter(
        player_score, x="round", y="total_points", 
        color="color", text="total_points", color_continuous_scale=[(0, "red"), (0.5, "yellow"), (1, "green")], labels="total_points", hover_data=['opponent_team'])
    
    hover_data={'species':False}
    fig.update_yaxes(range=[lowest-3, highest+3])  
    fig.update(layout_showlegend=False)
    fig.update_traces(textposition='top center')
    fig.update(layout_coloraxis_showscale=False)
    fig.update_layout(hovermode='x unified')

    fig2 = px.scatter(
        player_score, x="round", y="value", 
        text="value", labels="value")
    fig2.update_traces(textposition='top center')

    player_score['cumulative_score'] = player_score.total_points.cumsum()
    fig3 = px.line(player_score, x="round", y="cumulative_score")
    return fig,fig2, fig3

@app.callback(
    [dash.dependencies.Output("player_image", "src")], 
    [dash.dependencies.Output("player_cost", "children")],
    [dash.dependencies.Output("player_points", "children")],
    [dash.dependencies.Output("player_ownership", "children")],
    [dash.dependencies.Output("player_rank", "children")],
    [dash.dependencies.Input("player-drop-down", "value")]
    )
def update_player(player_name):
    selected_player = players_df.loc[players_df.web_name==player_name]
    code = selected_player.code.iat[0]
    image_string = "https://resources.premierleague.com/premierleague/photos/players/110x140/p" + str(code) + ".png"
    ownership = str(selected_player.selected_by_percent.iat[0]) + "%"
    rank = str(selected_player.ict_index_rank.iat[0])

    return image_string, str(selected_player.now_cost.iat[0]/10), str(selected_player.total_points.iat[0]), ownership, rank

@app.callback(
    dash.dependencies.Output("history_table", "children"), 
    [dash.dependencies.Input("player-drop-down", "value")]
    )
def update_player_table(player_name):
    selected_player = players_df.loc[players_df.web_name==player_name]
    return selected_player.total_points.iat[0]

@app.callback(
    dash.dependencies.Output("player-drop-down", "options"),
    [dash.dependencies.Input("team-drop-down", "value")],
    [dash.dependencies.Input("position-drop-down", "value")]
)
def update_dropdown(team, position):
    positions_map = {"Goalkeeper" : 1,
    "Defender" : 2,
    "Midfielder" : 3,
    "Forward" : 4}
    position = positions_map[position]
    players_1 = players_df.loc[players_df.team_name==team]
    players = players_1.loc[players_1.element_type==position]
    return players.web_name.unique()

@app.callback(
    [dash.dependencies.Output("sequential-scoring", "figure")],
    [dash.dependencies.Output("player-price", "figure")],
    [dash.dependencies.Input("multi-player-drop-down", "value")],
    [dash.dependencies.Input("stat-drop-down", "value")],
    [dash.dependencies.Input("stat-drop-down-2", "value")],
)
def sequential_graphs(player_names, stat, lower_stat):
    if isinstance(player_names, str):
        player_names = [player_names]
    selected_players = pd.DataFrame()
    if ctx.triggered[0]['prop_id']=='.' :
        # store the selected players in the cache object
        cache.set('selected_seq_players', player_names)
        names_to_add = player_names
        selected_players = pd.DataFrame()
        
    elif ctx.triggered[0]['prop_id'] == "multi-player-drop-down.value" or ctx.triggered[0]['prop_id']=='stat-drop-down.value'or ctx.triggered[0]['prop_id']=='stat-drop-down-2.value':
        cached_names = cache.get('selected_seq_players')
        selected_players = pd.DataFrame(cache.get('selected_seq_playersdf'))
        names_to_add = list(set(player_names) - set(cached_names)) 
        
    map=dict(zip(players_df.web_name, players_df.id))
    team_map=dict(zip(players_df.team, players_df.team_name))

    selected_players = add_seq_names(selected_players, names_to_add, map, team_map)
    selected_players = remove_names(selected_players, player_names)

    cache.set('selected_seq_players', player_names)
    cache.set('selected_seq_playersdf', selected_players.to_dict('records'))
    fig = px.line(selected_players, x="round", y=stat, color='name')
    fig2 = px.line(selected_players, x="round", y=lower_stat, color='name')
    return fig, fig2

@app.callback(
    [dash.dependencies.Output("cumulative-scoring-2", "figure")],
    [dash.dependencies.Output("player-price-2", "figure")],
    [dash.dependencies.Input("multi-player-drop-down-2", "value")],
    [dash.dependencies.Input("cum-stat-drop-down", "value")],
    [dash.dependencies.Input("cum-stat-drop-down-2", "value")]
)
def cumulative_graphs(player_names, stat, lower_stat):

    if isinstance(player_names, str):
        player_names = [player_names]
    selected_players = pd.DataFrame()
    if ctx.triggered[0]['prop_id']=='.' :
        # store the selected players in the cache object
        cache.set('selected_players', player_names)
        names_to_add = player_names
        selected_players = pd.DataFrame()
    elif ctx.triggered[0]['prop_id'] == "multi-player-drop-down-2.value" or ctx.triggered[0]['prop_id']=='cum-stat-drop-down.value' or ctx.triggered[0]['prop_id']=='cum-stat-drop-down-2.value':
        cached_names = cache.get('selected_players')
        selected_players = pd.DataFrame(cache.get('selected_playersdf'))
        names_to_add = list(set(player_names) - set(cached_names)) 

    map=dict(zip(players_df.web_name, players_df.id))
    
    team_map=dict(zip(players_df.team, players_df.team_name))
    # if ctx.triggered[0]['prop_id']=='.' or ctx.triggered[0]['prop_id'] == "multi-player-drop-down-2.value" or ctx.triggered[0]['prop_id']=='cum-stat-drop-down.value':
    selected_players = add_names(selected_players, names_to_add,map, team_map)
    selected_players = remove_names(selected_players, player_names)
    cache.set('selected_players', player_names)
    cache.set('selected_playersdf', selected_players.to_dict('records'))
    

    fig = px.line(selected_players, x="round", y=stat, color='name')
    fig2 = px.line(selected_players, x="round", y=lower_stat, color='name')
    return fig, fig2

@app.callback(
    dash.dependencies.Output('team-table', 'data'),
    [dash.dependencies.Input('fpl-id', 'value')]
)
def update_table(FPL_ID):
    # Set the default value of the FPL ID input to 123456 if the input is blank
    if not FPL_ID:
        FPL_ID = 123456

    positions_map = {1 : "Goalkeeper",
    2 : "Defender" ,
    3 : "Midfielder",
    4 : "Forward" }

    # Get the user's team data from the Fantasy Premier League API
    response = requests.get(f'https://fantasy.premierleague.com/api/entry/{FPL_ID}/event/16/picks/')
    data = response.json()

    # Make a request to the bootstrap-static endpoint and pick out the player data for each player in the user's team
    player_ids = [p['element'] for p in data['picks']]
    player_data = players_df.loc[players_df['id'].isin(player_ids)]
    player_data = player_data.sort_values('element_type')
    player_data['element_type'] =  player_data['element_type'].map(positions_map)

    player_data = player_data.to_dict('records')
    # Create a list of dictionaries with the player data
    players = [{'name': p['first_name'] + ' ' + p['second_name'], 'position': p['element_type'], 'team': p['team_name'], 'cost': p['now_cost'] / 10} for p in player_data]

    # Return the player data for the table
    return players

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
    away_ids = [x['element'] for x in fixture['stats'][-1]['a']]
    home_ids = [x['element'] for x in fixture['stats'][-1]['h']]
    away_players = []
    home_players = []
    for p_history in all_history_df:
        if p_history['id'] in away_ids:
            try:
                game = next(x for x in p_history['history'] if x['fixture'] == fixture_id)
            except StopIteration:
                print(f"Unable to find fixture {fixture_id} in player history.")
            except Exception as e:
                print(f"An error occurred while searching for fixture {fixture_id}: {str(e)}")

            away_players.append(game)
        elif p_history['id'] in home_ids:
            try:
                game = next(x for x in p_history['history'] if x['fixture'] == fixture_id)
            except StopIteration:
                print(f"Unable to find fixture {fixture_id} in player history.")
            except Exception as e:
                print(f"An error occurred while searching for fixture {fixture_id}: {str(e)}")

            home_players.append(game)

    team_map=dict(zip(players_df.team, players_df.team_name))
    f_df = pd.DataFrame(fixtures)
    f_df['team_a_name'] = f_df['team_a'].map(team_map)
    f_df['team_h_name'] = f_df['team_h'].map(team_map)
    f_df['fixture_title'] = f_df['id'].astype(str) + ": " + f_df['team_h_name'] + " v " + f_df['team_a_name']
    
    away_df = pd.DataFrame(away_players)
    home_df = pd.DataFrame(home_players)
    away_df['id'] = away_df['element']
    home_df['id'] = home_df['element']
    away_players_df = pd.merge(players_df, away_df, how='inner', on=["id"] )
    home_players_df = pd.merge(players_df, home_df, how='inner', on=["id"] )
    away_players_df['photo'] = image_url_prefix + away_players_df['photo'].str.slice(start=0, stop=-3) + 'png'
    home_players_df['photo'] = image_url_prefix + home_players_df['photo'].str.slice(start=0, stop=-3) + 'png'

    away_players_df = away_players_df.sort_values('minutes_y', ascending=False)
    away_players_df_starters = away_players_df.iloc[:11]
    away_players_subs = away_players_df.iloc[11:]

    home_players_df = home_players_df.sort_values('minutes_y', ascending=False)
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
    return options, options[0]['value']

# @app.callback(
#     dash.dependencies.Output('player-chart', 'figure'),
#     [dash.dependencies.Input('element-type', 'value')]
# )
# def update_fig2(element_type):
#     graph2_df = 
#     graph2_df = graph2_df.loc[graph2_df.element_type == element_type]

#     fig2 = px.bar(graph2_df, x='web_name', y='ranking', color='element_type')

#     return fig2

@app.callback(
    dash.dependencies.Output("page-content", "children"),
    [dash.dependencies.Input("url", "pathname")]
)
def render_page_content(pathname):
    if pathname == "/":
        return [
                html.H1('ERROR PAGE',
                        style={'textAlign':'center'}),                
                ]
    elif pathname == "/player":
        return player_history(players_df, teams_df)

    elif pathname == "/player_compare":
        return player_compare(players_df, teams_df)
    
    elif pathname == "/upcoming_gameweek":
        return upcoming(bet_df, players_df, teams_df)
    
    elif pathname == "/transfer_recommender":
        return change_recommender()

    elif pathname == "/gameweek_review":
        return gameweek_review(players_df,teams_df, gameweek-1)
                
    # If the user tries to reach a different page, return a 404 message
    return dbc.Jumbotron(
        [
            html.H1("404: Not found", className="text-danger"),
            html.Hr(),
            html.P(f"The pathname {pathname} was not recognised..."),
        ]
    )


if __name__ == '__main__':
    app.run_server(debug=True)