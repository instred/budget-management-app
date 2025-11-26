import customtkinter as ctk
import sqlite3
from database import ensure_expense_table

DB_PATH = "users.db"

# --------------------------
# Database Setup
# --------------------------
def init_database():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
    """)

    cur.execute("SELECT COUNT(*) FROM users")
    if cur.fetchone()[0] == 0:
        cur.execute("INSERT INTO users (username, password) VALUES (?, ?)", ("admin", "admin"))
        conn.commit()

    conn.close()

# --------------------------
# Login Frame
# --------------------------
class LoginFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.pack(expand=True, padx=20, pady=20)

        # --------------------------
        # Login Section
        # --------------------------
        self.login_frame = ctk.CTkFrame(self)
        self.login_frame.pack(expand=True)

        self.label_title = ctk.CTkLabel(self.login_frame, text="Login", font=("Arial", 22))
        self.label_title.pack(pady=5)

        self.username_entry = ctk.CTkEntry(self.login_frame, placeholder_text="Username")
        self.username_entry.pack(pady=5)

        self.password_entry = ctk.CTkEntry(self.login_frame, placeholder_text="Password", show="*")
        self.password_entry.pack(pady=5)

        self.login_button = ctk.CTkButton(self.login_frame, text="Login", command=self.check_login)
        self.login_button.pack(pady=5)

        self.login_message_label = ctk.CTkLabel(self.login_frame, text="", text_color="red")
        self.login_message_label.pack(pady=5)

        self.show_register_button = ctk.CTkButton(self.login_frame, text="Register", command=self.show_register)
        self.show_register_button.pack(pady=5)

        # --------------------------
        # Registration Section
        # --------------------------
        self.register_frame = ctk.CTkFrame(self)

        self.label_register = ctk.CTkLabel(self.register_frame, text="Register", font=("Arial", 20))
        self.label_register.pack(pady=5)

        self.reg_username_entry = ctk.CTkEntry(self.register_frame, placeholder_text="New Username")
        self.reg_username_entry.pack(pady=5)

        self.reg_password_entry = ctk.CTkEntry(self.register_frame, placeholder_text="Password", show="*")
        self.reg_password_entry.pack(pady=5)

        self.reg_confirm_entry = ctk.CTkEntry(self.register_frame, placeholder_text="Confirm Password", show="*")
        self.reg_confirm_entry.pack(pady=5)

        self.register_button = ctk.CTkButton(self.register_frame, text="Register", command=self.register_user)
        self.register_button.pack(pady=5)

        self.register_message_label = ctk.CTkLabel(self.register_frame, text="", text_color="red")
        self.register_message_label.pack(pady=5)

        self.back_to_login_button = ctk.CTkButton(self.register_frame, text="Back to Login", command=self.show_login)
        self.back_to_login_button.pack(pady=5)

    # --------------------------
    # Show register screen
    # --------------------------
    def show_register(self):
        self.login_frame.pack_forget()
        self.register_frame.pack(expand=True)

    # --------------------------
    # Show login screen
    # --------------------------
    def show_login(self):
        self.register_frame.pack_forget()
        self.login_frame.pack(expand=True)

    # --------------------------
    # Login Logic
    # --------------------------
    def check_login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()

        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
        result = cur.fetchone()
        conn.close()

        if result:
            user_id = result[0]  # id from users table
            username = result[1]
            self.controller.current_user = {"id": user_id, "username": username}
            # create user-specific expense table if it doesn't exist
            ensure_expense_table(user_id, username)
            self.controller.show_main_app()
        else:
            self.login_message_label.configure(text="Invalid credentials.")

    # --------------------------
    # Registration Logic
    # --------------------------
    def register_user(self):
        username = self.reg_username_entry.get().strip()
        password = self.reg_password_entry.get().strip()
        confirm = self.reg_confirm_entry.get().strip()

        if not username or not password or not confirm:
            self.register_message_label.configure(text="All fields are required.", text_color="red")
            return

        if password != confirm:
            self.register_message_label.configure(text="Passwords do not match.", text_color="red")
            return

        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        try:
            cur.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            conn.commit()
            self.register_message_label.configure(text="User registered successfully!", text_color="green")
            # Clear registration fields
            self.reg_username_entry.delete(0, "end")
            self.reg_password_entry.delete(0, "end")
            self.reg_confirm_entry.delete(0, "end")
        except sqlite3.IntegrityError:
            self.register_message_label.configure(text="Username already exists.", text_color="red")
        finally:
            conn.close()

