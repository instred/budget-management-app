import customtkinter as ctk
from database import fetch_expenses
from datetime import datetime
from collections import defaultdict

class AnalyticsPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.pack(expand=True, fill="both", padx=10, pady=10)

        # Title
        label = ctk.CTkLabel(self, text="Analytics", font=("Arial", 22))
        label.pack(pady=10)

        # -------------------------
        # Main horizontal frame
        # -------------------------
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(expand=True, fill="both")

        # Left frame: top 5, budget tracker, timeline
        self.left_frame = ctk.CTkFrame(self.main_frame)
        self.left_frame.pack(side="left", fill="both", expand=True, padx=(0,10))

        # Top 5 Expenses
        ctk.CTkLabel(self.left_frame, text="Top 5 Expenses", font=("Arial", 14)).pack(pady=5)
        self.top5_frame = ctk.CTkScrollableFrame(self.left_frame, height=150)
        self.top5_frame.pack(fill="x", pady=5)

        # Budget Tracker
        ctk.CTkLabel(self.left_frame, text="Budget Tracker", font=("Arial", 14)).pack(pady=5)
        self.budget_frame = ctk.CTkFrame(self.left_frame, height=100)
        self.budget_frame.pack(fill="x", pady=5)
        self.budget_label = ctk.CTkLabel(self.budget_frame, text="", font=("Arial", 12))
        self.budget_label.pack(pady=10)

        self.budget_progress = ctk.CTkProgressBar(self.budget_frame, width=250)
        self.budget_progress.pack(pady=5)
        self.budget_progress.set(0)

        # Expense Timeline
        ctk.CTkLabel(self.left_frame, text="Expense Timeline", font=("Arial", 14)).pack(pady=5)
        self.timeline_frame = ctk.CTkScrollableFrame(self.left_frame, height=150)
        self.timeline_frame.pack(fill="x", pady=5)

        # Right frame: charts
        self.right_frame = ctk.CTkFrame(self.main_frame)
        self.right_frame.pack(side="right", fill="both", padx=(10,0))

        # Bar chart frame
        self.bar_canvas = ctk.CTkCanvas(self.right_frame, width=400, height=250, bg="#2b2b2b")
        self.bar_canvas.pack(pady=5, fill="x")

        # Line chart frame
        self.line_canvas = ctk.CTkCanvas(self.right_frame, width=400, height=250, bg="#2b2b2b")
        self.line_canvas.pack(pady=5, fill="x")

        # Initial refresh
        self.refresh_all()

    # -------------------------
    # Refresh all components
    # -------------------------
    def refresh_all(self):
        self.refresh_charts()
        self.refresh_top5()
        self.refresh_budget_tracker()
        self.refresh_timeline()

    # -------------------------
    # Charts
    # -------------------------
    def refresh_charts(self):
        self.refresh_bar_chart()
        self.refresh_monthly_line_chart()

    def refresh_bar_chart(self):
        self.bar_canvas.delete("all")
        user = self.controller.current_user
        expenses = fetch_expenses(user["id"], user["username"])
        if not expenses:
            return

        # Sum by category
        category_totals = {}
        for _, _, category, amount, _ in expenses:
            category_totals[category] = category_totals.get(category, 0) + amount

        categories = list(category_totals.keys())
        amounts = list(category_totals.values())
        max_amount = max(amounts) if amounts else 1

        # Margins
        left_margin = 40
        right_margin = 20
        top_margin = 20
        bottom_margin = 40

        canvas_width = 380
        canvas_height = 220
        usable_width = canvas_width - left_margin - right_margin
        usable_height = canvas_height - top_margin - bottom_margin

        bar_width = usable_width / len(categories) - 10

        for i, (cat, amt) in enumerate(category_totals.items()):
            x0 = left_margin + i * (bar_width + 10)
            y0 = top_margin + (1 - amt / max_amount) * usable_height
            x1 = x0 + bar_width
            y1 = top_margin + usable_height

            self.bar_canvas.create_rectangle(x0, y0, x1, y1, fill="#00bcd4")
            self.bar_canvas.create_text((x0 + x1) / 2, y0 - 10, text=f"${amt:.2f}", fill="white", font=("Arial", 8))
            self.bar_canvas.create_text((x0 + x1) / 2, canvas_height - bottom_margin / 2, text=cat, fill="white", font=("Arial", 8))


    def refresh_monthly_line_chart(self):
        self.line_canvas.delete("all")
        user = self.controller.current_user
        expenses = fetch_expenses(user["id"], user["username"])
        if not expenses:
            return

        monthly_totals = defaultdict(float)
        for _, _, _, amount, date in expenses:
            dt = datetime.strptime(date, "%Y-%m-%d")
            key = dt.strftime("%Y-%m")
            monthly_totals[key] += amount

        months_sorted = sorted(monthly_totals.keys())
        totals_sorted = [monthly_totals[m] for m in months_sorted]

        canvas_width = 380
        canvas_height = 220
        left_margin = 40
        right_margin = 20
        top_margin = 20
        bottom_margin = 40

        usable_width = canvas_width - left_margin - right_margin
        usable_height = canvas_height - top_margin - bottom_margin

        if not months_sorted:
            return

        max_total = max(totals_sorted) or 1
        x_gap = usable_width / max(len(months_sorted) - 1, 1)

        coords = []
        for i, amt in enumerate(totals_sorted):
            x = left_margin + i * x_gap
            y = top_margin + (1 - amt / max_total) * usable_height
            coords.append((x, y))
            self.line_canvas.create_oval(x - 3, y - 3, x + 3, y + 3, fill="#ff9800")

        for i in range(len(coords) - 1):
            self.line_canvas.create_line(*coords[i], *coords[i + 1], fill="#ff9800", width=2)

        for i, m in enumerate(months_sorted):
            label = datetime.strptime(m, "%Y-%m").strftime("%b %Y")
            self.line_canvas.create_text(left_margin + i * x_gap, canvas_height - bottom_margin / 2,
                                        text=label, fill="white", font=("Arial", 8), anchor="n")


    # -------------------------
    # Top 5 Expenses
    # -------------------------
    def refresh_top5(self):
        for widget in self.top5_frame.winfo_children():
            widget.destroy()

        user = self.controller.current_user
        expenses = fetch_expenses(user["id"], user["username"])
        if not expenses:
            ctk.CTkLabel(self.top5_frame, text="No expenses yet").pack()
            return

        top5 = sorted(expenses, key=lambda x: x[3], reverse=True)[:5]
        for exp in top5:
            _, title, category, amount, date = exp
            ctk.CTkLabel(self.top5_frame, text=f"{title} | {category} | ${amount:.2f} | {date}").pack(anchor="w")

    def refresh_budget_tracker(self):
        user = self.controller.current_user
        expenses = fetch_expenses(user["id"], user["username"])
        if not expenses:
            self.budget_label.configure(text="No expenses yet")
            self.budget_progress.set(0)
            return

        # Monthly total (current month)
        total_month = 0
        budget_limit = 2000  # Example fixed budget
        current_month = datetime.now().strftime("%Y-%m")

        for _, _, _, amount, date in expenses:
            if date.startswith(current_month):
                total_month += amount

        self.budget_label.configure(text=f"Spent this month: ${total_month:.2f} / ${budget_limit}")
        self.budget_progress.set(min(total_month / budget_limit, 1.0))

    def refresh_timeline(self):
        # Clear previous
        for widget in self.timeline_frame.winfo_children():
            widget.destroy()

        user = self.controller.current_user
        expenses = fetch_expenses(user["id"], user["username"])
        if not expenses:
            ctk.CTkLabel(self.timeline_frame, text="No expenses yet").pack()
            return

        # Sort descending by date
        expenses_sorted = sorted(expenses, key=lambda x: x[4], reverse=True)

        for exp in expenses_sorted:
            _, title, category, amount, date = exp
            ctk.CTkLabel(self.timeline_frame, text=f"{date} | {title} | {category} | ${amount:.2f}").pack(anchor="w")

