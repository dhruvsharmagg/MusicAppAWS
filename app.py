import boto3.dynamodb
import boto3.dynamodb.conditions
from flask import Flask, render_template,request,redirect,url_for,session,flash
import boto3
from dotenv import load_dotenv
import os

# Load AWS credentials from .env file
load_dotenv() 

app = Flask(__name__)
app.secret_key = "super-secret-key"
region = "us-east-1"
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
# ROUTE 2: Dashboard Page (/dashboard)
# --------------------------
@app.route('/dashboard')
def dashboard():
    #Only allow access if user is logged in
    if 'username' in session:
        return f"Welcome, {session['username']}! Your logged in."
    else:
        return redirect(url_for('login'))

# --------------------------
# ROUTE 3: Register Page (/register)
# --------------------------
@app.route('/register', methods = ['GET','POST'])
def register():
    if request.method == "POST":
        email = request.form['email']
        username = request.form['username']
        password = request.form['password']

        #Checking if email is already registerd
        response = login_table.get_item(Key = {'email' : email})
        existing_user = response.get('Item')

        if existing_user:
            flash('❌ Email already registered. Try logging in instead.')
            print('❌ Email already registered. Try logging in instead.')
            return redirect(url_for('register'))
        
        # if email not found, create new user
        login_table.put_item(Item = {
            'email' : email,
            'user_name' : username,
            'password' : password
        })
        
        flash('✅ Registered successfully! Please log in.')
        return  redirect(url_for('login'))
    return render_template('register.html')

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

@app.route('/subscribe',methods=["POST"])
def subscribe():
    if 'email' not in session:
        return redirect(url_for('login'))
    
    title = request.form['title']
    artist = request.form['artist']
    email = session['email']

    subs_table = dynamodb.Table('subscriptions')
    subs_table.put_item(Item = 
        {'email' : email,
        'song_title' : title,
        'artist' : artist})
    
    return redirect(url_for('main'))

@app.route('/unsubscribe',methods = ['POST'])
def unsubscribe():
    if 'email' not in session:
        return redirect(url_for('login'))
    title = request.form['title']
    email = session['email']

    subs_table = dynamodb.Table('subscriptions')
    subs_table.delete_item(
        Key = {
            'email' : email,
            'song_title' : title 
        }
    )
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

    if not (title or artist or album or year):
        flash("❗ Please enter at least one field to query.")
        return redirect(url_for('main'))

    # Load all songs
    music_table = dynamodb.Table('music')
    response = music_table.scan()
    all_songs = response.get('Items', [])

    # Filter songs based on input
    def matches(song):
        return (
            (not title or title in song.get('title', '').lower()) and
            (not artist or artist in song.get('artist', '').lower()) and
            (not album or album in song.get('album', '').lower()) and
            (not year or year in str(song.get('year', '')).lower())
        )

    matched_songs = list(filter(matches, all_songs))

    # Get subscriptions
    subs_table = dynamodb.Table('subscriptions')
    sub_response = subs_table.query(
        KeyConditionExpression=boto3.dynamodb.conditions.Key('email').eq(email)
    )
    subscribed_titles = set(item['song_title'] for item in sub_response['Items'])

    # Add image URLs and subscription status

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



if __name__=='__main__':
    app.run(debug=True)

