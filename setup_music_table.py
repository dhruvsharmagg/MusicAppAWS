import boto3
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize DynamoDB resource
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

# Create the 'music' table if not exists
try:
    music_table = dynamodb.create_table(
        TableName='music',
        KeySchema=[
            {'AttributeName': 'title', 'KeyType': 'HASH'},   # Primary key
            {'AttributeName': 'artist', 'KeyType': 'RANGE'}  # Sort key
        ],
        AttributeDefinitions=[
            {'AttributeName': 'title', 'AttributeType': 'S'},
            {'AttributeName': 'artist', 'AttributeType': 'S'}
        ],
        ProvisionedThroughput={
            'ReadCapacityUnits': 5,
            'WriteCapacityUnits': 5
        }
    )
    music_table.wait_until_exists()
    print("Table 'music' has been created successfully.")

except dynamodb.meta.client.exceptions.ResourceInUseException:
    music_table = dynamodb.Table('music')
    print("Table 'music' already exists.")

# Insert records from JSON file into table
with open('2025a1.json', 'r') as json_file:
    content = json.load(json_file)
    entries = content.get('songs', [])

processed = set()

with music_table.batch_writer() as writer:
    for entry in entries:
        track_key = (entry['title'], entry['artist'])

        if track_key in processed:
            print(f"Duplicate found, skipping: {entry['title']} - {entry['artist']}")
            continue

        processed.add(track_key)

        writer.put_item(Item={
            'title': entry['title'],
            'artist': entry['artist'],
            'year': entry['year'],
            'album': entry['album'],
            'image_url': entry['img_url']
        })
        print(f"Inserted: {entry['title']} by {entry['artist']}")

print("Data import complete.")
