import json
import boto3

dynamodb = boto3.resource('dynamodb')
subs_table = dynamodb.Table('subscriptions')

def lambda_handler(event, context):
    try:
        body = json.loads(event['body'])
        email = body.get('email')
        title = body.get('title')

        if not email or not title:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Missing input"})
            }

        subs_table.delete_item(Key={
            'email': email,
            'song_title': title
        })

        return {
            "statusCode": 200,
            "body": json.dumps({"message": "Unsubscribed successfully"})
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }
