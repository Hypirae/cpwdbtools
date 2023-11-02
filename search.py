"""
File: search.py
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
import argparse

def search_all(db, query):
    db = db.execute('''
    SELECT title
    FROM pages
    WHERE content LIKE ?;
    ''', [query])

    return db.fetchall()

def search_category(db, category, query):
    db = db.execute('''
    SELECT title
    FROM pages
    JOIN category_listing ON category_listing.page_id = pages.id
    WHERE category_listing.category_id = (SELECT id FROM categories WHERE name LIKE ?)
    AND content LIKE ?;
    ''', [category, query])

    return db.fetchall()

def main():
    # set up argparse
    parser = argparse.ArgumentParser(description='Search the database.')
    parser.add_argument('db', help='database file to use')
    parser.add_argument('query', help='query to search for')
    parser.add_argument('--category', default=None, help='optional category to search within')

    # parse arguments
    args = parser.parse_args()

    if not args.db:
        print("Error: no database file specified.")
        sys.exit(1)

    if not args.query:
        print("Error: no query specified.")
        sys.exit(1)

    # open database
    db = sqlite3.connect(args.db)
    cursor = db.cursor()

    if args.category:
        results = search_category(cursor, args.category, args.query)
    else:
        results = search_all(cursor, args.query)

    # print results
    for result in results:
        print(result[0])

if __name__ == '__main__':
    main()