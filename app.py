import boto3.dynamodb
import boto3.dynamodb.conditions
from flask import Flask, render_template, request, redirect, url_for, session, flash
import requests
import boto3
from dotenv import load_dotenv
import os
import json

# Load AWS credentials
load_dotenv(dotenv_path="/var/www/Code_dhruv/.env") 

app = Flask(__name__)
app.secret_key = "super-secret-key"

# AWS clients
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
s3_client = boto3.client('s3', region_name='us-east-1')
bucket_name = "cloudcomputingsongimages"

# Tables
login_table = dynamodb.Table('login')
music_table = dynamodb.Table('music')
subs_table = dynamodb.Table('subscriptions')

# --------------------------
# LOGIN
# --------------------------
@app.route('/', methods=["GET", "POST"])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        # 🔍 Debug AWS credentials (will show in Apache logs)
        print("🔐 AWS_ACCESS_KEY_ID:", os.getenv('AWS_ACCESS_KEY_ID'))
        print("🔐 AWS_SECRET_ACCESS_KEY:", os.getenv('AWS_SECRET_ACCESS_KEY')[:4], "****")
        print("🔐 AWS_SESSION_TOKEN:", os.getenv('AWS_SESSION_TOKEN')[:15], "...")

        response = login_table.get_item(Key={'email': email})
        user = response.get('Item')

        if user and user['password'] == password:
            session['username'] = user['user_name']
            session['email'] = user['email']
            return redirect(url_for('main'))
        else:
            flash('❌ Email or password is incorrect.')

    return render_template('login.html')

# --------------------------
# REGISTER (via Lambda)
# --------------------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == "POST":
        payload = {
            "email": request.form['email'],
            "username": request.form['username'],
            "password": request.form['password']
        }

        try:
            response = requests.post(
                'https://zyzbozj5o2.execute-api.us-east-1.amazonaws.com/CloudAss1/register',
                data=json.dumps(payload),
                headers={"Content-Type": "application/json"}
            )
            print("✅ Lambda raw response:", response.text)
            body = response.json()

            if response.status_code == 200:
                flash("✅ " + body.get("message", "Registered successfully!"))
                return redirect(url_for('login'))
            else:
                flash("❌ " + body.get("error", "Something went wrong."))

        except Exception as e:
            flash(f"❌ Error: {str(e)}")

    return render_template("register.html")

# --------------------------
# DASHBOARD
# --------------------------
@app.route('/main')
def main():
    if 'username' not in session or 'email' not in session:
        return redirect(url_for('login'))

    email = session['email']
    response = music_table.scan()
    songs = response.get('Items', [])

    sub_response = subs_table.query(
        KeyConditionExpression=boto3.dynamodb.conditions.Key('email').eq(email)
    )
    subscribed_titles = set(item['song_title'] for item in sub_response['Items'])

    for song in songs:
        image_file = song.get('image_url', '')
        if image_file:
            filename = image_file.split("/")[-1]
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

    return render_template("main.html", songs=songs, user=session['username'])

# --------------------------
# SUBSCRIBE
# --------------------------
@app.route('/subscribe', methods=["POST"])
def subscribe():
    if 'email' not in session:
        return redirect(url_for('login'))

    payload = {
        "body": json.dumps({
            "email": session['email'],
            "title": request.form['title'],
            "artist": request.form['artist']
        })
    }

    try:
        response = requests.post(
            'https://zyzbozj5o2.execute-api.us-east-1.amazonaws.com/CloudAss1/subscription',
            data=json.dumps(payload),
            headers={"Content-Type": "application/json"}
        )
        result = response.json()
        if response.status_code == 200:
            flash("✅ Subscribed successfully!")
        else:
            flash("❌ " + result.get("error", "Failed to subscribe."))
    except Exception as e:
        flash(f"❌ Error: {str(e)}")

    return redirect(url_for('main'))

# --------------------------
# UNSUBSCRIBE
# --------------------------
@app.route('/unsubscribe', methods=["POST"])
def unsubscribe():
    if 'email' not in session:
        return redirect(url_for('login'))

    payload = {
        "body": json.dumps({
            "email": session['email'],
            "title": request.form['title']
        })
    }

    try:
        response = requests.post(
            'https://zyzbozj5o2.execute-api.us-east-1.amazonaws.com/CloudAss1/unsubscribe',
            data=json.dumps(payload),
            headers={"Content-Type": "application/json"}
        )
        result = response.json()
        if response.status_code == 200:
            flash("✅ Unsubscribed successfully!")
        else:
            flash("❌ " + result.get("error", "Failed to unsubscribe."))
    except Exception as e:
        flash(f"❌ Error: {str(e)}")

    return redirect(url_for('main'))

# --------------------------
# SEARCH SONGS
# --------------------------
@app.route('/search', methods=['GET'])
def search():
    if 'username' not in session or 'email' not in session:
        return redirect(url_for('login'))

    email = session['email']
    title = request.args.get('title', '').lower()
    artist = request.args.get('artist', '').lower()
    album = request.args.get('album', '').lower()
    year = request.args.get('year', '').lower()

    if not (title or artist or album or year):
        flash("❗ Please enter at least one field to query.")
        return render_template("search.html", songs=[], user=session['username'])

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

    sub_response = subs_table.query(
        KeyConditionExpression=boto3.dynamodb.conditions.Key('email').eq(email)
    )
    subscribed_titles = set(item['song_title'] for item in sub_response['Items'])

    for song in matched_songs:
        image_file = song.get('image_url', '')
        if image_file:
            filename = image_file.split("/")[-1]
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

# --------------------------
# LOGOUT
# --------------------------
@app.route('/logout')
def logout():
    session.clear()
    flash("✅ Logged out successfully!")
    return redirect(url_for('login'))

# --------------------------
# LAUNCH (for local testing only)
# --------------------------
if __name__ == '__main__':
    app.run(debug=True)
