#!/usr/bin/env python3
"""
Test script to verify event parsing logic works correctly
"""
import json

def test_event_parsing():
    """Test the event parsing logic from bedrock_test.py"""
    
    # Test different event structures
    test_cases = [
        {
            "name": "API Gateway Event",
            "event": {
                "body": json.dumps({
                    "team_id": 1192105,
                    "persona": "analyst", 
                    "gameweek": 7
                }),
                "requestContext": {"resourcePath": "/team-change-recommender"}
            }
        },
        {
            "name": "Direct Invocation Event",
            "event": {
                "team_id": 1192105,
                "persona": "veteran",
                "gameweek": 7
            }
        },
        {
            "name": "Query String Event",
            "event": {
                "queryStringParameters": {
                    "team_id": "1192105",
                    "persona": "contrarian",
                    "gameweek": "7"
                }
            }
        }
    ]
    
    for test_case in test_cases:
        print(f"\n🧪 Testing: {test_case['name']}")
        event = test_case['event']
        
        # Replicate the parsing logic from bedrock_test.py
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
        
        print(f"   team_id: {team_id}")
        print(f"   persona: {persona}")
        print(f"   gameweek: {gameweek}")
        
        # Validate
        if team_id and persona and gameweek:
            print("   ✅ Parsing successful!")
        else:
            print("   ❌ Parsing failed!")

if __name__ == "__main__":
    print("Testing event parsing logic...")
    test_event_parsing()
    print("\n✅ Event parsing tests completed!")
