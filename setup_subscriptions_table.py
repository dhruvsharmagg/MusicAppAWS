import boto3

from dotenv import load_dotenv

load_dotenv()

dynamodb = boto3.resource('dynamodb' , region_name = 'us-east-1')

table_name = 'subscriptions'

try:

    table = dynamodb.create_table(
        TableName = table_name,
        KeySchema = [
            {'AttributeName' : 'email', 'KeyType' : 'HASH'},
            {'AttributeName' : 'song_title', 'KeyType' : 'RANGE'}
        ],
        AttributeDefinitions = [
            {'AttributeName' : 'email', 'AttributeType' : 'S'},
            {'AttributeName' : 'song_title', 'AttributeType' : 'S'}
        ],
        ProvisionedThroughput = { 'ReadCapacityUnits' : 5,
                                 'WriteCapacityUnits' : 5}
    )
    table.wait_until_exists()
    print("✅ 'subscriptions' table created.")

except dynamodb.meta.client.exceptions.ResourceInUseException:
    print("ℹ️ Table already exists.")