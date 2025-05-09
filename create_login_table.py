import boto3
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Connect to DynamoDB
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table_name = 'login'

# Try to create the login table if it doesn't exist
try:
    table = dynamodb.create_table(
        TableName=table_name,
        KeySchema=[
            {'AttributeName': 'email', 'KeyType': 'HASH'}
        ],
        AttributeDefinitions=[
            {'AttributeName': 'email', 'AttributeType': 'S'}
        ],
        BillingMode='PAY_PER_REQUEST'  # On-demand billing
    )
    print("Creating table...")
    table.wait_until_exists()
    print("Table 'login' created successfully.")
except dynamodb.meta.client.exceptions.ResourceInUseException:
    print("Table already exists.")

# List of user entries to insert
users = [
    {'email': 's40374120@student.rmit.edu.au', 'user_name': 'dhruvsharma0', 'password': '123456'},
    {'email': 's40347661@student.rmit.edu.au', 'user_name': 'harjasthapar1', 'password': '123213'},
    {'email': 's40176172@student.rmit.edu.au', 'user_name': 'sahilsurve2', 'password': '213123'},
    {'email': 's40353213@student.rmit.edu.au', 'user_name': 'suyashalekar3', 'password': '964589'},
    {'email': 's1231234@student.rmit.edu.au', 'user_name': 'atharvaparab4', 'password': '213413'},
    {'email': 's9798215@student.rmit.edu.au', 'user_name': 'siddharthraul5', 'password': '547835'},
    {'email': 's4021336@student.rmit.edu.au', 'user_name': 'vidhisinha6', 'password': '605460'},
    {'email': 's4213217@student.rmit.edu.au', 'user_name': 'nikhilmunde7', 'password': '543853'},
    {'email': 's4567898@student.rmit.edu.au', 'user_name': 'vaishnavilokhande8', 'password': '123021'},
    {'email': 's4453539@student.rmit.edu.au', 'user_name': 'kajalhule9', 'password': '965946'},
]

# Insert each user into the table
for user in users:
    table.put_item(Item=user)
    print(f"Inserted: {user['email']}")

print("All users added to the 'login' table.")
