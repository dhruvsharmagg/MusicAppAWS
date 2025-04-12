import boto3
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize DynamoDB connection
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

# Set the table name
table_name = 'subscriptions'

# Attempt to create the table
try:
    subscriptions_table = dynamodb.create_table(
        TableName=table_name,
        KeySchema=[
            {'AttributeName': 'email', 'KeyType': 'HASH'},       # Partition key
            {'AttributeName': 'song_title', 'KeyType': 'RANGE'}  # Sort key
        ],
        AttributeDefinitions=[
            {'AttributeName': 'email', 'AttributeType': 'S'},
            {'AttributeName': 'song_title', 'AttributeType': 'S'}
        ],
        ProvisionedThroughput={
            'ReadCapacityUnits': 5,
            'WriteCapacityUnits': 5
        }
    )

    # Wait until the table is fully created
    subscriptions_table.wait_until_exists()
    print("'subscriptions' table successfully created.")

except dynamodb.meta.client.exceptions.ResourceInUseException:
    print("The 'subscriptions' table already exists.")
