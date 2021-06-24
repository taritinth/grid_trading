### JUST FOR LEARNING PURPOSE USE AT YOUR OWN RISK !!!!! ####

# import neccessary package
from re import T
import ccxt
import json
import pandas as pd
import time
import math
import decimal
from datetime import datetime
import pytz
import csv
from collections import defaultdict, deque

import websocket
import _thread
import hmac

from colorama import init, Fore, Back, Style
init(autoreset=True)

# Initial Variables
file_name = 'config.txt'
file_obj = open(file_name)
params = {}
for line in file_obj:
    line = line.strip()
    if not line.startswith("#"):
        key_value = line.split("=")
        if len(key_value) == 2:
            params[key_value[0].strip()] = key_value[1].strip()

# Api and secret
api_key = params['api_key']
api_secret = params['api_secret']
subaccount = params['subaccount']

# Exchange Details
exchange = ccxt.ftx({
    'apiKey': api_key,
    'secret': api_secret,
    'enableRateLimit': True}
)
exchange.headers = {'FTX-SUBACCOUNT': subaccount}

post_only = True
asset_name = params['asset_name']
pair = params['pair']

timeframe = params['timeframe']
upper = float(params['upper'])
lower = float(params['lower'])
digits = [1, 10, 100, 1000, 10000, 100000, 1000000, 10000000, 100000000, 1000000000, 10000000000]  # DO NOT EDIT

min_usd = float(params['min_usd'])
min_trade_size = float(params['min_trade_size'])
min_trade_size_decimal = int(params['min_trade_size_decimal'])

price_decimal = int(params['price_decimal'])

gap_entry = float(params['gap_entry'])
gap_tp = float(params['gap_tp'])
maker_fee = float(params['maker_fee'])

# Fix Value Setting
# capital = 100

open_range = float(params['open_range'])
loop_time = int(params['loop_time'])

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


def get_min_trade_value(price):
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


# Database Function Part
def get_csv_column():
    column = ['no', 'entry', 'tp',
              'recommended_amount', 'sum_actual_amount', 'sum_recommended_amount', 'usd_value', 'sum_usd', 'usd_for_collectzone', 'tp_status', 'order_buy_id', 'order_buy_avg_price', 'order_buy_datetime', 'order_sell_id', 'order_sell_datetime']
    return column


def check_database():
    print_underline()
    print('Checking Database file.....')
    try:
        trading_strategy = pd.read_csv("trading_strategy.csv")
        print('DataBase Exist Loading DataBase....')
    except:
        print('Creating DataBase....')
        fieldnames = get_csv_column()
        trading_strategy = pd.DataFrame(columns=fieldnames)
        trading_strategy.to_csv("trading_strategy.csv", index=False)

        data = []
        data.append(get_csv_column())

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
                item.append(count_zone)
                item.append("{:.{precision}f}".format(
                    entry_price, precision=price_decimal))
                item.append("{:.{precision}f}".format(
                    tp_price, precision=price_decimal))

                item.append("{:.8f}".format(recommended_amount))
                item.append("{:.8f}".format(sum_amount))
                item.append("{:.8f}".format(sum_recommended_amount))
                item.append("{:.2f}".format(usd_value))
                item.append("{:.2f}".format(sum_usd))
                item.append("{:.2f}".format(usd_collect_zone))

                item.append(False) if count_zone == 1 else item.append(
                    True)

                item.append("")  # buy_id
                item.append("")  # buy_avg_price
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
    return 'Uptrend'


def print_trend(trend):
    trend_color = None
    if trend == 'Uptrend':
        trend_color = Fore.GREEN
    else:
        trend_color = Fore.RED
    print("Identifying Trends of a Graph {}{}: {}{}".format(Fore.YELLOW, timeframe, trend_color, trend))


def get_trading_strategy():
    trading_strategy = []
    with open("trading_strategy.csv", encoding='utf-8') as csvf:
        data = csv.DictReader(csvf)
        for row in data:
            trading_strategy.append(row)
    return trading_strategy


def save_trading_strategy(json):
    with open("trading_strategy.csv".format(subaccount), 'w', newline='') as csvfile:
        fieldnames = get_csv_column()
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(json)


def get_min_buy_limit(price):
    return price * (100 - open_range) / 100


def get_max_sell_limit(price):
    return price * (100 + open_range) / 100


