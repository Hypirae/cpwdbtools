import sys
import os
import sqlite3

def main():
    dbfile = sys.argv[1]

    if not dbfile:
        print("Error: no dbfile specified.")
        return

    if not os.path.exists(dbfile):
        print("Error: dbfile does not exist.")
        return

    db = sqlite3.connect(dbfile)
    cursor = db.cursor()

    # read the query from stdin ending on \n
    query = ""
    while True:
        line = sys.stdin.readline()
        if line == "\n":
            break
        query += line

    cursor.execute(query)
    result = cursor.fetchall()

    for row in result:
        for col in row:
            print(col, end="\t")
            
        print()

if __name__ == "__main__":
    main()