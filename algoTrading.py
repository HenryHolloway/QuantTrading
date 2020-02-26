#  ********************* STONKS *********************
stockList = ['AMD', 'GDX', 'MU', 'EEM', 'XLF', 'BAC']
#  **************************************************


import threading

import time
import os

import datetime


from talib import RSI, BBANDS, SMA, EMA

import numpy as np

import yfinance as yf

from notify_run import Notify
notify = Notify()

import requests

# *********** ALPACA API SETUP ***********
import os
os.environ['APCA_API_BASE_URL']='https://paper-api.alpaca.markets'


import alpaca_api as keys #keyID secretKey
import alpaca_trade_api as tradeapi

try:
    api = tradeapi.REST(keys.keyID, keys.secretKey, api_version='v2') # or use ENV Vars shown below
    account = api.get_account()

    if account.status == 'ACTIVE':
        tradingAlpaca = True
    else:
        print("Cannot trade with alpaca.")
        tradingAlpaca = False

except:
    print("Cannot trade with alpaca.")
    tradingAlpaca = False
# ****************************************

# **** ROBINHOOD UNNOFICIAL API SETUP ****
import rh_api as info
from Robinhood import Robinhood
myTrader = Robinhood()
tradingRH = myTrader.login(username = info.username, password = info.password, qr_code = info.qr)

print("Trading with RH: " , tradingRH)
# ****************************************





def getData(symbol):
    stock = yf.Ticker(symbol)
    data = stock.history(period="5d", interval="15m")
    # data = yf.download(  # or pdr.get_data_yahoo(...
    #         # tickers list or string as well
    #         tickers = symbol,

    #         # use "period" instead of start/end
    #         # valid periods: 1d,5d,1mo,3mo,6mo,1y,2y,5y,10y,ytd,max
    #         # (optional, default is '1mo')
    #         period = "5d",

    #         # fetch data by interval (including intraday if period < 60 days)
    #         # valid intervals: 1m,2m,5m,15m,30m,60m,90m,1h,1d,5d,1wk,1mo,3mo
    #         # (optional, default is '1d')
    #         interval = "1m",

    #         # group by ticker (to access via data['SPY'])
    #         # (optional, default is 'column')
    #         group_by = 'ticker'
    #     )

    # Available paramaters for the history() method are:

    # period: data period to download (Either Use period parameter or use start and end) Valid periods are: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max
    # interval: data interval (intraday data cannot extend last 60 days) Valid intervals are: 1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo
    # start: If not using period - Download start date string (YYYY-MM-DD) or datetime.
    # end: If not using period - Download end date string (YYYY-MM-DD) or datetime.
    # prepost: Include Pre and Post market data in results? (Default is False)
    # auto_adjust: Adjust all OHLC automatically? (Default is True)
    # actions: Download stock dividends and stock splits events? (Default is True)

    return data




def getPrice(data):
    price = data['Close']
    price = price.tail(1)
    price = price.iloc[0]
    return price



def getRSI(data):
    rsi = RSI(data['Close'])
    rsi = rsi.tail(1)
    rsi = rsi.iloc[0]
    return rsi


def getEMA(data, period=13):
    ema = EMA(data['Close'], timeperiod=period)

    ema = ema.tail(1)
    ema = ema.iloc[0]
    return ema

def getEMAslope(data, period=13):
    ema = EMA(data['Close'], timeperiod=period)

    ema = ema.dropna()
    iroc = ema.diff() / 1
    return iroc
def checkEMAslope(data, period=13):
    ema = getEMA(data)

    ema_slope = getEMAslope(data)

    if -.006 < ema_slope.tail(1).iloc[0] < .006:
        return "Flat"

    elif ema_slope.tail(1).iloc[0] > .006:
        return "Increasing"

    elif ema_slope.tail(1).iloc[0] < -.006:
        return "Decreasing"

    else:
        return 0



def bbp(data):
    price = data.dropna()
    close = price['Close'].values
    up, mid, low = BBANDS(close, timeperiod=20, nbdevup=2, nbdevdn=2, matype=0)
    bbp = (price['Close'] - low) / (up - low)
    return bbp
def getBBP(data):
    stock_bbp = bbp(data)
    stock_bbp = stock_bbp.tail(1)
    stock_bbp = stock_bbp.iloc[0]
    return stock_bbp



