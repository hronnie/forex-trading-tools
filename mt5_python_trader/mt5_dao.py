# mt5_dao.py
import MetaTrader5 as mt5

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
