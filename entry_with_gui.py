import tkinter as tk
from tkinter import ttk
import yfinance as yf
import MetaTrader5 as mt5



def get_current_price(symbol):
    """
    Fetches the current price of the given symbol from Yahoo Finance, with a fallback for different key names.
    
    :param symbol: The ticker symbol of the asset to fetch the current price for.
    :return: The current price of the asset, or None if not found.
    """
    ticker = yf.Ticker(symbol)
    ticker_info = ticker.info
    # Attempt to fetch the current price from various possible keys
    possible_keys = ['regularMarketPrice', 'price', 'ask', 'bid']
    for key in possible_keys:
        if key in ticker_info:
            return ticker_info[key]
    return None  # Return None if no relevant key is found


def forex_trade_calculator(symbol, leverage, base_currency, account_balance, risk_percent, stop_loss_pips):
    """
    Calculates the forex trading values based on the provided parameters.
    
    :param symbol: Name of the currency pair traded
    :param leverage: The leverage ratio (e.g., 30 for 1:30 leverage)
    :param base_currency: The base currency of the trader's account
    :param account_balance: The current balance of the account
    :param risk_percent: The percentage of the account balance the trader is willing to risk
    :param stop_loss_pips: The stop loss value in pips
    
    :return: A dictionary with the calculated maximum lot size, risk-respecting lot size, and pip value.
    """
    # Determine the correct symbol for fetching the conversion rate
    conversion_rate = 1  # Default to 1 if no conversion is needed

    # Constants
    units_per_lot = 100000  # Number of units per 1 standard lot
    pip_value_per_lot = 10  # Value of one pip for a standard lot in USD
    
    # Calculating maximum lot size that can be bought with the current balance and leverage
    max_lot_size = (account_balance * leverage) / (units_per_lot * conversion_rate)
    
    # Calculating the money at risk
    money_at_risk = account_balance * (risk_percent / 100)
    
    # Calculating the lot size that respects the risk tolerance
    # Formula: (money at risk) / (stop loss in pips * pip value per lot * conversion rate)
    risk_respecting_lot_size = money_at_risk / (stop_loss_pips * pip_value_per_lot * conversion_rate)
    
    # Calculating how much money a pip worth based on the risk-respecting lot size
    # Formula: (risk respecting lot size * units per lot * pip value per lot) / units per lot
    pip_value = risk_respecting_lot_size * pip_value_per_lot
    
    return {
        "maximum_lot_size": round(max_lot_size, 2),
        "risk_respecting_lot_size": round(risk_respecting_lot_size, 2),
        "pip_value": round(pip_value, 2)
    }



def create_mt5_order(lot_size, symbol, is_buy: bool, sl_pips, stop_limit_price = None):
    point = mt5.symbol_info(symbol).point
    price = mt5.symbol_info_tick(symbol).ask
    action = mt5.SYMBOL_TRADE_EXECUTION_MARKET
    if stop_limit_price != None:
        price = stop_limit_price
        action = mt5.TRADE_ACTION_PENDING
    
    one_pip = 10 * point

    sl_price = None
    tp_price = None
    type = None
    if is_buy:
        type = mt5.ORDER_TYPE_BUY
        sl_price = price - sl_pips * one_pip
        tp_price = price + sl_pips * one_pip * 3
    else: 
        type = mt5.ORDER_TYPE_SELL
        sl_price = price + sl_pips * one_pip
        tp_price = price - sl_pips * one_pip * 3

    if is_buy and stop_limit_price != None:
        type = mt5.ORDER_TYPE_BUY_STOP_LIMIT
    if is_buy != True and stop_limit_price != None: 
        type = mt5.ORDER_TYPE_SELL_STOP_LIMIT
    

    deviation = 20

    request = {
        "action": action,
        "symbol": symbol,
        "volume": lot_size,
        "type": type,
        "price": price,
        "stoplimit": price,
        "sl": sl_price,
        "tp": tp_price,
        "deviation": deviation,
        "comment": "hronnie python entry",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }


    if stop_limit_price == None: 
        print(f"Market order at {price} with {symbol}")
    else:
        print(f"Limit order at {price} with {symbol}")    
    print(f"Lot size: {lot_size}")
    print(f"Type: {type}")
    print(f"SL: ${sl_price}")
    print(f"TP: ${tp_price}")


    result = mt5.order_send(request)
    print(result)
    return result

def create_mt5_order_market(lot_size, symbol, is_buy: bool, sl_pips):
    return create_mt5_order(lot_size, symbol, is_buy, sl_pips)

def create_mt5_order_stop_limit(lot_size, symbol, is_buy: bool, sl_pips, stop_limit_price):
    return create_mt5_order(lot_size, symbol, is_buy, sl_pips, stop_limit_price)    


