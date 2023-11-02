"""
File: classify.py
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

import os
import sys
import sqlite3
import pickle
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences
from transform import get_and_normalize

def get_category_members(db, category):
    db = db.execute('''
    SELECT title
    FROM pages
    JOIN category_listing ON category_listing.page_id = pages.id
    WHERE category_listing.category_id = (SELECT id FROM categories WHERE name LIKE ?);
    ''', [category])

    return db.fetchall()

def get_page_content(db, page):
    db = db.execute('''
    SELECT content
    FROM pages
    WHERE title LIKE ?;
    ''', [page])

    return db.fetchone()[0]

def main():
    category = sys.argv[1]
    certainthreshold = float(sys.argv[2])
    modelfile = sys.argv[3]
    tokenizerfile = sys.argv[4]
    dbfile = sys.argv[5]

    if not category:
        print("Error: no category specified.")
        return

    if not certainthreshold:
        print("Error: no certainthreshold specified.")
        return

    if not modelfile:
        print("Error: no modelfile specified.")
        return

    if not tokenizerfile:
        print("Error: no tokenizerfile specified.")
        return

    if not dbfile:
        print("Error: no dbfile specified.")
        return

    if not category and not certainthreshold and not modelfile and not tokenizerfile and not dbfile:
        print("Usage: python classify.py <category> <certainty> <modelfile> <tokenizerfile> <dbfile>")
        return

    if not os.path.exists(modelfile):
        print("Error: modelfile does not exist.")
        return

    if not os.path.exists(dbfile):
        print("Error: dbfile does not exist.")
        return

    db = sqlite3.connect(dbfile)
    cursor = db.cursor()
    members = get_category_members(db, category)
    max_length = int(tokenizerfile.split('.')[1])


    print("Loading model... ", end="")
    model = load_model(modelfile)
    print("Done.")

    print("Loading tokenizer... ", end="")
    tokenizer = None
    with open(tokenizerfile, 'rb') as f:
        tokenizer = pickle.load(f)

    print("Done.")

    # get and normalize the content
    print("Getting and normalizing content...")
    page_title_content = []
    for member in members:
        title = member[0]
        content = get_and_normalize(cursor, title)
        page_title_content.append((title, content))
        print("\rPages normalized: " + str(len(page_title_content)), end="")

    print()
    print("Done.")

    # tokenize the content
    print("Tokenizing content... ", end="")
    texts = []
    for page in page_title_content:
        texts.append(page[1])

    sequences = tokenizer.texts_to_sequences(texts)
    data = pad_sequences(sequences, maxlen=max_length)
    print("Done.")

    # classify the content
    print("Classifying content...", end="")
    predictions = model.predict(data)
    print("Done.")

    # print the results
    print("Results:")
    results = []
    for i in range(len(page_title_content)):
        page = page_title_content[i]
        prediction = predictions[i]
        certainty = prediction[0]

        # only add those with a good probability of being in the category
        

        results.append((page[0], certainty))

    results.sort(key=lambda x: x[1])
    for result in results:
        print(result[0] + " - " + str(result[1]))
            
    db.close()
    print("Done.")

if __name__ == "__main__":
    main()