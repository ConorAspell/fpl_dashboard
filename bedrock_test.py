import json
import pandas as pd
import requests
import boto3 
import io
from datetime import datetime

def lambda_handler(event, context):
    """
    Enhanced Lambda handler for FPL AI advisor
    
    Expected event structure:
    {
        "body": {
            "team_id": "123456",
            "persona": "pundit|analyst|veteran|contrarian",
            "gameweek": 10 (optional, defaults to current)
        }
    }
    """
    
    # Initialize AWS clients
    bedrock_runtime = boto3.client(
        service_name="bedrock-runtime",
        region_name="eu-central-1"
    )
    
    # Default response
    response_object = {
        'statusCode': 400,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Credentials': True,
            'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
        },
        'body': json.dumps("Invalid request")
    }
    
    try:
        # Parse input - handle different event structures
        body = None
        
        # Check if this is an API Gateway event with body
        if 'body' in event and event['body'] is not None:
            # API Gateway passes body as a string
            if isinstance(event['body'], str):
                body = json.loads(event['body'])
            else:
                body = event['body']
        # Check for query string parameters (GET request)
        elif 'queryStringParameters' in event and event['queryStringParameters'] is not None:
            body = event['queryStringParameters']
        # Direct invocation or test event (body is at root level)
        else:
            # For testing, the parameters might be at the root level
            body = event
        
        # Extract parameters with defaults
        team_id = body.get('team_id') if body else None
        persona = body.get('persona', 'pundit') if body else 'pundit'
        gameweek = body.get('gameweek') if body else None
        
        if not team_id:
            response_object['body'] = json.dumps({
                'error': 'team_id is required'
            })
            return response_object
        
        # Get current gameweek if not provided
        if not gameweek:
            gameweek = get_gameweek()
        else:
            gameweek = int(gameweek)
        
        print(f"Processing team {team_id} for gameweek {gameweek} with persona {persona}")
        
        # Load data from S3
        players_df = get_df('fpl-bucket-2025', f"players-gameweek-{gameweek}.csv")
        fixture_df = get_df('fpl-bucket-2025', f"odds-gameweek-{gameweek}.csv")
        

        
        # Get team data
        team_data = get('https://fantasy.premierleague.com/api/entry/' + str(team_id) + '/')
        team_picks = get('https://fantasy.premierleague.com/api/entry/' + str(team_id) + '/event/' + str(gameweek-1) + '/picks/')
        
        # Get player IDs
        players = [x['element'] for x in team_picks['picks']]
        captain_id = next((x['element'] for x in team_picks['picks'] if x['is_captain']), None)
        
        # Check if 'id' column exists, otherwise use common alternatives
        id_column = None
        for col_name in ['id', 'id_x', 'element', 'player_id', 'element_id']:
            if col_name in players_df.columns:
                id_column = col_name
                break
        
        if id_column is None:
            raise ValueError(f"No suitable ID column found in players_df. Available columns: {players_df.columns.tolist()}")
        
        # Get original team
        original_team = players_df.loc[players_df[id_column].isin(players)].copy()
        potential_players = players_df.loc[~players_df[id_column].isin(players)].copy()
        
        # Check if we have enough players
        if original_team.empty:
            raise ValueError(f"No players found for team {team_id} in gameweek {gameweek}")
        
        # Calculate transfer recommendation
        my_team = original_team.copy()
        my_team, player_out = calc_out_weight(my_team)
        my_team = my_team.drop(player_out.index)
        
        # Find replacement
        position = player_out.element_type.iat[0]
        out_cost = player_out.now_cost.iat[0]
        budget = out_cost
        
        # Check team limits (max 3 from same team)
        dups_team = my_team.pivot_table(index=['team'], aggfunc='size')
        invalid_teams = dups_team.loc[dups_team==3].index.tolist()
        
        # Filter potential replacements
        potential_players = potential_players.loc[~potential_players.team.isin(invalid_teams)]
        potential_players = potential_players.loc[potential_players.element_type==position]
        potential_players = potential_players.loc[potential_players.now_cost<=budget]
        
        player_in = calc_in_weights(potential_players)
        my_team = pd.concat([my_team, player_in])
        
        # Split into starting 11 and subs
        goalkeepers = my_team.loc[my_team.element_type==1]
        my_team_outfield = my_team.drop(goalkeepers.index)
        
        starting_goalkeeper = goalkeepers.sort_values(by='out_weight').iloc[:1]
        sub_goalkeeper = goalkeepers.sort_values(by='out_weight').iloc[1:]
        starting_outfielder = my_team_outfield.sort_values(by='out_weight').iloc[:10]
        sub_outfielder = my_team_outfield.sort_values(by='out_weight').iloc[10:]
        
        starting_team = pd.concat([starting_goalkeeper, starting_outfielder])
        sub_team = pd.concat([sub_goalkeeper, sub_outfielder])
        
        starting_team = starting_team.sort_values(by='element_type')
        sub_team = sub_team.sort_values(by='element_type')
        
        # Recommended captain
        recommended_captain = starting_outfielder.iloc[0]
        
        # Build enhanced context for AI
        team_context = build_team_context(
            team_data, 
            original_team, 
            fixture_df, 
            gameweek,
            captain_id,
            players_df
        )
        
        # Get persona-specific system prompt
        system_prompt = get_persona_prompt(persona)
        
        # Build comprehensive user prompt
        user_prompt = build_analysis_prompt(
            team_context,
            original_team,
            player_out,
            player_in,
            starting_team,
            sub_team,
            recommended_captain,
            fixture_df
        )
        
        # Call Bedrock with Claude 3.5 Sonnet
        ai_response = invoke_bedrock(
            bedrock_runtime,
            system_prompt,
            user_prompt
        )
        
        # Build response - ensure all values are JSON serializable
        response_body = {
            "team_info": {
                "manager_name": str(team_data['name']),
                "team_name": str(team_data['player_first_name']) + " " + str(team_data['player_last_name']),
                "overall_rank": int(team_data['summary_overall_rank']),
                "overall_points": int(team_data['summary_overall_points']),
                "gameweek_points": int(team_data.get('summary_event_points', 0)),
                "team_value": float(team_data['last_deadline_value']) / 10
            },
            "recommendations": {
                "transfer": {
                    "out": {
                        "name": str(player_out.web_name.iat[0]),
                        "team": str(player_out.team_name.iat[0]) if 'team_name' in player_out else '',
                        "cost": float(player_out.now_cost.iat[0]) / 10,
                        "form": float(player_out.form.iat[0])
                    },
                    "in": {
                        "name": str(player_in.web_name.iat[0]),
                        "team": str(player_in.team_name.iat[0]) if 'team_name' in player_in else '',
                        "cost": float(player_in.now_cost.iat[0]) / 10,
                        "form": float(player_in.form.iat[0])
                    }
                },
                "starting_11": [
                    {
                        "name": str(row.web_name),
                        "position": get_position_name(int(row.element_type)),
                        "team": str(row.team_name) if 'team_name' in row else ''
                    } for _, row in starting_team.iterrows()
                ],
                "captain": {
                    "name": str(recommended_captain.web_name),
                    "team": str(recommended_captain.team_name) if 'team_name' in recommended_captain else '',
                    "form": float(recommended_captain.form)
                },
                "substitutes": [
                    {
                        "name": str(row.web_name),
                        "position": get_position_name(int(row.element_type))
                    } for _, row in sub_team.iterrows()
                ]
            },
            "ai_analysis": str(ai_response),
            "upcoming_fixtures": convert_to_json_serializable(fixture_df.head(10).to_dict('records')) if not fixture_df.empty else [],
            "gameweek": int(gameweek),
            "persona": str(persona)
        }
        
        response_object['statusCode'] = 200
        response_object['body'] = json.dumps(response_body, ensure_ascii=False)
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        
        response_object['statusCode'] = 500
        response_object['body'] = json.dumps({
            'error': str(e),
            'message': 'Internal server error'
        })
    
    return response_object


