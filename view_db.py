import sqlite3
import os

db_path = os.path.abspath("sketch_guess.db")
print("Database:", db_path)
print()

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print("Tables found:", [t[0] for t in tables])
print()

for (table,) in tables:
    print("=" * 50)
    print("  TABLE:", table)
    print("=" * 50)
    cursor.execute("PRAGMA table_info({})".format(table))
    cols = [c[1] for c in cursor.fetchall()]
    print("  Columns:", cols)
    cursor.execute("SELECT * FROM {}".format(table))
    rows = cursor.fetchall()
    if rows:
        for row in rows:
            print(" ", dict(zip(cols, row)))
    else:
        print("  (no data yet)")
    print()

conn.close()
