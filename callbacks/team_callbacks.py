import dash
from dash import html
import dash_bootstrap_components as dbc
import pandas as pd
import requests
from build import get

def register_team_callbacks(app, players_df):
    """Register all team-related callbacks"""
    
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

        try:
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
        except Exception as e:
            print(f"Error fetching team data: {str(e)}")
            return []