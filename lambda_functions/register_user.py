import json
import boto3

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('login')

def lambda_handler(event, context):
    try:
        body = json.loads(event['body'])
        email = body.get('email')
        username = body.get('username')
        password = body.get('password')

        if not email or not username or not password:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Missing input"})
            }

        response = table.get_item(Key={'email': email})
        if 'Item' in response:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "User already exists"})
            }

        table.put_item(Item={
            'email': email,
            'user_name': username,
            'password': password
        })

        return {
            "statusCode": 200,
            "body": json.dumps({"message": "User registered successfully"})
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }
