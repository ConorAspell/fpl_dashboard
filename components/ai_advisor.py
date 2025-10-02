import dash
from dash import dcc, html, Input, Output, State, callback, ctx
import dash_bootstrap_components as dbc
import requests
import json
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

def create_ai_advisor_layout():
    """Create the AI Advisor page layout"""
    return dbc.Container([
        # Header
        dbc.Row([
            dbc.Col([
                html.Div([
                    html.H1("🤖 FPL AI Advisor", className="text-center mb-3"),
                    html.P("Get personalized team analysis and recommendations from our AI experts", 
                           className="text-center text-muted mb-4")
                ])
            ])
        ]),
        
        # Input Form
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H4("📝 Team Analysis Request", className="mb-0")),
                    dbc.CardBody([
                        # Team ID Input
                        dbc.Row([
                            dbc.Col([
                                dbc.Label("FPL Team ID:", html_for="team-id-input"),
                                dbc.InputGroup([
                                    dbc.Input(
                                        id="team-id-input",
                                        type="number",
                                        placeholder="Enter your FPL team ID (e.g., 1192105)",
                                        value="",
                                        style={"fontSize": "16px"}
                                    ),
                                    dbc.Button("ℹ️", id="team-id-info", color="outline-info", size="sm")
                                ]),
                                dbc.Tooltip(
                                    "Find your team ID in your FPL URL: fantasy.premierleague.com/entry/YOUR_TEAM_ID/",
                                    target="team-id-info"
                                )
                            ], md=6),
                            
                            # Gameweek Input
                            dbc.Col([
                                dbc.Label("Gameweek (optional):", html_for="gameweek-input"),
                                dbc.Input(
                                    id="gameweek-input",
                                    type="number",
                                    placeholder="Leave blank for current GW",
                                    min=1,
                                    max=38,
                                    style={"fontSize": "16px"}
                                )
                            ], md=6)
                        ], className="mb-3"),
                        
                        # Persona Selection
                        dbc.Row([
                            dbc.Col([
                                dbc.Label("Choose Your AI Advisor:", className="mb-2"),
                                dbc.RadioItems(
                                    id="persona-selection",
                                    options=[
                                        {
                                            "label": html.Div([
                                                html.Strong("📺 Pundit"), 
                                                html.Br(),
                                                html.Small("Tactical expert like Match of the Day analysis", className="text-muted")
                                            ]), 
                                            "value": "pundit"
                                        },
                                        {
                                            "label": html.Div([
                                                html.Strong("📊 Analyst"), 
                                                html.Br(),
                                                html.Small("Data-driven analysis with xG, ICT, and advanced stats", className="text-muted")
                                            ]), 
                                            "value": "analyst"
                                        },
                                        {
                                            "label": html.Div([
                                                html.Strong("🏆 Veteran"), 
                                                html.Br(),
                                                html.Small("Experienced manager with 10+ years of FPL wisdom", className="text-muted")
                                            ]), 
                                            "value": "veteran"
                                        },
                                        {
                                            "label": html.Div([
                                                html.Strong("🎲 Contrarian"), 
                                                html.Br(),
                                                html.Small("Bold differential picks and risky strategies", className="text-muted")
                                            ]), 
                                            "value": "contrarian"
                                        }
                                    ],
                                    value="pundit",
                                    inline=False,
                                    className="mb-3"
                                )
                            ])
                        ]),
                        
                        # Submit Button
                        dbc.Row([
                            dbc.Col([
                                dbc.Button(
                                    "🚀 Get AI Analysis",
                                    id="analyze-button",
                                    color="primary",
                                    size="lg",
                                    className="w-100",
                                    disabled=False
                                )
                            ])
                        ])
                    ])
                ])
            ], md=8, className="mx-auto")
        ], className="mb-4"),
        
        # Loading Spinner
        dbc.Row([
            dbc.Col([
                dcc.Loading(
                    id="loading-analysis",
                    type="default",
                    children=html.Div(id="loading-placeholder")
                )
            ])
        ]),
        
        # Results Section
        html.Div(id="analysis-results", className="mt-4"),
        
        # Store for data
        dcc.Store(id="analysis-data")
        
    ], fluid=True)


# Helper functions are now in callbacks/ai_advisor_callbacks.py


# Callbacks are handled in callbacks/ai_advisor_callbacks.py
