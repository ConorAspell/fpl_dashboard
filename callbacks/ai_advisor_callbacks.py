import dash
from dash import Input, Output, State, callback, ctx
import requests
import json
import dash_bootstrap_components as dbc
from dash import html

def register_ai_advisor_callbacks(app, lambda_endpoint="https://uci9x83zqa.execute-api.eu-west-1.amazonaws.com/Prod/bedrock_test_2"):
    """Register callbacks for AI Advisor functionality"""
    
    @app.callback(
        [Output("analysis-results", "children"),
         Output("analysis-data", "data"),
         Output("loading-placeholder", "children")],
        [Input("analyze-button", "n_clicks")],
        [State("team-id-input", "value"),
         State("gameweek-input", "value"),
         State("persona-selection", "value")]
    )
    def handle_analysis_request(analyze_clicks, team_id, gameweek, persona):
        """Handle analysis request to Lambda function"""
        
        if not analyze_clicks:
            return html.Div(), None, html.Div()
        
        if not team_id:
            return dbc.Alert("Please enter a valid FPL Team ID", color="danger"), None, html.Div()
        
        try:
            # Prepare the request
            payload = {
                "team_id": int(team_id),
                "persona": persona or "pundit"
            }
            
            if gameweek:
                payload["gameweek"] = int(gameweek)
            
            # Make the API call to your Lambda function
            if lambda_endpoint:
                try:
                    response = requests.post(lambda_endpoint, json=payload, timeout=30)
                    if response.status_code == 200:
                        analysis_data = response.json()
                    else:
                        return dbc.Alert(f"API Error: {response.status_code} - {response.text}", color="danger"), None, html.Div()
                except requests.exceptions.RequestException as e:
                    return dbc.Alert(f"Connection Error: {str(e)}", color="danger"), None, html.Div()
            else:
                # Mock response for testing when no endpoint is provided
                analysis_data = create_mock_response(team_id, persona, gameweek)
            
            results_layout = create_results_layout(analysis_data)
            
            return results_layout, analysis_data, html.Div()
            
        except Exception as e:
            error_message = f"Error: {str(e)}"
            return dbc.Alert(error_message, color="danger"), None, html.Div()
    
    @app.callback(
        Output("analyze-button", "disabled"),
        Input("team-id-input", "value")
    )
    def toggle_analyze_button(team_id):
        """Enable/disable analyze button based on team ID input"""
        return not bool(team_id and str(team_id).strip())


