from dash import dcc, html
import dash_bootstrap_components as dbc
from dash import dash_table
import pandas as pd
import plotly.express as px
import json

from build import get

def upcoming(bet_df, players_df, teams_df):

    title ='Gameweek: ' + str(bet_df['game_week'].iat[0])
    
    # Create a dataframe for team odds visualization
    # Aggregate odds by team (home and away)
    home_df = bet_df[['home_team', 'away_team','home_chance']].copy()
    away_df = bet_df[['away_team', 'home_team','away_chance']].copy()

    home_df=home_df.rename(columns={'home_team' : 'team', 'away_team': 'opponent', 'home_chance' : 'chance'})
    away_df=away_df.rename(columns={'away_team' : 'team', 'home_team': 'opponent', 'away_chance' : 'chance'})
    
    # Combine home and away data
    odds_df = pd.concat([home_df, away_df], ignore_index=True)
    
    # Group by team and calculate average win chance for next gameweek
    team_odds = odds_df.groupby('team').agg({
        'chance': 'mean',
        'opponent': lambda x: ', '.join(x)
    }).reset_index()
    
    team_odds = team_odds.sort_values('chance', ascending=False)
    team_odds['chance_percent'] = team_odds['chance'].round(1)
    
    # Create bar chart showing odds for each team
    fig_odds = px.bar(
        team_odds, 
        x='team', 
        y='chance',
        title=f'{title} - Team Win Probabilities',
        labels={'chance': 'Win Probability (%)', 'team': 'Team'},
        color='chance',
        color_continuous_scale='RdYlGn',
        hover_data={'opponent': True, 'chance_percent': True}
    )
    
    fig_odds.update_layout(
        xaxis_tickangle=-45,
        height=600,
        showlegend=False
    )
    
    fig_odds.update_traces(
        hovertemplate='<b>%{x}</b><br>Win Probability: %{customdata[1]}%<br>Opponent: %{customdata[0]}<extra></extra>'
    )

    # Player rankings section - improved to combine team odds with player stats
    graph2_df = players_df.copy()
    
    # Convert numeric columns
    graph2_df['form'] = pd.to_numeric(graph2_df['form'], errors='coerce')
    graph2_df['creativity'] = pd.to_numeric(graph2_df['creativity'], errors='coerce')
    graph2_df['influence'] = pd.to_numeric(graph2_df['influence'], errors='coerce')
    graph2_df['threat'] = pd.to_numeric(graph2_df['threat'], errors='coerce')
    graph2_df['selected_by_percent'] = pd.to_numeric(graph2_df.get('selected_by_percent', 0), errors='coerce')
    
    # Filter only players likely to play
    graph2_df = graph2_df.loc[graph2_df['chance_of_playing_this_round'] != 0].copy()
    
    # Merge team win probabilities with players
    # First, create a mapping from teams_df to link team IDs with names from bet_df
    # We need to match the team names from bet_df with the team names from teams_df
    team_name_mapping = dict(zip(teams_df['name'], teams_df['name']))
    
    # Create a mapping of team to their win chance using odds_df (not aggregated)
    # For each team, use their actual win chance (not averaged)
    team_win_dict = {}
    
    # Process home games
    for _, row in bet_df.iterrows():
        home_team = row['home_team']
        away_team = row['away_team']
        
        # For home team, use home_chance
        if home_team not in team_win_dict:
            team_win_dict[home_team] = []
        team_win_dict[home_team].append(row['home_chance'])
        
        # For away team, use away_chance
        if away_team not in team_win_dict:
            team_win_dict[away_team] = []
        team_win_dict[away_team].append(row['away_chance'])
    
    # Average if a team has multiple games in the gameweek
    team_win_map = {team: sum(chances) / len(chances) for team, chances in team_win_dict.items()}
    
    # Map the win chances to players using team_name
    graph2_df['team_win_chance'] = graph2_df['team_name'].map(team_win_map).fillna(50)  # Default to 50% if not found
    
    # Improved ranking formula combining multiple factors
    # Normalize form to 0-100 scale (form is usually 0-10)
    graph2_df['form_normalized'] = graph2_df['form'] * 10
    
    # Calculate composite ranking score
    graph2_df['ranking'] = (
        graph2_df['form_normalized'] * 0.25 +           # 25% weight on form
        graph2_df['creativity'] * 0.20 +                # 20% weight on creativity
        graph2_df['threat'] * 0.20 +                    # 20% weight on threat
        graph2_df['influence'] * 0.15 +                 # 15% weight on influence
        graph2_df['team_win_chance'] * 0.20             # 20% weight on team's win probability
    )
    
    # Select relevant columns
    graph2_df = graph2_df[['web_name', 'element_type', 'ranking', 'form', 'creativity', 
                            'threat', 'team_name', 'team_win_chance']].copy()
    
    # Get top 50 players (so we have more for filtering)
    top_players_df = graph2_df.sort_values('ranking', ascending=False).head(50).reset_index(drop=True)
    
    # Round for display
    top_players_df['ranking'] = top_players_df['ranking'].round(1)
    
    # Create dropdown for position filtering
    drop = dcc.Dropdown(
        id='element-type-filter',
        options=[
            {'label': 'All Positions', 'value': 'All'},
            {'label': 'Goalkeepers', 'value': '1'},
            {'label': 'Defenders', 'value': '2'},
            {'label': 'Midfielders', 'value': '3'},
            {'label': 'Forwards', 'value': '4'}
        ],
        value='All',
        clearable=False
    )
    
    # Store the data for the callback
    players_store = dcc.Store(id='top-players-data', data=top_players_df.to_dict('records'))
    
    # Filter for initial display (top 20 of all)
    display_df = top_players_df.head(20)
    
    # Create improved bar chart with more information
    fig2 = px.bar(
        display_df, 
        x='web_name', 
        y='ranking',
        title=f'{title} - Top Players by Combined Score',
        labels={'ranking': 'Player Score', 'web_name': 'Player'},
        color='team_win_chance',
        color_continuous_scale='RdYlGn',
        hover_data={
            'form': ':.1f',
            'creativity': ':.1f', 
            'threat': ':.1f',
            'team_name': True,
            'team_win_chance': ':.1f'
        }
    )
    
    fig2.update_layout(
        xaxis_tickangle=-45,
        height=600
    )

    
    layout = html.Div(children=[
        dcc.Graph(
            id='team-odds-chart',
            figure=fig_odds
            ),
        html.Div([
            html.Label('Filter by Position:', style={'fontWeight': 'bold', 'marginRight': '10px'}),
            drop
        ], style={'margin': '20px 0'}),
        players_store,
        dcc.Graph(
            id='player-ranking-chart',
            figure=fig2   
            )
        ]
    )
    return layout