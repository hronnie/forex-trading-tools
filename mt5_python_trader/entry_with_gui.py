import tkinter as tk
from tkinter import ttk

import MetaTrader5 as mt5
from mt5_dao import create_mt5_order_market, create_mt5_order_stop_limit
from forex_calculators import calculate_lot_size
from gui_handlers import display_results


def enter_main(symbol_input, stop_loss_pips_input, is_buy_input):

    ######## START TRADE INPUTS ########

    is_stop_limit = False
    stop_limit_price = 1

    ######## END TRADE INPUTS ########


    mt5.initialize()
    account = mt5.account_info()
    account_balance_input = account.balance
    risk_percent_input = 1

    lot_size, pip_value, money_at_risk = calculate_lot_size(account_balance=account_balance_input, risk_percentage=risk_percent_input, stop_loss_pips=stop_loss_pips_input, symbol=symbol_input)
 
    order_send_result = None
    if is_stop_limit: 
        order_send_result = create_mt5_order_stop_limit(lot_size - 0.01, symbol_input, is_buy_input, stop_loss_pips_input,stop_limit_price)
    else: 
        order_send_result = create_mt5_order_market(lot_size, symbol_input, is_buy_input, stop_loss_pips_input)

    position_info = {
        "risk_respecting_lot_size": lot_size,
        "pip_value": pip_value,
        "money_at_risk": money_at_risk,
        "comment": order_send_result.comment
    }
    
    return position_info




def on_buy():
    global stop_loss_pips_input
    stop_loss_pips_input = float(stop_loss_pips_entry.get())
    position_info_result = enter_main(pair_var.get(), stop_loss_pips_input, True)
    display_text = display_results(position_info_result)
    status_message_var.set(display_text)
    print(f"Buy order for {pair_var.get()} with stop loss at {stop_loss_pips_input} pips")

def on_sell():
    global stop_loss_pips_input
    stop_loss_pips_input = float(stop_loss_pips_entry.get())
    position_info_result = enter_main(pair_var.get(), stop_loss_pips_input, False)
    display_text = display_results(position_info_result)
    status_message_var.set(display_text)
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
