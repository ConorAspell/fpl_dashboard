import dash
from dash import html, dcc
import dash_bootstrap_components as dbc
import pandas as pd
import requests
import plotly.graph_objs as go
from build import get

def register_team_callbacks(app, players_df, gameweek):
    """Register all team-related callbacks"""
    
    @app.callback(
        [dash.dependencies.Output('team-info-banner', 'children'),
         dash.dependencies.Output('team-pitch', 'children'),
         dash.dependencies.Output('substitutes-section', 'children'),
         dash.dependencies.Output('position-history-graph', 'children'),
         dash.dependencies.Output('squad-value-section', 'children'),
         dash.dependencies.Output('price-changes-section', 'children')],
        [dash.dependencies.Input('load-team-button', 'n_clicks')],
        [dash.dependencies.State('fpl-id-input', 'value')]
    )
    def load_team(n_clicks, fpl_id):
        """Load and display the user's FPL team"""
        if n_clicks == 0 or not fpl_id:
            return html.Div(), html.Div(), html.Div(), html.Div(), html.Div(), html.Div()
        
        positions_map = {
            1: "GK",
            2: "DEF",
            3: "MID",
            4: "FWD"
        }
        
        try:
            # Get the user's team data from the Fantasy Premier League API
            # Use the last completed gameweek (current gameweek - 1)
            last_gameweek = gameweek - 1
            response = requests.get(
                f'https://fantasy.premierleague.com/api/entry/{fpl_id}/event/{last_gameweek}/picks/',
                verify=False
            )
            data = response.json()
            
            # Check if we got valid data
            if 'picks' not in data:
                raise ValueError("No team data found for this gameweek")
            
            # Get team entry info
            entry_response = requests.get(
                f'https://fantasy.premierleague.com/api/entry/{fpl_id}/',
                verify=False
            )
            entry_data = entry_response.json()
            
            # Get player IDs and their data
            picks = data['picks']
            player_ids = [p['element'] for p in picks]
            
            # Filter players and remove duplicates (keep only unique player IDs)
            player_data = players_df.loc[players_df['id_x'].isin(player_ids)].copy()
            player_data = player_data.drop_duplicates(subset='id_x', keep='first')
            
            # Create a dictionary for quick lookup
            player_lookup = player_data.set_index('id_x').to_dict('index')
            
            # Organize players by position
            starting_11 = []
            substitutes = []
            
            for pick in picks:
                player_id = pick['element']
                if player_id not in player_lookup:
                    continue
                    
                player = player_lookup[player_id]
                player_info = {
                    'id': player_id,
                    'name': player['web_name'],
                    'position': positions_map.get(player['element_type'], 'Unknown'),
                    'team': player.get('team_name', ''),
                    'photo': player.get('photo', ''),
                    'is_captain': pick['is_captain'],
                    'is_vice_captain': pick['is_vice_captain'],
                    'multiplier': pick['multiplier'],
                    'event_points': player.get('event_points', 0),  # Last gameweek points
                    'now_cost': player.get('now_cost', 0) / 10  # Current price in millions
                }
                
                if pick['position'] <= 11:
                    starting_11.append(player_info)
                else:
                    substitutes.append(player_info)
            
            # Create pitch layout with players
            pitch_layout = create_pitch_layout(starting_11)
            
            # Create substitutes section
            subs_section = create_substitutes_section(substitutes)
            
            # Fetch gameweek history for position graph
            history_response = requests.get(
                f'https://fantasy.premierleague.com/api/entry/{fpl_id}/history/',
                verify=False
            )
            history_data = history_response.json()
            
            # Fetch transfer history to calculate cumulative points
            transfers_response = requests.get(
                f'https://fantasy.premierleague.com/api/entry/{fpl_id}/transfers/',
                verify=False
            )
            transfers_data = transfers_response.json()
            
            # Fetch all gameweek picks and live data to calculate player contributions
            all_gameweek_picks = []
            current_season = history_data.get('current', [])
            for gw_data in current_season:
                gw = gw_data['event']
                try:
                    # Get picks for this gameweek
                    picks_response = requests.get(
                        f'https://fantasy.premierleague.com/api/entry/{fpl_id}/event/{gw}/picks/',
                        verify=False
                    )
                    picks_data = picks_response.json()
                    
                    # Get live points data for this gameweek
                    live_response = requests.get(
                        f'https://fantasy.premierleague.com/api/event/{gw}/live/',
                        verify=False
                    )
                    live_data = live_response.json()
                    
                    # Create a lookup dict of player_id -> points
                    player_points_lookup = {}
                    for element in live_data.get('elements', []):
                        player_points_lookup[element['id']] = element['stats']['total_points']
                    
                    all_gameweek_picks.append({
                        'gameweek': gw,
                        'picks': picks_data.get('picks', []),
                        'player_points': player_points_lookup
                    })
                except:
                    continue
            
            # Create position history graph with top contributors
            position_graph = create_position_graph(history_data, transfers_data, players_df, all_gameweek_picks)
            
            # Create squad value graph
            squad_value = create_squad_value_graph(history_data)
            
            # Create price changes list
            price_changes = create_price_changes_list(transfers_data, players_df, starting_11, substitutes)
            
            # Create team info banner
            team_info_banner = create_team_info_banner(entry_data, history_data, last_gameweek)
            
            return team_info_banner, pitch_layout, subs_section, position_graph, squad_value, price_changes
            
        except Exception as e:
            error_msg = html.Div([
                dbc.Alert(
                    f"Error loading team: {str(e)}. Please check the FPL ID and try again.",
                    color="danger"
                )
            ])
            return error_msg, html.Div(), html.Div(), html.Div(), html.Div(), html.Div()