def get_buy_limit_range(price, min_buy_limit, entry_price):
    return price > entry_price and entry_price > min_buy_limit


def get_sell_limit_range(price, max_sell_limit, entry_price, tp_price):
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


def create_buy_market_order(buy_size):
    # Order Parameter
    types = 'market'
    side = 'buy'
    size = buy_size
    price = None
    response = exchange.create_order(pair, types, side, size,
                                     price)
    print("BUY MARKET {} Order ID {} Created at {} Size {}".format(
        response['symbol'], response['id'], response['price'], response['amount']))


def create_buy_limit_order(buy_price, buy_size):
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


def create_sell_limit_order(sell_price, sell_size):
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


def cancel_order(order_id):
    exchange.cancel_order(order_id)
    print("Order ID : {} Successfully Canceled".format(order_id))


def multiplier(volatility):
    return (volatility / 100.0 + 1)


# Define WebSocket callback functions

ws = None
subscriptions = []

ws_connected = False
logged_in = False

handling_ws = False
handling_main = False

def send_json(message):
    ws.send(json.dumps(message))


def login():
    global logged_in
    ts = int(time.time() * 1000)
    send_json({
        'op': 'login',
        'args': {
            'key': api_key,
            'sign': hmac.new(
                api_secret.encode(), f'{ts}websocket_login'.encode(), 'sha256').hexdigest(),
            'time': ts,
            'subaccount': subaccount
        }})
    logged_in = True
    print(Fore.GREEN + 'Logged in WebSocket')


def subscribe(subscription):
    send_json({'op': 'subscribe', **subscription})
    subscriptions.append(subscription)


def unsubscribe(ws, subscription):
    send_json({'op': 'unsubscribe', **subscription})
    while subscription in subscriptions:
        subscriptions.remove(subscription)


