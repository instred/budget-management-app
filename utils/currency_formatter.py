def format_currency(amount: float, currency_symbol: str) -> str:
    """Helper function for currency formatting"""
    
    if currency_symbol == "JPY":
        formatted_amount = f"{int(round(amount)):,}" 
    else:
        formatted_amount = f"{amount:,.2f}"

    return f"{formatted_amount} {currency_symbol}"