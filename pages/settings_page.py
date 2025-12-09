import customtkinter as ctk
from tkinter import messagebox
from database import save_user_setting, delete_all_expenses
import threading

class AccountSettingsPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.pack(expand=True, fill="both")

        # -------------------------
        # Title
        # -------------------------
        ctk.CTkLabel(self, text="Settings", font=("Arial", 22)).pack(pady=(15, 10))

        user_settings = controller.settings

        # -------------------------
        # Theme Selector
        # -------------------------
        ctk.CTkLabel(self, text="Theme", anchor="w").pack(fill="x", padx=20)
        self.theme_option = ctk.CTkOptionMenu(
            master=self,
            values=["System", "Light", "Dark"],
            command=self.change_theme
        )
        self.theme_option.set(user_settings.get("theme", "System"))
        self.theme_option.pack(fill="x", padx=20, pady=(0, 15))

        # -------------------------
        # Currency Selector
        # -------------------------
        ctk.CTkLabel(self, text="Currency", anchor="w").pack(fill="x", padx=20)
        self.currency_option = ctk.CTkOptionMenu(
            master=self,
            values=["PLN", "USD", "EUR", "GBP", "JPY"],
            command=self.change_currency
        )
        self.currency_option.set(user_settings.get("currency", "PLN"))
        self.currency_option.pack(fill="x", padx=20, pady=(0, 15))

        # -------------------------
        # Monthly Budget
        # -------------------------
        budget_frame = ctk.CTkFrame(self)
        budget_frame.pack(fill="x", padx=20, pady=15)

        ctk.CTkLabel(budget_frame, text="Monthly Budget", font=("Arial", 14)).pack(pady=5)

        current_budget = user_settings.get("budget", 0.0)
        self.budget_entry = ctk.CTkEntry(budget_frame, placeholder_text="Enter budget amount")
        self.budget_entry.pack(fill="x", padx=10, pady=5)
        self.budget_entry.insert(0, str(current_budget))

        self.save_budget_button = ctk.CTkButton(budget_frame, text="Save Budget", command=self.save_budget)
        self.save_budget_button.pack(pady=5)

        self.budget_message_label = ctk.CTkLabel(budget_frame, text="", text_color="green")
        self.budget_message_label.pack()

        # -------------------------
        # Danger Zone / Reset Expenses
        # -------------------------
        reset_frame = ctk.CTkFrame(self)
        reset_frame.pack(fill="x", padx=20, pady=15)

        ctk.CTkLabel(reset_frame, text="Danger Zone", font=("Arial", 14), text_color="red").pack(pady=5)

        self.reset_button = ctk.CTkButton(
            reset_frame,
            text="Delete ALL Expenses",
            command=self.reset_expenses,
            fg_color="red",
            hover_color="darkred"
        )
        self.reset_button.pack(pady=10)

    # -------------------------
    # Theme / Currency Changes
    # -------------------------
    def change_theme(self, value):
        """Apply theme immediately and save in background."""
        ctk.set_appearance_mode(value)
        self.controller.settings["theme"] = value
        user_id = self.controller.current_user["id"]
        threading.Thread(
            target=self._save_setting_task, 
            args=(user_id, "Theme", value, None)
        ).start()

    def change_currency(self, value):
        """Update currency and save in background, then refresh pages."""
        self.controller.settings["currency"] = value
        user_id = self.controller.current_user["id"]
        threading.Thread(
            target=self._save_setting_task, 
            args=(user_id, "Currency", value, self._on_currency_saved)
        ).start()

    def _save_setting_task(self, user_id, name, value, callback):
        """Background DB save with optional callback in main thread."""
        success = False
        try:
            save_user_setting(user_id, name, value)
            success = True
        except Exception as e:
            print(f"Error saving setting {name}: {e}")

        if success and callback:
            self.controller.after(1, callback)
        elif not success:
            self.controller.after(1, lambda: messagebox.showerror("DB Error", f"Failed to save setting: {name}"))

    def _on_currency_saved(self):
        """Refresh all pages after currency change."""
        self.controller.refresh_all_pages()

    # -------------------------
    # Budget Saving
    # -------------------------
    def save_budget(self):
        """Validate and save budget in background."""
        try:
            budget_value = float(self.budget_entry.get().replace(',', '.'))
            if budget_value < 0:
                raise ValueError
        except ValueError:
            self.budget_message_label.configure(
                text="Invalid budget value (must be positive).", text_color="red"
            )
            return

        user_id = self.controller.current_user["id"]
        threading.Thread(
            target=self._save_budget_task, 
            args=(user_id, budget_value)
        ).start()

    def _save_budget_task(self, user_id, value):
        """Background DB save for budget."""
        success = False
        try:
            save_user_setting(user_id, "Budget", value)
            success = True
        except Exception as e:
            print(f"Error saving budget: {e}")

        self.controller.after(1, lambda: self._on_budget_saved(success, value))

    def _on_budget_saved(self, success, value):
        """Update GUI after budget save."""
        if success:
            self.controller.settings["budget"] = value
            formatted = self.controller.format_currency(value)
            self.budget_message_label.configure(text=f"Budget saved: {formatted}", text_color="green")
            self.controller.refresh_all_pages()
        else:
            self.budget_message_label.configure(text="Error saving budget.", text_color="red")
            messagebox.showerror("DB Error", "Failed to save budget.")

    # -------------------------
    # Reset All Expenses
    # -------------------------
    def reset_expenses(self):
        """Confirm and delete all expenses in background."""
        confirm = messagebox.askyesno(
            "Reset Confirmation",
            "Are you sure you want to delete ALL expenses?\nThis cannot be undone."
        )
        if not confirm:
            return

        user_id = self.controller.current_user["id"]
        threading.Thread(
            target=self._reset_expenses_task, 
            args=(user_id,)
        ).start()

    def _reset_expenses_task(self, user_id):
        """Background DB deletion."""
        success = False
        try:
            delete_all_expenses(user_id)
            success = True
        except Exception as e:
            print(f"Error deleting expenses: {e}")

        self.controller.after(1, lambda: self._on_reset_expenses(success))

    def _on_reset_expenses(self, success):
        """Update GUI after expenses reset."""
        if success:
            messagebox.showinfo("Success", "All expenses have been deleted.")
            self.controller.refresh_all_pages()
        else:
            messagebox.showerror("Error", "Failed to delete expenses.")

    # -------------------------
    # Refresh Fields from Controller
    # -------------------------
    def refresh(self):
        """Called by controller.refresh_all_pages()"""
        current_budget = self.controller.settings.get("budget", 0.0)
        self.budget_entry.delete(0, ctk.END)
        self.budget_entry.insert(0, str(current_budget))
        self.budget_message_label.configure(text="")

        self.theme_option.set(self.controller.settings.get("theme", "System"))
        self.currency_option.set(self.controller.settings.get("currency", "PLN"))
