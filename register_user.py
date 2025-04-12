import json
import boto3

dynamodb = boto3.resource('dynamodb')
login_table = dynamodb.Table('login')

def lambda_handler(event, context):
    email = event['email']
    username = event['username']
    password = event['password']

    # Check if user already exists
    response = login_table.get_item(Key={'email': email})
    if 'Item' in response:
        return {
            'statusCode': 400,
            'body': json.dumps('User already exists.')
        }

    # Create new user
    login_table.put_item(Item={
        'email': email,
        'user_name': username,
        'password': password
    })

    return {
        'statusCode': 200,
        'body': json.dumps('User registered successfully!')
    }
