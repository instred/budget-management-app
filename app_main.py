import customtkinter as ctk
from summary_page import SummaryPage
from expenses_page import ExpensesPage
from analytics_page import AnalyticsPage
from settings_page import AccountSettingsPage

class MainApp(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.pack(expand=True, fill="both")

        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(expand=True, fill="both", padx=20, pady=20)

        self.tab_summary = self.tabview.add("Summary Page (Dashboard)")
        self.tab_expenses = self.tabview.add("Expenses Management Page")
        self.tab_analytics = self.tabview.add("Analytics")
        self.tab_settings = self.tabview.add("Account Settings")

        self.pages = {
            "summary": SummaryPage(self.tab_summary, controller),
            "expenses": ExpensesPage(self.tab_expenses, controller),
            "analytics": AnalyticsPage(self.tab_analytics, controller),
            "settings": AccountSettingsPage(self.tab_settings, controller),
        }

        # FIX: use command instead of bind
        self.tabview.configure(command=self.on_tab_change)

        logout_btn = ctk.CTkButton(self, text="Logout", width=80,
                                   command=self.controller.show_login)
        logout_btn.place(relx=0.92, rely=0.02)

    def on_tab_change(self):
        if self.tabview.get() == "Summary Page (Dashboard)":
            self.pages["summary"].refresh()
