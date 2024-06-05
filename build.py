import requests
import pandas  as pd
import json
from datetime import datetime
import boto3
import io


columns = ['chance_of_playing_next_round', 'chance_of_playing_this_round',
 'element_type', 'ep_next',
       'ep_this',  'first_name', 'form', 'id', 'in_dreamteam',
        'now_cost', 'points_per_game',
       'second_name', 'selected_by_percent', 
        'team', 'team_code', 'total_points', 'transfers_in',
        'transfers_out',
       'value_form', 'value_season', 'web_name',      
        'influence', 'creativity', 'threat',
       'ict_index', 'position']

cum_columns = ['minutes',
       'goals_scored', 'assists', 'clean_sheets', 'goals_conceded',
       'own_goals', 'penalties_saved', 'penalties_missed', 'yellow_cards',
       'red_cards', 'saves', 'bonus', 'bps', 'influence', 'creativity',
       'threat', 'ict_index', 'starts', 'expected_goals', 'expected_assists',
       'expected_goal_involvements', 'expected_goals_conceded', 'value',
       'transfers_balance', 'selected', 'transfers_in', 'transfers_out']

s3_client = boto3.client('s3')

def get_data():
    today = datetime.now().timestamp()
    
    players =  get('https://fantasy.premierleague.com/api/bootstrap-static/')
    teams_df = pd.DataFrame(players['teams'])
    fixtures_df = pd.DataFrame(players['events'])
    fixtures_df = fixtures_df.loc[fixtures_df.deadline_time_epoch>today]
    gameweek =  fixtures_df.iloc[0].id

    key = "odds-gameweek-" +str(gameweek) +".csv"
    bucket_name = "fpl-bucket-2023"
    bet_df = get_df(bucket_name, key)

    key = "players-gameweek-" +str(gameweek) +".csv"
    players_df = get_df(bucket_name, key)


    bet_df.reset_index(inplace=True)
    bet_df['game_week'] = gameweek

    history = get('https://fantasy.premierleague.com/api/element-summary/318/')
    history_df = pd.DataFrame(history['history'])

    all_history_df = load_player_data_from_s3('fpl-bucket-2022', 'player_data.json')

    return bet_df, players_df, fixtures_df, gameweek, history_df,teams_df, all_history_df


def load_player_data_from_s3(bucket_name, file_name):
    """
    Loads the player data from the specified S3 bucket and file name and returns it as a list of dictionaries.
    """
    s3 = boto3.resource('s3')
    obj = s3.Object(bucket_name, file_name)
    response = obj.get()

    player_data = json.loads(response['Body'].read().decode('utf-8'))

    return player_data

def get_df(bucket, key):
    s3 = boto3.client('s3')
    obj = s3.get_object(Bucket=bucket, Key=key)
    df = pd.read_csv(io.BytesIO(obj['Body'].read()))
    return df

def get(url):
    response = requests.get(url)
    return json.loads(response.content)

def add_names(selected_players, names_to_add, map, team_map):
    for name in names_to_add:
        id = map[name]
        history = get("https://fantasy.premierleague.com/api/element-summary/"+str(id)+"/")
        history = pd.DataFrame(history['history'])
        history.opponent_team = history.opponent_team.map(team_map)
        history['name'] = name
        history['cum_sum'] = history['total_points'].cumsum()
        for column in cum_columns:
            if 'expected' in column:
                history[column] = pd.to_numeric(history[column])
            col_name = "cum_" + column
            history[col_name] = history[column].cumsum()
        selected_players = selected_players.append(history)
    return selected_players

def add_seq_names(selected_players, names_to_add, map, team_map):
    for name in names_to_add:
        id = map[name]
        history = get("https://fantasy.premierleague.com/api/element-summary/"+str(id)+"/")
        history = pd.DataFrame(history['history'])
        history.opponent_team = history.opponent_team.map(team_map)
        history['name'] = name
        selected_players = selected_players.append(history)
    return selected_players


def remove_names(selected_players, selected_names):
    selected_players = selected_players.loc[selected_players.name.isin(selected_names)]
    return selected_players