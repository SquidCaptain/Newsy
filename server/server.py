import hashlib
import jwt
import requests
import datetime

from flask import Flask, jsonify, request, make_response
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt

import numpy as np
import tensorflow as tf
import keras

import tensorflow_hub as hub
import tensorflow_text as text

from newspaper import Article

from functools import wraps

from config import Config

app = Flask(__name__)
app.config.from_object(Config)
CORS(app)
bcrypt = Bcrypt(app)
db = SQLAlchemy(app)
last_news_query_time = datetime.datetime.utcnow()
last_news_result = None
model = keras.models.load_model("model.keras", custom_objects={"KerasLayer": hub.KerasLayer})

# Model(s) for SQLAlchemy to create and manage database ----

# User table
# pimary key: id
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(64), nullable=False)
    comment = db.relationship("Comments", backref="user", lazy=True)

# Comments table used to store comments on news from user
class Comments(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    url = db.Column("url", db.Text, nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now(datetime.UTC))
    comment = db.Column("comment", db.Text)
# Models end

# Functions ----------------------------------------

# token_requrired(f) a decorator for routes that need login
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if "x-access-token" in request.headers:
            token = request.headers["x-access-token"]
        if not token:
            return jsonify({"message": "Token required."}), 401
        try:
            data = jwt.decode(token, app.config["SECRET_KEY"])
            current_user = User.query.filter_by(username=data["username"]).first()
        except:
            return jsonify({"message": "Token is invalid"}), 401
        return f(current_user, *args, **kwargs)
    return decorated

# create_db() creates the database
def create_db(self):
    db.create_all()

# decode_prob()
def decode_prob(prob):
    best_index = 0
    best_prob = 0
    for i in range(0, 5):
        if prob[0][i] > best_prob:
             best_index = i
             best_prob = prob[0][i]
    if best_index == 0:
        return "sport"
    elif best_index == 1:
        return "tech"
    elif best_index == 2:
        return "entertainment"
    elif best_index == 3:
        return "politics"
    elif best_index == 4:
        return "business"

# get_news() get news from the Newsapi API and return the response as a JSON object
def get_news(self):
    url = (
        'https://newsapi.org/v2/top-headlines?'
        'country=ca&'
        'sortBy=popularity&'
        'apiKey=35da19d5a4914f129e92db072d4b869f')
    datetime.datetime.now(datetime.UTC)
    if (datetime - last_news_query_time) > datetime.timedelta(hours=1):
        response = jsonify(requests.get(url))
        if response["status"] == "ok":
            articles = []
            for i in response["articles"]:
                article = Article(i["url"])
                article.download()
                article.parse()
                articles.append(jsonify({"url": i["url"], "category": decode_prob(model.predict([article.txt])),"title": article.title}))
        last_news_result = jsonify({
            "totalResults": response["totalResults"],
            "articles": articles
        })
    
    return last_news_result

# validate_password(password) returns true if password is in a valid format
def validate_password(self, password):
    if password is not str or len(password) != 64:
        return False
    return True
 

# validate_username(username) returns true if username is not already in database
# Behaviour: String -> Bool
def validate_username(self, username):
    if username is not str or len(username) > 20:
        return False
    existing_user_username = User.query.filter_by(username=username).first()
    if existing_user_username:
        return False
    return True
# Functions end


# API endpoints ----------------------------------------
# Home API Route
# Enpoint for getting instructions
@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "result": "Success",
        "message": "Hello, this is the a RESTful API that brings you news",
        "username": "length of username must be 20 characters or less.",
        "password": "passwords should be hashed with sha256 hash function prior to sending as a string.",
        "token": "put token in header under x-access-token",
        "endpoints": {
            "register": "to register",
            "login": "to login",
            "news": "to see articles",
            "comment": {
                "GET": "shows comments made by current user",
                "POST": "posts a new comment"
            },
        },
        "news": {
            "category": "Business, Entertainment, Politics, Sport, Tech"
        },
        "comment": {
            "url": "url of news article",
            "comment": "your comment"
        },
        "register": {
            "username": "username",
            "password": "password"
        }
    })

# Register API Route
# Enpoint to register
@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    
    username = data["username"]
    password = data["password"]

    if validate_username(username) and validate_password(password):
        hashed_password = bcrypt.generate_password_hash(password, 10)
        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

    return jsonify({
        "result": "Success"
    })

# Login API Route
# Enpoint to login
@app.route("/login", methods=["GET"])
def login():
    auth = request.authorization
    if not auth or not auth.username or not auth.password:
        return make_response("Could not verify!", 401, {"WWW-Authenticate": "Basic realm=\"Login Required\""})
    
    username =  auth.username
    password = auth.password
    
    if validate_password(password):
        user = User.query.filter_by(username=username).first()
        if user:
            if bcrypt.check_password_hash(user.password, password):
                token = jwt.encode({"user": username, "exp": datetime.datetime.now(datetime.UTC) + datetime.timedelta(hours=24)}, app.config["SECRET_KEY"])
                return jsonify({"token": token.decode("utf-8")})
    return make_response("Could not verify!", 401, {"WWW-Authenticate": "Basic realm=\"Login Required\""})

# News API Route
# Endpoint to get a response given a prompt
@app.route("/news", methods=["GET"])
@token_required
def news(current_user):
    data = request.get_json()
    reply = "this is a temp reply"
    reply = get_news()
    if reply:
        return jsonify({
            "result": "Success",
            "reply": reply
        })
    return make_response("Something went wrong!", 501)

# Logs API Route
# Endpoint to get comments for logged in user
@app.route("/comment", methods=["GET", "POST"])
@token_required
def comment(current_user):
    if request.method == "GET":
        # comments = Comments.query.filter_by(user_id=current_user.id)
        comments = db.session.execute(db.select(Comments).filter_by(user_id=current_user.id).order_by(Comments.date)).scalars().all()
        results = []
        for i in comments:
            results.append(jsonify({"url" : i.url, "comment" : i.comment, "date" : i.date}))
        return jsonify({
            "result": "Success",
            "comments": results
        })
    elif request.method == "POST":
        data = request.get_json()
        if data["comment"] and data["url"]:
            new_comment = Comments(user_id=current_user.id, url=data["url"], comment=data["comment"])
            db.session.add(new_comment)
            db.session.commit()
        else:
            return jsonify({"message": "Invalid format"}), 401


# API endpoints end

# main
if __name__=="__main__":
    app.run(debug=True)