import math
import pandas as pd
import csv

upper = 4  # EDIT
lower = 0.1  # EDIT
digits = [1, 10, 100, 1000, 10000, 100000]  # DO NOT EDIT

min_usd = 4  # EDIT -> minimum USD for buy with min_size at upper
min_trade_size = 1  # EDIT
min_trade_size_decimal = 0  # EDIT -> number of size decimal places

# check if priceIncrement not is 0.xxx1, 0.x1, 1, you must round asset price
price_decimal = 4  # EDIT -> number of price decimal places

gap_entry = 8  # EDIT %
gap_tp = 9  # EDIT %
maker_fee = 0.02  # EDIT %

def get_csv_column():
    column = ['no', 'entry', 'tp',
              'recommended_amount', 'sum_actual_amount', 'sum_recommended_amount', 'usd_value', 'sum_usd', 'usd_for_collectzone', 'tp_status', 'order_buy_id', 'order_buy_datetime', 'order_sell_id', 'order_sell_datetime']
    return column


def create_zone():
    fieldnames = get_csv_column()
    trading_strategy = pd.DataFrame(columns=fieldnames)
    trading_strategy.to_csv("trading_strategy.csv", index=False)

    data = []
    data.append(fieldnames)

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


create_zone()