def get_persona_prompt(persona):
    """Return system prompt based on persona"""
    personas = {
        'pundit': """You are a tactical football expert and FPL pundit analyzing teams like a TV analyst.
Focus on formations, team tactics, fixture difficulty, and recent match performances.
Be conversational and engaging, like you're presenting on Match of the Day.
Keep responses under 250 words.""",
        
        'analyst': """You are a data-driven FPL analyst who relies on statistics and metrics.
Use xG, xA, ICT index, creativity, threat, and influence scores in your analysis.
Reference specific numbers and compare actual vs expected performance.
Be precise and analytical. Keep responses under 250 words.""",
        
        'veteran': """You are an experienced FPL manager with 10+ years of playing.
Share practical strategies, chip timing, template vs differential picks.
Consider price changes and long-term team value optimization.
Be practical and share insider tips. Keep responses under 250 words.""",
        
        'contrarian': """You are a bold FPL manager who loves differential picks and risky strategies.
Suggest unconventional picks that others overlook.
Challenge the template and popular ownership.
Be creative with high-risk, high-reward ideas. Keep responses under 250 words."""
    }
    
    return personas.get(persona, personas['pundit'])


def build_team_context(team_data, original_team, fixture_df, gameweek, captain_id, players_df):
    """Build comprehensive context about the team"""
    
    # Get captain name
    captain_name = "Unknown"
    if captain_id:
        # Use the same ID column that was determined earlier
        id_column = None
        for col_name in ['id', 'id_x', 'element', 'player_id', 'element_id']:
            if col_name in original_team.columns:
                id_column = col_name
                break
        
        if id_column:
            captain_row = original_team[original_team[id_column] == captain_id]
            if not captain_row.empty:
                captain_name = captain_row.web_name.iat[0]
    
    # Squad composition
    positions = {1: 'GK', 2: 'DEF', 3: 'MID', 4: 'FWD'}
    squad_by_position = {}
    for pos_id, pos_name in positions.items():
        pos_players = original_team[original_team.element_type == pos_id]
        squad_by_position[pos_name] = pos_players.web_name.tolist()
    
    # Top performers
    top_performers = original_team.nlargest(3, 'total_points')[['web_name', 'total_points', 'form']]
    
    # Players in form
    in_form = original_team.nlargest(3, 'form')[['web_name', 'form', 'total_points']]
    
    return {
        'manager_name': team_data['name'],
        'overall_rank': team_data['summary_overall_rank'],
        'overall_points': team_data['summary_overall_points'],
        'gameweek': gameweek,
        'captain': captain_name,
        'squad': squad_by_position,
        'top_performers': top_performers.to_dict('records'),
        'in_form_players': in_form.to_dict('records'),
        'team_value': team_data['last_deadline_value'] / 10
    }


