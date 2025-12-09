import threading
from database import load_user_settings
from tkinter import messagebox

class AppInitializer:
    def __init__(self, controller):
        self.controller = controller
        self.user_id = None  # <--- Ustawienie user_id na None na początku
        
    def start_loading(self):
        """Uruchamia ładowanie ustawień w wątku tła."""
        if self.user_id is None:
             raise ValueError("User ID must be set before starting initializer.")
        
        thread = threading.Thread(target=self._perform_settings_load)
        thread.start()

    def _perform_settings_load(self):
        """(WĄTEK TŁA) Ładuje ustawienia z bazy danych."""
        settings_data = {}
        try:
            # Zakładamy, że load_user_settings jest zaimportowane z database.py
            settings_data = load_user_settings(self.user_id)  # Wolna operacja DB
        except Exception as e:
            print(f"Błąd ładowania ustawień: {e}")
            self.controller.after(1, lambda: messagebox.showerror("Startup Error", "Failed to load user settings."))

        # Powrót do wątku głównego
        self.controller.after(1, lambda: self.controller.complete_main_app_load(settings_data))