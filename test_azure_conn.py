import pyodbc
import bcrypt
import os
from dotenv import load_dotenv

# =======================================================
# INSTALACJA
# W terminalu uruchom: pip install pyodbc bcrypt
# Pamiętaj o sterowniku ODBC Driver 18 for SQL Server
# =======================================================

# -------------------------------------------------------
# KONFIGURACJA POŁĄCZENIA
# Zmienne środowiskowe do bezpiecznego przechowywania danych
# Ustaw je w swoim systemie (np. w pliku .env i ładuj go)
# -------------------------------------------------------
DRIVER = '{ODBC Driver 18 for SQL Server}' 

# Odczyt danych z opcją domyślnych (PLACEHOLDERY!)
# Zmień "PLACEHOLDER_..." na swoje rzeczywiste dane w systemie/pliku .env
load_dotenv()

SQL_SERVER = os.getenv('AZURE_SQL_SERVER')
SQL_DATABASE = os.getenv('AZURE_SQL_DB')
SQL_USERNAME = os.getenv('AZURE_SQL_UID') 
SQL_PASSWORD = os.getenv('AZURE_SQL_PWD')


# Konstrukcja ciągu połączenia
CONNECTION_STRING = (
    f'Driver={DRIVER};'
    f'Server=tcp:{SQL_SERVER},1433;'
    f'Database={SQL_DATABASE};'
    f'UID={SQL_USERNAME};'
    f'PWD={SQL_PASSWORD};'
    'Encrypt=yes;'
    'TrustServerCertificate=no;'
    'Connection Timeout=30;'
)

def connect_and_insert_user():
    """Testuje połączenie SQL Auth, hashuje hasło i wstawia rekord do tabeli Users."""
    print("--- Testowanie Połączenia z Azure SQL (SQL Auth) ---")
    conn = None
    
    # 1. Haszowanie Hasła (konieczne dla tabeli Users)
    plain_password = "testpassword123"
    # Generowanie soli i hasha
    hashed_bytes = bcrypt.hashpw(plain_password.encode('utf-8'), bcrypt.gensalt())
    password_hash = hashed_bytes.decode('utf-8')
    new_username = "sql_test_user_456"

    try:
        # 2. Nawiązanie połączenia
        conn = pyodbc.connect(CONNECTION_STRING)
        cursor = conn.cursor()
        print("✅ Pomyślnie połączono z bazą danych Azure SQL przy użyciu SQL Authentication!")
        
        # 3. Wstawianie Danych (INSERT)
        print(f"\n--- Wstawianie nowego użytkownika: '{new_username}' ---")
        
        # Zapytanie używa ? jako placeholderów dla bezpieczeństwa (SQL Injection)
        sql_insert = "INSERT INTO Users (Username, PasswordHash) VALUES (?, ?)"
        
        cursor.execute(sql_insert, new_username, password_hash)
        conn.commit()
        
        # Odczyt wstawionego ID (SCOPE_IDENTITY() działa w SQL Server)
        cursor.execute("SELECT SCOPE_IDENTITY()")
        user_id = cursor.fetchone()[0]
        
        print(f"Pomyślnie dodano rekord do tabeli Users. UserID: {user_id}")
        
    except pyodbc.Error as ex:
        # Obsługa błędów
        sqlstate = ex.args[0]
        print(f"❌ BŁĄD POŁĄCZENIA/SQL:\n{sqlstate}")
        
    finally:
        if conn:
            conn.close()
            print("\nPołączenie zamknięte.")

if __name__ == "__main__":
    connect_and_insert_user()