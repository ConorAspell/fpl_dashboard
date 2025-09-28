import dash
from dash import ctx
import pandas as pd
import plotly.express as px
from build import get, add_names, remove_names, add_seq_names
import json

def register_player_callbacks(app, players_df, cache):
    """Register all player-related callbacks"""
    
    @app.callback(
        [dash.dependencies.Output("scatter-plot", "figure")], 
        [dash.dependencies.Output("price-scatter-plot", "figure")],
        [dash.dependencies.Output("cumulative-scoring", "figure")],
        [dash.dependencies.Input("player-drop-down", "value")]
    )
    def update_scatter_chart(player_name):
        if not player_name:
            # Return empty figures if no player selected
            empty_fig = px.scatter(title="Select a player to view data")
            return empty_fig, empty_fig, empty_fig
        
        try:
            # Get player data more efficiently - use 'id' column instead of index
            player_map = dict(zip(players_df.web_name, players_df.id_x))
            team_map = dict(zip(players_df.team, players_df.team_name))
            
            pid = player_map[player_name]
            history = get("https://fantasy.premierleague.com/api/element-summary/"+str(pid)+"/")
            history = pd.DataFrame(history['history'])
            history.opponent_team = history.opponent_team.map(team_map)

            history.loc[history['total_points'] < 3, "color" ] = 0
            history.loc[history['total_points'] >= 3, "color" ] = 1
            history.loc[history['total_points'] > 6, "color" ] = 2
            history.loc[history['total_points'] > 9, "color" ] = 3
            player_score = history.loc[history.element==player_map[player_name]]
            player_score['value'] = player_score['value']/10
            highest = max(max(player_score.total_points), 17)
            lowest = min(min(player_score.total_points), 0)

            hover = {'color' : False, 'opponent_team' : True}

            fig = px.scatter(
                player_score, x="round", y="total_points", 
                color="color", text="total_points", color_continuous_scale=[(0, "red"), (0.5, "yellow"), (1, "green")], labels="total_points", hover_data=['opponent_team'])
            
            hover_data={'species':False}
            fig.update_yaxes(range=[lowest-3, highest+3])  
            fig.update(layout_showlegend=False)
            fig.update_traces(textposition='top center')
            fig.update(layout_coloraxis_showscale=False)
            fig.update_layout(hovermode='x unified')

            fig2 = px.scatter(
                player_score, x="round", y="value", 
                text="value", labels="value")
            fig2.update_traces(textposition='top center')

            player_score['cumulative_score'] = player_score.total_points.cumsum()
            fig3 = px.line(player_score, x="round", y="cumulative_score")
            return fig,fig2, fig3
        except Exception as e:
            print(f"Error in update_scatter_chart: {str(e)}")
            # Return empty figures with error message on error
            error_msg = f"Error loading data for {player_name}: {str(e)}"
            empty_fig = px.scatter(title=error_msg)
            return empty_fig, empty_fig, empty_fig

    @app.callback(
        [dash.dependencies.Output("player_image", "src")], 
        [dash.dependencies.Output("player_cost", "children")],
        [dash.dependencies.Output("player_points", "children")],
        [dash.dependencies.Output("player_ownership", "children")],
        [dash.dependencies.Output("player_rank", "children")],
        [dash.dependencies.Input("player-drop-down", "value")]
        )
    def update_player(player_name):
        if not player_name:
            return "", "", "", "", ""
            
        selected_player = players_df.loc[players_df.web_name==player_name]
        if selected_player.empty:
            return "", "", "", "", ""
            
        code = selected_player.photo.iat[0].split('.')[0]  # Remove file extension if present
        image_string = "https://resources.premierleague.com/premierleague/photos/players/110x140/p" + str(code) + ".png"
        ownership = str(selected_player.selected_by_percent.iat[0]) + "%"
        rank = str(selected_player.ict_index.iat[0])

        return image_string, str(selected_player.now_cost.iat[0]/10), str(selected_player.total_points.iat[0]), ownership, rank

    @app.callback(
        dash.dependencies.Output("history_table", "children"), 
        [dash.dependencies.Input("player-drop-down", "value")]
        )
    def update_player_table(player_name):
        if not player_name:
            return ""
            
        selected_player = players_df.loc[players_df.web_name==player_name]
        if selected_player.empty:
            return ""
            
        return selected_player.total_points.iat[0]

    @app.callback(
        dash.dependencies.Output("player-drop-down", "options"),
        [dash.dependencies.Input("team-drop-down", "value")],
        [dash.dependencies.Input("position-drop-down", "value")]
    )
    def update_dropdown(team, position):
        if not team or not position:
            return []
            
        positions_map = {"Goalkeeper" : 1,
        "Defender" : 2,
        "Midfielder" : 3,
        "Forward" : 4}
        position = positions_map[position]
        players_1 = players_df.loc[players_df.team_name==team]
        players = players_1.loc[players_1.element_type==position]
        return players.web_name.unique()