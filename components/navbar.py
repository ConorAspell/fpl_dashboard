import dash_bootstrap_components as dbc
def Navbar():
    navbar = dbc.Nav(
           [
                dbc.NavLink("Player History", href="/player"),
                dbc.NavLink("Player Compare", href="/player_compare"),
                dbc.NavLink("Your Team", href="/your-team"),
                dbc.NavLink("Transfer Recommender", href="/transfer"),
                dbc.NavLink("Donate", href="/donate"),
              
                    ],
          vertical=False,
          justified=True,
          pills=True,
          style={'color' : 'blue'}
        )
    return navbar