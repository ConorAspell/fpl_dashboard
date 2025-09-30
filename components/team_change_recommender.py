from dash import html, dcc, Dash, dash_table
import dash_bootstrap_components as dbc
import requests
from dash.dependencies import Input, Output

def change_recommender():
    """Create the team display page with FPL ID input"""
    
    content = html.Div([
        # Header section
        html.H2('Your FPL Team', style={'textAlign': 'center', 'marginBottom': '20px'}),
        
        # Input section
        dbc.Card([
            dbc.CardBody([
                html.Div([
                    html.Label('Enter your FPL ID:', style={'fontWeight': 'bold', 'marginRight': '10px'}),
                    dcc.Input(
                        id='fpl-id-input', 
                        type='number', 
                        placeholder='e.g., 123456',
                        style={'width': '200px', 'marginRight': '10px'}
                    ),
                    dbc.Button(
                        'Load Team', 
                        id='load-team-button', 
                        color='primary',
                        n_clicks=0
                    ),
                ], style={'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center'})
            ])
        ], style={'marginBottom': '20px'}),
        
        # Loading indicator
        dcc.Loading(
            id="loading-team",
            type="default",
            children=[
                # Team info banner at the top
                html.Div(id='team-info-banner', style={'marginBottom': '20px'}),
                
                # Row with 3 sections: Rank graph, Team/Subs, Squad value graph
                dbc.Row([
                    # Left column - Rank History
                    dbc.Col(html.Div(id='position-history-graph'), width=4),
                    
                    # Middle column - Team and Substitutes
                    dbc.Col([
                        # Football pitch with players
                        html.Div(
                            id='team-pitch',
                            style={
                                'backgroundImage': 'url(https://upload.wikimedia.org/wikipedia/commons/4/45/Football_field.svg)',
                                'backgroundSize': 'contain',
                                'backgroundPosition': 'center',
                                'backgroundRepeat': 'no-repeat',
                                'minHeight': '800px',
                                'borderRadius': '10px',
                                'padding': '40px 20px',
                                'position': 'relative',
                                'marginBottom': '20px'
                            }
                        ),
                        # Substitutes section
                        html.Div(id='substitutes-section')
                    ], width=4),
                    
                    # Right column - Squad Value and Price Changes
                    dbc.Col([
                        html.Div(id='squad-value-section', style={'marginBottom': '20px'}),
                        html.Div(id='price-changes-section')
                    ], width=4)
                ])
            ]
        )
    ], style={'padding': '20px'})

    return content


