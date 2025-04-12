import boto3
import json
from dotenv import load_dotenv
import os

load_dotenv()

dynamodb = boto3.resource('dynamodb',region_name = 'us-east-1')

# -----------------------------
# Step 1: Create music table
# -----------------------------

try:
    table = dynamodb.create_table(
        TableName = 'music',
        KeySchema = [
            {'AttributeName' : 'title', 'KeyType' : 'HASH'}, # Partition key
            {'AttributeName' : 'artist', 'KeyType' : 'RANGE'} # Sort key
        ], 
        AttributeDefinitions = [
            { 'AttributeName' : 'title', 'AttributeType' : 'S'},
            { 'AttributeName' : 'artist', 'AttributeType' : 'S'},
        ],
        ProvisionedThroughput = {'ReadCapacityUnits' : 5, 
                                 'WriteCapacityUnits' : 5}
    )
    table.wait_until_exists()
    print("✅ 'music' table created.")

except dynamodb.meta.client.exceptions.ResourceInUseException:
    table = dynamodb.Table('music')
    print("ℹ️ 'music' table already exists.")

# -----------------------------
# Step 2: Load data from 2025a1.json
# -----------------------------

with open('2025a1.json') as f:
    data = json.load(f)
    songs = data['songs']

seen_songs = set() # Filter duplicates

with table.batch_writer() as batch:
    for song in songs:
        song_key = (song['title'],song['artist'])

        if song_key in seen_songs:
            print(f"⚠️ Skipping duplicate: {song['title']} by {song['artist']}")
            continue

        seen_songs.add(song_key)

        batch.put_item(
            Item = {
                'title' : song['title'],
                'artist' : song['artist'],
                'year' : song['year'],
                'album' : song['album'],
                'image_url' : song['img_url']
            }
        )
        print(f"🎵 Loaded: {song['title']} by {song['artist']}")

print("✅ All songs loaded into 'music' table.")
