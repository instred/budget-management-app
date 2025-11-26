import sqlite3
from datetime import datetime

DB_PATH = "users.db"


# ------------------------------------------------------------
# Helper: Connect to DB
# ------------------------------------------------------------
def _connect():
    return sqlite3.connect(DB_PATH)


# ------------------------------------------------------------
# USER MANAGEMENT
# ------------------------------------------------------------
def create_user(username, password):
    conn = _connect()
    cur = conn.cursor()

    try:
        cur.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (username, password)
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        # Username already exists
        return False
    finally:
        conn.close()


def get_user(username):
    conn = _connect()
    cur = conn.cursor()

    cur.execute("SELECT id, username, password FROM users WHERE username=?", (username,))
    result = cur.fetchone()

    conn.close()

    if result:
        return {"id": result[0], "username": result[1], "password": result[2]}
    return None


# ------------------------------------------------------------
# EXPENSE TABLE CREATION (per user)
# ------------------------------------------------------------
def ensure_expense_table(user_id, username):
    """
    Each user gets their own expense table.
    """
    table_name = f"expenses_{user_id}_{username}"

    conn = _connect()
    cur = conn.cursor()

    cur.execute(f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            category TEXT,
            amount REAL,
            timestamp TEXT
        )
    """)

    conn.commit()
    conn.close()

    return table_name


# ------------------------------------------------------------
# INSERT EXPENSE
# ------------------------------------------------------------
def insert_expense(user_id, username, title, category, amount, timestamp=None):
    """
    Insert an expense for a user.
    
    Args:
        user_id (int): User ID
        username (str): Username
        title (str): Expense title
        category (str): Expense category
        amount (float): Expense amount
        timestamp (str or None): Optional timestamp in 'YYYY-MM-DD' format
    """
    table = ensure_expense_table(user_id, username)

    if timestamp is None:
        timestamp = datetime.now().strftime("%Y-%m-%d")
    
    conn = _connect()
    cur = conn.cursor()

    cur.execute(
        f"INSERT INTO {table} (title, category, amount, timestamp) VALUES (?, ?, ?, ?)",
        (title, category, amount, timestamp)
    )

    conn.commit()
    conn.close()


# ------------------------------------------------------------
# DELETE EXPENSE
# ------------------------------------------------------------
def delete_expense(user_id, username, expense_id):
    table = ensure_expense_table(user_id, username)

    conn = _connect()
    cur = conn.cursor()

    cur.execute(f"DELETE FROM {table} WHERE id=?", (expense_id,))

    conn.commit()
    conn.close()


# ------------------------------------------------------------
# FETCH EXPENSES (optionally limit)
# ------------------------------------------------------------
def fetch_expenses(user_id, username, limit=None):
    table = ensure_expense_table(user_id, username)

    conn = _connect()
    cur = conn.cursor()

    if limit:
        cur.execute(
            f"SELECT id, title, category, amount, timestamp FROM {table} ORDER BY id DESC LIMIT ?",
            (limit,)
        )
    else:
        cur.execute(
            f"SELECT id, title, category, amount, timestamp FROM {table} ORDER BY id DESC"
        )

    rows = cur.fetchall()
    conn.close()
    return rows

def get_total_amount(user_id, username):
    table = ensure_expense_table(user_id, username)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(f"SELECT SUM(amount) FROM {table}")
    result = cursor.fetchone()[0]

    conn.close()
    return result if result else 0