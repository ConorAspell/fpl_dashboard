from dash import dcc, html
import dash_bootstrap_components as dbc
from dash import dash_table
import pandas as pd
import plotly.express as px

from build import get

def upcoming(bet_df, players_df, teams_df):

    title ='Gameweek: ' + str(bet_df['game_week'].iat[0])
    home_df = bet_df[['home_team', 'away_team','home_chance']]
    away_df = bet_df[['away_team', 'home_team','away_chance']]

    home_df=home_df.rename(columns={'home_team' : 'team', 'away_team': 'opponent', 'home_chance' : 'chance'})
    away_df=away_df.rename(columns={'away_team' : 'team', 'home_team': 'opponent', 'away_chance' : 'chance'})
    
    graph_df = home_df.append(away_df)
    
    graph_df = graph_df.sort_values('chance', ascending=False)
    

    graph2_df= players_df.sort_values('form', ascending=False)
    graph2_df['form'] = pd.to_numeric(graph2_df.form)
    graph2_df['creativity'] = pd.to_numeric(graph2_df.creativity)
    graph2_df['influence'] = pd.to_numeric(graph2_df.influence)
    graph2_df['threat'] = pd.to_numeric(graph2_df.threat)
    graph2_df= graph2_df.loc[graph2_df.chance_of_playing_this_round!=0]

    graph2_df['ranking'] = graph2_df['creativity'] + graph2_df['influence'] + graph2_df['threat'] - (graph2_df['diff']*20) - (100-graph2_df['chance_of_playing_this_round']) + (graph2_df['form']*20)
    graph2_df=graph2_df[['web_name','element_type', 'ranking']]
    graph2_df=graph2_df.groupby(['web_name', 'element_type']).sum()
    graph2_df = graph2_df.sort_values('ranking', ascending=False).iloc[:20].reset_index()
    fig = px.bar(graph_df, x='team', y='chance',
             color='opponent',title=title )
    fig2 = px.bar(graph2_df, x='web_name', y='ranking',
            title=title )

    
    layout = html.Div(children=[
        dcc.Graph(
            id='bar-chart',
            figure=fig
            ),
        dcc.Graph(
            id='player-chart',
            figure=fig2
            )
        ]
    )
    return layout