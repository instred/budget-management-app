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
            date TEXT
        )
    """)

    conn.commit()
    conn.close()

    return table_name


def ensure_user_settings(user_id):
    conn = _connect()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS user_settings (
            user_id INTEGER PRIMARY KEY,
            currency TEXT DEFAULT 'USD',
            theme TEXT DEFAULT 'System'
        )
    """)
    # Insert default row if not exists
    cur.execute("INSERT OR IGNORE INTO user_settings (user_id) VALUES (?)", (user_id,))
    conn.commit()
    conn.close()


# ------------------------------------------------------------
# INSERT EXPENSE
# ------------------------------------------------------------
def insert_expense(user_id, username, title, category, amount, date=None):
    """
    Insert an expense for a user.
    
    Args:
        user_id (int): User ID
        username (str): Username
        title (str): Expense title
        category (str): Expense category
        amount (float): Expense amount
        date (str or None): 'YYYY-MM-DD' 
    """
    table = ensure_expense_table(user_id, username)

    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")
    
    conn = _connect()
    cur = conn.cursor()

    cur.execute(
        f"INSERT INTO {table} (title, category, amount, date) VALUES (?, ?, ?, ?)",
        (title, category, amount, date)
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
            f"SELECT id, title, category, amount, date FROM {table} ORDER BY id DESC LIMIT ?",
            (limit,)
        )
    else:
        cur.execute(
            f"SELECT id, title, category, amount, date FROM {table} ORDER BY id DESC"
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

def delete_all_expenses(self):
    cursor = self.conn.cursor()
    cursor.execute("DELETE FROM expenses")
    self.conn.commit()

def load_user_settings(user_id):
    ensure_user_settings(user_id)
    conn = _connect()
    cur = conn.cursor()
    cur.execute("SELECT currency, theme FROM user_settings WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    conn.close()
    if row:
        return {"currency": row[0], "theme": row[1]}
    return {"currency": "USD", "theme": "System"}



def save_user_setting(user_id, key, value):
    ensure_user_settings(user_id)
    conn = _connect()
    cur = conn.cursor()
    cur.execute(f"UPDATE user_settings SET {key} = ? WHERE user_id = ?", (value, user_id))
    conn.commit()
    conn.close()