import dash
from dash import html
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
from components.player_history import player_history
from components.player_compare import player_compare
from components.upcoming_gameweek import upcoming
from components.team_change_recommender import change_recommender
from components.gameweek_review import gameweek_review
from components.ai_advisor import create_ai_advisor_layout

def register_navigation_callbacks(app, players_df, teams_df, bet_df, gameweek):
    """Register navigation and page routing callbacks"""
    
    @app.callback(
        dash.dependencies.Output("page-content", "children"),
        [dash.dependencies.Input("url", "pathname")]
    )
    def render_page_content(pathname):
        if pathname == "/":
            return [
                    html.H1('ERROR PAGE',
                            style={'textAlign':'center'}),                
                    ]
        elif pathname == "/player":
            return player_history(players_df, teams_df)

        elif pathname == "/player_compare":
            return player_compare(players_df, teams_df)
        
        elif pathname == "/upcoming_gameweek":
            return upcoming(bet_df, players_df, teams_df)
        
        elif pathname == "/transfer_recommender":
            return change_recommender()

        elif pathname == "/gameweek_review":
            return gameweek_review(players_df, teams_df, gameweek-1)
        
        elif pathname == "/ai_advisor":
            return create_ai_advisor_layout()
                    
        # If the user tries to reach a different page, return a 404 message
        return dbc.Jumbotron(
            [
                html.H1("404: Not found", className="text-danger"),
                html.Hr(),
                html.P(f"The pathname {pathname} was not recognised..."),
            ]
        )
    
    @app.callback(
        dash.dependencies.Output('player-ranking-chart', 'figure'),
        [dash.dependencies.Input('element-type-filter', 'value'),
         dash.dependencies.Input('top-players-data', 'data')]
    )
    def update_player_chart(selected_position, players_data):
        """Update player ranking chart based on selected position"""
        if not players_data:
            return {}
        
        # Convert stored data back to DataFrame
        df = pd.DataFrame(players_data)
        
        # Filter by position if not 'All'
        if selected_position != 'All':
            df = df[df['element_type'] == int(selected_position)]
        
        # Get top 20 players
        df = df.head(20)
        
        if df.empty:
            return {}
        
        # Create the bar chart
        fig = px.bar(
            df, 
            x='web_name', 
            y='ranking',
            title=f'Top Players by Combined Score',
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
        
        fig.update_layout(
            xaxis_tickangle=-45,
            height=600
        )
        
        return fig