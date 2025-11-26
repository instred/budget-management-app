import customtkinter as ctk
from login import LoginFrame
from app_main import MainApp

# --------------------------
# Main Application Controller (single root window)
# --------------------------
class AppController(ctk.CTk):
    def __init__(self):
        super().__init__()
        
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

        # Store the main app in the controller
        self.main_app = MainApp(self.container, self)
