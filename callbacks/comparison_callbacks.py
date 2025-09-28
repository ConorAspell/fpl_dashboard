import dash
from dash import ctx
import pandas as pd
import plotly.express as px
from build import get, add_names, remove_names, add_seq_names

def register_comparison_callbacks(app, players_df, cache):
    """Register all player comparison callbacks"""
    
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
        selected_players = add_names(selected_players, names_to_add,map, team_map)
        selected_players = remove_names(selected_players, player_names)
        cache.set('selected_players', player_names)
        cache.set('selected_playersdf', selected_players.to_dict('records'))
        

        fig = px.line(selected_players, x="round", y=stat, color='name')
        fig2 = px.line(selected_players, x="round", y=lower_stat, color='name')
        return fig, fig2