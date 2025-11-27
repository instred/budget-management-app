# Budget App

A personal finance management tool built in **Python** using **CustomTkinter**. Track your expenses, manage categories, and visualize your spending habits with interactive charts and summaries.
This app is the first part of the full project. Second part is to integrate it with azure to store data, authenticate users and add analytical features.
---

## 📌 Features

### Authentication
- User login and registration
- Logout functionality

### Expenses Management
- Add and remove expenses
- Assign categories to expenses (with custom categories)
- Select expense date using a calendar popup
- View last expenses and total spending
- Filter and sort expenses

### Analytics
- Bar chart by category
- Monthly spending line chart
- Top 5 most expensive purchases
- Budget tracker
- Expense timeline
- All charts and summaries update dynamically when expenses change

### Pages / Interface
- **Summary Page (Dashboard)**: Quick overview of spending
- **Expenses Management Page**: Add, remove, and filter expenses
- **Analytics Page**: Charts, top expenses, timeline, and budget tracker
- **Account Settings Page**: Manage user account details


## Current Plans
- Track monthly expenses with a user-defined budget
- Add more detailed analytics and filtering options
- Add settings page
- Refactor code files, move helper functions into separate file

## Future Plans
- Integration with **Azure** for:
  - Cloud storage
  - User authentication
  - Syncing data across devices
- Enable multi-device access and secure remote storage


##  Installation

Make sure to have Python 3.10+ installed.

1. Clone the repository:
   ```bash
   git clone https://github.com/instred/budget-management-app
   cd budget-app
   ```

2. Create a virtual environment:

    ```bash
    python -m venv .venv
    source .venv/bin/activate    # Windows: .venv\Scripts\activate

3. Install dependencies

    ```bash 
    pip install -r requirements.txt

4. Run the application

    ```bash
    python main.py