def create_team_info_banner(entry_data, history_data, gameweek):
    """Create a banner displaying team information"""
    try:
        # Get current gameweek data
        current_season = history_data.get('current', [])
        current_gw_data = None
        for gw in current_season:
            if gw['event'] == gameweek:
                current_gw_data = gw
                break
        
        # Extract team information
        manager_name = f"{entry_data.get('player_first_name', '')} {entry_data.get('player_last_name', '')}"
        team_name = entry_data.get('name', 'N/A')
        overall_rank = current_gw_data.get('overall_rank', 'N/A') if current_gw_data else entry_data.get('summary_overall_rank', 'N/A')
        overall_points = current_gw_data.get('total_points', 'N/A') if current_gw_data else entry_data.get('summary_overall_points', 'N/A')
        gameweek_points = current_gw_data.get('points', 'N/A') if current_gw_data else 'N/A'
        team_value = current_gw_data.get('value', 0) / 10 if current_gw_data else entry_data.get('last_deadline_value', 0) / 10
        bank = current_gw_data.get('bank', 0) / 10 if current_gw_data else entry_data.get('last_deadline_bank', 0) / 10
        
        # Format rank with commas
        if isinstance(overall_rank, int):
            overall_rank = f"{overall_rank:,}"
        
        return dbc.Card([
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        html.Div([
                            html.H4(team_name, style={'marginBottom': '5px', 'color': 'white', 'fontWeight': 'bold'}),
                            html.P(f"Manager: {manager_name}", style={'marginBottom': '0', 'color': 'rgba(255,255,255,0.9)'})
                        ])
                    ], width=3),
                    dbc.Col([
                        html.Div([
                            html.H6("Overall Rank", style={'marginBottom': '5px', 'color': 'rgba(255,255,255,0.8)', 'fontSize': '12px'}),
                            html.H4(overall_rank, style={'marginBottom': '0', 'color': 'white', 'fontWeight': 'bold'})
                        ])
                    ], width=2, style={'textAlign': 'center'}),
                    dbc.Col([
                        html.Div([
                            html.H6("Overall Points", style={'marginBottom': '5px', 'color': 'rgba(255,255,255,0.8)', 'fontSize': '12px'}),
                            html.H4(overall_points, style={'marginBottom': '0', 'color': 'white', 'fontWeight': 'bold'})
                        ])
                    ], width=2, style={'textAlign': 'center'}),
                    dbc.Col([
                        html.Div([
                            html.H6(f"GW{gameweek} Points", style={'marginBottom': '5px', 'color': 'rgba(255,255,255,0.8)', 'fontSize': '12px'}),
                            html.H4(gameweek_points, style={'marginBottom': '0', 'color': '#00ff87', 'fontWeight': 'bold'})
                        ])
                    ], width=2, style={'textAlign': 'center'}),
                    dbc.Col([
                        html.Div([
                            html.H6("Team Value", style={'marginBottom': '5px', 'color': 'rgba(255,255,255,0.8)', 'fontSize': '12px'}),
                            html.H4(f"£{team_value:.1f}m", style={'marginBottom': '0', 'color': 'white', 'fontWeight': 'bold'})
                        ])
                    ], width=2, style={'textAlign': 'center'}),
                    dbc.Col([
                        html.Div([
                            html.H6("In Bank", style={'marginBottom': '5px', 'color': 'rgba(255,255,255,0.8)', 'fontSize': '12px'}),
                            html.H4(f"£{bank:.1f}m", style={'marginBottom': '0', 'color': 'white', 'fontWeight': 'bold'})
                        ])
                    ], width=1, style={'textAlign': 'center'})
                ], align='center')
            ])
        ], style={'marginBottom': '20px', 'background': 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', 'border': 'none'})
        
    except Exception as e:
        print(f"Error creating team info banner: {e}")
        return html.Div()


def create_position_graph(history_data, transfers_data, players_df, all_gameweek_picks):
    """Create a line chart showing overall rank by gameweek and top contributors list"""
    try:
        current_season = history_data.get('current', [])
        
        if not current_season:
            return html.Div()
        
        # Extract gameweeks and ranks
        gameweeks = [gw['event'] for gw in current_season]
        ranks = [gw['overall_rank'] for gw in current_season]
        
        # Create the line chart
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=gameweeks,
            y=ranks,
            mode='lines+markers',
            name='Overall Rank',
            line=dict(color='#37003c', width=3),
            marker=dict(size=8)
        ))
        
        fig.update_layout(
            title='Rank by Gameweek',
            xaxis_title='Gameweek',
            yaxis_title='Overall Rank',
            yaxis=dict(autorange='reversed'),  # Lower rank is better, so reverse the axis
            hovermode='x unified',
            template='plotly_white',
            height=250,
            margin=dict(l=40, r=20, t=60, b=40)
        )
        
        # Calculate top contributors based on transfer history and gameweek picks
        top_contributors = calculate_top_contributors(transfers_data, players_df, all_gameweek_picks)
        
        # Create top contributors list
        contributors_list = html.Div([
            html.H6("Top Contributors", style={'marginTop': '15px', 'marginBottom': '10px', 'fontWeight': 'bold'}),
            html.Div([
                html.Div([
                    html.Span(f"{i+1}. ", style={'fontWeight': 'bold', 'marginRight': '5px', 'color': '#37003c'}),
                    html.Span(player['name'], style={'marginRight': '5px'}),
                    html.Span(f"{player['total_points']} pts", 
                             style={'color': '#00ff87', 'fontWeight': 'bold', 'fontSize': '12px', 'float': 'right'})
                ], style={'padding': '5px 0', 'borderBottom': '1px solid #eee'})
                for i, player in enumerate(top_contributors[:12])
            ])
        ], style={'marginTop': '10px'})
        
        return dbc.Card([
            dbc.CardHeader(html.H5("Rank History")),
            dbc.CardBody([
                dcc.Graph(figure=fig, config={'displayModeBar': False}),
                contributors_list
            ])
        ])
        
    except Exception as e:
        return html.Div()


