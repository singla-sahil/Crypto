from requests import Request, Session
import json
from datetime import date, timedelta
import time

API_key = "dbcf72303201985477dd8a32641794c4e1416d88"
currencies = []
# good_currencies = ['BTC','ETH','BNB','ADA','DOGE','XRP','DOT','UNI','ICP','BCH','LINK','LTC',
#                    'MATIC','SOL','THETA','XLM','VET','ETC','FIL','EOS','TRX','XMR','DAI','AAVE',
#                    'NEO','MKR','KSM','MIOTA','CAKE','KLAY','FTT','BSV','ATOM','ALGO',
#                    'CRO','HT','BTT','BTCB','LUNA','LEO','RUNE','XTZ','AVAX','TFUEL','COMP','HBAR',
#                    'DASH','ZEC','CEL','DCR','TEL']                  
def get_my_key(obj):
  return obj['ratio']

def getCurrencies():
    url = "https://api.nomics.com/v1/currencies?key="+API_key+"&attributes=id"
    #url = "https://api.nomics.com/v1/currencies?key"+API_key+"&attributes=id"
    response = session.get(url)
    #print(response)
    data = json.loads(response.text)
    for entry in data:
        currencies.append(entry.get('id'))
    #print(currencies)    

def getMonthlyLowHigh(date,currency):
    lo = 1e9+7
    hi = 0
    current_price = 0
    startdate = (date - timedelta(days=6)).strftime("%Y-%m-%d")
    enddate = date.strftime("%Y-%m-%d")
    if currency in good_currencies:
        #print(currency)
        #url = "https://www.alphavantage.co/query?function=DIGITAL_CURRENCY_DAILY&symbol=BTC&market=USD&apikey=BICS1KAYICQN43MK"
        url = "https://api.nomics.com/v1/currencies/sparkline?key="+API_key+"&ids="+currency+"&start="+startdate+"T00%3A00%3A00Z&end="+enddate+"T00%3A00%3A00Z"
        time.sleep(1.5)
        response = session.get(url)
        data = json.loads(response.text)
        print(data)
        #print(data[-1].get('prices'))
        if(not data):
            return 0,1e9+7,1e9+7
        cp = data[-1].get('prices')[-1]
        current_price = (float)(cp)    
        #current_price = (float)((str(data[-1].get('prices')))[-1]) 
        #current_price = price_arr[-1]
        for price in data[-1].get('prices'):    
            lo = min(lo,(float)(price))
            hi = max(hi,(float)(price))
    return lo,hi,current_price    
    #print(data)

def calculate_one_day_return(buy_date,currency,amount):
    tomm = buy_date+timedelta(days=1)
    tod = buy_date.strftime("%Y-%m-%d")
    tommor = tomm.strftime("%Y-%m-%d")
    url = "https://api.nomics.com/v1/currencies/sparkline?key="+API_key+"&ids="+currency+"&start="+tod+"T00%3A00%3A00Z&end="+tommor+"T00%3A00%3A00Z"
    time.sleep(1.5)
    response = session.get(url)
    data = json.loads(response.text)
    print(data)
    initial_price = (float)(data[-1].get('prices')[0])
    final_price = (float)(data[-1].get('prices')[-1])
    profit = (amount*final_price/initial_price-amount)
    print(tod,tomm,currency,initial_price,final_price,profit)
    return profit    

def get_best_five(date):
    buy_options = []
    #print(currencies)
    for currency in good_currencies:
        monthlo, monthhi, current_price = getMonthlyLowHigh(date,currency) 
        if current_price==monthlo:
            ratio = 1e9+7
        else:       
            ratio = (monthhi-current_price)/(current_price-monthlo)
        if(ratio!=0 and ratio!=1e9+7):    
            buy_options.append({'currency':currency,'ratio':ratio})     
            #print(currency,monthlo,monthhi,current_price,ratio)
    #print(buy_options)        
    buy_options.sort(key=get_my_key)
    return buy_options[-3:]

def simulate():
    principal = 15000
    today = date.today()
    curr_date = today-timedelta(days=2)
    while(curr_date<date.today()-timedelta(days=1)):
        #print(curr_date)
        buy_options = get_best_five(curr_date)
        print(buy_options)
        for entry in buy_options:
            principal+=calculate_one_day_return(curr_date,entry.get('currency'),principal/5)
        print(curr_date,principal)    
        curr_date = curr_date+timedelta(days=1)
        #print(principal)       
    print("Final amount is "+(str)(principal))     
        


good_currencies = []
with open("currencies.txt") as f:
    for currency in f:
        good_currencies.append(currency.rstrip())
currency_symbols = [];
session = Session()
getCurrencies();
#random_date = today-timedelta(days=3)
simulate()

    
