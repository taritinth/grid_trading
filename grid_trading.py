### JUST FOR LEARNING PURPOSE USE AT YOUR OWN RISK !!!!! ####

# import neccessary package
import ccxt
import json
import pandas as pd
import time
import math
import decimal
from datetime import datetime
import pytz
import csv

import websocket
import _thread
import hmac

# Api and secret
api_key = "8eoZURlwL28c7T96cl2qzTT2HMjFZ2gl_jahaJGq"
api_secret = "j7i-8jNXGHG5s7jq_GxC2fMLARERmhigi0aiCgys"
subaccount = "AAVE_GT"
# Set your account name (ตั้งชื่อ Account ที่ต้องการให้แสดงผล)

# Exchange Details
exchange = ccxt.ftx({
    'apiKey': api_key,
    'secret': api_secret,
    'enableRateLimit': True}
)
exchange.headers = {'FTX-SUBACCOUNT': subaccount}
# Maker or Taker (วางโพซิชั่นเป็น MAKER เท่านั้นหรือไม่ True = ใช่)
post_only = True

# Name of Rebalancing Token (ใส่ชื่อเหรียญที่ต้องการ Rebalance)
token_name_lst = ["ALPHA"]
# Rebalancing Pair (ใส่ชื่อคู่ที่ต้องการ Rebalance เช่น XRP จะเป็น XRP/USD)
pair_lst = ["ALPHA/USD"]
fix_value_lst = [0]  # ไม่ต้องแก้อะไร

upper = 4  # EDIT
lower = 0.1  # EDIT
digits = [1, 10, 100, 1000, 10000, 100000]  # DO NOT EDIT

# EDIT minimum USD for buy with min_size at upper (you can input > min)
min_usd = 4
min_trade_size = 1  # EDIT
min_trade_size_decimal = 0  # EDIT INPUT DECIMAL OF MIN SIZE

# check if priceIncrement not is 0.xxx1, 0.x1, 1, you must round price number
price_decimal = 4

gap_entry = 8  # EDIT %
gap_tp = 9  # EDIT %
maker_fee = 0.02  # EDIT %

# Fix Value Setting
# capital = 100

# List to Dict Setting
token_fix_value = {token_name_lst[i]: fix_value_lst[i]
                   for i in range(len(token_name_lst))}
pair_dict = {token_name_lst[i]: pair_lst[i]
             for i in range(len(token_name_lst))}

last_price = None
open_range = 30  # percent
is_connect = False
handling_ws = False
handling_main = False

### Function Part ###


def print_underline():
    print("-------------------------------------------")


def get_time():  # เวลาปัจจุบัน
    named_tuple = time.localtime()  # get struct_time
    Time = time.strftime("%m/%d/%Y, %H:%M:%S", named_tuple)
    return Time


def get_price():
    price = exchange.fetch_ticker(pair)['last']
    return float(price)


def get_ask_price():
    ask_price = exchange.fetch_ticker(pair)['ask']
    return float(ask_price)


def get_bid_price():
    bid_price = exchange.fetch_ticker(pair)['bid']
    return float(bid_price)


def get_minimum_size():
    minimum_size = float(exchange.fetch_ticker(pair)['info']['minProvideSize'])
    return minimum_size


def get_step_size():
    step_size = float(exchange.fetch_ticker(pair)['info']['sizeIncrement'])
    return step_size


def get_step_price():
    step_price = float(exchange.fetch_ticker(pair)['info']['priceIncrement'])
    return step_price


def get_min_trade_value():
    min_trade_value = float(exchange.fetch_ticker(
        pair)['info']['sizeIncrement']) * price
    return min_trade_value


def get_wallet_details():
    wallet = exchange.privateGetWalletBalances()['result']
    return wallet


def get_cash():
    wallet = exchange.privateGetWalletBalances()['result']
    for t in wallet:
        if t['coin'] == 'USD':
            cash = float(t['availableWithoutBorrow'])
    return cash


def get_last_trade_price(pair):
    pair = pair
    trade_history = pd.DataFrame(exchange.fetchMyTrades(pair, limit=1),
                                 columns=['id', 'timestamp', 'datetime', 'symbol', 'side', 'price', 'amount', 'cost', 'fee'])
    last_trade_price = trade_history['price']

    return float(last_trade_price)

# Database Function Part


