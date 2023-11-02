"""
File: transform.py
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
import string
import sqlite3
import sys
import nltk
from nltk.corpus import stopwords

def print_help():
    print("Usage: python transform.py <category> <dbfile> <outdir>")
    print("    category: category to transform")
    print("    dbfile:   database file to use")
    print("    outdir:   directory to write files to")

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

def strip_stopwords(text):
    stop_words = set(stopwords.words('english'))
    word_tokens = nltk.word_tokenize(text)
    filtered_sentence = [w for w in word_tokens if not w in stop_words]

    return ' '.join(filtered_sentence)

def strip_punctuation(text):
    return text.translate(str.maketrans('', '', string.punctuation))

def strip_numbers(text):
    return text.translate(str.maketrans('', '', string.digits))

def normalize_text(text):
    text = strip_stopwords(text)
    text = strip_punctuation(text)
    text = strip_numbers(text)

    return text

def get_and_normalize(db, page):
    content = get_page_content(db, page)
    content = normalize_text(content)

    return content

def main():
    if len(sys.argv) == 2:
        if sys.argv[1] == '--help' or sys.argv[1] == '-h':
            print_help()
            return

    if len(sys.argv) < 4:
        print('Error: not enough arguments.')
        print_help()
        return

    category = sys.argv[1]
    dbfile = sys.argv[2]
    outdir = sys.argv[3]

    if not category:
        print("Error: no category specified.")
        print_help()
        return

    if not dbfile:
        print("Error: no dbfile specified.")
        print_help()
        return

    if not os.path.exists(dbfile):
        print("Error: dbfile does not exist.")
        print_help()
        return

    if not outdir:
        print("Error: no outdir specified.")
        print_help()
        return

    if not category and not dbfile and not outdir:
        print("Usage: python transform.py <category> <dbfile> <outdir>")
        return

    print("Downloading nltk stopwords...")
    nltk.download('punkt')
    nltk.download('stopwords')
    print("Done.")

    if not os.path.exists(outdir):
        os.makedirs(outdir)

    print("Connecting to database...")
    db = sqlite3.connect(dbfile)
    cursor = db.cursor()
    print("Done.")
    print("Getting category members...")
    members = get_category_members(db, category)
    print("Done.")

    print("Normalizing and writing to files...")
    for member in members:
        title = member[0]
        content = get_and_normalize(db, title)

        # escape forward slashes
        title = title.replace('/', '_')
        with open(os.path.join(outdir, title), 'w') as f:
            f.write(content)

    db.close()
    print("Done.")

if __name__ == '__main__':
    main()