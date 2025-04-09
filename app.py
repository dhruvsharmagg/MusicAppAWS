import boto3.dynamodb
import boto3.dynamodb.conditions
from flask import Flask, render_template,request,redirect,url_for,session,flash
import requests
import boto3
from dotenv import load_dotenv
import os
import json

# Load AWS credentials from .env file
load_dotenv() 

app = Flask(__name__)
app.secret_key = "super-secret-key"
dynamodb = boto3.resource('dynamodb',region_name = 'us-east-1')
s3_client = boto3.client('s3', region_name='us-east-1')
bucket_name = "suyash-music-image-bucket"

#Reference to 'login' table

login_table = dynamodb.Table('login')

# --------------------------
# ROUTE 1: Login Page (/)
# --------------------------
@app.route('/', methods = ["GET","POST"])
def login():
    if request.method == 'POST':
        # Get from input form
        email = request.form['email']
        password = request.form['password']

        print(email,'\n',password)

        # Searching email and passwords in DynamoDB
        response = login_table.get_item(Key = {'email' : email})
        user = response.get('Item') #This will be None if user not found

        #Validate password
        if user and user['password'] == password:

            #Store user information in session
            session['username'] = user['user_name']
            session['email'] = user['email']

            return redirect(url_for('main'))
        else:
            print('❌ Email or password is incorrect.')
            flash('❌ Email or password is incorrect.')

    return render_template('login.html') # Show the form


# --------------------------
# ROUTE 3: Register Page (/register)
# --------------------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == "POST":
        email = request.form['email']
        username = request.form['username']
        password = request.form['password']

        payload = {
            "email": email,
            "username": username,
            "password": password
        }

        try:
            response = requests.post(
                'https://75g2mv4jp6.execute-api.us-east-1.amazonaws.com/dev1/register',
                data=json.dumps(payload),
                headers={"Content-Type": "application/json"}
            )

            print("✅ Lambda raw response:", response.text)
            print("response.status_code" ,response.status_code)

            body = response.json()  # Lambda's 'body' is a string, already flattened by API Gateway
            if response.status_code == 200:
                flash("✅ " + body.get("message", "Registered successfully!"))
                return redirect(url_for('login'))
            else:
                flash("❌ " + body.get("error", "Something went wrong."))

        except Exception as e:
            flash(f"❌ Error: {str(e)}")

    return render_template("register.html")



# --------------------------
# ROUTE 4: Main Dashboard Page (/main)
# --------------------------

@app.route('/main')
def main():
    if 'username' not in session or 'email' not in session:
        return redirect(url_for('login'))
    
    email = session['email']

    #Load all songs from DynamoDB
    music_table = dynamodb.Table('music')
    response = music_table.scan()
    songs = response.get('Items',[])


    subs_table = dynamodb.Table('subscriptions')
    sub_response = subs_table.query(
        KeyConditionExpression = boto3.dynamodb.conditions.Key('email').eq(email)
    )
    subscribe_titles = set(item['song_title'] for item in sub_response['Items'])


    #Construct full S3 image URL
    
    
    for song in songs:
        image_file = song.get('image_url','')
        if image_file:
            filename = image_file.split("/")[-1]

            try:
                #Generate presigned URL for image (only valid for 1 hour)

                url = s3_client.generate_presigned_url(
                    'get_object',
                    Params = {'Bucket': bucket_name, 'Key' : filename},
                    ExpiresIn = 3600
                )
                song['image_url'] = url
            except Exception as e:
                print(f"⚠️ Error generating URL for {filename}: {e}")
                song['image_url'] = ""
        song['subscribed'] = song['title'] in subscribe_titles # add this flag
            
    return render_template("main.html", songs = songs, user = session['username'])

@app.route('/subscribe', methods=["POST"])
def subscribe():
    if 'email' not in session:
        return redirect(url_for('login'))
    
    title = request.form['title']
    artist = request.form['artist']
    email = session['email']

    # 👇 IMPORTANT: Wrap the payload inside a "body" key as a string (like API Gateway)
    payload = {
        "body": json.dumps({
            "email": email,
            "title": title,
            "artist": artist
        })
    }
    try:
        response = requests.post(
            'https://75g2mv4jp6.execute-api.us-east-1.amazonaws.com/dev1/subscribe',
            data=json.dumps(payload),
            headers={"Content-Type": "application/json"}
        )
        result = response.json()
        print('result', result)

        if response.status_code == 200:
            flash("✅ Subscribed successfully!")
        else:
            flash("❌ " + result.get("error", "Failed to subscribe."))
    except Exception as e:
        flash(f"❌ Error: {str(e)}")

    return redirect(url_for('main'))


@app.route('/unsubscribe', methods=["POST"])
def unsubscribe():
    if 'email' not in session:
        return redirect(url_for('login'))

    email = session['email']
    title = request.form['title']

    payload = {
    "body": json.dumps({
        "email": email,
        "title": title
    })
}

    try:
        response = requests.post(
            'https://75g2mv4jp6.execute-api.us-east-1.amazonaws.com/dev1/unsubscribe',
            data=json.dumps(payload)
        )
        result = response.json()

        if response.status_code == 200:
            flash("✅ Unsubscribed successfully!")
        else:
            flash("❌ " + result.get("error", "Failed to unsubscribe."))
    except Exception as e:
        flash(f"❌ Error: {str(e)}")

    return redirect(url_for('main'))


@app.route('/search', methods=['GET'])
def search():
    if 'username' not in session or 'email' not in session:
        return redirect(url_for('login'))

    email = session['email']
    title = request.args.get('title', '').lower()
    artist = request.args.get('artist', '').lower()
    album = request.args.get('album', '').lower()
    year = request.args.get('year', '').lower()

    # ⚠️ Instead of redirecting, show empty results with a flash
    if not (title or artist or album or year):
        flash("❗ Please enter at least one field to query.")
        return render_template("search.html", songs=[], user=session['username'])

    # Load and filter songs
    music_table = dynamodb.Table('music')
    response = music_table.scan()
    all_songs = response.get('Items', [])

    def matches(song):
        return (
            (not title or title in song.get('title', '').lower()) and
            (not artist or artist in song.get('artist', '').lower()) and
            (not album or album in song.get('album', '').lower()) and
            (not year or year in str(song.get('year', '')).lower())
        )

    matched_songs = list(filter(matches, all_songs))

    subs_table = dynamodb.Table('subscriptions')
    sub_response = subs_table.query(
        KeyConditionExpression=boto3.dynamodb.conditions.Key('email').eq(email)
    )
    subscribed_titles = set(item['song_title'] for item in sub_response['Items'])

    for song in matched_songs:
        img = song.get('image_url', '')
        if img:
            filename = img.split("/")[-1]
            try:
                url = s3_client.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': bucket_name, 'Key': filename},
                    ExpiresIn=3600
                )
                song['image_url'] = url
            except:
                song['image_url'] = ""
        song['subscribed'] = song['title'] in subscribed_titles

    return render_template("search.html", songs=matched_songs, user=session['username'])

@app.route('/logout')
def logout():
    session.clear()
    flash("✅ Logged out successfully!")
    return redirect(url_for('login'))


if __name__=='__main__':
    app.run(debug=True)