def truncate(f, n):
    '''Truncates/pads a float f to n decimal places without rounding'''
    s = '{}'.format(f)
    if 'e' in s or 'E' in s:
        return '{0:.{1}f}'.format(f, n)
    i, p, d = s.partition('.')
    return '.'.join([i, (d+'0'*n)[:n]])




def isBottom(data): #if return true, likely near bottom, likely not at the exact bottom
    df = data[(data.shift(1) > data) & (data.shift(-1) > data)]
    df = df.dropna()

    floor = df.tail(4)[0]
    price = getPrice(data)

    if abs(price - floor) < .005 * price:
        return True

    elif abs(price - floor) > .005 * price:
        return False
    
    else:
        return True






def processStock(stopEvent, stock=""):
    if stock == "":
        return
    
    now = datetime.datetime.now()

    if stock != "":
        fil = stock + ".action"
        fo = open(fil, "a")
        fo.write("\n*********************************************")
        fo.write("\n\n\n" + "Current date is: " + now.strftime('%d-%m-%Y') + "\n" + "It's a new dawn, it's a new day.\n\n\n")
        fo.write("\n*********************************************")
        fo.close()


    while not stopEvent.is_set():
        now = datetime.datetime.now()

        if stock != "":
            fil = stock + ".action"
            fo = open(fil, "a")
            fo.write("\n" + stock + "   -   Current time is: " + now.strftime('%H:%M:%S %d-%m-%Y') + "\n\n")




            tFilePath = os.path.join(os.getcwd(), "SP", "{}_Buying".format(stock))

            if os.path.isfile(tFilePath):
                ft = open(tFilePath, "r")
                initBuy = ft.readline()
                ft.close()

            else:
                initBuy = "False"
                ft = open(tFilePath, "w")
                ft.write(initBuy)
                ft.close()



            sFilePath = os.path.join(os.getcwd(), "SP", "{}_Selling".format(stock))

            if os.path.isfile(sFilePath):
                fs = open(sFilePath, "r")
                initSell = fs.readline()
                fs.close()

            else:
                initSell = "False"
                fs = open(tFilePath, "w")
                fs.write(initSell)
                fs.close()

            

############
            avgPrice_stock = 1

            positions = api.list_positions()
            for p in positions:
                if p.symbol == stock:
                    avgPrice_stock = float(p.avg_entry_price)

            

            if avgPrice_stock == 1:
                fo.write("Currently not holding any " + stock + ". \n")
            elif avgPrice_stock != 1:
                fo.write("Current holding price for " + stock + " is " + str(avgPrice_stock) + ".\n")

############
            fo.write("Fetching "+ stock +" data.\n")
            try:
                stock_data = getData(stock)
                fo.write("Succeeded in fetching data.\n")
            except:
                print("Failed to get data for " + stock + ". Restarting...")
                fo.write("Failed to get data for " + stock + ". Restarting...")
                continue

############

            stock_price = getPrice(stock_data)
            stock_rsi = getRSI(stock_data)
            fo.write("Current price for " + stock + " is " + str(stock_price) + '\n')
            fo.write("RSI is " + str(stock_rsi) + '\n')

############

            stock_bbp = getBBP(stock_data)
            fo.write("BBP is " + str(stock_bbp) + '\n')

