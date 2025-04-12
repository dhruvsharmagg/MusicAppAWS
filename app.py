import boto3.dynamodb
import boto3.dynamodb.conditions
from flask import Flask, render_template, request, redirect, url_for, session, flash
import requests
import boto3
#from dotenv import load_dotenv
import os
import json

# Load AWS credentials
#load_dotenv(dotenv_path="/var/www/Code_dhruv/.env") 

# Initialize Flask app
app = Flask(__name__)
app.secret_key = "super-secret-key"

# Setup AWS services
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
s3_client = boto3.client('s3', region_name='us-east-1')
bucket_name = "cloudcomputingsongimages"

# Reference DynamoDB tables
login_table = dynamodb.Table('login')
music_table = dynamodb.Table('music')
subs_table = dynamodb.Table('subscriptions')

# Login route
@app.route('/', methods=["GET", "POST"])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        response = login_table.get_item(Key={'email': email})
        user = response.get('Item')

        if user and user['password'] == password:
            session['username'] = user['user_name']
            session['email'] = user['email']
            return redirect(url_for('main'))
        else:
            flash('Invalid email or password.')

    return render_template('login.html')

# Register via Lambda
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = {
            "email": request.form['email'],
            "username": request.form['username'],
            "password": request.form['password']
        }

        try:
            response = requests.post(
                'https://zyzbozj5o2.execute-api.us-east-1.amazonaws.com/CloudAss1/register',
                data=json.dumps(data),
                headers={"Content-Type": "application/json"}
            )

            res = response.json()
            if response.status_code == 200:
                flash(res.get("message", "Registration successful."))
                return redirect(url_for('login'))
            else:
                flash(res.get("error", "Registration failed."))

        except Exception as e:
            flash(f"Error: {str(e)}")

    return render_template("register.html")

# Dashboard route
@app.route('/main')
def main():
    if 'email' not in session or 'username' not in session:
        return redirect(url_for('login'))

    email = session['email']

    music_data = music_table.scan().get('Items', [])
    subs_data = subs_table.query(
        KeyConditionExpression=boto3.dynamodb.conditions.Key('email').eq(email)
    ).get('Items', [])

    subscribed = set(item['song_title'] for item in subs_data)

    for song in music_data:
        image_path = song.get('image_url', '')
        if image_path:
            filename = image_path.split('/')[-1]
            try:
                url = s3_client.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': bucket_name, 'Key': filename},
                    ExpiresIn=3600
                )
                song['image_url'] = url
            except:
                song['image_url'] = ''
        song['subscribed'] = song['title'] in subscribed

    return render_template("main.html", songs=music_data, user=session['username'])

# Subscribe to a song
@app.route('/subscribe', methods=['POST'])
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

        if response.status_code == 200:
            flash("Subscription successful.")
        else:
            error_msg = response.json().get("error", "Subscription failed.")
            flash(error_msg)

    except Exception as e:
        flash(f"Error: {str(e)}")

    return redirect(url_for('main'))

# Unsubscribe from a song
@app.route('/unsubscribe', methods=['POST'])
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

        if response.status_code == 200:
            flash("Unsubscribed successfully.")
        else:
            error_msg = response.json().get("error", "Unsubscribe failed.")
            flash(error_msg)

    except Exception as e:
        flash(f"Error: {str(e)}")

    return redirect(url_for('main'))

# Search songs by fields
@app.route('/search', methods=['GET'])
def search():
    if 'email' not in session or 'username' not in session:
        return redirect(url_for('login'))

    title = request.args.get('title', '').lower()
    artist = request.args.get('artist', '').lower()
    album = request.args.get('album', '').lower()
    year = request.args.get('year', '').lower()

    if not (title or artist or album or year):
        flash("Please enter at least one search field.")
        return render_template("search.html", songs=[], user=session['username'])

    songs = music_table.scan().get('Items', [])

    def is_match(song):
        return (
            (not title or title in song.get('title', '').lower()) and
            (not artist or artist in song.get('artist', '').lower()) and
            (not album or album in song.get('album', '').lower()) and
            (not year or year in str(song.get('year', '')).lower())
        )

    filtered_songs = list(filter(is_match, songs))

    subs = subs_table.query(
        KeyConditionExpression=boto3.dynamodb.conditions.Key('email').eq(session['email'])
    ).get('Items', [])
    subscribed = set(item['song_title'] for item in subs)

    for song in filtered_songs:
        image_path = song.get('image_url', '')
        if image_path:
            filename = image_path.split('/')[-1]
            try:
                url = s3_client.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': bucket_name, 'Key': filename},
                    ExpiresIn=3600
                )
                song['image_url'] = url
            except:
                song['image_url'] = ''
        song['subscribed'] = song['title'] in subscribed

    return render_template("search.html", songs=filtered_songs, user=session['username'])

# Logout and clear session
@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out.")
    return redirect(url_for('login'))

# Run app 
if __name__ == '__main__':
    app.run(debug=True)
