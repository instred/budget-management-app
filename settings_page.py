import customtkinter as ctk

class AccountSettingsPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)

        # FIX: make this frame visible!
        self.pack(expand=True, fill="both")

        label = ctk.CTkLabel(self, text="Account Settings", font=("Arial", 18))
        label.pack(pady=40)