def build_analysis_prompt(team_context, original_team, player_out, player_in, 
                         starting_team, sub_team, recommended_captain, fixture_df):
    """Build detailed prompt for AI analysis"""
    
    prompt = f"""Analyze this Fantasy Premier League team for Gameweek {team_context['gameweek']}:

TEAM OVERVIEW:
Manager: {team_context['manager_name']}
Overall Rank: {team_context['overall_rank']:,}
Overall Points: {team_context['overall_points']}
Team Value: £{team_context['team_value']:.1f}m
Current Captain: {team_context['captain']}

CURRENT SQUAD:
Goalkeepers: {', '.join(team_context['squad']['GK'])}
Defenders: {', '.join(team_context['squad']['DEF'])}
Midfielders: {', '.join(team_context['squad']['MID'])}
Forwards: {', '.join(team_context['squad']['FWD'])}

TOP PERFORMERS THIS SEASON:
{chr(10).join([f"- {p['web_name']}: {p['total_points']} pts (Form: {p['form']})" for p in team_context['top_performers']])}

RECOMMENDED CHANGES:

Transfer Out: {player_out.web_name.iat[0]} (£{player_out.now_cost.iat[0]/10:.1f}m, Form: {player_out.form.iat[0]})
Transfer In: {player_in.web_name.iat[0]} (£{player_in.now_cost.iat[0]/10:.1f}m, Form: {player_in.form.iat[0]})

Recommended Starting XI: {', '.join(starting_team.web_name.tolist())}

Recommended Captain: {recommended_captain.web_name}

Substitutes: {', '.join(sub_team.web_name.tolist())}

Please provide:
1. Brief assessment of the current team's strengths and weaknesses
2. Opinion on the recommended transfer
3. Captain pick rationale
4. One key strategic tip for the upcoming gameweek

Keep your response concise and actionable (under 250 words)."""
    
    return prompt


