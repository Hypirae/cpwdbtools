"""
File: learn.py
Author: Hypirae 2023
Version: 1.0.0

License: MIT
MIT License

Copyright (c) 2023 Hypirae

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import sys
import os
import sqlite3
import nltk
import pickle
import numpy as np
import tensorflow as tf
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Embedding, GlobalAveragePooling1D
from keras.regularizers import l2
from keras.layers import Dropout
from keras.callbacks import EarlyStopping
from transform import get_and_normalize

# turn off tensorflow warnings
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

# number of words to use in the tokenizer
NUM_WORDS = 60000

def read_random_pages(db, count):
    db = db.execute('''
    SELECT title
    FROM pages
    ORDER BY RANDOM()
    LIMIT ?;
    ''', [count])

    return db.fetchall()

def get_categories_for_page(db, page):
    db = db.execute('''
    SELECT name
    FROM categories
    JOIN category_listing ON category_listing.category_id = categories.id
    WHERE category_listing.page_id = (SELECT id FROM pages WHERE title LIKE ?);
    ''', [page])

    return db.fetchall()

def to_classifier_format(db, page_title_content, category):
    texts = []
    labels = []

    for page, content in page_title_content:
        categories = get_categories_for_page(db, page)
        words = nltk.word_tokenize(content)
        texts.append(' '.join(words))
        
        if category in categories:
            labels.append(1)
        else:
            labels.append(0)

    return texts, labels

def train_classifier(texts, labels):
    tokenizer = Tokenizer(num_words=NUM_WORDS, oov_token="<OOV>")
    tokenizer.fit_on_texts(texts)
    sequences = tokenizer.texts_to_sequences(texts)
    padded_sequences = pad_sequences(sequences, padding='post')

    model = Sequential([
    Embedding(NUM_WORDS, 16, input_length=padded_sequences.shape[1]),
    GlobalAveragePooling1D(),
    Dense(16, activation='relu', kernel_regularizer=l2(0.001)),  # L2 regularization
    Dropout(0.5),  # Dropout layer
    Dense(1, activation='sigmoid')
])

    # Early stopping
    early_stopping = EarlyStopping(monitor='val_loss', patience=3)

    # Compile the model
    model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
    
    # Train the model
    labels = np.array(labels)  # Convert labels to numpy array
    model.fit(padded_sequences, labels, epochs=50, validation_split=0.2, callbacks=[early_stopping])

    return tokenizer, model

def test_classifier(model, tokenizer, texts, labels, max_length):
    sequences = tokenizer.texts_to_sequences(texts)
    padded_sequences = pad_sequences(sequences, maxlen=max_length, padding='post')
    labels = np.array(labels)  # Convert labels to numpy array

    loss, accuracy = model.evaluate(padded_sequences, labels)

    print(f"Loss: {loss}. Accuracy: {accuracy}")

def main():
    category = sys.argv[1]
    indir = sys.argv[2]
    dbfile = sys.argv[3]
    pages = []
    page_title_content = []
    db = sqlite3.connect(dbfile)
    cursor = db.cursor()

    if not category:
        print("Error: no category specified.")
        return

    if not indir:
        print("Error: no indir specified.")
        return

    if not dbfile:
        print("Error: no dbfile specified.")
        return

    print("Reading page names...")
    for filename in os.listdir(indir):
        pages.append(filename)
    
    print("Reading pages...")
    for page in pages:
        with open(os.path.join(indir, page), 'r') as f:
            page_title_content.append((page, f.read()))

    # unescape forward slashes
    for i in range(len(page_title_content)):
        page = page_title_content[i]
        page_title_content[i] = (page[0].replace('_', '/'), page[1])

    # read 1000 random pages from the database
    print("Reading random pages...")
    random_pages = read_random_pages(cursor, 1000)

    print("Normalizing random pages... ")
    page_i = 0
    for page in random_pages:
        page_i += 1
        title = page[0]
        content = get_and_normalize(cursor, title)
        page_title_content.append((title, content))
        print("\rPages normalized: " + str(page_i), end="")
    
    print()

    # shuffle the pages
    print("Shuffling pages...")
    np.random.shuffle(page_title_content)

    # split the pages into training and testing sets
    training_pages = page_title_content[:800]
    testing_pages = page_title_content[800:]

    # train the classifier
    print("Training classifier... ", end='')
    texts, labels = to_classifier_format(db, training_pages, category)
    tokenizer, classifier = train_classifier(texts, labels)
    print("Done.")

    print("Done.")
    print("Saving classifier...")
    classifier.save(category + '.keras')
    print("Done.")

    # determine maximum sequence length
    max_length = 0
    for page, content in page_title_content:
        words = nltk.word_tokenize(content)
        if len(words) > max_length:
            max_length = len(words)

    print("Maximum sequence length: " + str(max_length))
    print("Saving tokenizer... ", end="")
    pickle_filename = category + '.' + str(max_length) + '.pickle'
    print(pickle_filename)
    with open(pickle_filename, 'wb') as f:
        pickle.dump(tokenizer, f)

        # test the classifier
        print("Testing classifier... ", end="")
        classifier = tf.keras.models.load_model(category + '.keras')
        with open(pickle_filename, 'rb') as fi:
            tokenizer = pickle.load(fi)
            texts, labels = to_classifier_format(db, testing_pages, category)
            test_classifier(classifier, tokenizer, texts, labels, max_length)

        print("Done.")

    db.close()

if __name__ == '__main__':
    main()