def calculate_top_contributors(transfers_data, players_df, all_gameweek_picks):
    """Calculate cumulative points for each player since they were added to the team"""
    try:
        # Build transfer timeline: track when players were transferred in/out
        player_timeline = {}  # player_id: {'in_gw': X, 'out_gw': Y or None}
        
        # Get first gameweek from picks data
        first_gw = min([gw_data['gameweek'] for gw_data in all_gameweek_picks]) if all_gameweek_picks else 1
        
        # Process transfers to build timeline
        for transfer in transfers_data:
            element_in = transfer['element_in']
            element_out = transfer['element_out']
            event = transfer['event']
            
            # Player transferred in
            if element_in not in player_timeline:
                player_timeline[element_in] = {'in_gw': event, 'out_gw': None}
            else:
                # Player was transferred back in
                player_timeline[element_in]['in_gw'] = event
                player_timeline[element_in]['out_gw'] = None
            
            # Player transferred out
            if element_out in player_timeline:
                player_timeline[element_out]['out_gw'] = event
            else:
                # Player was in original squad and transferred out
                player_timeline[element_out] = {'in_gw': first_gw, 'out_gw': event}
        
        # Calculate cumulative points for each player
        player_points = {}  # player_id: cumulative_points
        
        for gw_data in all_gameweek_picks:
            gw = gw_data['gameweek']
            picks = gw_data['picks']
            player_points_lookup = gw_data.get('player_points', {})
            
            for pick in picks:
                player_id = pick['element']
                # Get actual points from live data
                points = player_points_lookup.get(player_id, 0)
                multiplier = pick.get('multiplier', 1)
                
                # Check if player was in squad for this gameweek
                if player_id in player_timeline:
                    timeline = player_timeline[player_id]
                    # Only count if gameweek is after transfer in and before transfer out (if any)
                    if gw >= timeline['in_gw'] and (timeline['out_gw'] is None or gw < timeline['out_gw']):
                        if player_id not in player_points:
                            player_points[player_id] = 0
                        player_points[player_id] += points * multiplier
                else:
                    # Player was in original squad and never transferred out
                    if player_id not in player_points:
                        player_points[player_id] = 0
                    player_points[player_id] += points * multiplier
        
        # Build list of player contributions
        player_contributions = []
        for player_id, total_points in player_points.items():
            # Get player info
            player_info = players_df[players_df['id_x'] == player_id]
            if player_info.empty:
                continue
            
            player_name = player_info.iloc[0]['web_name']
            
            player_contributions.append({
                'name': player_name,
                'total_points': total_points,
                'player_id': player_id
            })
        
        # Sort by total points descending
        player_contributions.sort(key=lambda x: x['total_points'], reverse=True)
        
        return player_contributions
        
    except Exception as e:
        print(f"Error calculating top contributors: {e}")
        return []


