import json
import boto3

dynamodb = boto3.resource('dynamodb')
subs_table = dynamodb.Table('subscriptions')

def lambda_handler(event, context):
    try:
        body = json.loads(event['body'])
        email = body.get('email')
        title = body.get('title')
        artist = body.get('artist')

        if not email or not title or not artist:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Missing input"})
            }

        subs_table.put_item(Item={
            'email': email,
            'song_title': title,
            'artist': artist
        })

        return {
            "statusCode": 200,
            "body": json.dumps({"message": "Subscription successful"})
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }
