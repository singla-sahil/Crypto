import pandas as pd
import math
import os
import os.path
import time
from bitmex import bitmex
import datetime
from datetime import timedelta
from dateutil import parser
from tqdm import tqdm
from matplotlib import pyplot as plt
import warnings
warnings.filterwarnings('ignore')


bitmex_api_key = os.environ.get('APIKEY')
bitmex_api_secret = os.environ.get('SECRETAPIKEY')

binsizes = {"1m": 1, "5m": 5, "1h": 60, "1d": 1440}
batch_size = 750
bitmex_client = bitmex(test=False, api_key=bitmex_api_key, api_secret=bitmex_api_secret)

with open('symbols.txt', 'r') as f:
    symbols = [i.strip() for i in f.readlines()]

def minutes_of_new_data(symbol, kline_size, data, source):
    if len(data) > 0:  old = parser.parse(data["timestamp"].iloc[-1])
    elif source == "bitmex": old = bitmex_client.Trade.Trade_getBucketed(symbol=symbol, binSize=kline_size, count=1, reverse=False).result()[0][0]['timestamp']
    if source == "bitmex": new = bitmex_client.Trade.Trade_getBucketed(symbol=symbol, binSize=kline_size, count=1, reverse=True).result()[0][0]['timestamp']
    return old, new

def get_all_bitmex(symbol, kline_size, save = False):
    filename = '%s-%s-data.csv' % (symbol, kline_size)
    if os.path.isfile(filename): data_df = pd.read_csv(filename)
    else: data_df = pd.DataFrame()
    oldest_point, newest_point = minutes_of_new_data(symbol, kline_size, data_df, source = "bitmex")
    delta_min = (newest_point - oldest_point).total_seconds()/60
    available_data = math.ceil(delta_min/binsizes[kline_size])
    rounds = math.ceil(available_data / batch_size)
    if rounds > 0:
        print('Downloading %d minutes of new data available for %s, i.e. %d instances of %s data in %d rounds.' % (delta_min, symbol, available_data, kline_size, rounds))
        for round_num in tqdm(range(rounds)):
            time.sleep(1)
            new_time = (oldest_point + timedelta(minutes = round_num * batch_size * binsizes[kline_size]))
            data = bitmex_client.Trade.Trade_getBucketed(symbol=symbol, binSize=kline_size, count=batch_size, startTime = new_time).result()[0]
            temp_df = pd.DataFrame(data)
            data_df = data_df.append(temp_df)
    # data_df.set_index('timestamp', inplace=True)
    if save and rounds > 0: data_df.to_csv(os.path.join('data',filename))
    print('All caught up..!')
    return data_df

def get_day(date):
    year, month, day  = (int(x) for x in (date.split('T')[0]).split('-')) 
    ans = datetime.date(year, month, day)
    return ans.strftime("%A")

def plot(data, symbol, task):
    # plt.figure(figsize=(20, 10))
    xs = data.iloc[::-1]
    proj = xs.day.values
    proj_x = range(len(proj))
    fig = plt.figure(figsize=(20, 10))
    if task == 'pct_change':
        for i in zip(['high', 'avg', 'low'], ['g', 'b', 'r']):
            plt.plot(proj_x, xs[i[0]].pct_change().values)
    elif task == 'diff':
        for i in zip(['high', 'avg', 'low'], ['g', 'b', 'r']):
            plt.plot(proj_x, xs[i[0]].diff().values)
    else:
        for i in zip(['high', 'avg', 'low'], ['g', 'b', 'r']):
            plt.plot(proj_x, xs[i[0]].values)
    plt.plot(proj_x, [0]*len(xs), r'--') 
    plt.xticks(proj_x, proj)
    degrees = 70
    plt.grid()
    plt.xticks(rotation=degrees)
    plt.title(f"Data of {symbol} with {task} Thursday-Sunday starting since {xs.index.values[0]}")
    plt.savefig(f'plots/{symbol}-thursday-sunday-strat-{task}.png')


if __name__ == "__main__":
    for symbol in symbols:
        df = get_all_bitmex(symbol, "1d", save = True)
        #Getting past 150 days of data [4 months]
        sample = df.tail(150).iloc[::-1]
        sample['timestamp'] = sample.timestamp.apply(lambda x: parser.parse(str(x)))
        sample = sample.set_index('timestamp')
        sample['day'] = [get_day(str(x)) for x in sample.index.values]
        subset = sample[sample.day.isin(['Sunday', 'Thursday'])]
        if subset.iloc[0]['day'] == 'Thursday':
            subset = subset.iloc[1:]
        subset['avg'] = (subset.high + subset.low)/2
        for task in ['pct_change', 'diff', 'absolute_value']:
            plot(subset, symbol, task)
        print("Your Graphs are saved in data folder.")