def create_squad_value_graph(history_data):
    """Create a line chart showing squad value by gameweek"""
    try:
        current_season = history_data.get('current', [])
        
        if not current_season:
            return html.Div()
        
        # Extract gameweeks and values
        gameweeks = [gw['event'] for gw in current_season]
        values = [gw['value'] / 10 for gw in current_season]  # Convert to millions
        
        # Create the line chart
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=gameweeks,
            y=values,
            mode='lines+markers',
            name='Squad Value',
            line=dict(color='#00ff87', width=3),
            marker=dict(size=8),
            fill='tozeroy',
            fillcolor='rgba(0, 255, 135, 0.1)'
        ))
        
        fig.update_layout(
            title='Squad Value by Gameweek',
            xaxis_title='Gameweek',
            yaxis_title='Squad Value (£m)',
            yaxis=dict(range=[95, 105]),  # Set minimum to 95 to make small changes visible
            hovermode='x unified',
            template='plotly_white',
            height=350,
            margin=dict(l=40, r=20, t=60, b=40)
        )
        
        return dbc.Card([
            dbc.CardHeader(html.H5("Squad Value History")),
            dbc.CardBody([
                dcc.Graph(figure=fig, config={'displayModeBar': False})
            ])
        ])
        
    except Exception as e:
        return html.Div()