def check_database():
    print_underline()
    print('Checking Database file.....')
    try:
        trading_strategy = pd.read_csv("trading_strategy.csv")
        print('DataBase Exist Loading DataBase....')
    except:
        print('Creating DataBase....')
        column = ['no', 'entry', 'tp',
                  'recommended_amount', 'sum_actual_amount', 'sum_recommended_amount', 'usd_value', 'sum_usd', 'usd_for_collectzone', 'tp_status', 'order_buy_id', 'order_buy_datetime', 'order_sell_id', 'order_sell_datetime']
        trading_strategy = pd.DataFrame(columns=column)
        trading_strategy.to_csv("trading_strategy.csv", index=False)

        data = []
        data.append(column)

        sum_usd = 0
        sum_amount = 0
        sum_recommended_amount = 0

        sum_amount_collect = 0
        count_zone = 0
        entry_price = upper

        while True:
            entry_price = entry_price - (entry_price * gap_entry / 100)
            if(lower < entry_price < upper):
                count_zone += 1
                tp_price = entry_price + (entry_price * gap_tp / 100)

                recommended_amount = math.floor(
                    (min_usd / entry_price) * digits[min_trade_size_decimal]) / digits[min_trade_size_decimal]

                usd_value = entry_price * recommended_amount
                sum_amount += recommended_amount - \
                    (recommended_amount * maker_fee / 100)
                sum_recommended_amount += recommended_amount

                sum_amount_collect += recommended_amount
                sum_usd += usd_value

                usd_collect_zone = entry_price * sum_amount_collect

                item = []
                item.append(count_zone)  # EDIT
                item.append("{:.{precision}f}".format(
                    entry_price, precision=price_decimal))  # EDIT
                item.append("{:.{precision}f}".format(
                    tp_price, precision=price_decimal))  # EDIT

                item.append("{:.8f}".format(recommended_amount))
                item.append("{:.8f}".format(sum_amount))
                item.append("{:.8f}".format(sum_recommended_amount))
                item.append("{:.2f}".format(usd_value))
                item.append("{:.2f}".format(sum_usd))
                item.append("{:.2f}".format(usd_collect_zone))

                item.append(False) if count_zone == 1 else item.append(
                    True)

                item.append("")  # buy_id
                item.append("")  # buy_datetime

                item.append("")  # sell_id
                item.append("")  # sell_datetime

                data.append(item)  # add row

                with open("trading_strategy.csv", "a+", newline='') as fp:
                    wr = csv.writer(fp, dialect='excel')
                    wr.writerow(item)
            else:
                break
        print("Database has been created")


# Database Setup

check_database()


def identify_trend():
    return 'UPTREND'


def get_trading_strategy():
    trading_strategy = []
    with open("trading_strategy.csv", encoding='utf-8') as csvf:
        data = csv.DictReader(csvf)
        for row in data:
            trading_strategy.append(row)
    return trading_strategy


def save_trading_strategy(json):
    with open("trading_strategy.csv".format(subaccount), 'w', newline='') as csvfile:
        fieldnames = ['no', 'entry', 'tp',
                      'recommended_amount', 'sum_actual_amount', 'sum_recommended_amount', 'usd_value', 'sum_usd', 'usd_for_collectzone', 'tp_status', 'order_buy_id', 'order_buy_datetime', 'order_sell_id', 'order_sell_datetime']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(json)


def get_min_buy_limit():
    return price * (100 - open_range) / 100


def get_max_sell_limit():
    return price * (100 + open_range) / 100


def get_buy_limit_range():
    return price > entry_price and entry_price > min_buy_limit


def get_sell_limit_range():
    return price < tp_price and price < entry_price and tp_price < max_sell_limit


def get_pending_buy_id():
    pending_buy_list = []
    pending_buy = get_pending_buy()
    for item in pending_buy:
        pending_buy_list.append(item['id'])
    return pending_buy_list


def get_pending_buy_price():
    pending_buy_price_list = []
    pending_buy = get_pending_buy()
    for item in pending_buy:
        pending_buy_price_list.append(float(item['price']))
    return pending_buy_price_list


def get_pending_sell_id():
    pending_sell_list = []
    pending_sell = get_pending_sell()
    for item in pending_sell:
        pending_sell_list.append(item['id'])
    return pending_sell_list


def get_pending_sell_price():
    pending_sell_price_list = []
    pending_sell = get_pending_sell()
    for item in pending_sell:
        pending_sell_price_list.append(float(item['price']))
    return pending_sell_price_list


def get_buy_limit_id():
    buy_limit_list = []
    trading_strategy = get_trading_strategy()
    for row in trading_strategy:
        order_buy_id = row['order_buy_id']
        if order_buy_id != '':
            buy_limit_list.append(order_buy_id)
    return buy_limit_list


def get_sell_limit_id():
    sell_limit_list = []
    trading_strategy = get_trading_strategy()
    for row in trading_strategy:
        order_sell_id = row['order_sell_id']
        if order_sell_id != '':
            sell_limit_list.append(order_sell_id)
    return sell_limit_list


