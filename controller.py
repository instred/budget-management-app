import customtkinter as ctk
from login import LoginFrame
from app_main import MainApp
from database import load_user_settings

class AppController(ctk.CTk):
    def __init__(self):
        super().__init__()

        # --------------------------
        # NEW: Settings storage
        # --------------------------
        self.settings = {
            "currency": "USD",
            "theme": "System"
        }

        self.title("Budget App")
        self.geometry("1200x800")

        # container frame for swapping screens
        self.container = ctk.CTkFrame(self)
        self.container.pack(fill="both", expand=True)

        self.show_login()

    # --------------------------
    # show login screen
    # --------------------------
    def show_login(self):
        for widget in self.container.winfo_children():
            widget.destroy()

        LoginFrame(self.container, self)

    # --------------------------
    # show main app screen
    # --------------------------
    def show_main_app(self):
        for widget in self.container.winfo_children():
            widget.destroy()

        user = getattr(self, "current_user", None)
        if user:
            self.settings = load_user_settings(user["id"])  # load settings from DB

        self.main_app = MainApp(self.container, self)

    # --------------------------
    # NEW: refresh method for pages
    # --------------------------
    def refresh_all_pages(self):
        if not hasattr(self, "main_app"):
            return

        pages = self.main_app.pages

        for key in ["expenses", "summary", "analytics", "settings"]:
            if key in pages:
                pages[key].refresh()

    def format_currency(self, value: float) -> str:
        currency = self.settings.get("currency", "USD")

        symbols = {
            "USD": "$",
            "EUR": "€",
            "GBP": "£",
            "PLN": "zł",
            "JPY": "¥",
        }

        symbol = symbols.get(currency, currency + " ")

        # Format with 2 decimal places, comma separators
        if symbol == "$":
            return f"{symbol}{value:,.2f}"
        else: 
            return f"{value:,.2f}{symbol}"