def create_price_changes_list(transfers_data, players_df, starting_11, substitutes):
    """Create a list showing price changes for each player since they were added"""
    try:
        # Build transfer timeline to know when each player was added
        player_timeline = {}
        
        # Get first gameweek (assume GW1 for original squad)
        first_gw = 1
        
        # Process transfers to build timeline
        for transfer in transfers_data:
            element_in = transfer['element_in']
            element_out = transfer['element_out']
            event = transfer['event']
            element_in_cost = transfer['element_in_cost']  # Price when bought in (in 0.1m units)
            
            # Player transferred in
            if element_in not in player_timeline:
                player_timeline[element_in] = {
                    'in_gw': event, 
                    'in_cost': element_in_cost / 10  # Convert to millions
                }
            else:
                player_timeline[element_in]['in_gw'] = event
                player_timeline[element_in]['in_cost'] = element_in_cost / 10
        
        # Calculate price changes for current squad
        all_players = starting_11 + substitutes
        price_changes = []
        
        for player in all_players:
            player_id = player['id']
            current_price = player['now_cost']  # Already in millions
            
            # Get player info from players_df for initial price
            player_info = players_df[players_df['id_x'] == player_id]
            if player_info.empty:
                continue
            
            # Determine purchase price
            if player_id in player_timeline:
                purchase_price = player_timeline[player_id]['in_cost']
            else:
                # Player was in original squad, use their initial price (now_cost - total price change)
                # We can approximate with their current cost minus any known changes
                # For now, we'll get it from the full player data if available
                purchase_price = player_info.iloc[0].get('cost', current_price)
            
            price_change = current_price - purchase_price
            
            price_changes.append({
                'name': player['name'],
                'price_change': price_change,
                'current_price': current_price,
                'purchase_price': purchase_price
            })
        
        # Sort by price change (biggest risers first, then fallers)
        price_changes.sort(key=lambda x: x['price_change'], reverse=True)
        
        # Create price changes list
        changes_list = html.Div([
            html.H6("Price Changes", style={'marginTop': '15px', 'marginBottom': '10px', 'fontWeight': 'bold'}),
            html.Div([
                html.Div([
                    html.Span(f"{i+1}. ", style={'fontWeight': 'bold', 'marginRight': '5px', 'color': '#37003c'}),
                    html.Span(player['name'], style={'marginRight': '5px'}),
                    html.Span(
                        f"{'+' if player['price_change'] >= 0 else ''}{player['price_change']:.1f}m", 
                        style={
                            'color': '#00ff87' if player['price_change'] >= 0 else '#ff1744',
                            'fontWeight': 'bold',
                            'fontSize': '12px',
                            'float': 'right'
                        }
                    )
                ], style={'padding': '5px 0', 'borderBottom': '1px solid #eee'})
                for i, player in enumerate(price_changes[:12])
            ])
        ], style={'marginTop': '10px'})
        
        return dbc.Card([
            dbc.CardHeader(html.H5("Squad Value History")),
            dbc.CardBody([
                changes_list
            ])
        ])
        
    except Exception as e:
        print(f"Error calculating price changes: {e}")
        return html.Div()


