"""
File: import.py
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

import re
import sys
import sqlite3
import xml.etree.ElementTree as ET

CATEGORIES_TABLE_NAME = 'categories'
CATEGORY_LISTING_TABLE_NAME = 'category_listing'
PAGES_TABLE_NAME = 'pages'

categories = []
category_id = 0

def print_help():
    print('Usage: python import.py <file> <db>')
    print('    file: XML file to import')
    print('    db:   SQLite database to create')

def add_category(category):
    global category_id
    if category == '':
        return
    category = re.sub(r'[\x00-\x1F\x7F-\x9F]', '', category)
    category = category.strip()
    if any(c['name'] == category for c in categories):
        return
    if '|' in category:
        return
    categories.append({
        'id': category_id,
        'name': category,
        'page_ids': [],
    })
    category_id += 1

def add_id_to_category(category, page_id):
    for cat in categories:
        if cat['name'] == category:
            if page_id not in cat['page_ids']:
                cat['page_ids'].append(page_id)

def extract_categories(page):
    categories = re.findall(r'\[\[Category:([^\]]+)\]\]', page['content'])
    return categories

def create_tables(db):
    db.execute(f'''
        CREATE TABLE IF NOT EXISTS {CATEGORIES_TABLE_NAME} (
            id INTEGER,
            name TEXT
        )
    ''')
    db.execute(f'''
        CREATE TABLE IF NOT EXISTS {CATEGORY_LISTING_TABLE_NAME} (
            category_id INTEGER,
            page_id INTEGER,
            FOREIGN KEY(category_id) REFERENCES {CATEGORIES_TABLE_NAME}(id),
            FOREIGN KEY(page_id) REFERENCES {PAGES_TABLE_NAME}(id)
        )
    ''')
    db.execute(f'''
        CREATE TABLE IF NOT EXISTS {PAGES_TABLE_NAME} (
            id INTEGER,
            title TEXT,
            content TEXT
        )
    ''')

def insert_categories(db):
    for category in categories:
        db.execute(f'INSERT INTO {CATEGORIES_TABLE_NAME} VALUES (?, ?)', (category['id'], category['name']))
        
    db.commit()

def insert_category_listing(db):
    for category in categories:
        for page_id in category['page_ids']:
            db.execute(f'INSERT INTO {CATEGORY_LISTING_TABLE_NAME} VALUES (?, ?)', (category['id'], page_id))
            
    db.commit()

def insert_page(db, page):
    db.execute(f'INSERT INTO {PAGES_TABLE_NAME} VALUES (?, ?, ?)', (page['id'], page['title'], page['content']))
    db.commit()

def main():
    if len(sys.argv) == 2:
        if sys.argv[1] == '--help' or sys.argv[1] == '-h':
            print_help()
            return

    if len(sys.argv) < 3:
        print('Error: not enough arguments.')
        print_help()
        return

    file_name = sys.argv[1] or ''
    db_name = sys.argv[2] or ''
    categories_read = 0
    pages_read = 0
    pages_saved = 0

    print('Creating database...')
    db = sqlite3.connect(db_name)
    print('Database created.')
    print('Creating tables...')
    create_tables(db)
    print('Tables created.')

    try:
        print('Loading XML file...')
        tree = ET.parse(file_name)
        root = tree.getroot()
        print('XML file loaded.')

        # Define the namespace
        ns = {'ns0': 'http://www.mediawiki.org/xml/export-0.11/'}

        for page in root.findall('.//ns0:page', ns):
            pages_read += 1
            page_ns = int(page.find('ns0:ns', ns).text)
            if page_ns != 0:
                continue
            pages_saved += 1
            page_id = int(page.find('ns0:id', ns).text)
            page_title = page.find('ns0:title', ns).text
            revision = page.find('ns0:revision', ns)
            if revision is not None:
                page_content = revision.find('ns0:text', ns).text
            else:
                page_content = ''

            page_categories = extract_categories({
                'id': page_id,
                'title': page_title,
                'content': page_content,
            })
            for category in page_categories:
                add_category(category)
                add_id_to_category(category, page_id)
                categories_read += 1
            insert_page(db, {
                'id': page_id,
                'title': page_title,
                'content': page_content,
            })

            print(f'\rPages read: {pages_read} (saved {pages_saved})', end='')
    
        print('\nFinalizing database...')
        print('Generating categories table...')
        insert_categories(db)
        print('Categories table generated.')
        print('Generating category listing table...')
        insert_category_listing(db)
        print('Category listing table generated.')
        print(f'Categories read: {len(categories)}')
    except Exception as e:
        print(e)
    finally:
        db.commit()
        db.close()

if __name__ == '__main__':
    main()