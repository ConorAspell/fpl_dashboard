import dash
from dash import html
import dash_bootstrap_components as dbc
from components.player_history import player_history
from components.player_compare import player_compare
from components.upcoming_gameweek import upcoming
from components.team_change_recommender import change_recommender
from components.gameweek_review import gameweek_review

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
                    
        # If the user tries to reach a different page, return a 404 message
        return dbc.Jumbotron(
            [
                html.H1("404: Not found", className="text-danger"),
                html.Hr(),
                html.P(f"The pathname {pathname} was not recognised..."),
            ]
        )