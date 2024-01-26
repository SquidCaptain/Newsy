# Newsy
A RESTful API that shows top news stories to members

## Motivation
The motivation for this project came from needing a quick source of conversational topics that is relevant and engaging.
The AI classification implementation allows for a filter to be put up for topics users are intrested in.

## Technologies used
- Python
- Flask
  - Flask-SQLAlchemy
- AI
  - Google colab
  - Tensorflow Keras
  - BERT model
  - Kaggle's BBC News Classification Dataset

## External Dependencies
- newspaper3k
 


## Checklist

### Checklist (initial functionality)
- [x] Model compiled and trained
- [x] Model implemented into API
- [x] API routes finished
  - [x] Home
    - [x] Guide on API
  - [x] Login
    - [x] Database implemented
    - [x] JWT implemented
  - [x] Register
  - [x] News
    - [x] Request to NewsAPI implemented
    - [x] Parse article 
    - [x] Catagorize article
  - [x] Comment
    - [x] Create comments
    - [x] See self comment history

### Checklist (more) 
- [ ] See other people's comments on a specified article
- [ ] React frontend as an example frontend that uses the API
- [ ] Host API on a server or some platform (ex. AWS)
