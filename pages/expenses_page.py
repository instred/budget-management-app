import customtkinter as ctk
from database import insert_expense, delete_expense, fetch_expenses
from tkcalendar import Calendar
from datetime import datetime
import tkinter as tk
from tkinter import filedialog, messagebox
import pandas as pd
import threading

class ExpensesPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.pack(fill="both", expand=True, padx=10, pady=10)

        user = controller.current_user
        if not user:
            return

        self.default_categories = ["Food", "Transport", "Housing", "Entertainment", "Shopping", "Health", "Other"]
        self.categories_from_db = ["All"] + self.default_categories

        # Title
        ctk.CTkLabel(self, text="Manage Expenses", font=("Arial", 22)).pack(pady=10)

        # Filter & Sort
        filter_sort_frame = ctk.CTkFrame(self)
        filter_sort_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(filter_sort_frame, text="Filter:").pack(side="left", padx=5)
        self.filter_var = ctk.StringVar(value="All")
        self.filter_dropdown = ctk.CTkOptionMenu(
            filter_sort_frame,
            values=self.categories_from_db,
            variable=self.filter_var,
            command=self.apply_filter_or_sort
        )
        self.filter_dropdown.pack(side="left", padx=5)
        ctk.CTkLabel(filter_sort_frame, text="Sort:").pack(side="left", padx=20)
        self.sort_var = ctk.StringVar(value="Date (Newest)")
        self.sort_dropdown = ctk.CTkOptionMenu(
            filter_sort_frame,
            values=["Date (Newest)", "Date (Oldest)", "Amount (High → Low)",
                    "Amount (Low → High)", "Title (A → Z)", "Title (Z → A)",
                    "Category (A → Z)"],
            variable=self.sort_var,
            command=self.apply_filter_or_sort
        )
        self.sort_dropdown.pack(side="left", padx=5)

        # Add Expense Form
        form_frame = ctk.CTkFrame(self)
        form_frame.pack(fill="x", pady=10)
        self.entry_title = ctk.CTkEntry(form_frame, placeholder_text="Expense Title", width=150)
        self.entry_title.pack(side="left", padx=5)
        self.entry_date = ctk.CTkEntry(form_frame, width=120)
        self.entry_date.pack(side="left", padx=5)
        self.entry_date.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.entry_date.bind("<Button-1>", lambda e: pick_date())
        def pick_date():
            current_value = self.entry_date.get()
            try:
                date_obj = datetime.strptime(current_value, "%Y-%m-%d")
            except ValueError:
                date_obj = datetime.today()
            def on_date_selected():
                self.entry_date.delete(0, "end")
                self.entry_date.insert(0, cal.get_date())
                top.destroy()
            top = tk.Toplevel(self)
            top.title("Select Date")
            cal = Calendar(top, selectmode="day", date_pattern="yyyy-mm-dd",
                           year=date_obj.year, month=date_obj.month, day=date_obj.day)
            cal.pack(padx=10, pady=10)
            ctk.CTkButton(top, text="Select", command=on_date_selected).pack(pady=5)

        self.categories = self.default_categories
        self.category_var = ctk.StringVar(value=self.categories[0])
        self.dropdown_category = ctk.CTkOptionMenu(
            form_frame, values=self.categories, variable=self.category_var,
            command=self.category_changed
        )
        self.dropdown_category.pack(side="left", padx=5)
        self.entry_custom_category = ctk.CTkEntry(form_frame, placeholder_text="Custom Category")
        self.entry_amount = ctk.CTkEntry(form_frame, placeholder_text="Amount", width=100)
        self.entry_amount.pack(side="left", padx=5)
        ctk.CTkLabel(form_frame, text="").pack(side="left", expand=True)
        ctk.CTkButton(form_frame, text="Remove Selected", command=self.remove_selected).pack(side="right", padx=10)
        ctk.CTkButton(form_frame, text="Add", command=self.add_expense).pack(side="left", padx=10)

        # Header frame
        header_frame = ctk.CTkFrame(self)
        header_frame.pack(fill="x", pady=(10,0), padx=10)
        self.select_all_var = ctk.BooleanVar(value=False)
        self.select_all_cb = ctk.CTkCheckBox(header_frame, text="", variable=self.select_all_var,
                                             command=self.toggle_select_all)
        self.select_all_cb.pack(side="left", padx=(0,5))
        ctk.CTkLabel(header_frame, text="Your Expenses", font=("Arial", 16)).place(relx=0.5, rely=0.5, anchor="center")

        # Scrollable list area
        self.list_frame = ctk.CTkScrollableFrame(self)
        self.list_frame.pack(expand=True, fill="both", pady=10, padx=10)
        self.checkboxes = []

        # Total bar
        self.total_frame = ctk.CTkFrame(self)
        self.total_frame.pack(fill="x", pady=(10,5))
        self.total_label = ctk.CTkLabel(self.total_frame, text="Total: N/A", font=("Arial", 15, "bold"))
        self.total_label.pack(side="left", padx=10)

        # Action row
        action_row = ctk.CTkFrame(self)
        action_row.pack(fill="x", pady=5)
        action_row.grid_columnconfigure(0, weight=1)
        ctk.CTkButton(action_row, text="Export CSV", width=120, command=self.export_csv).grid(row=0, column=1, padx=5)
        ctk.CTkButton(action_row, text="Import CSV", width=120, command=self.import_csv).grid(row=0, column=2, padx=5)

        # Initial refresh
        self.refresh()

    # --------------------- Background Refresh ---------------------
    def refresh(self):
        """Start background thread to fetch all expenses and categories."""
        user = self.controller.current_user
        if not user:
            return
        threading.Thread(target=self.perform_full_refresh_task, args=(user["id"],), daemon=True).start()

    def perform_full_refresh_task(self, user_id):
        """Fetch all expenses and categories in background."""
        expenses, categories = [], []
        try:
            expenses = fetch_expenses(user_id)
            categories = sorted({exp[2] for exp in expenses})
        except Exception as e:
            print(f"Error loading expenses: {e}")
            self.controller.after(1, lambda: messagebox.showerror("DB Error", "Failed to load expense data."))
        self.controller.after(1, lambda: self.complete_full_refresh(expenses, categories))

    def complete_full_refresh(self, expenses, categories_from_db):
        """Update GUI with fetched expenses and categories."""
        self.categories_from_db = ["All"] + categories_from_db
        self.filter_dropdown.configure(values=self.categories_from_db)
        self.update_expense_list_gui(expenses, self.filter_var.get(), self.sort_var.get())

    # --------------------- Filter & Sort ---------------------
    def apply_filter_or_sort(self, event=None):
        """Start background thread for filtering/sorting."""
        user = self.controller.current_user
        if not user:
            return
        threading.Thread(target=self.perform_filter_sort_task, args=(user["id"],), daemon=True).start()

    def perform_filter_sort_task(self, user_id):
        """Fetch expenses in background for filtering/sorting."""
        expenses = []
        try:
            expenses = fetch_expenses(user_id)
        except Exception as e:
            print(f"Error fetching expenses: {e}")
            self.controller.after(1, lambda: messagebox.showerror("DB Error", "Failed to load expenses."))
        self.controller.after(1, lambda: self.update_expense_list_gui(expenses, self.filter_var.get(), self.sort_var.get()))

    # --------------------- GUI Update ---------------------
    def update_expense_list_gui(self, expenses, filter_by="All", sort_by="Date (Newest)"):
        """Update GUI expense list based on data, filter, and sort."""
        for cb in self.checkboxes:
            cb.destroy()
        self.checkboxes.clear()

        if filter_by != "All":
            expenses = [e for e in expenses if e[2] == filter_by]

        if sort_by == "Date (Newest)": expenses.sort(key=lambda e: e[4], reverse=True)
        elif sort_by == "Date (Oldest)": expenses.sort(key=lambda e: e[4])
        elif sort_by == "Amount (High → Low)": expenses.sort(key=lambda e: e[3], reverse=True)
        elif sort_by == "Amount (Low → High)": expenses.sort(key=lambda e: e[3])
        elif sort_by == "Title (A → Z)": expenses.sort(key=lambda e: e[1].lower())
        elif sort_by == "Title (Z → A)": expenses.sort(key=lambda e: e[1].lower(), reverse=True)
        elif sort_by == "Category (A → Z)": expenses.sort(key=lambda e: e[2].lower())

        total = sum(e[3] for e in expenses)
        self.total_label.configure(text=f"Total: {self.controller.format_currency(total)}")

        if not expenses:
            lbl = ctk.CTkLabel(self.list_frame, text="No expenses found.")
            lbl.pack(pady=5)
            self.checkboxes.append(lbl)
            self.select_all_var.set(False)
            return

        self.select_all_cb.pack(anchor="nw", padx=5, pady=5)
        for exp in expenses:
            exp_id, title, category, amount, date = exp
            cb = ctk.CTkCheckBox(master=self.list_frame, text=f"{title} | {category} | {self.controller.format_currency(amount)} | {date}", variable=ctk.BooleanVar())
            cb.expense_id = exp_id
            cb.var = cb.cget("variable")
            cb.pack(anchor="w", pady=3)
            self.checkboxes.append(cb)
        self.select_all_var.set(all(cb.var.get() for cb in self.checkboxes if hasattr(cb, "var")))
        self.filter_dropdown.configure(values=["All"] + sorted({exp[2] for exp in expenses}))

    # --------------------- Add Expense ---------------------
    def add_expense(self):
        """Validate input and start background thread to insert expense."""
        title = self.entry_title.get().strip()
        category = self.category_var.get()
        if category == "Other":
            custom = self.entry_custom_category.get().strip()
            if custom:
                category = custom
            else:
                messagebox.showerror("Error", "Please provide a custom category name.")
                return
        amount = self.entry_amount.get().strip()
        if not title or not category or not amount:
            messagebox.showerror("Error", "All fields (Title, Category, Amount) are required.")
            return
        try:
            amount_float = float(amount)
        except ValueError:
            messagebox.showerror("Error", "Amount must be a number.")
            return
        user_id = self.controller.current_user["id"]
        date = self.entry_date.get().strip()
        threading.Thread(target=self.perform_add_task, args=(user_id, title, category, amount_float, date), daemon=True).start()

    def perform_add_task(self, user_id, title, category, amount, date):
        """Insert expense in DB (background thread)."""
        try:
            insert_expense(user_id, title, category, amount, date)
            self.controller.after(1, self.complete_add_task)
            self.perform_full_refresh_task(user_id)
        except Exception as e:
            print(f"Error inserting expense: {e}")
            self.controller.after(1, lambda: messagebox.showerror("DB Error", "Failed to insert expense."))

    def complete_add_task(self):
        """Clear input fields and notify other pages."""
        self.entry_title.delete(0, "end")
        self.entry_amount.delete(0, "end")
        self.entry_custom_category.delete(0, "end")
        if hasattr(self.controller, "main_app"):
            for page in ["analytics", "summary"]:
                p = self.controller.main_app.pages.get(page)
                if p: p.refresh_all() if page=="analytics" else p.refresh()

    # --------------------- Remove Expense ---------------------
    def remove_selected(self):
        """Collect IDs and start background thread to delete."""
        user_id = self.controller.current_user["id"]
        ids_to_delete = [cb.expense_id for cb in self.checkboxes if hasattr(cb, "var") and cb.var.get()]
        if not ids_to_delete:
            messagebox.showinfo("Select", "Select at least one expense to delete.")
            return
        if not messagebox.askyesno("Confirm Delete", f"Delete {len(ids_to_delete)} selected expenses?"):
            return
        threading.Thread(target=self.perform_remove_task, args=(user_id, ids_to_delete), daemon=True).start()

    def perform_remove_task(self, user_id, ids_to_delete):
        """Delete expenses in background."""
        try:
            for eid in ids_to_delete:
                delete_expense(eid, user_id)
            self.controller.after(1, self.complete_remove_task)
            self.perform_full_refresh_task(user_id)
        except Exception as e:
            print(f"Error deleting expenses: {e}")
            self.controller.after(1, lambda: messagebox.showerror("DB Error", "Failed to delete one or more expenses."))

    def complete_remove_task(self):
        """Notify other pages after deletion."""
        if hasattr(self.controller, "main_app"):
            for page in ["analytics", "summary"]:
                p = self.controller.main_app.pages.get(page)
                if p: p.refresh_all() if page=="analytics" else p.refresh()

    # --------------------- CSV Export ---------------------
    def export_csv(self):
        user_id = self.controller.current_user["id"]
        threading.Thread(target=self.perform_export_task, args=(user_id,), daemon=True).start()

    def perform_export_task(self, user_id):
        try:
            expenses = fetch_expenses(user_id)
            if not expenses:
                self.controller.after(1, lambda: messagebox.showwarning("No Data", "No expenses to export."))
                return
            df = pd.DataFrame(expenses, columns=["id", "title", "category", "amount", "date"])
            self.controller.after(1, lambda: self.save_csv_file(df))
        except Exception as e:
            self.controller.after(1, lambda: messagebox.showerror("DB Error", f"Failed to fetch data for export:\n{e}"))

    def save_csv_file(self, df):
        file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files","*.csv")], title="Save Expenses to CSV")
        if file_path:
            try:
                df.to_csv(file_path, index=False)
                messagebox.showinfo("Success", f"Expenses exported to:\n{file_path}")
            except Exception as e:
                messagebox.showerror("Save Error", f"Failed to save file:\n{e}")

    # --------------------- CSV Import ---------------------
    def import_csv(self):
        user_id = self.controller.current_user["id"]
        file_path = filedialog.askopenfilename(title="Select CSV file", filetypes=[("CSV files","*.csv")])
        if file_path:
            threading.Thread(target=self.perform_import_task, args=(user_id, file_path), daemon=True).start()

    def perform_import_task(self, user_id, file_path):
        try:
            df = pd.read_csv(file_path)
            required_cols = {"title", "category", "amount", "date"}
            if not required_cols.issubset(df.columns):
                self.controller.after(1, lambda: messagebox.showerror("Error", f"CSV must contain columns:\n{', '.join(required_cols)}"))
                return
            for _, row in df.iterrows():
                insert_expense(user_id, str(row["title"]), str(row["category"]), float(row["amount"]), str(row["date"]))
            self.controller.after(1, self.complete_import_task)
            self.perform_full_refresh_task(user_id)
        except Exception as e:
            self.controller.after(1, lambda: messagebox.showerror("Import Error", f"Failed to import CSV:\n{e}"))

    def complete_import_task(self):
        messagebox.showinfo("Success", "Expenses imported successfully!")
        if hasattr(self.controller, "main_app"):
            for page in ["analytics", "summary"]:
                p = self.controller.main_app.pages.get(page)
                if p: p.refresh_all() if page=="analytics" else p.refresh()

    # --------------------- Misc GUI Methods ---------------------
    def category_changed(self, selected_value):
        if selected_value == "Other":
            self.entry_custom_category.pack(side="left", padx=5)
        else:
            self.entry_custom_category.pack_forget()

    def toggle_select_all(self):
        for cb in self.checkboxes:
            if hasattr(cb, "var"):
                cb.var.set(self.select_all_var.get())
