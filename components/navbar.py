import dash_bootstrap_components as dbc
def Navbar():
    navbar = dbc.Nav(
           [
                dbc.NavLink("Player History", href="/player"),
                dbc.NavLink("Player Compare", href="/player_compare"),
                dbc.NavLink("Upcoming Gameweek", href="/upcoming_gameweek"),
                dbc.NavLink("Gameweek Review", href="/gameweek_review"),
                dbc.NavLink("My Team", href="/transfer_recommender"),
                dbc.NavLink("Donate", href="/donate"),
              
                    ],
          vertical=False,
          justified=True,
          pills=True,
          style={'color' : 'blue'}
        )
    return navbar