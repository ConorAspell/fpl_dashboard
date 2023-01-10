from dash import dcc, html
import dash_bootstrap_components as dbc
from dash import dash_table, get_asset_url
import pandas as pd
import plotly.express as px
import plotly.graph_objs as go

from build import get
import os
from PIL import Image

image_path = os.path.join('assets', 'football_pitch.jpg')
pil_image = Image.open(image_path)
new_size = (pil_image.width * 3, pil_image.height * 3)
pil_image = pil_image.resize(new_size)
position_points = {
    'Goalkeeper': {
        'goal': 6,
        'assist': 3,
        'clean_sheet': 4,
    },
    'Defender': {
        'goal': 5,
        'assist': 3,
        'clean_sheet': 4,
    },
    'Midfielder': {
        'goal': 4,
        'assist': 3,
        'clean_sheet': 1,
    },
    'Forward': {
        'goal': 4,
        'assist': 3,
        'clean_sheet': 0,
    }
}



def gameweek_review(players_df, teams_df, gameweek):
    teams=dict(zip(teams_df.id, teams_df.name))
    image_url_prefix = 'https://resources.premierleague.com/premierleague/photos/players/110x140/p'
    fixtures = get('https://fantasy.premierleague.com/api/fixtures/?event='+str(gameweek))
    fixture_id=fixtures[0]['id']
    fixture = next(fixture for fixture in fixtures if fixture['id'] == fixture_id)
    away_players = []
    home_players = []
    for player in fixture['stats'][-1]['a']:
        history = get("https://fantasy.premierleague.com/api/element-summary/"+str(player['element'])+"/")
        his = next(f for f in history['history'] if f['fixture'] == fixture_id)
        away_players.append(his)
    for player in fixture['stats'][-1]['h']:
        history = get("https://fantasy.premierleague.com/api/element-summary/"+str(player['element'])+"/")
        his = next(f for f in history['history'] if f['fixture'] == fixture_id)
        home_players.append(his)

    team_map=dict(zip(players_df.team, players_df.team_name))
    f_df = pd.DataFrame(fixtures)
    f_df['team_a_name'] = f_df['team_a'].map(team_map)
    f_df['team_h_name'] = f_df['team_h'].map(team_map)
    f_df['fixture_title'] = f_df['id'].astype(str) + ": " + f_df['team_h_name'] + " v " + f_df['team_a_name']
    ids = [d['fixture_title'] for d in f_df.to_dict('records')]
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

    home_goalkeeper = home_players_df_starters.loc[home_players_df_starters.element_type==1]
    home_defender = home_players_df_starters.loc[home_players_df_starters.element_type==2]
    home_midfielder = home_players_df_starters.loc[home_players_df_starters.element_type==3]
    home_forward = home_players_df_starters.loc[home_players_df_starters.element_type==4]

    
    height = '50%'
    width = "50%"
    layout = html.Div(
        children=[html.Div([
                dbc.Row([
                    dbc.Col(dcc.Dropdown(list(range(1, gameweek+1)),value=gameweek,id='gameweek-drop-down',placeholder="Select Gameweek")),
                    dbc.Col(dcc.Dropdown(ids,value=ids[0], id='game-drop-down', placeholder="Select Fixture"))
                ])
            ]),
            html.Div(style= {  'verticalAlign':'middle',
                        'textAlign': 'center',
                        'background': 'url(https://upload.wikimedia.org/wikipedia/commons/thumb/9/91/Football_pitch_v2.svg/2560px-Football_pitch_v2.svg.png) no-repeat center center fixed',
                        'background-size': 'cover'}, 
                children=[
                    dbc.Row([
                    dbc.Col(width=6, children=[
                    dbc.Row([                    
                            dbc.Col( width=3,
                                children=[
                                    html.Div(
                                    html.Img(src='{}'.format(field), style={'border-radius' : '500%', 'height' : height, 'width' : width})
                                    ) for field in home_goalkeeper.photo.to_list()
                                ], align='center' ),
                            dbc.Col(width=3,
                                children=[
                                    html.Div(
                                    html.Img(src='{}'.format(field), style={'border-radius' : '500%','height' : height, 'width' : width})
                                    ) for field in home_defender.photo.to_list()
                                ], align='center'),
                            dbc.Col(width=3,
                                children=[
                                    html.Div(
                                    html.Img(src='{}'.format(field), style={'border-radius' : '500%','height' : height, 'width' : width})
                                    ) for field in home_midfielder.photo.to_list()
                                ], align='center'),
                                dbc.Col(width=3,
                                children=[
                                    html.Div(
                                    html.Img(src='{}'.format(field), style={'border-radius' : '500%','height' : height, 'width' : width})
                                    ) for field in home_forward.photo.to_list()
                                ], align='center') 

                    ], justify="start"),
                    ]),
                    dbc.Col(width=6, children=[
                    dbc.Row([                    
                            dbc.Col( width=3,
                                children=[
                                    html.Div(
                                    html.Img(src='{}'.format(field), style={'border-radius' : '500%', 'height' : height, 'width' : width})
                                    ) for field in away_forward.photo.to_list()
                                ], align='center' ),
                            dbc.Col(width=3,
                                children=[
                                    html.Div(
                                    html.Img(src='{}'.format(field), style={'border-radius' : '500%','height' : height, 'width' : width})
                                    ) for field in away_midfielder.photo.to_list()
                                ], align='center'),
                            dbc.Col(width=3,
                                children=[
                                    html.Div(
                                    html.Img(src='{}'.format(field), style={'border-radius' : '500%','height' : height, 'width' : width})
                                    ) for field in away_defender.photo.to_list()
                                ], align='center'),
                                dbc.Col(width=3,
                                children=[
                                    html.Div(
                                    html.Img(src='{}'.format(field), style={'border-radius' : '500%','height' : height, 'width' : width})
                                    ) for field in away_goalkeeper.photo.to_list()
                                ], align='center') 

                    ], justify="end"),
                    ])
                    ])
                    

                    # ]),
                    # dbc.Col(width=3, children= [
                    #     dbc.Row(children=[
                    #         dbc.Row(html.Img(src='{}'.format(field), style={'height' :'75%','width' : '75%'}),style={'height': height})
                    #     ]) for field in home_midfielder.photo.to_list()
                    # ]),
                    # dbc.Col(width=3, children= [
                    #     dbc.Row(children=[
                    #         dbc.Row(html.Img(src='{}'.format(field), style={'height' :'75%','width' : '75%'}),style={'height': height})
                    #     ]) for field in home_forward.photo.to_list()
                    # ]),
                    # dbc.Col(width=3, children= [
                    #     dbc.Row(children=[
                    #         dbc.Row(html.Img(src='{}'.format(field), style={'height' :'75%','width' : '75%'}),style={'height': height})
                    #     ]) for field in away_forward.photo.to_list()
                    # ]),
                    # dbc.Col(width=3, children= [
                    #     dbc.Row(children=[
                    #         dbc.Row(html.Img(src='{}'.format(field), style={'height' :'75%','width' : '75%'}),style={'height': height})
                    #     ]) for field in away_midfielder.photo.to_list()
                    # ]),
                    # dbc.Col(width=3, children= [
                    #     dbc.Row(children=[
                    #         dbc.Row(html.Img(src='{}'.format(field), style={'height' :'75%','width' : '75%'}),style={'height': height})
                    #     ]) for field in away_defender.photo.to_list()
                    # ]),
                    # dbc.Col(width=3, children= [
                    #     dbc.Row(children=[
                    #         dbc.Row(html.Img(src='{}'.format(field), style={'height' :'75%','width' : '75%'}),style={'height': height})
                    #     ]) for field in away_goalkeeper.photo.to_list()
               
                    
            ])    
        ]
    )
    return layout
