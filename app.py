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
bet_df, players_df, fixtures_df, gameweek, history, teams_df = get_data()
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

@app.callback(
    [dash.dependencies.Output("sequential-scoring", "figure")],
    [dash.dependencies.Output("player-price", "figure")],
    [dash.dependencies.Input("multi-player-drop-down", "value")],
    [dash.dependencies.Input("stat-drop-down", "value")],
)
def sequential_graphs(player_names, stat):
    selected_players = pd.DataFrame()
    if ctx.triggered[0]['prop_id']=='.' :
        # store the selected players in the cache object
        cache.set('selected_players', player_names)
        names_to_add = player_names
        
    elif ctx.triggered[0]['prop_id'] == "multi-player-drop-down.value" or ctx.triggered[0]['prop_id']=='stat-drop-down.value':
        cached_names = cache.get('selected_players')
        selected_players = pd.DataFrame(cache.get('selected_playersdf'))
        names_to_add = list(set(player_names) - set(cached_names)) 
        
    map=dict(zip(players_df.web_name, players_df.id))
    team_map=dict(zip(players_df.team, players_df.team_name))

    selected_players = add_seq_names(selected_players, names_to_add, map, team_map)
    selected_players = remove_names(selected_players, player_names)
    fig = px.line(selected_players, x="round", y=stat, color='name')
    fig2 = px.line(selected_players, x="round", y="value", color='name')
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
        return gameweek_review(players_df,teams_df, fixtures_df)
                
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