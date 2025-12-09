import customtkinter as ctk
import threading
from tkinter import messagebox
from database import fetch_expenses, get_total_amount

class SummaryPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.pack(expand=True, fill="both")

        ctk.CTkLabel(self, text="Dashboard Summary", font=("Arial", 22)).pack(pady=10)
        self.total_label = ctk.CTkLabel(self, text="Total Spent: N/A", font=("Arial", 18))
        self.total_label.pack(pady=5)
        ctk.CTkLabel(self, text="Recent Expenses", font=("Arial", 16)).pack(pady=5)

        self.recent_box = ctk.CTkTextbox(self, width=500, height=200, state="disabled")
        self.recent_box.pack(pady=10)

        self.refresh()

    def refresh(self):
        """Start background thread to fetch user data."""
        user = self.controller.current_user
        if not user:
            self.total_label.configure(text="Total Spent: $0.00")
            return
        threading.Thread(target=self.perform_fetch_task, args=(user["id"],), daemon=True).start()

    def perform_fetch_task(self, user_id):
        """Fetch total and recent expenses in a background thread."""
        total, expenses = 0.0, []
        try:
            total = get_total_amount(user_id)
            expenses = fetch_expenses(user_id, limit=5)
        except Exception as e:
            print(f"Error fetching summary data: {e}")
            self.controller.after(1, lambda: messagebox.showerror("Database Error", "Failed to load summary data."))

        self.controller.after(1, lambda: self.complete_refresh(total, expenses))

    def complete_refresh(self, total, expenses):
        """Update GUI widgets with fetched data."""
        self.total_label.configure(text=f"Total Spent: {self.controller.format_currency(total)}")
        self.recent_box.configure(state="normal")
        self.recent_box.delete("1.0", "end")

        if not expenses:
            self.recent_box.insert("end", "No expenses recorded yet.")
        else:
            for _, title, category, amount, date in expenses:
                self.recent_box.insert("end", f"{date} - {title} | {category} | {self.controller.format_currency(amount)}\n")

        self.recent_box.configure(state="disabled")
