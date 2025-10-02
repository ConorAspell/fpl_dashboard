import json
import pandas as pd
import requests
import boto3 
import io
import json
import boto3
from datetime import datetime

def lambda_handler(event, context):
    
    bedrock = boto3.client(
                    service_name="bedrock",
                    region_name="eu-central-1"
            )
    bedrock_runtime = boto3.client(
                    service_name="bedrock-runtime",
                    region_name="eu-central-1"
            )
    
    foundation_models = bedrock.list_foundation_models()
    matching_model = next((model for model in foundation_models["modelSummaries"] if model.get("modelName") == "Llama 3.1 70B Instruct"), None)
    
    response_object = {}
    response_object['statusCode'] = 400
    response_object['headers'] = {}
    response_object['headers']['Content-Type'] = 'application/json'
    response_object['body'] = json.dumps("Please include a valid team id in your request")

    team_id = str(event["queryStringParameters"]['team_id'])

    # try: 
        
    team_id = str(event["queryStringParameters"]['team_id'])
    gameweek= 10
    players_df = get_df('fpl-bucket-2025', f"players-gameweek-{gameweek}.csv")
    fixture_df = get_df('fpl-bucket-2025', f"odds-gameweek-{gameweek}.csv")
    
    
    team = get('https://fantasy.premierleague.com/api/entry/'+str(team_id)+'/event/'+str(gameweek-1) +'/picks/')
    players = [x['element'] for x in team['picks']]
    
    print(len(players))

    original_team = players_df.loc[players_df.id.isin(players)]

    potential_players = players_df.loc[~players_df.id.isin(players)]
    my_team = original_team.copy()
    my_team, player_out = calc_out_weight(my_team)
    print("My Team", my_team.web_name.to_list())
    print(player_out.web_name)
    my_team = my_team.drop(player_out.index)
    print("My Team with player dropped", my_team.web_name.to_list())
    print(len(my_team))

    position = player_out.element_type.iat[0]
    out_cost = player_out.now_cost.iat[0]
    budget = out_cost
    dups_team = my_team.pivot_table(index=['team'], aggfunc='size')
    invalid_teams = dups_team.loc[dups_team==3].index.tolist()
    print("here3")

    potential_players=potential_players.loc[~potential_players.team.isin(invalid_teams)]
    potential_players=potential_players.loc[potential_players.element_type==position]
    potential_players = potential_players.loc[potential_players.now_cost<=budget]

    player_in = calc_in_weights(potential_players)
    my_team = pd.concat([my_team, player_in])

    goalkeepers=my_team.loc[my_team.element_type==1]
    my_team=my_team.drop(goalkeepers.index)
    print("my team: ", my_team.web_name)

    starting_goalkeeper = goalkeepers.sort_values(by='out_weight').iloc[:1]
    sub_goalkeeper = goalkeepers.sort_values(by='out_weight').iloc[1:]
    starting_outfielder =  my_team.sort_values(by='out_weight').iloc[:10]
    sub_outfielder =  my_team.sort_values(by='out_weight').iloc[10:]
    print(sub_outfielder)

    starting_team = pd.concat([starting_goalkeeper, starting_outfielder])
    sub_team = pd.concat([sub_goalkeeper, sub_outfielder])

    starting_team = starting_team.sort_values(by='element_type')
    sub_team = sub_team.sort_values(by='element_type')
    prompt = f"\nHuman: Analyse this Fantasy Premier League team, {original_team['web_name'].tolist()}. Recommend they change {player_out['web_name'].iat[0]} for {player_in['web_name'].iat[0]}. Recommend this starting team {starting_team['web_name'].tolist()}. Recommend these substitutions {sub_team['web_name'].tolist()}. Recommend this captain {starting_outfielder['web_name'].iat[0]}. Do it in the style of Moss from the IT Crowd\n\nAssistant:"
    prompt_json = json.dumps({"prompt": prompt, "max_tokens_to_sample": 1000, "top_p" : 0.8, "temperature" : 0.5})
    input = {
    "modelId": 'anthropic.claude-instant-v1',
    "contentType": "application/json",
    "accept": "*/*",
    "body": prompt_json
    }
    
    print(prompt)
    print(input)
    
    response = bedrock_runtime.invoke_model(body=input["body"], modelId= input["modelId"], accept=input["accept"], contentType=input["contentType"])
    response = json.loads(response["body"].read())
    print(response)
    body = {
    "recommended_change" : player_out.web_name.iat[0] + "->" + player_in.web_name.iat[0],
    "recommended_starting_team" : starting_team.web_name.to_list(),
    "captain" : starting_outfielder.web_name.iat[0],
    "substitutions" : sub_team.web_name.to_list(),
    "bedrock_text" : response["completion"],
    "upcoming_fixtures" : fixture_df.to_dict('records')
    }
    
    
    headers = {'Access-Control-Allow-Headers': 'Content-Type',
             "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Credentials": True, 
            'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'}
    response_object['headers'] = headers
    response_object['statusCode'] = 200
    response_object['body'] = json.dumps(body, ensure_ascii=False)
    
    return response_object

def calc_out_weight(players):
    players_copy = players.copy()

    # Modify the copy using .loc
    players_copy['out_weight'] = 100
    players_copy['out_weight'] -= players_copy['diff']
    players_copy['out_weight'] -= players_copy['form'].astype("float") * 10

    # Use .loc to modify specific rows
    players_copy.loc[players_copy['element_type'] == 1, 'out_weight'] -= 10
    players_copy.loc[players_copy['out_weight'] < 0, 'out_weight'] = 0

    # Sort and return the modified DataFrame
    return players_copy, players_copy.sort_values('out_weight', ascending=False).iloc[:1]

def calc_in_weights(players):
    players['in_weight'] = 1
    players['in_weight'] += players['diff']
    players['in_weight'] += players['form'].astype("float")*10
    players.loc[players['in_weight'] <0, 'in_weight'] =0

    return players.sort_values('in_weight', ascending=False).iloc[:1]
    

def calc_starters(players):
    return players.sort_values(by='out_weight', ascending=False)

def get_df(bucket, key):
    s3 = boto3.client('s3')
    obj = s3.get_object(Bucket=bucket, Key=key)
    df = pd.read_csv(io.BytesIO(obj['Body'].read()))
    return df

def get(url):
    response = requests.get(url)
    return json.loads(response.content)

def get_gameweek():
    players =  get('https://fantasy.premierleague.com/api/bootstrap-static/')
    fixtures_df = pd.DataFrame(players['events'])
    today = datetime.now().timestamp()
    fixtures_df = fixtures_df.loc[fixtures_df.deadline_time_epoch>today]
    gameweek =  fixtures_df.id.iat[0]
    return gameweek