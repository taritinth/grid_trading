import json
import math
import pandas as pd
import csv
from texttable import Texttable

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

def get_csv_column():
    column = ['no', 'entry', 'tp',
              'recommended_amount', 'sum_actual_amount', 'sum_recommended_amount', 'usd_value', 'sum_usd', 'usd_for_collectzone', 'tp_status']
    return column


def create_zone():
    fieldnames = get_csv_column()
    # trading_strategy = pd.DataFrame(columns=fieldnames)
    # trading_strategy.to_csv("trading_strategy.csv", index=False)

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

            # if(recommended_amount <= min_trade_size):
            #     recommended_amount += min_trade_size

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

            data.append(item)  # add row

            # with open("trading_strategy.csv", "a+", newline='') as fp:
            #     wr = csv.writer(fp, dialect='excel')
            #     wr.writerow(item)
        else:
            break
    
    data.append(fieldnames)
    
    # print(json.dumps(data, indent=4))

    table = Texttable()
    table.set_cols_width([len(str(i)) + 5 for i in data[1]])
    table.set_cols_dtype(['t' for i in fieldnames])
    table.set_cols_align(['c' for i in fieldnames])
    table.add_rows(data)

    print(table.draw())
    print("------------------------------")
    print('COUNT ZONE: %d' % count_zone)
    print("------------------------------")


create_zone()
