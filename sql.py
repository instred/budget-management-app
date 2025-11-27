import sqlite3
from datetime import datetime

DB_PATH = "users.db"


conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

table = ensure_expense_table(user_id, username)  # get the table name

cur.execute(f"ALTER TABLE {table} RENAME COLUMN timestamp TO date")

conn.commit()
conn.close()