def create_mock_response(team_id, persona, gameweek):
    """Create a mock response for testing purposes"""
    
    persona_responses = {
        'pundit': f"""Looking at your team for gameweek {gameweek or 'current'}, I can see some tactical considerations worth discussing.

**Formation Analysis:**
Your defensive line looks solid with premium options that should provide clean sheet returns. The midfield has good creativity with proven performers.

**Transfer Recommendation:**
The suggested transfer makes tactical sense - moving away from a player with limited minutes to someone with more consistent game time and better underlying stats.

**Captain Strategy:**
Your captain choice aligns with the template for good reason. They have the best fixtures and form combination this week.

**Key Insight:**
Consider the fixture rotation coming up - having bench players who can step in during busy periods will be crucial for maintaining team value.""",
        
        'analyst': f"""Data analysis for Team {team_id} - Gameweek {gameweek or 'Current'}:

**Performance Metrics:**
• xG overperformance indicators suggest some players may regress
• ICT index analysis shows strong creativity scores in midfield
• Clean sheet probability models favor your defensive picks

**Transfer Analysis:**
Statistical models indicate the recommended transfer improves expected points by 0.8 per gameweek based on:
- xG90: +0.12 improvement
- xA90: +0.05 improvement  
- Threat index: +15.2 points

**Captaincy Data:**
Form vs. fixture difficulty matrix suggests optimal captain choice. 12.7 recent form rating with 2.3 fixture difficulty rating.

**Model Prediction:**
Team expected to score 52.4 points this gameweek (±8.2 confidence interval).""",
        
        'veteran': f"""10+ year FPL veteran analysis for your team:

**Experience Says:**
Your squad has the hallmarks of a solid mid-season team. Good balance between premiums and enablers.

**Transfer Timing:**  
This transfer fits the template shift we're seeing. Don't be afraid to follow the crowd when the data supports it - differentials for the sake of it rarely pay off.

**Long-term Strategy:**
Keep one eye on the next 4-5 gameweeks. Price rises are coming for in-form players, so consider getting ahead of the curve.

**Chip Planning:**
With your current team structure, you're well-positioned for a Free Hit in the blank gameweeks. Don't waste transfers now on players you'll want to remove later.

**Veteran Tip:**
The bench boost chip works best with this defensive structure - plan 2-3 gameweeks ahead.""",
        
        'contrarian': f"""Contrarian analysis - Let's think differently about your team:

**Template Concerns:**
Your team is becoming too template-heavy. Everyone has these players - where's your edge?

**Differential Opportunities:**
Instead of the obvious transfer, consider: Lower-owned defenders from attacking teams, Midfield bargains from promoted sides, or Forwards in good form but overlooked.

**Captain Punt:**
The template captain is obvious - but what if they blank? Consider a differential captain from a player with easier fixtures but lower ownership.

**Risky Strategy:**
Take a -4 hit for a double transfer that brings in two differentials. If both deliver, you'll gain massive ground on rivals.

**Bold Prediction:**
The recommended transfer is what everyone will do. Be brave - sometimes the contrarian choice pays off spectacularly."""
    }
    
    return {
        "team_info": {
            "manager_name": f"Manager {team_id}",
            "team_name": "FPL Manager",
            "overall_rank": 450000 + (int(team_id) % 100000),
            "overall_points": 380 + (int(team_id) % 50),
            "gameweek_points": 45 + (int(team_id) % 20),
            "team_value": 100.0 + ((int(team_id) % 50) / 10)
        },
        "recommendations": {
            "transfer": {
                "out": {
                    "name": "Sample Player Out",
                    "team": "Example FC",
                    "cost": 4.5,
                    "form": 1.2
                },
                "in": {
                    "name": "Sample Player In", 
                    "team": "Better FC",
                    "cost": 4.5,
                    "form": 3.8
                }
            },
            "starting_11": [
                {"name": "Goalkeeper A", "position": "Goalkeeper", "team": "Team A"},
                {"name": "Defender A", "position": "Defender", "team": "Team B"},
                {"name": "Defender B", "position": "Defender", "team": "Team C"},
                {"name": "Defender C", "position": "Defender", "team": "Team D"},
                {"name": "Defender D", "position": "Defender", "team": "Team E"},
                {"name": "Midfielder A", "position": "Midfielder", "team": "Team F"},
                {"name": "Midfielder B", "position": "Midfielder", "team": "Team G"},
                {"name": "Midfielder C", "position": "Midfielder", "team": "Team H"},
                {"name": "Midfielder D", "position": "Midfielder", "team": "Team I"},
                {"name": "Forward A", "position": "Forward", "team": "Team J"},
                {"name": "Forward B", "position": "Forward", "team": "Team K"}
            ],
            "captain": {
                "name": "Star Player",
                "team": "Premium FC",
                "form": 8.5
            },
            "substitutes": [
                {"name": "Sub GK", "position": "Goalkeeper", "team": "Bench FC"},
                {"name": "Sub DEF", "position": "Defender", "team": "Bench FC"},
                {"name": "Sub MID", "position": "Midfielder", "team": "Bench FC"},
                {"name": "Sub FWD", "position": "Forward", "team": "Bench FC"}
            ]
        },
        "ai_analysis": persona_responses.get(persona, persona_responses['pundit']),
        "gameweek": gameweek or 7,
        "persona": persona or "pundit"
    }


