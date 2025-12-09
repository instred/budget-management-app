import customtkinter as ctk
from database import get_user, create_user
import bcrypt
import threading


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
        self.controller.show_loading_spinner()

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

        if not username or not password:
            self.login_message_label.configure(text="Username and password are required.", text_color="red")
            return

        login_thread = threading.Thread(target=self.perform_login_task, args=(username, password))
        login_thread.start()

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

        # UŻYWAMY FUNKCJI create_user Z database.py
        # Funkcja create_user zajmuje się teraz: hashowaniem, wstawianiem do Users i wstawianiem domyślnych UserSettings
        if create_user(username, password):
            self.register_message_label.configure(text="User registered successfully!", text_color="green")
            # Clear registration fields
            self.reg_username_entry.delete(0, "end")
            self.reg_password_entry.delete(0, "end")
            self.reg_confirm_entry.delete(0, "end")
        else:
            # Obsługa błędu IntegrityError (nazwa użytkownika już istnieje)
            self.register_message_label.configure(text="Username already exists.", text_color="red")

    def perform_login_task(self, username, password):
        """Wątkowa funkcja do obsługi połączenia z DB i weryfikacji."""
        
        # UWAGA: Ta część trwa długo, ale NIE blokuje GUI
        try:
            # 1. Logika weryfikacji
            user_data = get_user(username)
            login_success = False
            user_id = None
            
            if user_data and user_data.get("password_hash"): # Musisz mieć pole 'password_hash' z bazy
                stored_hash = user_data["password_hash"]
                # bcrypt.checkpw to funkcja CPU-intensywna i jest to OK w wątku tła
                if bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8')):
                    login_success = True
                    user_id = user_data["id"]

        except Exception as e:
            # Złapanie błędu pyodbc/SQL
            print(f"Błąd połączenia z bazą danych: {e}")
            login_success = False
            user_id = None
        
        # 2. Powrót do Main Thread (manipulacja GUI)
        # Używamy self.controller.after() do bezpiecznego wykonania handle_login_result 
        # w wątku głównym Tkinter, gdy operacja tła się zakończy.
        self.controller.after(
            1, # Wykonaj natychmiast
            lambda: self.handle_login_result(login_success, username, user_id)
        )

    # --------------------------
    # Login Logic (WYKONYWANE PONOWNIE W MAIN THREAD)
    # --------------------------
    def handle_login_result(self, success, username, user_id):

        if success:
            # Ustaw użytkownika i przejdź do aplikacji
            self.controller.current_user = {"id": user_id, "username": username}
            self.controller.show_main_app()
        else:
            # Pokaż błąd
            self.login_message_label.configure(text="Invalid credentials.", text_color="red")

