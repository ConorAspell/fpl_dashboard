from dash import dcc, html
import dash_bootstrap_components as dbc
from dash import dash_table
import pandas as pd

from build import get 

tabs_styles = {
    'height': '44px',
    'backgroundColor' : 'black'
}
tab_style = {
    'borderBottom': '1px solid #d6d6d6',
    'padding': '6px',
    'fontWeight': 'bold',
    'backgroundColor' : 'black',
    'color': 'white',
}

tab_selected_style = {
    'borderTop': '1px solid #d6d6d6',
    'borderBottom': '1px solid #d6d6d6',
    'backgroundColor': '#119DFF',
    'color': 'white',
    'padding': '6px'
}

def player_history(players_df, teams_df):
    positions_map = {1 : "Goalkeeper",
    2 : "Defender",
    3 : "Midfielder",
    4 : "Forward"}
    style_sheet_1 = {"color": "black", "text-align" : "center", "font-family" : "Roboto"}
    style_sheet_2 = {"color": "gray", "text-align" : "center", "font-family" : "Roboto"}
    
    teams_map=dict(zip(teams_df.id, teams_df.name))
    players = players_df.web_name.unique()
    teams = players_df.team_name.unique()
    positions = players_df.element_type.unique()
    positions = [positions_map[x] for x in positions]
    

    selected_player = players_df.loc[players_df.web_name == "Haaland"]
    code = selected_player.code.iat[0]
    image_string = "https://resources.premierleague.com/premierleague/photos/players/110x140/p" + str(code) + ".png"
    id = selected_player.id.iat[0]
    history = get("https://fantasy.premierleague.com/api/element-summary/"+str(id)+"/")
    history_df = pd.DataFrame(history['history'])
    history_df.opponent_team = history_df.opponent_team.map(teams_map)
    history_df['fixture'] = history_df['opponent_team'] + " v " + selected_player['team_name'].iat[0]
    image = html.A([
            html.Img(
                src=image_string,
                id='player_image'), 
        ])
    content = html.Div(children=[
        dbc.Row([
            dbc.Col(
                dbc.Card(
                    dbc.CardBody([
                        html.P("Ownership: ",style=style_sheet_2),
                        html.P(str(selected_player.selected_by_percent.iat[0]) + "%", id="player_ownership",style=style_sheet_1),
                        html.P("ICT Rank: ",style=style_sheet_2),
                        html.P(str(selected_player.ict_index_rank.iat[0]), id="player_rank",style=style_sheet_1)], 
                    style={"background-color" : "white"}
                ), style={"width": "18rem", "border-radius" : "25px", "padding": "20px"}
            ), width={"size": 3, "offset" : 1}
            ),
            dbc.Col(image, width={"size": 2, "offset" : 1}),
            dbc.Col(
                dbc.Card(
                    dbc.CardBody([
                        html.P("Cost: ",style=style_sheet_2),
                        html.P(str(selected_player.now_cost.iat[0]/10), id="player_cost",style=style_sheet_1),
                        html.P("Total Points:\n ",style=style_sheet_2),
                        html.P(str(selected_player.total_points.iat[0]), id="player_points",style=style_sheet_1)], 
                    style={"background-color" : "white"}
                ), style={"width": "18rem", "border-radius" : "25px", "padding": "20px"}
            ), width={"size": 3, "offset" : 1}
        )
    ]),
        dbc.Row([
            dbc.Col(dcc.Dropdown(positions, 'Forward', id='position-drop-down')),
            dbc.Col(dcc.Dropdown(teams, 'Man City', id='team-drop-down')),
            dbc.Col(dcc.Dropdown(players, 'Haaland', id='player-drop-down')),
    ]),

    dcc.Tabs([
        dcc.Tab(label='Scoring History', style=tab_style, selected_style=tab_selected_style,
            children=[
                dcc.Graph(id="scatter-plot"),
    
                html.Div([
                    dash_table.DataTable(
                    id='history-table',
                    columns=[{"name": i, "id": i} for i in history_df.columns if i in ['round', 'fixture','value', 'total_points']],
                    data=history_df.to_dict('records'),
                    editable=True,
        )])

            ]),
        dcc.Tab(label='Price History', style=tab_style, selected_style=tab_selected_style,
            children=[
                dcc.Graph(id="price-scatter-plot")
            ]),
        dcc.Tab(label='Cumulative Scoring', style=tab_style, selected_style=tab_selected_style,
            children=[
                dcc.Graph(id="cumulative-scoring")
            ]),
            
            ]),

        ]),
    return content