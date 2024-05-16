import yfinance as yf

rate_pair_map = {
    "USDCHF": "EURCHF=X",
    "EURUSD": "EURUSD=X",
    "GBPUSD": "EURUSD=X",
    "EURGBP": "EURGBP=X",
    "USDJPY": "EURJPY=X",
    "USDCAD": "EURCAD=X",
    "AUDUSD": "EURUSD=X",
    "AUDJPY": "EURJPY=X",
    "GBPJPY": "EURJPY=X",
    "NZDUSD": "EURUSD=X",
}

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

def calculate_lot_size(account_balance, risk_percentage, stop_loss_pips, symbol):
    pip_size = 0.01 if "JPY" in symbol else 0.0001
    contract_size = 100000 
    eur_conv_price = get_current_price(rate_pair_map[symbol])
    risk_amount = account_balance * (risk_percentage / 100)
    pip_value = pip_size / eur_conv_price
    lot_size = risk_amount / (stop_loss_pips * pip_value * contract_size)
    money_at_risk = stop_loss_pips * pip_value * lot_size * contract_size
    change_per_pip = round(money_at_risk / stop_loss_pips, 2)
    print(f"Lot Size: {lot_size:.3f}")
    print(f"Change per pip: €{int(change_per_pip)}")
    print(f"Money at risk: €{money_at_risk:.2f}")
    return round(lot_size, 2), change_per_pip, money_at_risk