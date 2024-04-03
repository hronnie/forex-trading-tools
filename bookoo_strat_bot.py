import MetaTrader5 as mt5
import time
import datetime
import yfinance as yf
import logging



mt5.initialize()

current_date = datetime.datetime.now().strftime("%Y-%m-%d")

log_filename = f"C:\\Users\\aronharsfalvi\\Documents\\log\\trading_bot_{current_date}.log"

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler(log_filename),
                        logging.StreamHandler()
                    ])
logger = logging.getLogger(__name__)

def determine_conversion_symbol(account_base_currency, traded_symbol): 
    base_currency = traded_symbol[:3]
    if account_base_currency != base_currency:
        return f"{base_currency}{account_base_currency}=X"    


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
    conversion_symbol = determine_conversion_symbol(base_currency, symbol)
    conversion_rate = 1  # Default to 1 if no conversion is needed
    if conversion_symbol:
        conversion_rate = get_current_price(conversion_symbol)
        if conversion_rate is None:
            logger.error("Error fetching conversion rate.")
            return None
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
        logger.info(f"Market order at {price} with {symbol}")
    else:
        logger.info(f"Limit order at {price} with {symbol}")    
    logger.info(f"Lot size: {lot_size}")
    display_type = "Long"
    if type == 1: 
        display_type = "Short"
    logger.info(f"Type: {display_type}")
    logger.info(f"SL: ${sl_price}")
    logger.info(f"TP: ${tp_price}")


    result = mt5.order_send(request)
    logger.info(result)

def create_mt5_order_market(lot_size, symbol, is_buy: bool, sl_pips):
    create_mt5_order(lot_size, symbol, is_buy, sl_pips)

def create_mt5_order_stop_limit(lot_size, symbol, is_buy: bool, sl_pips, stop_limit_price):
    create_mt5_order(lot_size, symbol, is_buy, sl_pips, stop_limit_price)    



def enter_position(symbol_input, stop_loss_pips_input, is_buy_input):

    ######## START TRADE INPUTS ########

    is_stop_limit = False
    stop_limit_price = 1.08726

    ######## END TRADE INPUTS ########


    mt5.initialize()
    account = mt5.account_info()
    base_currency_input = "EUR"
    account_balance_input = account.balance
    risk_percent_input = 1
    leverage_input = 5


    if account.margin_free == account.balance: 
        calculated_info = forex_trade_calculator(symbol=symbol_input, leverage=leverage_input, base_currency=base_currency_input, account_balance=account_balance_input, risk_percent=risk_percent_input, stop_loss_pips=stop_loss_pips_input)
        lot_size = None
        if calculated_info['risk_respecting_lot_size'] >  calculated_info['maximum_lot_size']: 
            lot_size = calculated_info['maximum_lot_size']
        else: 
            lot_size = calculated_info['risk_respecting_lot_size']
        if is_stop_limit: 
            create_mt5_order_stop_limit(lot_size - 0.01, symbol_input, is_buy_input, stop_loss_pips_input,stop_limit_price)
        else: 
            create_mt5_order_market(lot_size, symbol_input, is_buy_input, stop_loss_pips_input)
        

    else: 
        logger.error("There is already a position")

def is_current_position_exist(symbol): 
    positions = mt5.positions_get(symbol=symbol)
    return len(positions) > 0

def get_last_position(symbol): 
    if not mt5.initialize():
        logger.error("initialize() failed")

    from_date = datetime.datetime.now() - datetime.timedelta(days=2)  # Adjusted to your needs
    to_date = datetime.datetime.now() + datetime.timedelta(days=1)  # Includes today by adding a day

    deals = mt5.history_deals_get(from_date, to_date)
    if deals is None:
        logger.error("No deals found")
        return None

    # Filter deals by symbol and sort them by time
    filtered_deals = [deal for deal in deals if deal.symbol == symbol]
    filtered_deals.sort(key=lambda x: x.time, reverse=True)

    # Check if we found any deals and print the most recent
    if filtered_deals:
        last_deal = filtered_deals[0]
        logger.info(f"Last deal for {symbol}: ticket={last_deal.ticket}, type={last_deal.type}, volume={last_deal.volume}, price={last_deal.price}, profit={last_deal.profit}")
        return last_deal
    else:
        logger.error(f"No deals found for {symbol}")



def main():
    global isFirstPosition
    global stat_profit
    global stat_loss_trades
    global stat_win_trades
    if is_current_position_exist(bot_symbol) == False and isFirstPosition == True: # If there is no position and start, create one
        logger.info("*****************************************************************")
        logger.info("*****************************************************************")
        logger.info("*****************************************************************")
        logger.info("*****************   STRATEGY START   ****************************")
        logger.info("*****************************************************************")
        logger.info("*****************************************************************")
        logger.info("*****************************************************************")

        is_buy_input = False
        if startDirection == "LONG": 
            is_buy_input = True
        logger.info('Creating first position')
        enter_position(bot_symbol, stop_loss_pips_input, is_buy_input)
        isFirstPosition = False
    elif is_current_position_exist(bot_symbol) == False and isFirstPosition == False:  # If there is no position and not start:
        current_last_position = get_last_position(bot_symbol)
        logger.debug(f"Last deal for {bot_symbol}: ticket={current_last_position.ticket}, type={current_last_position.type}, volume={current_last_position.volume}, price={current_last_position.price}, profit={current_last_position.profit}")
        is_buy_input = False
        stat_profit += current_last_position.profit
        if current_last_position.profit < 0 and current_last_position.type == mt5.ORDER_TYPE_BUY:
            logger.debug("Last SHORT position was a LOSS therefore switching to LONG")
            is_buy_input = True
            stat_loss_trades += 1
        elif current_last_position.profit >= 0 and current_last_position.type == mt5.ORDER_TYPE_BUY:
            logger.debug("Last SHORT position was WIN therefore staying to SHORT")
            is_buy_input = False
            stat_win_trades += 1
        elif current_last_position.profit < 0 and current_last_position.type == mt5.ORDER_TYPE_SELL:
            logger.debug("Last LONG position was LOSS therefore switching to SHORT")
            is_buy_input = False
            stat_loss_trades += 1
        elif current_last_position.profit >= 0 and current_last_position.type == mt5.ORDER_TYPE_SELL:
            logger.debug("Last LONG position was WIN therefore staying to LONG")
            is_buy_input = True
            stat_win_trades += 1

        enter_position(bot_symbol, stop_loss_pips_input, is_buy_input)
        logger.debug("***************** START Current statistics *****************")
        logger.debug(f"Profit: {stat_profit}")
        logger.debug(f"Lost trades: {stat_loss_trades}")
        logger.debug(f"Win trades: {stat_win_trades}")
        if stat_win_trades + stat_loss_trades > 0:
            win_ratio = (stat_win_trades / (stat_win_trades + stat_loss_trades)) * 100
            logger.debug(f"Win Ratio: {round(win_ratio, 2)}%")
        else:
            logger.debug("Win Ratio: No trades completed")
        logger.debug("***************** END Current statistics *****************")
    else:
        logger.debug('There is a running position. No action needed.')

isFirstPosition = True
startDirection = "SHORT" # LONG/SHORT
nextDirection = "" # LONG/SHORT
bot_symbol = "EURUSD"
stop_loss_pips_input = 0.1

stat_profit = 0
stat_loss_trades = 0
stat_win_trades = 0

while True:
    logger.debug("********************** New thread is starting **********************")
    main()  # Call your method
    logger.debug("********************** Thread ended **********************")
    time.sleep(10)  # Wait for 60 seconds before the next loop iteration

