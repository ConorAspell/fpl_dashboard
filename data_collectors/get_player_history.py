import json
import boto3
import requests

def get_all_player_ids():
    """
    Returns a list of all player IDs from the FPL bootstrap static API.
    """
    url = "https://fantasy.premierleague.com/api/bootstrap-static/"
    response = requests.get(url)

    response.raise_for_status()

    data = response.json()
    player_ids = [player['id'] for player in data['elements']]

    return player_ids

def get_player_history(player_id):
    """
    Returns the history data for a given player ID from the FPL API.
    """
    url = f"https://fantasy.premierleague.com/api/element-summary/{player_id}/"
    response = requests.get(url)

    response.raise_for_status()

    return response.json()['history']


def upload_to_s3(bucket_name, file_name, data):
    """
    Uploads the given data to the specified S3 bucket and file name.
    """
    s3 = boto3.resource('s3')
    obj = s3.Object(bucket_name, file_name)
    obj.put(Body=json.dumps(data))

def main():
    # Get player IDs
    player_ids = get_all_player_ids()

    # Get player data
    player_data = []
    for player_id in player_ids:
        history = get_player_history(player_id)
        player_data.append({'id': player_id, 'history': history})

    # Write player data to CSV
    # Write player data to JSON file
    bucket_name = 'fpl-bucket-2022'
    file_name = 'player_data.json'
    upload_to_s3(bucket_name, file_name, player_data)

if __name__ == '__main__':
    main()
