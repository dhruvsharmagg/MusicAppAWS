import boto3
import json
import requests
from dotenv import load_dotenv
import os 

load_dotenv()

# -- setup S3 connection --

s3 = boto3.client('s3',region_name='us-east-1')
BUCKET_NAME = 'suyash-music-image-bucket' # name of our bucket

# create bucket

def create_bucket():
    try:
        s3.create_bucket(Bucket = BUCKET_NAME)
        print(f"✅ Bucket '{BUCKET_NAME}' created.")
        
    except s3.exceptions.BucketAlreadyOwnedByYou:
        print(f"ℹ️ Bucket '{BUCKET_NAME}' already exists.")

# Upload images
def upload_image():
    with open("2025a1.json") as f:
        songs = json.load(f)["songs"]
    
    uploaded = set() # this is to avoid duplicate songs

    for song in songs:
        image_url = song.get("img_url")
        if not image_url:
            continue

        #Use the image filename from url
        file_name = image_url.split('/')[-1]

        print(file_name)

        if file_name in uploaded:
            continue

        try:
            #Download image
            response = requests.get(image_url, timeout=10)
            if response.status_code == 200:

                s3.put_object(
                    Bucket = BUCKET_NAME,
                    Key = file_name,
                    Body = response.content,
                    ContentType = 'image/jpeg'
                )
                print(f"🖼️ Uploaded: {file_name}")
                uploaded.add(file_name)
            else:
                print(f"⚠️ Failed to download: {image_url}")
        except Exception as e:
            print(f"⚠️ Error with {image_url}: {e}")

if __name__=="__main__":
    create_bucket()
    upload_image()
    print("✅ All images uploaded to S3.")