def create_pitch_layout(players):
    """Create the football pitch layout with players"""
    # Group players by position
    gk = [p for p in players if p['position'] == 'GK']
    defenders = [p for p in players if p['position'] == 'DEF']
    midfielders = [p for p in players if p['position'] == 'MID']
    forwards = [p for p in players if p['position'] == 'FWD']
    
    # Image URL prefix (same as gameweek_callbacks)
    image_url_prefix = 'https://resources.premierleague.com/premierleague25/photos/players/110x140/'
    
    def create_player_card(player):
        """Create a player card with image"""
        # Construct photo URL same way as gameweek_callbacks
        # photo field is like 'p12345.jpg', we slice off '.jpg' and add '.png'
        photo_url = image_url_prefix + player['photo'][:-4] + '.png' if player.get('photo') else ''
        
        return html.Div([
            html.Div([
                html.Img(
                    src=photo_url,
                    style={
                        'width': '60px',
                        'height': '75px',
                        'borderRadius': '5px',
                        'border': '3px solid #00ff87' if player['is_captain'] else '2px solid white',
                        'backgroundColor': 'white'
                    }
                ),
                html.Div([
                    html.Span('(C)', style={'color': '#00ff87', 'fontWeight': 'bold'}) if player['is_captain'] else '',
                    html.Span('(V)', style={'color': '#00ffff', 'fontWeight': 'bold'}) if player['is_vice_captain'] else ''
                ], style={'fontSize': '10px', 'marginTop': '2px'}),
                html.Div(
                    player['name'],
                    style={
                        'color': 'white',
                        'fontSize': '12px',
                        'fontWeight': 'bold',
                        'textAlign': 'center',
                        'marginTop': '5px',
                        'textShadow': '2px 2px 4px rgba(0,0,0,0.8)',
                        'maxWidth': '80px',
                        'overflow': 'hidden',
                        'textOverflow': 'ellipsis',
                        'whiteSpace': 'nowrap'
                    }
                ),
                html.Div([
                    html.Div(f"{player['event_points']} pts", 
                            style={'color': 'white', 'fontSize': '10px', 'textShadow': '1px 1px 2px rgba(0,0,0,0.8)'}),
                    html.Div(f"£{player['now_cost']:.1f}m", 
                            style={'color': '#00ff87', 'fontSize': '10px', 'fontWeight': 'bold', 'textShadow': '1px 1px 2px rgba(0,0,0,0.8)'})
                ], style={'marginTop': '3px'})
            ], style={'textAlign': 'center'})
        ], style={'margin': '0 10px'})
    
    # Create rows for each position
    layout = html.Div([
        # Forwards
        html.Div([
            create_player_card(p) for p in forwards
        ], style={
            'display': 'flex',
            'justifyContent': 'center',
            'marginBottom': '60px'
        }),
        
        # Midfielders
        html.Div([
            create_player_card(p) for p in midfielders
        ], style={
            'display': 'flex',
            'justifyContent': 'center',
            'marginBottom': '60px'
        }),
        
        # Defenders
        html.Div([
            create_player_card(p) for p in defenders
        ], style={
            'display': 'flex',
            'justifyContent': 'center',
            'marginBottom': '60px'
        }),
        
        # Goalkeeper
        html.Div([
            create_player_card(p) for p in gk
        ], style={
            'display': 'flex',
            'justifyContent': 'center'
        })
    ], style={'padding': '40px 20px'})
    
    return layout


def create_substitutes_section(substitutes):
    """Create the substitutes section"""
    if not substitutes:
        return html.Div()
    
    # Image URL prefix (same as gameweek_callbacks)
    image_url_prefix = 'https://resources.premierleague.com/premierleague25/photos/players/110x140/'
    
    subs_cards = []
    for i, sub in enumerate(substitutes):
        # Construct photo URL same way as gameweek_callbacks
        photo_url = image_url_prefix + sub['photo'][:-4] + '.png' if sub.get('photo') else ''
        
        subs_cards.append(
            html.Div([
                html.Img(
                    src=photo_url,
                    style={
                        'width': '40px',
                        'height': '50px',
                        'borderRadius': '5px',
                        'marginRight': '10px'
                    }
                ),
                html.Div([
                    html.Strong(f"Sub {i+1}: "),
                    html.Span(sub['name']),
                    html.Br(),
                    html.Span(f"{sub['position']} - {sub['team']}", 
                             style={'fontSize': '12px', 'color': '#666'}),
                    html.Br(),
                    html.Span([
                        html.Span(f"{sub['event_points']} pts", 
                                 style={'fontSize': '11px', 'color': '#666', 'marginRight': '10px'}),
                        html.Span(f"£{sub['now_cost']:.1f}m", 
                                 style={'fontSize': '11px', 'color': '#00ff87', 'fontWeight': 'bold'})
                    ])
                ], style={'display': 'inline-block', 'verticalAlign': 'middle'})
            ], style={
                'display': 'flex',
                'alignItems': 'center',
                'padding': '10px',
                'marginBottom': '10px',
                'backgroundColor': '#f8f9fa',
                'borderRadius': '5px'
            })
        )
    
    return dbc.Card([
        dbc.CardHeader(html.H5("Substitutes")),
        dbc.CardBody(subs_cards)
    ])