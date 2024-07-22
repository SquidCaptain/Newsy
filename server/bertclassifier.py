# -*- coding: utf-8 -*-
"""BERTClassifier.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1n0mrs8uq4Vgexq05OzuT4aELvQimS7VW
"""

!pip install tensorflow_text
from google.colab import files
import tensorflow_hub as hub
import tensorflow_text as text

preprocess_url = "https://kaggle.com/models/tensorflow/bert/frameworks/TensorFlow2/variations/en-uncased-preprocess/versions/3"
encoder_url = "https://kaggle.com/models/tensorflow/bert/frameworks/TensorFlow2/variations/en-uncased-l-12-h-768-a-12/versions/3"

#preprocess_url = "https://tfhub.dev/tensorflow/bert_en_uncased_preprocess/3"
#encoder_url = "https://tfhub.dev/tensorflow/bert_en_uncased_L-12_H-768_A-12/4"

bert_preprocess_model = hub.KerasLayer(preprocess_url)

text_test = ['nice movie indeed','I love python programming']
text_preprocessed = bert_preprocess_model(text_test)
text_preprocessed.keys()

bert_model = hub.KerasLayer(encoder_url)

bert_results = bert_model(text_preprocessed)

bert_results.keys()

#from google.colab import files
#files.upload()

#!unzip archive.zip

import pandas as pd
import os
folders = ["business","entertainment","politics","sport","tech"]
if os.getcwd() != "/content/bbc":
  os.chdir("bbc")

f_text = []
f_cat = []

for i in folders:
    files = os.listdir(i)
    for text_file in files:
        file_path = i + "/" +text_file
        #print ("reading file:", file_path)
        with open(file_path,encoding = 'unicode_escape') as f:
            data = f.readlines()
        data = ' '.join(data)
        f_text.append(data)
        f_cat.append(i)

data = {'news': f_text, 'category': f_cat}
df = pd.DataFrame(data)

df.head(5)

df.groupby('category').category.count()

df.shape

from sklearn.model_selection import train_test_split

train_df, test_df = train_test_split(df, test_size=0.2, random_state=22, stratify=df["category"])

train_df, val_df = train_test_split(train_df, test_size=0.2, random_state=22, stratify=train_df["category"])

train_news=train_df["news"]
train_category=train_df["category"]

val_news=val_df["news"]
val_category=val_df["category"]

test_news=test_df["news"]
test_category=test_df["category"]

from keras.utils import to_categorical

def encode_sentiments(polarity):
    if polarity == 'sport':
        return 0
    elif polarity == 'tech':
        return 1
    elif polarity == 'entertainment':
        return 2
    elif polarity == 'politics':
        return 3
    elif polarity == 'business':
        return 4

train_category = train_category.apply(encode_sentiments)
test_category = test_category.apply(encode_sentiments)
val_category = val_category.apply(encode_sentiments)

train_category = to_categorical(train_category, num_classes=5)
val_category = to_categorical(val_category, num_classes=5)
test_category = to_categorical(test_category, num_classes=5)

def get_sentence_embeding(sentences):
  preprocessed_text = bert_preprocess_model(sentences)
  return bert_model(preprocessed_text)['pooled_output']

print(train_news[0])

print(get_sentence_embeding([train_news[0], train_news[1]]))

#train_text_embeddings = get_sentence_embeding(train_news)

#test_text_embeddings = get_sentence_embeding(test_news)

#val_text_embeddings = get_sentence_embeding(train_news)

import tensorflow as tf

from tensorflow import keras
#from keras import layers
'''
def get_model(input_shape=(3, 768), hidden_dim_one=16, hidden_dim_two=32, num_classes=5):
    inputs = keras.Input(shape=input_shape)
    x = layers.Bidirectional(layers.LSTM(128, return_sequences=True))(inputs)
    x = layers.Bidirectional(layers.LSTM(64, return_sequences=True))(x)
    x = layers.Flatten()(x)
    x = layers.Dropout(0.5)(x)
    outputs = layers.Dense(5, activation="softmax")(x)

    model = keras.Model(inputs, outputs)
    model.compile(optimizer="adam",
                  loss="categorical_crossentropy",
                  metrics=["accuracy"])
    return model'''

inputs = keras.layers.Input(shape=(), dtype=tf.string, name='text')
preprocessed_text = bert_preprocess_model(inputs)
x = bert_model(preprocessed_text)
#x = layers.Bidirectional(layers.LSTM(128, return_sequences=True))(x["sequence_output"])
#x = layers.Bidirectional(layers.LSTM(64, return_sequences=True))(x)
x = layers.Flatten()(x["pooled_output"])
x = keras.layers.Dropout(0.5)(x)
outputs = keras.layers.Dense(5, activation="softmax")(x)

model = keras.Model(inputs=[inputs], outputs=[outputs])
model.compile(optimizer="adam",
  loss="categorical_crossentropy",
  metrics=["accuracy"])

model.summary()

model.fit(
    train_news,
    train_category,
    epochs=20,
    batch_size=128,
    validation_data=(val_news, val_category),
    validation_steps=1
)

!ls

keras.models.save_model(model, "model.keras")

#files.download("model.keras")

model.evaluate(test_news, test_category)

#os.chdir("../")
!rm model.keras

!ls

loaded_model = keras.models.load_model("model.keras", custom_objects={"KerasLayer": hub.KerasLayer})