def get_pending_buy():
    pending_buy = []
    for i in exchange.fetch_open_orders(pair):
        if i['side'] == 'buy':
            pending_buy.append(i['info'])
    return pending_buy


def get_pending_sell():
    pending_sell = []
    for i in exchange.fetch_open_orders(pair):
        if i['side'] == 'sell':
            pending_sell.append(i['info'])
    return pending_sell


def create_buy_market_order():
    # Order Parameter
    types = 'market'
    side = 'buy'
    size = buy_size
    price = None
    response = exchange.create_order(pair, types, side, size,
                                     price)
    print("BUY MARKET {} Order ID {} Created at {} Size {}".format(
        response['symbol'], response['id'], response['price'], response['amount']))
    print_underline()


def create_buy_limit_order():
    # Order Parameter
    types = 'limit'
    side = 'buy'
    size = buy_size
    price = buy_price
    response = exchange.create_order(pair, types, side, size,
                                     price, {'postOnly': post_only})

    trading_strategy = get_trading_strategy()
    for item in trading_strategy:
        if float(item['entry']) == response['price']:
            item['order_buy_id'] = response['id']
            item['order_buy_datetime'] = response['datetime']

    save_trading_strategy(trading_strategy)

    print("BUY LIMIT {} Order ID : {} Created at {} Size {}".format(
        response['symbol'], response['id'], response['price'], response['amount']))
    print_underline()


def create_sell_limit_order():
    # Order Parameter
    types = 'limit'
    side = 'sell'
    size = sell_size
    price = sell_price
    response = exchange.create_order(pair, types, side, size,
                                     price, {'postOnly': post_only})

    trading_strategy = get_trading_strategy()
    for item in trading_strategy:
        if float(item['tp']) == response['price']:
            item['order_sell_id'] = response['id']
            item['order_sell_datetime'] = response['datetime']

    save_trading_strategy(trading_strategy)

    print("SELL LIMIT {} Order ID : {} Created at {} Size {}".format(
        response['symbol'], response['id'], response['price'], response['amount']))
    print_underline()


def cancel_order(order_id):
    order_id = order_id
    exchange.cancel_order(order_id)
    print("Order ID : {} Successfully Canceled".format(order_id))


def multiplier(volatility):
    return (volatility / 100.0 + 1)


def handle_fills_message(message):
    print_underline()


# Define WebSocket callback functions
def ws_message(ws, raw_message):
    global is_connect, handling_ws
    is_connect = True
    handling_ws = True
    
    message = json.loads(raw_message)
    message_type = message['type']
    channel = message['channel']

    if message_type in {'subscribed', 'unsubscribed'}:
        return
    if channel == 'fills':
        handle_fills_message(message)


def ws_open(ws):
    ts = int(time.time() * 1000)
    signature = hmac.new(api_secret.encode(),
                         f'{ts}websocket_login'.encode(), 'sha256').hexdigest()
    auth = {
        'op': 'login',
        'args': {
            'key': api_key,
            'sign': signature,
            'time': ts,
            'subaccount': subaccount
        }
    }
    ticker = {
        "op": "subscribe",
        "channel": "ticker",
        "market": pair_lst[0]
    }
    ws.send(json.dumps(auth))
    ws.send('{"op": "subscribe", "channel": "orders"}')
    ws.send('{"op": "subscribe", "channel": "fills"}')
    ws.send(json.dumps(ticker))
    print('Listening on Websocket ......')
    print_underline()


def ws_close(ws):
    global is_connect, last_price
    is_connect = False
    last_price = None
    print('Websocket connection is closed.')


def ws_error(ws, error):
    global is_connect, last_price
    is_connect = False
    last_price = None
    print(error)


def ws_thread(*args):
    ws = websocket.WebSocketApp(
        'wss://ftx.com/ws/',
        on_open=ws_open,
        on_message=ws_message,
        on_close=ws_close,
        on_error=ws_error
    )
    while ws.run_forever():
        pass


# Start a new thread for the WebSocket interface
_thread.start_new_thread(ws_thread, ())


