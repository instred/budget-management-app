import customtkinter as ctk
from tkinter import messagebox
from database import save_user_setting


class AccountSettingsPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        self.pack(expand=True, fill="both")

        title = ctk.CTkLabel(self, text="Settings", font=("Arial", 18))
        title.pack(pady=(15, 10))

        user_settings = controller.settings  # contains last saved values

        # ----------------------
        # 1. THEME SELECTOR
        # ----------------------
        theme_label = ctk.CTkLabel(self, text="Theme", anchor="w")
        theme_label.pack(fill="x", padx=20)

        self.theme_option = ctk.CTkOptionMenu(
            master=self,
            values=["System", "Light", "Dark"],
            command=self.change_theme
        )
        # Set default to last saved value
        self.theme_option.set(user_settings.get("theme", "System"))
        self.theme_option.pack(fill="x", padx=20, pady=(0, 15))

        # ----------------------
        # 2. CURRENCY SELECTOR
        # ----------------------
        currency_label = ctk.CTkLabel(self, text="Currency", anchor="w")
        currency_label.pack(fill="x", padx=20)

        self.currency_option = ctk.CTkOptionMenu(
            master=self,
            values=["USD", "EUR", "GBP", "PLN", "JPY"],
            command=self.change_currency
        )
        # Set default to last saved value
        self.currency_option.set(user_settings.get("currency", "USD"))
        self.currency_option.pack(fill="x", padx=20, pady=(0, 15))

        # ----------------------
        # 3. RESET ALL EXPENSES
        # ----------------------
        reset_button = ctk.CTkButton(
            master=self,
            text="Reset All Expenses",
            fg_color="red",
            hover_color="#b30000",
            command=self.reset_expenses
        )
        reset_button.pack(pady=20)

    # -------------------------------------------------
    # SETTINGS CALLBACKS
    # -------------------------------------------------

    def change_theme(self, value):
        """Apply theme and save setting"""
        ctk.set_appearance_mode(value)
        user_id = self.controller.current_user["id"]
        save_user_setting(user_id, "theme", value)
        self.controller.settings["theme"] = value

    def change_currency(self, value):
        """Apply currency setting and refresh all pages"""
        self.controller.settings["currency"] = value
        user_id = self.controller.current_user["id"]
        save_user_setting(user_id, "currency", value)
        self.controller.refresh_all_pages()

    def reset_expenses(self):
        """Delete all expenses from database"""
        confirm = messagebox.askyesno(
            "Reset Confirmation",
            "Are you sure you want to delete ALL expenses?\nThis cannot be undone."
        )
        if confirm:
            self.controller.db.delete_all_expenses()  # adjust name if needed
            messagebox.showinfo("Success", "All expenses have been deleted.")
            self.controller.refresh_all_pages()

    def refresh(self):
        """Called by controller.refresh_all_pages()"""
        # Update dropdowns to current settings in case changed elsewhere
        self.theme_option.set(self.controller.settings.get("theme", "System"))
        self.currency_option.set(self.controller.settings.get("currency", "USD"))
