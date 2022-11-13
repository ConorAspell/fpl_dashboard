from turtle import title
import dash
from dash import dcc
from dash import html
import numpy as np
import pandas as pd
import dash_bootstrap_components as dbc
from components.player_history import player_history
from page import page
import requests
from build import get_data, get
import plotly.express as px

from components.player_compare import player_compare

df = pd.DataFrame()
players_df, fixtures_df, gameweek, history, teams_df = get_data()
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



@app.callback(
    [dash.dependencies.Output("scatter-plot", "figure")], 
    [dash.dependencies.Output("price-scatter-plot", "figure")],
    [dash.dependencies.Output("cumulative-scoring", "figure")],
    [dash.dependencies.Input("player-drop-down", "value")]
    )
def update_scatter_chart(player_name):

    
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
    if isinstance(player_names, str):
        player_names = [player_names]
    map=dict(zip(players_df.web_name, players_df.id))
    team_map=dict(zip(players_df.team, players_df.team_name))
    selected_players = pd.DataFrame()
    for name in player_names:
        id = map[name]
        history = get("https://fantasy.premierleague.com/api/element-summary/"+str(id)+"/")
        history = pd.DataFrame(history['history'])
        history.opponent_team = history.opponent_team.map(team_map)
        history['name'] = name
        selected_players = selected_players.append(history)

    fig = px.line(selected_players, x="round", y=stat, color='name')
    fig2 = px.line(selected_players, x="round", y="value", color='name')
    return fig, fig2

@app.callback(
    [dash.dependencies.Output("cumulative-scoring-2", "figure")],
    [dash.dependencies.Output("player-price-2", "figure")],
    [dash.dependencies.Input("multi-player-drop-down-2", "value")],
    [dash.dependencies.Input("cum-stat-drop-down", "value")],
)
def cumulative_graphs(player_names, stat):
    if isinstance(player_names, str):
        player_names = [player_names]
    map=dict(zip(players_df.web_name, players_df.id))
    team_map=dict(zip(players_df.team, players_df.team_name))
    selected_players = pd.DataFrame()
    for name in player_names:
        id = map[name]
        history = get("https://fantasy.premierleague.com/api/element-summary/"+str(id)+"/")
        history = pd.DataFrame(history['history'])
        history.opponent_team = history.opponent_team.map(team_map)
        history['name'] = name
        history['cum_sum'] = history['total_points'].cumsum()
        for column in columns:
            col_name = "cum_" + column
            history[col_name] = history[column].cumsum()
        selected_players = selected_players.append(history)

    fig = px.line(selected_players, x="round", y=stat, color='name')
    fig2 = px.line(selected_players, x="round", y="value", color='name')
    return fig, fig2

@app.callback(
    dash.dependencies.Output("page-content", "children"),
    [dash.dependencies.Input("url", "pathname")]
)
def render_page_content(pathname):
    if pathname == "/":
        return [
                html.H1('Kindergarten in Iran',
                        style={'textAlign':'center'}),
                
                ]
    elif pathname == "/player":
        return player_history(players_df, teams_df)

    elif pathname == "/player_compare":
        return player_compare(players_df, teams_df)

    # elif pathname == "/sign-ups":
    #     return [
    #             html.H1('SIGN UPS',
    #                     style={'textAlign':'center'}),
                
    #             ]
    # elif pathname == "/donate":
    #     return [
    #             html.H1('DONATE',
    #                     style={'textAlign':'center'}),
                
    #             ]
    # elif pathname == "/tournament":
    #     return [
    #             html.H1('TOURNAMENT',
    #                     style={'textAlign':'center'}),]
                
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