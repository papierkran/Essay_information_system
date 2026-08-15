import sqlite3
conn = sqlite3.connect('app/essay_system.db')
cur = conn.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
print("tables:", cur.fetchall())
try:
    cur.execute("SELECT id, name, deleted_at FROM course")
    for r in cur.fetchall():
        print(r)
except Exception as e:
    print("course err:", e)
