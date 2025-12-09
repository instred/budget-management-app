import os
import sys
import pyodbc
import bcrypt
from decimal import Decimal
from dotenv import load_dotenv

load_dotenv()

DRIVER = '{ODBC Driver 18 for SQL Server}'
SQL_SERVER = os.getenv('AZURE_SQL_SERVER')
SQL_DATABASE = os.getenv('AZURE_SQL_DB')
SQL_USERNAME = os.getenv('AZURE_SQL_UID')
SQL_PASSWORD = os.getenv('AZURE_SQL_PWD')

CONNECTION_STRING = (
    f"DRIVER={DRIVER};"
    f"SERVER=tcp:{SQL_SERVER},1433;"
    f"DATABASE={SQL_DATABASE};"
    f"UID={SQL_USERNAME};"
    f"PWD={SQL_PASSWORD};"
    "Encrypt=yes;"
    "TrustServerCertificate=no;"
    "Connection Timeout=30;"
)


def _get_connection():
    """Creates a secure Azure SQL connection."""
    if not all([SQL_SERVER, SQL_DATABASE, SQL_USERNAME, SQL_PASSWORD]):
        print("Credentials not loaded properly")
        sys.exit(1)
    try:
        return pyodbc.connect(CONNECTION_STRING)
    except pyodbc.Error as ex:
        sqlstate = ex.args[0]
        if '28000' in sqlstate:
            print("Authentication error (28000).")
        elif '08001' in sqlstate:
            print("Connection error (08001).")
        else:
            print(f"Unknown connection error: {ex}")
        raise


def init_database():
    """Ensures that all required SQL tables exist."""
    conn = None
    try:
        conn = _get_connection()
        cur = conn.cursor()

        cur.execute("""
            IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Users' AND xtype='U')
            CREATE TABLE Users (
                UserID INT IDENTITY(1,1) PRIMARY KEY,
                Username NVARCHAR(100) UNIQUE NOT NULL,
                PasswordHash VARCHAR(100) NOT NULL
            )
        """)

        cur.execute("""
            IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='UserSettings' AND xtype='U')
            CREATE TABLE UserSettings (
                UserID INT PRIMARY KEY,
                Currency NVARCHAR(10) DEFAULT 'PLN',
                Theme NVARCHAR(50) DEFAULT 'System',
                Budget DECIMAL(18, 2) DEFAULT 0.00
            )
        """)

        cur.execute("""
            IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Expenses' AND xtype='U')
            CREATE TABLE Expenses (
                ExpenseID INT IDENTITY(1,1) PRIMARY KEY,
                UserID INT NOT NULL,
                ExpenseName NVARCHAR(255) NOT NULL,
                Category NVARCHAR(100) NOT NULL,
                Amount DECIMAL(18, 2) NOT NULL,
                ExpenseDate DATE NOT NULL
            )
        """)

        conn.commit()
    except pyodbc.Error as ex:
        print(f"Error, cannot initialize the schema: {ex}")
        sys.exit(1)
    finally:
        if conn:
            conn.close()


# ------------ USER MANAGEMENT ------------

def create_user(username, password):
    """Creates a new user and stores default settings."""
    password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    conn = None
    try:
        conn = _get_connection()
        cur = conn.cursor()

        cur.execute(
            """
            INSERT INTO Users (Username, PasswordHash)
            OUTPUT INSERTED.UserID
            VALUES (?, ?)
            """,
            (username, password_hash)
        )
        user_id = cur.fetchone()[0]

        cur.execute(
            "INSERT INTO UserSettings (UserID, Currency, Theme, Budget) VALUES (?, ?, ?, ?)",
            (user_id, 'PLN', 'Dark', Decimal('0.00'))
        )

        conn.commit()
        return True
    except pyodbc.IntegrityError:
        return False
    except pyodbc.Error as ex:
        print(f"Error, cannot create new user: {ex}")
        return False
    finally:
        if conn:
            conn.close()


def get_user(username):
    """Returns user data including hashed password."""
    conn = None
    try:
        conn = _get_connection()
        cur = conn.cursor()
        cur.execute("SELECT UserID, Username, PasswordHash FROM Users WHERE Username=?", (username,))
        row = cur.fetchone()
        if row:
            return {"id": row[0], "username": row[1], "password_hash": row[2]}
        return None
    except pyodbc.Error as ex:
        print(f"Error, cannot fetch user: {ex}")
        return None
    finally:
        if conn:
            conn.close()


# ------------ EXPENSE MANAGEMENT ------------