def invoke_bedrock(bedrock_runtime, system_prompt, user_prompt):
    """Call Bedrock with available model"""
    
    # Try multiple model IDs in order of preference (cheapest first that actually work)
    model_options = [
        "anthropic.claude-3-haiku-20240307-v1:0",  # Claude Haiku (cheapest Claude that works well)
        "meta.llama3-2-3b-instruct-v1:0",          # Llama 3.2 3B (small and cheap)
        "meta.llama3-2-1b-instruct-v1:0",          # Llama 3.2 1B (smallest)
        "amazon.titan-text-lite-v1",               # Amazon Titan Lite (backup)
        "anthropic.claude-3-sonnet-20240229-v1:0", # Claude 3 Sonnet
        "anthropic.claude-3-5-sonnet-20240620-v1:0" # Claude 3.5 Sonnet (fallback)
    ]
    
    # Try each model until one works
    for model_id in model_options:
        try:
            # Prepare request body based on model type
            if model_id.startswith("amazon.nova"):
                # Amazon Nova format (newer models)
                request_body = {
                    "messages": [
                        {
                            "role": "system",
                            "content": system_prompt
                        },
                        {
                            "role": "user", 
                            "content": user_prompt
                        }
                    ],
                    "inferenceConfig": {
                        "max_new_tokens": 1024,
                        "temperature": 0.7,
                        "top_p": 0.9
                    }
                }
            elif model_id.startswith("amazon.titan"):
                # Amazon Titan format - simplified prompt structure
                combined_prompt = f"{system_prompt}\n\n{user_prompt}\n\nProvide your analysis:"
                request_body = {
                    "inputText": combined_prompt,
                    "textGenerationConfig": {
                        "maxTokenCount": 1024,
                        "temperature": 0.7,
                        "topP": 0.9,
                        "stopSequences": []
                    }
                }
            elif model_id.startswith("meta.llama"):
                # Llama format
                request_body = {
                    "prompt": f"<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n{system_prompt}<|eot_id|><|start_header_id|>user<|end_header_id|>\n{user_prompt}<|eot_id|><|start_header_id|>assistant<|end_header_id|>",
                    "max_gen_len": 1024,
                    "temperature": 0.7,
                    "top_p": 0.9
                }
            else:
                # Claude format
                request_body = {
                    "prompt": f"\n\nHuman: {system_prompt}\n\n{user_prompt}\n\nAssistant:",
                    "max_tokens_to_sample": 1024,
                    "temperature": 0.7,
                    "top_p": 0.9
                }
            
            response = bedrock_runtime.invoke_model(
                modelId=model_id,
                body=json.dumps(request_body)
            )
            
            response_body = json.loads(response['body'].read())
            
            # Extract text based on model type
            if model_id.startswith("amazon.nova"):
                return response_body.get('output', {}).get('message', {}).get('content', [{}])[0].get('text', 'Unable to generate analysis.')
            elif model_id.startswith("amazon.titan"):
                return response_body.get('results', [{}])[0].get('outputText', 'Unable to generate analysis.')
            elif model_id.startswith("meta.llama"):
                return response_body.get('generation', 'Unable to generate analysis.')
            else:
                # Claude format
                return response_body.get('completion', 'Unable to generate analysis.')
                
        except Exception as e:
            # Silently try next model
            continue
    
    return "Unable to generate analysis - no models available."


# Helper functions
def calc_out_weight(players):
    players_copy = players.copy()
    players_copy['out_weight'] = 100
    players_copy['out_weight'] -= players_copy['diff']
    players_copy['out_weight'] -= players_copy['form'].astype("float") * 10
    players_copy.loc[players_copy['element_type'] == 1, 'out_weight'] -= 10
    players_copy.loc[players_copy['out_weight'] < 0, 'out_weight'] = 0
    return players_copy, players_copy.sort_values('out_weight', ascending=False).iloc[:1]


def calc_in_weights(players):
    players['in_weight'] = 1
    players['in_weight'] += players['diff']
    players['in_weight'] += players['form'].astype("float") * 10
    players.loc[players['in_weight'] < 0, 'in_weight'] = 0
    return players.sort_values('in_weight', ascending=False).iloc[:1]


def get_df(bucket, key):
    s3 = boto3.client('s3')
    obj = s3.get_object(Bucket=bucket, Key=key)
    df = pd.read_csv(io.BytesIO(obj['Body'].read()))
    return df


def get(url):
    response = requests.get(url, verify=False)
    return json.loads(response.content)


def get_gameweek():
    players = get('https://fantasy.premierleague.com/api/bootstrap-static/')
    fixtures_df = pd.DataFrame(players['events'])
    today = datetime.now().timestamp()
    fixtures_df = fixtures_df.loc[fixtures_df.deadline_time_epoch > today]
    return fixtures_df.id.iat[0]


def get_position_name(element_type):
    positions = {1: 'Goalkeeper', 2: 'Defender', 3: 'Midfielder', 4: 'Forward'}
    return positions.get(element_type, 'Unknown')


def convert_to_json_serializable(obj):
    """Convert pandas types to JSON serializable types"""
    if isinstance(obj, dict):
        return {k: convert_to_json_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_to_json_serializable(v) for v in obj]
    elif hasattr(obj, 'item'):  # numpy/pandas scalar
        return obj.item()
    elif pd.isna(obj):  # Handle NaN values
        return None
    else:
        return obj