def trading_algorithm(mode):
    # Trading Algorithm
    # Do Everything About Trading
    try:
        global handling_ws, handling_main
        if mode == 'main':
            handling_main = True
        elif mode == 'event':
            handling_ws = True

        print_underline()

        date_time = get_time()
        wallet = get_wallet_details()
        cash = get_cash()

        total_asset = 0
        asset_amount = None

        # Get Port Value & Asset Amount
        for item in wallet:
            if item['coin'] == asset_name:
                asset_amount = float(item['total'])
            asset_value = round(float(item['usdValue']), 2)
            total_asset += asset_value

        print('Datetime : {}'.format(date_time))
        print_underline()

        if mode == 'main':
            # If Process In Main Loop, Print Account Details 
            if ws_connected:
                print(Fore.GREEN + 'WebSocket Status : Connected')
            else:
                print(Fore.RED + 'WebSocket Status : Disconnected')       
                    
            print_underline()
            print('Subaccount : {}'.format(subaccount))
            print('Your Remaining Balance : {}'.format(cash))
            print('Your Total Asset Value is : {}'.format(total_asset))
            print_underline()

        # Get Last Price
        price = get_price()

        if price < upper and price > lower:

            trend = identify_trend()
            print_trend(trend)

            if trend == 'Uptrend':
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

                print('{} Price is : {}{}$'.format(asset_name, Fore.YELLOW, price))

                asset_diff = sum_recommended_amount - asset_amount

                if asset_name not in asset_in_wallet or asset_diff >= min_size:
                    # If Asset is Missing or Not Enough, Buy Them

                    print('Calculated {} {}, {}/{} {}'.format(asset_diff,
                                                asset_name, asset_amount, sum_recommended_amount, asset_name))
                    print('{}{} is Missing or Not Enough'.format(Fore.RED, asset_name))
                    print_underline()

                    # Trade History Checking
                    # print('Validating Trading History')
                    # update_trade_log(pair)

                    # Innitial Asset BUY Params
                    min_trade_value = get_min_trade_value(price)
                    cash = get_cash()

                    # Create BUY Params
                    buy_size = sum_recommended_amount - asset_amount

                    if cash > min_trade_value and buy_size > min_size:
                        print('Creating Buy Market Order {} {} .......'.format(buy_size, asset_name))
                        # create_buy_market_order(buy_size)
                        print_underline()
                    else:
                        print("Not Enough Balance to buy {}".format(asset_name))
                        print(
                            'Your Cash is {} // Minimum Trade Value is {}'.format(cash, min_trade_value))
                else:
                    print('{}/{} {} is Already in Wallet'.format(asset_amount, sum_recommended_amount, asset_name))
                    print_underline()

                # Get Last Price Again
                price = get_price()

                # Create SELL LIMIT
                trading_strategy = get_trading_strategy()
                max_sell_limit = get_max_sell_limit(price)

                for row in reversed(trading_strategy):
                    order_sell_id = row['order_sell_id']
                    entry_price = float(row['entry'])
                    tp_price = float(row['tp'])
                    tp_status = row['tp_status'] == 'True'
                    recommended_amount = float(row['recommended_amount'])

                    sell_limit_range = get_sell_limit_range(price, max_sell_limit, entry_price, tp_price)
                    if sell_limit_range:
                        # Use [and] condition for prevent create repeat orders
                        pending_sell_price = get_pending_sell_price()
                        pending_sell_id = get_pending_sell_id()

                        if tp_price not in pending_sell_price and order_sell_id not in pending_sell_id and tp_status == True:
                            sell_price = tp_price
                            sell_size = recommended_amount
                            create_sell_limit_order(sell_price, sell_size)

                # Create BUY LIMIT
                trading_strategy = get_trading_strategy()
                min_buy_limit = get_min_buy_limit(price)

                for row in trading_strategy:
                    order_buy_id = row['order_buy_id']
                    entry_price = float(row['entry'])
                    recommended_amount = float(row['recommended_amount'])

                    buy_limit_range = get_buy_limit_range(price, min_buy_limit, entry_price)
                    if buy_limit_range:
                        # Use [and] condition for prevent create repeat orders
                        pending_buy_price = get_pending_buy_price()
                        pending_buy_id = get_pending_buy_id()

                        if entry_price not in pending_buy_price and order_buy_id not in pending_buy_id:
                            buy_price = entry_price
                            buy_size = recommended_amount
                            create_buy_limit_order(buy_price, buy_size)

                # Clear sell limit order not in trading strategy
                pending_sell = get_pending_sell()
                sell_limit_id = get_sell_limit_id()
                for pending_order in pending_sell:
                    if pending_order['id'] not in sell_limit_id:
                        cancel_order(pending_order['id'])

                # Clear buy limit order not in trading strategy
                pending_buy = get_pending_buy()
                buy_limit_id = get_buy_limit_id()
                for pending_order in pending_buy:
                    if pending_order['id'] not in buy_limit_id:
                        cancel_order(pending_order['id'])
            else:
                # Open only SELL LIMIT of bought order
                print("Open only sell limit of bought order")

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

        if mode == 'main':
            handling_main = False
        elif mode == 'event':
            handling_ws = False

        print('Wait for an event to be triggered')

    except Exception as e:
        print(Fore.RED + 'Error ({}) : {}'.format(mode, str(e)))
        time.sleep(10)


def handle_fills_message(message):
    if handling_main == False:
        if message['data']['type'] == 'limit' and message['data']['status'] == 'closed':
            trading_algorithm('event')


def ws_message(ws, raw_message):
    message = json.loads(raw_message)
    message_type = message['type']
    channel = message['channel']

    if message_type in {'subscribed', 'unsubscribed'}:
        return
    if channel == 'orders':
        handle_fills_message(message)


def ws_open(ws):
    global ws_connected
    ws_connected = True

    login()

    subscribe({'channel': 'fills'})
    subscribe({'channel': 'orders'})

    print(Fore.GREEN + 'Listening on WebSocket ......')
    print_underline()


def ws_close(ws):
    global ws_connected, logged_in
    ws_connected = False
    logged_in = False
    print('WebSocket connection is closed.')


def ws_error(ws, error):
    global ws_connected, logged_in
    ws_connected = False
    logged_in = False


def ws_thread(*args):
    global ws
    ws = websocket.WebSocketApp(
        'wss://ftx.com/ws/',
        on_open=ws_open,
        on_message=ws_message,
        on_close=ws_close,
        on_error=ws_error
    )
    while ws.run_forever(ping_interval=15, ping_timeout=10):
        pass


# Start a new thread for the WebSocket interface

_thread.start_new_thread(ws_thread, ())
# try:
#     _thread.start_new_thread(ws_thread, ())
# except RuntimeError as e:
#     print(e)


# Main Loop
while True:
    if handling_ws == False:
        trading_algorithm('main')
    time.sleep(loop_time)