def insert_expense(user_id, title, category, amount, date):
    """Inserts a new expense."""
    conn = None
    try:
        conn = _get_connection()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO Expenses (UserID, ExpenseName, Category, Amount, ExpenseDate)
            VALUES (?, ?, ?, ?, ?)
            """,
            (user_id, title, category, Decimal(str(amount)), date)
        )
        conn.commit()
        return True
    except pyodbc.Error as ex:
        print(f"Error during expenses adding: {ex}")
        return False
    finally:
        if conn:
            conn.close()


def fetch_expenses(user_id, limit=None):
    """Fetches user expenses sorted by newest first."""
    conn = None
    try:
        conn = _get_connection()
        cur = conn.cursor()

        sql = """
        SELECT ExpenseID, ExpenseName, Category, Amount, ExpenseDate
        FROM Expenses
        WHERE UserID = ?
        ORDER BY ExpenseDate DESC, ExpenseID DESC
        """

        if limit:
            sql += f" OFFSET 0 ROWS FETCH NEXT {int(limit)} ROWS ONLY"

        cur.execute(sql, (user_id,))
        rows = cur.fetchall()

        return [
            (r[0], r[1], r[2], float(r[3]), r[4].strftime('%Y-%m-%d'))
            for r in rows
        ]
    except pyodbc.Error as ex:
        print(f"Error during expenses fetching: {ex}")
        return []
    finally:
        if conn:
            conn.close()


def get_total_amount(user_id):
    """Returns total expense amount."""
    conn = None
    try:
        conn = _get_connection()
        cur = conn.cursor()
        cur.execute("SELECT SUM(Amount) FROM Expenses WHERE UserID = ?", (user_id,))
        result = cur.fetchone()[0]
        return float(result) if result else 0.0
    except pyodbc.Error as ex:
        print(f"Error during expenses summing: {ex}")
        return 0.0
    finally:
        if conn:
            conn.close()


def get_total_amount_for_month(user_id, year, month):
    """Returns total expenses for a specific month."""
    conn = None
    try:
        conn = _get_connection()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT SUM(Amount)
            FROM Expenses
            WHERE UserID = ?
              AND YEAR(ExpenseDate) = ?
              AND MONTH(ExpenseDate) = ?
            """,
            (user_id, year, month)
        )
        result = cur.fetchone()[0]
        return float(result) if result else 0.0
    except pyodbc.Error as ex:
        print(f"Error during monthly summing: {ex}")
        return 0.0
    finally:
        if conn:
            conn.close()


def delete_expense(expense_id, user_id):
    """Deletes a specific user expense."""
    conn = None
    try:
        conn = _get_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM Expenses WHERE ExpenseID = ? AND UserID = ?", (expense_id, user_id))
        conn.commit()
        return cur.rowcount > 0
    except pyodbc.Error as ex:
        print(f"Error during expense deletion: {ex}")
        return False
    finally:
        if conn:
            conn.close()


def delete_all_expenses(user_id):
    """Deletes all expenses for a user."""
    conn = None
    try:
        conn = _get_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM Expenses WHERE UserID = ?", (user_id,))
        conn.commit()
        return True
    except pyodbc.Error as ex:
        print(f"Error during expenses deletion: {ex}")
        return False
    finally:
        if conn:
            conn.close()


# ------------ USER SETTINGS ------------

def load_user_settings(user_id):
    """Loads all user settings."""
    conn = None
    try:
        conn = _get_connection()
        cur = conn.cursor()
        cur.execute("SELECT Currency, Theme, Budget FROM UserSettings WHERE UserID = ?", (user_id,))
        row = cur.fetchone()
        if not row:
            return {}
        return {
            "currency": row[0],
            "theme": row[1],
            "budget": float(row[2]) if row[2] is not None else 0.0
        }
    except pyodbc.Error as ex:
        print(f"Error during settings load: {ex}")
        return {}
    finally:
        if conn:
            conn.close()


def save_user_setting(user_id, setting_name, setting_value):
    """Saves a single user setting (currency/theme/budget)."""
    conn = None
    try:
        conn = _get_connection()
        cur = conn.cursor()

        if setting_name.lower() == 'budget':
            setting_value = Decimal(str(setting_value))

        sql = f"UPDATE UserSettings SET {setting_name} = ? WHERE UserID = ?"
        cur.execute(sql, (setting_value, user_id))
        conn.commit()
        return True
    except pyodbc.Error as ex:
        print(f"Error during settings saving: {ex}")
        return False
    finally:
        if conn:
            conn.close()
