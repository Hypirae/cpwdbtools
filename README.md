# DB Tools
A set of python scripts for working with [Creepypasta Wiki](https://creepypasta.fandom.com) database dumps.

## Import
To import an extracted db dump into an SQLite3 database you can use `import.py` which imports all Mainspace (NS: 0) pages. It also extracts their categories, generates a table of categories found, and generates a `category_listing` table with correlations between every page and what category it is.

### Usage
```bash
~$ python3 import.py creepypasta_pages_current.xml creepypasta.db
```

## Transform
For creating machine learning models it is useful to be able to strip a selection of pages of common tokens. This tool will take a category and a directory name to put the processed files into. It will then read all category members from the database, clean their contents, and then save each page to its own text file in the dump directory.

### Usage
```bash
~$ python3 transform.py <category name> creepypasta.db category.d
```

## Learn (in progress)
This is a utility meant to create a machine learning model which can classify pages according to their categories.

## Classify (in progress)
This is a utility meant to classify a given page as what categories it is most like.