############
############

            if avgPrice_stock == 1 or avgPrice_stock > stock_price: #SEEKING TO BUY stock
                fo.write("Seeking to buy " + stock)
                if initBuy == "False":
                    if stock_rsi <= 30 and -.1 < stock_bbp <= .05:
                        print("Can buy " + stock)
                        fo.write(now.strftime("%H:%M:%S") + " -- Can buy " + stock)
                        initBuy = "True"
                        ft = open(tFilePath, "w")
                        ft.write(initBuy)
                        ft.close()


                while initBuy == "True" and not stopEvent.is_set():
                    try:
                        stock_data = getData(stock)
                    except:
                        print("Failed to get data for " + stock + ". Retrying 20 times...")
                        fo.write("Failed to get data for " + stock + ". Retrying 20 times...")
                        dataTries = 0
                        while dataTries < 20:
                            try:
                                stock_data = getData(stock)
                                print("Successfully got data for " + stock + ".")
                                fo.write("Successfully got data for " + stock + ".")
                                break
                            except:
                                dataTries += 1
                                time.sleep(.25)

                        print("20  retries failed... Continuing...")
                        fo.write("20  retries failed... Continuing...")
                        continue


                    print("Checking EMA to find a good time to buy " + stock)
                    check = checkEMAslope(stock_data)
                
                    if check == "Increasing" or check == "Flat":
                        print("EMA is flat or increasing for " + stock + ". Buying...")


                        ### PRICE ACTION ###
                        positions = api.list_positions()
                        alpacaSharesOwned = 1
                        for p in positions:
                            if p.symbol == stock:
                                alpacaSharesOwned = int(p.qty)


                        #
                        if tradingAlpaca == True:
                            try:
                                
                                api.submit_order(stock, alpacaSharesOwned, side='buy', type='market', time_in_force='day')

                                try:
                                    initBuy = "False"
                                    ft  = open(tFilePath, "w")
                                    ft.write(initBuy)
                                    ft.close()

                                except:
                                    fo.write("Buy variable assignment/ writing failed.")
                                    print("Buy variable assignment/ writing failed.")


                                ### MESSAGING ###
                                messageBody = 'Alpaca - Bought ' + alpacaSharesOwned + ' shares of ' + stock + ' -- RSI @ {0}, BBP @ {1} - PRICE @ {2}'.format(stock_rsi, stock_bbp, stock_price)
                                messageTitle = 'Alpaca Bought {}'.format(stock)
                        

                                ###

                                
                            except:
                                messageTitle = "Alpaca Trading Failed"
                                messageBody = "Alpaca buying " + stock + " has failed. Continuing."
                                

                            notify.send(messageBody)
                            fo.write('\n\n' + messageBody)
                            requests.get('http://wirepusher.com/send?id=mpgJL&title=' + messageTitle + '&message=' + messageBody)
                            print(messageBody)


                        #
                        if tradingRH == True:
                            try:
                                stockInstrument = myTrader.instruments(stock)[0]
                                askP = (stock_price + (stock_price * .005))
                                askP = float(truncate(askP, 2))
                                myTrader.place_buy_order(stockInstrument, 1, ask_price=askP)


                                ### MESSAGING ###
                                messageBody = 'RH - Bought 1 share of ' + stock + ' -- RSI @ {0}, BBP @ {1} - PRICE @ {2}'.format(stock_rsi, stock_bbp, stock_price)
                                messageTitle = 'Robinhood Bought {}'.format(stock)
                        
                                notify.send(messageBody)
                                fo.write('\n\n' + messageBody)
                                requests.get('http://wirepusher.com/send?id=mpgJL&title=' + messageTitle + '&message=' + messageBody)
                                print(messageBody)
                                ###
                                
                            except:
                                messageBody = "Robinhood buying " + stock + " has failed. Continuing."
                                messageTitle = "RH Trading Failed"
                                print(messageBody)
                                fo.write('\n\n' + messageBody)
                                notify.send(messageBody)
                                requests.get('http://wirepusher.com/send?id=mpgJL&title=' + messageTitle + '&message=' + messageBody)
                                pass





                        



                        break


                    time.sleep(15)
                
            
            
            #
            elif avgPrice_stock < stock_price and avgPrice_stock != 1: #SEEKING TO SELL stocks
                fo.write("Seeking to sell " + stock)
                percentGain = float(((stock_price - avgPrice_stock)/avgPrice_stock)*100)
                pGain = "{:.3}".format(percentGain)

                if (stock_rsi >= 60 and stock_bbp >= .9) or (stock_rsi >= 67):
                    print("Can sell " + stock)
                    initSell = "True"
                    fs = open(sFilePath, "w")
                    fs.write(initSell)
                    fs.close()


            
                if initSell == "True" and percentGain >= .05:
                    while initSell == "True" and not stopEvent.is_set():
                        try:
                            stock_data = getData(stock)
                        except:
                            print("Failed to get data for " + stock + ". Retrying 20 times...")
                            fo.write("Failed to get data for " + stock + ". Retrying 20 times...")
                            dataTries = 0
                            while dataTries < 20:
                                try:
                                    stock_data = getData(stock)
                                    print("Successfully got data for " + stock + ".")
                                    break
                                except:
                                    dataTries += 1
                                    time.sleep(.25)

                            print("20  retries failed... Continuing...")
                            fo.write("20  retries failed... Continuing...")
                            continue

                        print("Checking EMA to find a good time to sell " + stock)
                        check = checkEMAslope(stock_data)
                    
                        if check == "Decreasing" or check == "Flat":
                            print("EMA is \'" + check + "\' for " + stock + ". Selling...")
                            fo.write("EMA is \'" + check + "\' for " + stock + ". Selling...")
                                
                            ### PRICE ACTION ###                        
                            positions = api.list_positions()
                            alpacaSharesOwned = 0
                            for p in positions:
                                if p.symbol == stock:
                                    alpacaSharesOwned = int(p.qty)
                            #
                            if tradingAlpaca == True and alpacaSharesOwned != 0:
                                try:
                                    
                                    api.submit_order(stock, alpacaSharesOwned, side='sell', type='market', time_in_force='day')

                                    try:
                                        initSell = "False"
                                        fs = open(sFilePath, "w")
                                        fs.write(initSell)
                                        fs.close()

                                    except:
                                        fo.write("Sell variable assignment/writing failed.")
                                        print("Sell variable assignment/writing failed.")


                                    messageBody = 'Alpaca - Sold ' + stock + ' ' + pGain + ' Percent Gain -- RSI @ {0}, BBP @ {1} - PRICE @ {2}'.format(stock_rsi, stock_bbp, stock_price)
                                    messageTitle = 'Aplaca Sold {}'.format(stock)

                                except:
                                    messageTitle = "Alpaca Trading Failed"
                                    messageBody = "Alpaca selling " + stock + " has failed. Continuing."


                                ### MESSAGING ###
                                notify.send(messageBody)
                                fo.write('\n\n' + messageBody)
                                requests.get('http://wirepusher.com/send?id=mpgJL&title=' + messageTitle + '&message=' + messageBody)
                                print(messageBody)
                                ###


                            #
                            if tradingRH == True:
                                try:
                                    stockInstrument = myTrader.instruments(stock)[0]
                                    positions = myTrader.positions()
                                    sellShares = 0
                                    for i in range(0, len(positions['results'])):
                                        if positions['results'][i]['instrument'] == stockInstrument['url']:
                                            ownSharesRH = True
                                            sellShares = positions['results'][i]['quantity']

                                    if ownSharesRH:
                                        bidP = (stock_price - (stock_price * .005))
                                        bidP = float(truncate(bidP, 2))
                                        myTrader.place_sell_order(stockInstrument, sellShares, bid_price=bidP)
                                        
                                        messageBody = 'RH Sold ' + stock + '.'
                                        messageTitle = 'Robinhood Sold {}'.format(stock)

                                        notify.send(messageBody)
                                        fo.write('\n\n' + messageBody)
                                        requests.get('http://wirepusher.com/send?id=mpgJL&title=' + messageTitle + '&message=' + messageBody)
                                        print(messageBody)
                                    
                                except:
                                    messageTitle = "RH Trading Failed"
                                    messageBody = "Robinhood selling " + stock + "has failed. Continuing."
                                    print(messageBody)
                                    fo.write('\n\n' + messageBody)
                                    notify.send(messageBody)
                                    requests.get('http://wirepusher.com/send?id=mpgJL&title=' + messageTitle + '&message=' + messageBody)
                                    pass




                        
                        else:
                            print("EMA is \'" , check , "\' for " + stock + ". Waiting 15 seconds and trying again...")

                        time.sleep(15)

                    


            fo.close()
        time.sleep(3)


        


def main():
    now = datetime.datetime.now()
    print("Starting up! Current time is + " + str(now))

    clock = api.get_clock()
    print('The market is {}'.format('open.' if clock.is_open else 'closed.'))

    while not clock.is_open:
        clock = api.get_clock()
        if now.hour >= 13:
            raise SystemExit


    pill2kill = threading.Event()
    threads = []
    for item in stockList:
        x = threading.Thread(target=processStock, args=(pill2kill, item,))
        x.start()
        print("Started thread for " + item)
        threads.append(x)



    while now.hour < 13:
        now = datetime.datetime.now()

        if now.hour >= 13:
            pill2kill.set()
            for thread in threads:
                thread.join()

            print("Exited successfully")
            raise SystemExit

    if now.hour >= 13:
        raise SystemExit


main()