def create_results_layout(analysis_data):
    """Create the results layout from analysis data"""
    if not analysis_data:
        return html.Div()
    
    team_info = analysis_data.get('team_info', {})
    recommendations = analysis_data.get('recommendations', {})
    ai_analysis = analysis_data.get('ai_analysis', '')
    persona = analysis_data.get('persona', 'unknown')
    gameweek = analysis_data.get('gameweek', 0)
    
    # Persona styling
    persona_styles = {
        'pundit': {'color': 'primary', 'icon': '📺'},
        'analyst': {'color': 'info', 'icon': '📊'},
        'veteran': {'color': 'success', 'icon': '🏆'},
        'contrarian': {'color': 'warning', 'icon': '🎲'}
    }
    
    style_info = persona_styles.get(persona, {'color': 'secondary', 'icon': '🤖'})
    
    return dbc.Container([
        # Team Overview Card
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H4([
                            "👤 Team Overview - Gameweek ", 
                            html.Span(str(gameweek), className="badge bg-primary ms-2")
                        ], className="mb-0")
                    ]),
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                html.H5(team_info.get('manager_name', 'Unknown'), className="text-primary"),
                                html.P(f"Team: {team_info.get('team_name', 'Unknown')}", className="mb-1"),
                            ], md=4),
                            dbc.Col([
                                html.P([
                                    html.Strong("Overall Rank: "),
                                    f"{team_info.get('overall_rank', 0):,}"
                                ], className="mb-1"),
                                html.P([
                                    html.Strong("Total Points: "),
                                    str(team_info.get('overall_points', 0))
                                ], className="mb-1"),
                            ], md=4),
                            dbc.Col([
                                html.P([
                                    html.Strong("Team Value: "),
                                    f"£{team_info.get('team_value', 0):.1f}m"
                                ], className="mb-1"),
                                html.P([
                                    html.Strong("GW Points: "),
                                    str(team_info.get('gameweek_points', 0))
                                ], className="mb-1"),
                            ], md=4)
                        ])
                    ])
                ])
            ])
        ], className="mb-4"),
        
        # AI Analysis Card
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H4([
                            style_info['icon'], " AI Analysis - ",
                            html.Span(persona.title(), className=f"badge bg-{style_info['color']} ms-2")
                        ], className="mb-0")
                    ]),
                    dbc.CardBody([
                        html.Div([
                            html.P(ai_analysis, style={'whiteSpace': 'pre-line', 'fontSize': '16px'})
                        ], className="analysis-text")
                    ])
                ])
            ])
        ], className="mb-4"),
        
        # Recommendations Cards
        dbc.Row([
            # Transfer Recommendation
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H5("🔄 Transfer Recommendation", className="mb-0")),
                    dbc.CardBody([
                        create_transfer_card(recommendations.get('transfer', {}))
                    ])
                ])
            ], md=6),
            
            # Captain Recommendation
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H5("👑 Captain Recommendation", className="mb-0")),
                    dbc.CardBody([
                        create_captain_card(recommendations.get('captain', {}))
                    ])
                ])
            ], md=6)
        ], className="mb-4"),
        
        # Starting XI and Subs
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H5("⚽ Recommended Starting XI", className="mb-0")),
                    dbc.CardBody([
                        create_team_list(recommendations.get('starting_11', []))
                    ])
                ])
            ], md=8),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H5("🔄 Substitutes", className="mb-0")),
                    dbc.CardBody([
                        create_team_list(recommendations.get('substitutes', []))
                    ])
                ])
            ], md=4)
        ], className="mb-4"),
        
        # New Analysis Button
        dbc.Row([
            dbc.Col([
                dbc.Button(
                    "🔄 Analyze Another Team",
                    id="new-analysis-button",
                    color="outline-primary",
                    className="w-100"
                )
            ], md=4, className="mx-auto")
        ])
        
    ], fluid=True)


def create_transfer_card(transfer_data):
    """Create transfer recommendation display"""
    if not transfer_data:
        return html.P("No transfer data available")
    
    out_player = transfer_data.get('out', {})
    in_player = transfer_data.get('in', {})
    
    return html.Div([
        # Out Player
        dbc.Row([
            dbc.Col([
                html.Div([
                    html.H6("❌ Transfer Out", className="text-danger mb-2"),
                    html.P([
                        html.Strong(out_player.get('name', 'Unknown')),
                        html.Br(),
                        html.Small(f"{out_player.get('team', '')} - £{out_player.get('cost', 0):.1f}m", className="text-muted"),
                        html.Br(),
                        html.Small(f"Form: {out_player.get('form', 0)}", className="text-muted")
                    ])
                ], className="text-center")
            ], md=5),
            
            dbc.Col([
                html.Div("➡️", className="text-center", style={'fontSize': '24px', 'marginTop': '20px'})
            ], md=2),
            
            dbc.Col([
                html.Div([
                    html.H6("✅ Transfer In", className="text-success mb-2"),
                    html.P([
                        html.Strong(in_player.get('name', 'Unknown')),
                        html.Br(),
                        html.Small(f"{in_player.get('team', '')} - £{in_player.get('cost', 0):.1f}m", className="text-muted"),
                        html.Br(),
                        html.Small(f"Form: {in_player.get('form', 0)}", className="text-muted")
                    ])
                ], className="text-center")
            ], md=5)
        ])
    ])


def create_captain_card(captain_data):
    """Create captain recommendation display"""
    if not captain_data:
        return html.P("No captain data available")
    
    return html.Div([
        html.Div([
            html.H5(captain_data.get('name', 'Unknown'), className="text-primary mb-1"),
            html.P([
                html.Strong("Team: "), captain_data.get('team', 'Unknown'),
                html.Br(),
                html.Strong("Form: "), f"{captain_data.get('form', 0)}"
            ])
        ], className="text-center")
    ])


def create_team_list(players):
    """Create a list of players"""
    if not players:
        return html.P("No player data available")
    
    # Group by position
    positions = {}
    for player in players:
        pos = player.get('position', 'Unknown')
        if pos not in positions:
            positions[pos] = []
        positions[pos].append(player)
    
    # Position order
    pos_order = ['Goalkeeper', 'Defender', 'Midfielder', 'Forward']
    
    team_list = []
    for pos in pos_order:
        if pos in positions:
            team_list.append(html.H6(f"{pos}s", className="mt-2 mb-1 text-muted"))
            for player in positions[pos]:
                team_list.append(
                    html.P([
                        html.Strong(player.get('name', 'Unknown')),
                        html.Br(),
                        html.Small(player.get('team', ''), className="text-muted")
                    ], className="mb-2")
                )
    
    return html.Div(team_list)
