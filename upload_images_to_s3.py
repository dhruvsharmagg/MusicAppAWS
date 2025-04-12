import boto3
import json
import requests
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Set up S3 client
s3_client = boto3.client('s3', region_name='us-east-1')
BUCKET_NAME = 'cloudcomputingsongimages'

# Create the S3 bucket if it doesn't already exist
def create_bucket_if_not_exists():
    try:
        s3_client.create_bucket(Bucket=BUCKET_NAME)
        print(f"Bucket '{BUCKET_NAME}' created.")
    except s3_client.exceptions.BucketAlreadyOwnedByYou:
        print(f"Bucket '{BUCKET_NAME}' already exists.")

# Upload images from the JSON file to the S3 bucket
def upload_images():
    with open("2025a1.json", "r") as f:
        data = json.load(f).get("songs", [])

    uploaded_files = set()  # Track uploaded filenames to avoid duplicates

    for song in data:
        image_url = song.get("img_url")
        if not image_url:
            continue

        filename = image_url.split("/")[-1]  # Extract image file name from URL

        if filename in uploaded_files:
            continue

        try:
            # Download image
            response = requests.get(image_url, timeout=10)
            if response.status_code == 200:
                # Upload image to S3
                s3_client.put_object(
                    Bucket=BUCKET_NAME,
                    Key=filename,
                    Body=response.content,
                    ContentType='image/jpeg'
                )
                print(f"Uploaded: {filename}")
                uploaded_files.add(filename)
            else:
                print(f"Failed to download: {image_url}")
        except Exception as e:
            print(f"Error with {image_url}: {e}")

# Run the main logic
if __name__ == "__main__":
    create_bucket_if_not_exists()
    upload_images()
    print("All images uploaded.")
