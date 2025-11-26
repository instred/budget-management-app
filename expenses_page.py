import customtkinter as ctk
from database import insert_expense, delete_expense, fetch_expenses
from tkcalendar import Calendar
from datetime import datetime
import tkinter as tk

class ExpensesPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.pack(fill="both", expand=True, padx=10, pady=10)

        user = controller.current_user
        if not user:
            return

        # -----------------------------------
        # Title
        # -----------------------------------
        title = ctk.CTkLabel(self, text="Manage Expenses", font=("Arial", 22))
        title.pack(pady=10)

        # ---------------------------------------------------------
        # FILTER + SORT BAR
        # ---------------------------------------------------------
        filter_sort_frame = ctk.CTkFrame(self)
        filter_sort_frame.pack(fill="x", pady=5)

        # ----- Filter -----
        ctk.CTkLabel(filter_sort_frame, text="Filter:").pack(side="left", padx=5)

        self.filter_var = ctk.StringVar(value="All")
        self.filter_dropdown = ctk.CTkOptionMenu(
            filter_sort_frame,
            values=self.get_all_categories_from_db(include_all=True),
            variable=self.filter_var,
            command=self.apply_filter_or_sort
        )
        self.filter_dropdown.pack(side="left", padx=5)

        # ----- Sort -----
        ctk.CTkLabel(filter_sort_frame, text="Sort:").pack(side="left", padx=20)

        self.sort_var = ctk.StringVar(value="Date (Newest)")
        self.sort_dropdown = ctk.CTkOptionMenu(
            filter_sort_frame,
            values=[
                "Date (Newest)",
                "Date (Oldest)",
                "Amount (High → Low)",
                "Amount (Low → High)",
                "Title (A → Z)",
                "Title (Z → A)",
                "Category (A → Z)"
            ],
            variable=self.sort_var,
            command=self.apply_filter_or_sort
        )
        self.sort_dropdown.pack(side="left", padx=5)

        # -----------------------------------
        # Add Expense Form
        # -----------------------------------
        form_frame = ctk.CTkFrame(self)
        form_frame.pack(fill="x", pady=10)

        self.entry_title = ctk.CTkEntry(form_frame, placeholder_text="Expense Title", width=150)
        self.entry_title.pack(side="left", padx=5)

        self.entry_date = ctk.CTkEntry(form_frame, width=120)
        self.entry_date.pack(side="left", padx=5)
        self.entry_date.insert(0, datetime.now().strftime("%Y-%m-%d"))

        self.entry_date.bind("<Button-1>", lambda e: pick_date())

        # Function to show calendar popup
        def pick_date():
            # Try to get current value of entry
            current_value = self.entry_date.get()
            try:
                date_obj = datetime.strptime(current_value, "%Y-%m-%d")
            except ValueError:
                date_obj = datetime.today()  # fallback to today if empty or invalid

            def on_date_selected():
                date_str = cal.get_date()
                self.entry_date.delete(0, "end")
                self.entry_date.insert(0, date_str)
                top.destroy()

            top = tk.Toplevel(self)
            top.title("Select Date")
            # Initialize calendar with previously selected date
            cal = Calendar(
                top,
                selectmode="day",
                date_pattern="yyyy-mm-dd",
                year=date_obj.year,
                month=date_obj.month,
                day=date_obj.day
            )
            cal.pack(padx=10, pady=10)
            btn = ctk.CTkButton(top, text="Select", command=on_date_selected)
            btn.pack(pady=5)

        # Categories
        self.categories = [
            "Food",
            "Transport",
            "Housing",
            "Entertainment",
            "Shopping",
            "Health",
            "Other"
        ]

        self.category_var = ctk.StringVar(value=self.categories[0])
        self.dropdown_category = ctk.CTkOptionMenu(
            form_frame,
            values=self.categories,
            variable=self.category_var,
            command=self.category_changed
        )
        self.dropdown_category.pack(side="left", padx=5)

        # Custom category input (hidden until Other)
        self.entry_custom_category = ctk.CTkEntry(form_frame, placeholder_text="Custom Category")

        self.entry_amount = ctk.CTkEntry(form_frame, placeholder_text="Amount", width=100)
        self.entry_amount.pack(side="left", padx=5)

        add_btn = ctk.CTkButton(form_frame, text="Add", command=self.add_expense)
        add_btn.pack(side="left", padx=10)

        # -----------------------------------
        # Scrollable list area
        # -----------------------------------
        self.list_frame = ctk.CTkScrollableFrame(self, label_text="Your Expenses")
        self.list_frame.pack(expand=True, fill="both", pady=10)

        self.checkboxes = []

        remove_btn = ctk.CTkButton(self, text="Remove Selected", command=self.remove_selected)
        remove_btn.pack(pady=5)

        # ---------------------------------------------------------
        # TOTAL BAR (bottom)
        # ---------------------------------------------------------

        self.total_frame = ctk.CTkFrame(self)
        self.total_frame.pack(fill="x", pady=(10, 5))

        self.total_label = ctk.CTkLabel(self.total_frame, text="Total: €0.00", font=("Arial", 15, "bold"))
        self.total_label.pack(side="left", padx=10)

        # Load initial data
        self.refresh_expense_list(
            filter_by=self.filter_var.get(),
            sort_by=self.sort_var.get()
        )

        

    # ---------------------------------------------------------
    # NEW: Load all categories from the DB
    # ---------------------------------------------------------
    def get_all_categories_from_db(self, include_all=False):
        """Returns a list of unique categories from the DB."""
        user = self.controller.current_user
        expenses = fetch_expenses(user["id"], user["username"])

        categories = set()

        for _, _, category, _, _ in expenses:
            categories.add(category)

        # Sort alphabetically
        categories = sorted(categories)

        if include_all:
            return ["All"] + categories

        return categories

    # ---------------------------------------------------------
    # When user selects category in Add form
    # ---------------------------------------------------------
    def category_changed(self, selected_value):
        if selected_value == "Other":
            self.entry_custom_category.pack(side="left", padx=5)
        else:
            self.entry_custom_category.pack_forget()

    # ---------------------------------------------------------
    # Apply category filter
    # ---------------------------------------------------------
    def apply_filter_or_sort(self, event=None):
        selected_category = self.filter_var.get()
        selected_sort = self.sort_var.get()
        self.refresh_expense_list(filter_by=selected_category, sort_by=selected_sort)

    # ---------------------------------------------------------
    # Refresh expense list (now supports filtering)
    # ---------------------------------------------------------
    def refresh_expense_list(self, filter_by="All", sort_by="Date (Newest)"):

        # Clear previous checkboxes
        for cb in self.checkboxes:
            cb.destroy()

        self.checkboxes.clear()

        user = self.controller.current_user
        expenses = fetch_expenses(user["id"], user["username"])

        # Apply filter
        if filter_by != "All":
            expenses = [exp for exp in expenses if exp[2] == filter_by]

        if not expenses:
            empty_label = ctk.CTkLabel(self.list_frame, text="No expenses found.")
            empty_label.pack(pady=5)
            self.checkboxes.append(empty_label)
            return
        
        if sort_by == "Date (Newest)":
            expenses.sort(key=lambda e: e[4], reverse=True)  # timestamp descending
        elif sort_by == "Date (Oldest)":
            expenses.sort(key=lambda e: e[4])  # timestamp ascending
        elif sort_by == "Amount (High → Low)":
            expenses.sort(key=lambda e: e[3], reverse=True)
        elif sort_by == "Amount (Low → High)":
            expenses.sort(key=lambda e: e[3])
        elif sort_by == "Title (A → Z)":
            expenses.sort(key=lambda e: e[1].lower())
        elif sort_by == "Title (Z → A)":
            expenses.sort(key=lambda e: e[1].lower(), reverse=True)
        elif sort_by == "Category (A → Z)":
            expenses.sort(key=lambda e: e[2].lower())

        total = sum(e[3] for e in expenses)
        self.total_label.configure(text=f"Total:  €{total:.2f}")

        # Create rows
        for exp in expenses:
            exp_id, title, category, amount, timestamp = exp

            text = f"{title} | {category} | ${amount:.2f} | {timestamp}"

            var = ctk.BooleanVar()
            cb = ctk.CTkCheckBox(
                master=self.list_frame,
                text=text,
                variable=var
            )
            cb.expense_id = exp_id
            cb.var = var
            cb.pack(anchor="w", pady=3)

            self.checkboxes.append(cb)

        # Update filter dropdown (in case new categories were added)
        self.filter_dropdown.configure(
            values=self.get_all_categories_from_db(include_all=True)
        )

    # ---------------------------------------------------------
    # ADD EXPENSE
    # ---------------------------------------------------------

    


    def add_expense(self):
        title = self.entry_title.get().strip()
        category = self.category_var.get()
        amount = self.entry_amount.get().strip()

        if category == "Other":
            custom = self.entry_custom_category.get().strip()
            if custom:
                category = custom
            else:
                return

        if not title or not category or not amount:
            return

        try:
            amount = float(amount)
        except ValueError:
            return

        user = self.controller.current_user

        expense_date = self.entry_date.get().strip()

        insert_expense(
            user_id=user["id"],
            username=user["username"],
            title=title,
            category=category,
            amount=amount,
            timestamp=expense_date
        )

        # Clear inputs
        self.entry_title.delete(0, "end")
        self.entry_amount.delete(0, "end")
        self.entry_custom_category.delete(0, "end")

        # Refresh list + update categories in filter
        self.refresh_expense_list(
            filter_by=self.filter_var.get(),
            sort_by=self.sort_var.get()
        )

        if hasattr(self.controller, "main_app"):
            analytics_page = self.controller.main_app.pages.get("analytics")
            if analytics_page:
                analytics_page.refresh_all()


    # ---------------------------------------------------------
    # REMOVE SELECTED EXPENSES
    # ---------------------------------------------------------
    def remove_selected(self):
        user = self.controller.current_user

        for cb in self.checkboxes:
            if hasattr(cb, "var") and cb.var.get():
                delete_expense(user["id"], user["username"], cb.expense_id)

        # Refresh list + update filter
        self.refresh_expense_list(
            filter_by=self.filter_var.get(),
            sort_by=self.sort_var.get()
        )

        if hasattr(self.controller, "main_app"):
            analytics_page = self.controller.main_app.pages.get("analytics")
            if analytics_page:
                analytics_page.refresh_all()
