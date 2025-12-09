import customtkinter as ctk
from database import fetch_expenses
from datetime import datetime
from collections import defaultdict
import threading
from tkinter import messagebox

class AnalyticsPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.pack(expand=True, fill="both", padx=10, pady=10)

        # -------------------------
        # Title
        # -------------------------
        ctk.CTkLabel(self, text="Analytics", font=("Arial", 22)).pack(pady=10)

        # -------------------------
        # Main Frames
        # -------------------------
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(expand=True, fill="both")

        self.left_frame = ctk.CTkFrame(self.main_frame)
        self.left_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))

        self.right_frame = ctk.CTkFrame(self.main_frame)
        self.right_frame.pack(side="right", fill="both", padx=(10, 0))

        # -------------------------
        # Left Panel: Top 5, Budget, Timeline
        # -------------------------
        # Top 5 Expenses
        ctk.CTkLabel(self.left_frame, text="Top 5 Expenses", font=("Arial", 14)).pack(pady=5)
        self.top5_frame = ctk.CTkScrollableFrame(self.left_frame, height=150)
        self.top5_frame.pack(fill="x", pady=5)

        # Budget Tracker
        ctk.CTkLabel(self.left_frame, text="Budget Tracker", font=("Arial", 14)).pack(pady=5)
        self.budget_frame = ctk.CTkFrame(self.left_frame, height=100)
        self.budget_frame.pack(fill="x", pady=5)
        self.budget_label = ctk.CTkLabel(self.budget_frame, text="Loading...", font=("Arial", 12))
        self.budget_label.pack(pady=10)
        self.budget_progress = ctk.CTkProgressBar(self.budget_frame, width=250)
        self.budget_progress.pack(pady=5)
        self.budget_progress.set(0)

        # Expense Timeline
        ctk.CTkLabel(self.left_frame, text="Expense Timeline", font=("Arial", 14)).pack(pady=5)
        self.timeline_frame = ctk.CTkScrollableFrame(self.left_frame, height=150)
        self.timeline_frame.pack(fill="x", pady=5)

        # -------------------------
        # Right Panel: Charts
        # -------------------------
        self.canvas_width = 400
        self.canvas_height = 250

        self.bar_canvas = ctk.CTkCanvas(
            self.right_frame, width=self.canvas_width, height=self.canvas_height, 
            bg=self.cget("fg_color")[1]
        )
        self.bar_canvas.pack(pady=5, fill="x")

        self.line_canvas = ctk.CTkCanvas(
            self.right_frame, width=self.canvas_width, height=self.canvas_height,
            bg=self.cget("fg_color")[1]
        )
        self.line_canvas.pack(pady=5, fill="x")

        # -------------------------
        # Initial Data Refresh (Threaded)
        # -------------------------
        self.refresh_all()

    def refresh(self):
        """Alias for refresh_all."""
        self.refresh_all()

    # ---------------------------------------------------------
    # Threaded Data Fetch
    # ---------------------------------------------------------
    def refresh_all(self):
        """Main entry point for refreshing all analytics data."""
        user = self.controller.current_user
        if not user:
            return

        self.budget_label.configure(text="Loading data...")

        thread = threading.Thread(target=self._fetch_analytics_data, args=(user["id"],))
        thread.start()

    def _fetch_analytics_data(self, user_id):
        """Fetch expenses in a background thread."""
        try:
            expenses = fetch_expenses(user_id)
        except Exception as e:
            print(f"Error fetching analytics data: {e}")
            self.controller.after(1, lambda: messagebox.showerror("DB Error", "Failed to load analytics data."))
            expenses = []

        self.controller.after(1, lambda: self._update_all_gui(expenses))

    # ---------------------------------------------------------
    # GUI Updates (Main Thread)
    # ---------------------------------------------------------
    def _update_all_gui(self, expenses):
        """Perform all calculations locally and update GUI widgets."""
        self._update_budget(expenses)
        self._update_top5(expenses)
        self._update_timeline(expenses)
        self._update_charts(expenses)

    # -------------------------
    # Budget Tracker
    # -------------------------
    def _update_budget(self, expenses):
        """Update budget tracker based on current month expenses."""
        current_month = datetime.now().strftime("%Y-%m")
        total_month = sum(amount for _, _, _, amount, date in expenses if date.startswith(current_month))

        budget_limit = self.controller.settings.get("budget", 0.0)
        formatted_total = self.controller.format_currency(total_month)
        formatted_limit = self.controller.format_currency(budget_limit)

        if not budget_limit or budget_limit <= 0:
            self.budget_label.configure(text=f"Spent this month: {formatted_total} / Budget not set")
            self.budget_progress.set(0)
        else:
            self.budget_label.configure(text=f"Spent this month: {formatted_total} / {formatted_limit}")
            self.budget_progress.set(min(total_month / budget_limit, 1.0))

    # -------------------------
    # Top 5 Expenses
    # -------------------------
    def _update_top5(self, expenses):
        for widget in self.top5_frame.winfo_children():
            widget.destroy()

        if not expenses:
            ctk.CTkLabel(self.top5_frame, text="No expenses yet").pack()
            return

        top5 = sorted(expenses, key=lambda x: x[3], reverse=True)[:5]
        for _, title, category, amount, date in top5:
            formatted_amount = self.controller.format_currency(amount)
            ctk.CTkLabel(self.top5_frame, text=f"{title} | {category} | {formatted_amount} | {date}").pack(anchor="w")

    # -------------------------
    # Timeline
    # -------------------------
    def _update_timeline(self, expenses):
        for widget in self.timeline_frame.winfo_children():
            widget.destroy()

        if not expenses:
            ctk.CTkLabel(self.timeline_frame, text="No expenses yet").pack()
            return

        sorted_expenses = sorted(expenses, key=lambda x: x[4], reverse=True)
        for _, title, category, amount, date in sorted_expenses:
            formatted_amount = self.controller.format_currency(amount)
            ctk.CTkLabel(self.timeline_frame, text=f"{date} | {title} | {category} | {formatted_amount}").pack(fill="x", padx=5, pady=2)

    # -------------------------
    # Charts
    # -------------------------
    def _update_charts(self, expenses):
        self._update_bar_chart(expenses)
        self._update_line_chart(expenses)

    def _update_bar_chart(self, expenses):
        self.bar_canvas.delete("all")
        if not expenses:
            return

        # Sum amounts per category
        totals = {}
        for _, _, category, amount, _ in expenses:
            totals[category] = totals.get(category, 0) + amount

        if not totals:
            return

        categories = list(totals.keys())
        amounts = list(totals.values())
        max_amount = max(amounts)

        text_color = "white" if ctk.get_appearance_mode() == "Dark" else "black"

        left, right, top, bottom = 40, 20, 20, 40
        usable_width = self.canvas_width - left - right
        usable_height = self.canvas_height - top - bottom
        bar_width = usable_width / len(categories) - 10

        for i, (cat, amt) in enumerate(totals.items()):
            x0 = left + i * (bar_width + 10)
            y0 = top + (1 - amt / max_amount) * usable_height
            x1 = x0 + bar_width
            y1 = top + usable_height

            self.bar_canvas.create_rectangle(x0, y0, x1, y1, fill="#00bcd4", outline="#00a8c0")
            self.bar_canvas.create_text((x0 + x1) / 2, y0 - 10, text=self.controller.format_currency(amt), fill=text_color, font=("Arial", 7))
            self.bar_canvas.create_text((x0 + x1) / 2, self.canvas_height - bottom / 2, text=cat, fill=text_color, font=("Arial", 7))

    def _update_line_chart(self, expenses):
        self.line_canvas.delete("all")
        if not expenses:
            return

        monthly_totals = defaultdict(float)
        for _, _, _, amount, date in expenses:
            try:
                key = datetime.strptime(date, "%Y-%m-%d").strftime("%Y-%m")
                monthly_totals[key] += amount
            except ValueError:
                continue

        months_sorted = sorted(monthly_totals.keys())
        totals_sorted = [monthly_totals[m] for m in months_sorted]

        if not months_sorted:
            return

        left, right, top, bottom = 40, 20, 20, 40
        usable_width = self.canvas_width - left - right
        usable_height = self.canvas_height - top - bottom
        x_gap = usable_width / max(len(months_sorted) - 1, 1)
        max_total = max(totals_sorted) or 1

        coords = []
        text_color = "white" if ctk.get_appearance_mode() == "Dark" else "black"

        for i, amt in enumerate(totals_sorted):
            x = left + i * x_gap
            y = top + (1 - amt / max_total) * usable_height
            coords.append((x, y))
            self.line_canvas.create_oval(x - 3, y - 3, x + 3, y + 3, fill="#ff9800")
            self.line_canvas.create_text(x, y - 10, text=self.controller.format_currency(amt), fill=text_color, font=("Arial", 7))

        for i in range(len(coords) - 1):
            self.line_canvas.create_line(*coords[i], *coords[i + 1], fill="#ff9800", width=2)

        for i, m in enumerate(months_sorted):
            label = datetime.strptime(m, "%Y-%m").strftime("%b %Y")
            self.line_canvas.create_text(left + i * x_gap, self.canvas_height - bottom / 2, text=label, fill=text_color, font=("Arial", 7), anchor="n")
