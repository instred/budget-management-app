import customtkinter as ctk
from datetime import datetime
from pages.login_page import LoginFrame
from app_main import MainApp
from database import get_total_amount_for_month
from utils.currency_formatter import format_currency
from utils.app_init import AppInitializer


class AppController(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Personal Finance Tracker")
        self.geometry("1200x800")

        self.settings = {
            "currency": "USD",
            "theme": "System",
            "budget": 0.0
        }

        self.current_user = None
        self.initializer = AppInitializer(self)

        self.container = ctk.CTkFrame(self)
        self.container.pack(fill="both", expand=True)
        self.show_login()

    def show_login(self):
        """Displays the login screen."""
        for widget in self.container.winfo_children():
            widget.destroy()
        LoginFrame(self.container, self)

    def show_main_app(self):
        """Loads the main app after login and triggers settings loading."""
        for widget in self.container.winfo_children():
            widget.destroy()
        if not self.current_user:
            self.show_login()
            return
        self.initializer.user_id = self.current_user["id"]
        self.initializer.start_loading()

    def get_total_amount_for_month(self):
        """Returns the user's total expenses for the current month."""
        if not self.current_user:
            return 0.0
        now = datetime.now()
        return get_total_amount_for_month(self.current_user["id"], now.year, now.month)

    def refresh_all_pages(self):
        """Triggers refresh on all active pages."""
        if not hasattr(self, "main_app"):
            return
        for key, page in self.main_app.pages.items():
            if hasattr(page, "refresh"):
                page.refresh()

    def format_currency(self, amount: float) -> str:
        """Formats a numeric value using the chosen currency."""
        return format_currency(amount, self.settings.get("currency", "PLN"))

    def complete_main_app_load(self, settings_data):
        """Applies loaded user settings and initializes the main interface."""
        self.settings.update(settings_data)
        ctk.set_appearance_mode(self.settings.get("theme", "System"))
        self.main_app = MainApp(self.container, self)
