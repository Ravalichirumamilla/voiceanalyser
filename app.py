from flask import Flask,render_template,request,session,redirect,jsonify
from pymongo import MongoClient
import boto3
import smtplib
import random
import json


transcribe = boto3.client('transcribe')
s3 = boto3.client('s3')
comprehend = boto3.client('comprehend')

cluster = MongoClient('mongodb+srv://ravalichirumamilla5:ravali@cluster0.1jivexg.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0')
db = cluster['sentiment']
users = db['users']
videos = db['videos']

mail_pass= 'kqlcwajnhaonvqcb'
smtp = smtplib.SMTP('smtp.gmail.com',587)

app = Flask(__name__)

app.secret_key="hdcsfgvuebnjjoihr567"

@app.route('/')
def land():
    return render_template('start.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/login',methods=['post'])
def dologin():
    email = request.form['email']
    password = request.form['password']
    user = users.find_one({"email":email,"password":password})

    if not user:
        return render_template('login.html',ack="incorrect crendentials..")
    session['email']= email
    return redirect('/dashboard')

@app.route('/dashboard')
def dash():
    return render_template('home.html')

@app.route('/forget')
def forg():
    return render_template('forgot.html')

@app.route('/forget',methods=['post'])
def fo():
    email = request.form['email']
    user = users.find_one({"email":email})
    if not user:
        return render_template('forgot.html',ack="user not found with this email")
    smtp.starttls()
    smtp.login('ravalichirumamilla5@gmail.com',mail_pass)
    smtp.sendmail('ravalichirumamilla5@gmail.com',email,'click on the follwing link to update the password \n http://127.0.0.1:5000/update/'+email)
    return render_template('forgot.html',ack="Mail sent ")

@app.route('/update/<email>',methods=['get'])
def loadchange(email):
    return render_template('change.html',data=email)

@app.route('/update/<email>',methods=['post'])
def change(email):
    npass = request.form['npass']
    cpass = request.form['cpass']
    if npass != cpass:
        return render_template('/change.html',ack="passwords miss match")
    users.update_one({'email':email},{'$set':{"password":npass}})
    return render_template('change.html',ack="password changed")

@app.route('/home')
def h():
    return render_template('home.html')

@app.route('/register')
def reg():
    return render_template('register.html')

@app.route('/register',methods=['post'])
def doreg():
    email = request.form['email']
    fname = request.form['fname']
    lname = request.form['lname']
    gender = request.form['gender']
    cpass = request.form['cpass']
    npass = request.form['npass']
    if cpass != npass:
        return render_template('register.html',ack='passwords miss match')
    user = users.find_one({'email':email})
    if user:
        return render_template('register.html',ack="user already exists with same email id")
    users.insert_one({"firstName":fname,"lastName":lname,"email":email,"gender":gender,"password":npass})
    return redirect('/login')
@app.route('/video-to-text')
def vtot():
    return render_template('video-to-text.html',data=None,sen=None,score=None)

@app.route('/voice-to-text')
def votot():
    return render_template('voice-to-text.html',ack=None,text=None)

@app.route('/back')
def back():
    return render_template('home.html')

@app.route('/voice-to-text',methods=['post'])
def sentimetof():
    text = request.form['text']
    res = comprehend.detect_sentiment(Text=text,LanguageCode='en')
    return render_template('voice-to-text.html',ack = res['SentimentScore'],sentiment = res['Sentiment'],text=text)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

@app.route('/video-to-text',methods=['post'])
def trans():
    email = session.get('email')
    video = request.files['video']
    key = str(random.randint(1000,10000))
    filetype = video.content_type
    ft = filetype.split('/')[-1]
    s3.upload_fileobj(video,'voice.analayser.app','inputs/'+key+'.'+ft)
    videos.insert_one({'email':email,"uri":"s3://voice.analayser.app/inputs/"+key+'.'+ft,'filetype':filetype})
    job_name= key
    lang = 'en-US'
    transcribe.start_transcription_job(
        TranscriptionJobName = job_name,
        LanguageCode = lang,
        Media={
            'MediaFileUri':"s3://voice.analayser.app/inputs/"+key+'.'+ft
        },
        OutputBucketName = 'voice.analayser.app',
        OutputKey = 'outputs/'+key+'.json'
    )
    res = transcribe.get_transcription_job(TranscriptionJobName=job_name)
    while res['TranscriptionJob']['TranscriptionJobStatus']=='IN_PROGRESS':
        res = transcribe.get_transcription_job(TranscriptionJobName=job_name)
    resfile = s3.get_object(Bucket='voice.analayser.app',Key='outputs/'+key+'.json')
    file_content = resfile['Body'].read().decode('utf-8')
    file_content = json.loads(file_content)
    text = file_content['results']['transcripts'][0]['transcript']
    sres = comprehend.detect_sentiment(Text = text,LanguageCode= 'en')
    return render_template('video-to-text.html',ack="File uploaded....",data=text,sen =sres['Sentiment'],score = sres['SentimentScore'] )


if __name__ == "__main__":
    app.run(port=3000) 