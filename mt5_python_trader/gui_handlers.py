def display_results(position_info):
    status = "Failed"
    if position_info['comment'] == "Request executed":
        status = "Success"

    result_message = (f"Order execution status: {status}\n"
                      f"Status comment: {position_info['comment']}\n"
                      f"Money at risk: {position_info['money_at_risk']}\n"
                      f"Risk respecting lot size: {position_info['risk_respecting_lot_size']}\n"
                      f"Pip value: € {position_info['pip_value']}")
    
    return result_message
    