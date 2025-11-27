import customtkinter as ctk
from database import fetch_expenses, get_total_amount

class SummaryPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        self.pack(expand=True, fill="both")

        title = ctk.CTkLabel(self, text="Dashboard Summary", font=("Arial", 22))
        title.pack(pady=10)

        self.total_label = ctk.CTkLabel(self, text="Total Spent: $0.00", font=("Arial", 18))
        self.total_label.pack(pady=5)

        recent_label = ctk.CTkLabel(self, text="Recent Expenses", font=("Arial", 16))
        recent_label.pack(pady=5)

        self.recent_box = ctk.CTkTextbox(self, width=500, height=200)
        self.recent_box.pack(pady=10)

        # Initial load
        self.refresh()

    def refresh(self):
        user = self.controller.current_user
        if not user:
            return

        # Refresh total
        total = get_total_amount(user["id"], user["username"])
        self.total_label.configure(text=f"Total Spent: ${total:.2f}")

        # Load last 5 expenses
        expenses = fetch_expenses(user["id"], user["username"], limit=5)
        self.recent_box.delete("1.0", "end")

        for exp in expenses:
            _, title, category, amount, date = exp
            self.recent_box.insert("end", f"{date} - {title} | {category} | ${amount:.2f}\n")