# Main Loop
while True and handling_ws == False:
    handling_main = True
    try:
        wallet = get_wallet_details()
        cash = get_cash()
        Time = get_time()

        asset_name = token_name_lst[0]
        pair = pair_lst[0]

        print_underline()
        print('Date Time : {}'.format(Time))
        print('Subaccount : {}'.format(subaccount))
        print('Your Remaining Balance : {}'.format(cash))
        print('Checking Your Asset')

        total_asset = 0
        asset_amount = None

        # get port value & asset amount
        for item in wallet:
            if item['coin'] == asset_name:
                asset_amount = float(item['total'])
            asset_value = round(float(item['usdValue']), 2)
            total_asset += asset_value

        print('Your Total Asset Value is : {}'.format(total_asset))
        print_underline()

        # Get Last Price
        price = get_price()

        if price < upper and price > lower:
            trend = identify_trend()
            print("Identifying Trends of a Graph : {}".format(trend))

            if trend == 'UPTREND':
                print('Entering Trading Loop')
                print_underline()

                wallet = get_wallet_details()
                price = get_price()
                asset_in_wallet = [item['coin'] for item in wallet]
                min_size = get_minimum_size()

                sum_recommended_amount = 0.0

                trading_strategy = get_trading_strategy()
                for row in trading_strategy:
                    entry_price = float(row['entry'])
                    tp_price = float(row['tp'])
                    if price < entry_price:
                        sum_recommended_amount += float(
                            row['recommended_amount'])

                asset_diff = sum_recommended_amount - asset_amount

                print('Calculated {} {}, {}/{} {}'.format(asset_diff,
                      asset_name, asset_amount, sum_recommended_amount, asset_name))

                if asset_name not in asset_in_wallet or asset_diff >= min_size:
                    print('{} is Missing or Not Enough'.format(asset_name))
                    print_underline()

                    # Trade history Checking
                    # print('Validating Trading History')
                    # update_trade_log(pair)

                    # Innitial asset BUY params
                    min_trade_value = get_min_trade_value()
                    cash = get_cash()

                    # Create BUY params
                    buy_size = sum_recommended_amount - asset_amount

                    # Get Last Price
                    price = get_price()
                    print('{} Price is : {}$'.format(asset_name, price))

                    if cash > min_trade_value and buy_size > min_size:
                        print('Buying {} {} '.format(buy_size, asset_name))
                        # create_buy_market_order()
                        print_underline()
                    else:
                        print("Not Enough Balance to buy {}".format(asset_name))
                        print(
                            'Your Cash is {} // Minimum Trade Value is {}'.format(cash, min_trade_value))
                else:
                    print('{} is Already in Wallet'.format(asset_name))
                    print_underline()

                # Get Last Price Again
                price = get_price()

                # Create SELL LIMIT
                trading_strategy = get_trading_strategy()
                max_sell_limit = get_max_sell_limit()

                for row in reversed(trading_strategy):
                    order_sell_id = row['order_sell_id']
                    entry_price = float(row['entry'])
                    tp_price = float(row['tp'])
                    tp_status = row['tp_status'] == 'True'
                    recommended_amount = float(row['recommended_amount'])

                    sell_limit_range = get_sell_limit_range()
                    if sell_limit_range:
                        # Use [and] condition for prevent create repeat orders
                        pending_sell_price = get_pending_sell_price()
                        pending_sell_id = get_pending_sell_id()

                        if tp_price not in pending_sell_price and order_sell_id not in pending_sell_id and tp_status == True:
                            sell_price = tp_price
                            sell_size = recommended_amount
                            create_sell_limit_order()

                # Create BUY LIMIT
                trading_strategy = get_trading_strategy()
                min_buy_limit = get_min_buy_limit()

                for row in trading_strategy:
                    order_buy_id = row['order_buy_id']
                    entry_price = float(row['entry'])
                    recommended_amount = float(row['recommended_amount'])

                    buy_limit_range = get_buy_limit_range()
                    if buy_limit_range:
                        # Use [and] condition for prevent create repeat orders
                        pending_buy_price = get_pending_buy_price()
                        pending_buy_id = get_pending_buy_id()

                        if entry_price not in pending_buy_price and order_buy_id not in pending_buy_id:
                            buy_price = entry_price
                            buy_size = recommended_amount
                            create_buy_limit_order()

                # Clear order not in sell limit rp statement
                pending_sell = get_pending_sell()
                pending_sell_id = get_pending_sell_id()
                for pending_order in pending_sell:
                    if pending_order['id'] not in pending_sell_id:
                        cancel_order(pending_order['id'])

                # Clear order not in buy limit rp statement
                pending_buy = get_pending_buy()
                pending_buy_id = get_buy_limit_id()
                for pending_order in pending_buy:
                    if pending_order['id'] not in pending_buy_id:
                        cancel_order(pending_order['id'])
            else:
                # Open only SELL LIMIT of bought order (can adjust with ATR, i think don't do)
                print("Open only SELL LIMIT of bought order")

                # Clear all of BUY LIMIT orders
                pending_buy = get_pending_buy()
                for pending_order in pending_buy:
                    cancel_order(pending_order['id'])
        elif price > upper:
            print("Out of trading zone")
            print("Price more than {}".format(str(upper)))
        else:
            print("Out of trading zone")
            print("Price lower than {}".format(str(lower)))

        handling_main = False
        time.sleep(5)

    except Exception as e:
        print('Error : {}'.format(str(e)))
        time.sleep(10)