def enter_main(symbol_input, stop_loss_pips_input, is_buy_input):

    ######## START TRADE INPUTS ########

    is_stop_limit = False
    stop_limit_price = 1

    ######## END TRADE INPUTS ########


    mt5.initialize()
    account = mt5.account_info()
    base_currency_input = "EUR"
    account_balance_input = account.balance
    risk_percent_input = 1
    leverage_input = 100


    calculated_info = forex_trade_calculator(symbol=symbol_input, leverage=leverage_input, base_currency=base_currency_input, account_balance=account_balance_input, risk_percent=risk_percent_input, stop_loss_pips=stop_loss_pips_input)
    print(f"Maximum Lot size: {calculated_info['maximum_lot_size']}")
    print(f"Risk respecting lot size: {calculated_info['risk_respecting_lot_size']}")
    print(f"Pip value: € {calculated_info['pip_value']}")
    lot_size = None
    if calculated_info['risk_respecting_lot_size'] >  calculated_info['maximum_lot_size']: 
        lot_size = calculated_info['maximum_lot_size']
    else: 
        lot_size = calculated_info['risk_respecting_lot_size']
    
    order_send_result = None
    if is_stop_limit: 
        order_send_result = create_mt5_order_stop_limit(lot_size - 0.01, symbol_input, is_buy_input, stop_loss_pips_input,stop_limit_price)
    else: 
        order_send_result = create_mt5_order_market(lot_size, symbol_input, is_buy_input, stop_loss_pips_input)

    calculated_info['comment'] = order_send_result.comment
    return calculated_info

def display_results(calculated_info):
    status = "Failed"
    if calculated_info['comment'] == "Request executed":
        status = "Success"

    result_message = (f"Order execution status: {status}\n"
                      f"Status comment: {calculated_info['comment']}\n"
                      f"Maximum Lot size: {calculated_info['maximum_lot_size']}\n"
                      f"Risk respecting lot size: {calculated_info['risk_respecting_lot_size']}\n"
                      f"Pip value: € {calculated_info['pip_value']}")
    
    # Update the status message variable
    status_message_var.set(result_message)


def on_buy():
    global stop_loss_pips_input
    stop_loss_pips_input = float(stop_loss_pips_entry.get())
    calculated_info_result = enter_main(pair_var.get(), stop_loss_pips_input, True)
    display_results(calculated_info_result)
    print(f"Buy order for {pair_var.get()} with stop loss at {stop_loss_pips_input} pips")

def on_sell():
    global stop_loss_pips_input
    stop_loss_pips_input = float(stop_loss_pips_entry.get())
    calculated_info_result = enter_main(pair_var.get(), stop_loss_pips_input, False)
    display_results(calculated_info_result)
    print(f"Sell order for {pair_var.get()} with stop loss at {stop_loss_pips_input} pips")

# Set up the Tkinter window
root = tk.Tk()
root.title("Forex Trade Calculator")
root.geometry("600x400")  # Make the window bigger

# Styling
style = ttk.Style()
style.configure("TLabel", font=("Arial", 12), padding=10)
style.configure("TButton", font=("Arial", 10), padding=10)
style.configure("TEntry", padding=5)
style.configure("TCombobox", padding=5)

# Currency pair selection
pair_var = tk.StringVar()
pair_label = ttk.Label(root, text="Select Currency Pair:", style="TLabel")
pair_label.pack()
pair_combobox = ttk.Combobox(root, textvariable=pair_var, width=20)
pair_combobox['values'] = ("EURUSD", "GBPUSD", "EURGPB", "USDJPY", "USDCAD", "USDCHF", "AUDUSD", "GBPJPY", "AUDJPY", "NZDUSD")  
pair_combobox.pack(pady=5)

# Stop loss pips input
stop_loss_pips_label = ttk.Label(root, text="Stop Loss Pips:", style="TLabel")
stop_loss_pips_label.pack()
stop_loss_pips_entry = ttk.Entry(root, width=25)
stop_loss_pips_entry.pack(pady=5)


# Buy and Sell buttons
buy_button = tk.Button(root, text="Buy", command=on_buy, bg="green", fg="white", font=("Arial", 12), height=2, width=10)
buy_button.pack(side=tk.RIGHT, padx=20, pady=10)

sell_button = tk.Button(root, text="Sell", command=on_sell, bg="red", fg="white", font=("Arial", 12), height=2, width=10)
sell_button.pack(side=tk.LEFT, padx=20, pady=10)

status_message_var = tk.StringVar()  # This variable will hold the message text
status_message_var.set("Status: Ready")  # Default message
status_message_label = ttk.Label(root, textvariable=status_message_var, font=("Arial", 10), foreground="blue")
status_message_label.pack(pady=10)

# Start the GUI loop
root.mainloop()
