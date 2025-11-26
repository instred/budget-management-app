import customtkinter as ctk
from controller import AppController
from login import init_database

if __name__ == "__main__":
    init_database()
    ctk.set_appearance_mode("dark")

    app = AppController()
    app.mainloop()
