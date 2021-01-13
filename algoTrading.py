#  ********************* STONKS *********************
stockList = ['GME', 'CDE', 'NIO', 'OXY', 'SPWR', 'APA']
#  **************************************************


import threading

import time
import os

import datetime


from talib import RSI, BBANDS, SMA, EMA

import numpy as np

import yfinance as yf

import wirepusher_api as wp_api

# *********** ALPACA API SETUP ***********
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
    wp_api.sendMessage("Alert!", "Cannot trade with alpaca.")
    tradingAlpaca = False
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

    stockBoughtToday = False

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
            fo.write("\n\n" + stock + "   -   Current time is: " + now.strftime('%H:%M:%S %d-%m-%Y') + "\n\n")



            initBuy = False
            initSell = False


            

############
            avgPrice_stock = 1
            alpacaSharesOwned = 2

            positions = api.list_positions()
            for p in positions:
                if p.symbol == stock:
                    avgPrice_stock = float(p.avg_entry_price)
                    alpacaSharesOwned = int(p.qty)

            

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

            if (avgPrice_stock == 1 or ((avgPrice_stock - (avgPrice_stock * .01)) > stock_price)) and ((stock_price*alpacaSharesOwned) < float(account.regt_buying_power)) and (alpacaSharesOwned < 16): #SEEKING TO BUY stock
                fo.write("Seeking to buy " + stock)
                if initBuy == False:
                    if stock_rsi <= 30 and -.1 < stock_bbp <= .05:
                        print("Can buy " + stock)
                        fo.write(now.strftime("%H:%M:%S") + " -- Can buy " + stock)
                        initBuy = True


                while initBuy == True and not stopEvent.is_set():
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


                    print("\nChecking EMA to find a good time to buy " + stock)
                    fo.write("\nChecking EMA to find a good time to buy " + stock)
                    check = checkEMAslope(stock_data)
                
                    if check == "Increasing" or check == "Flat":
                        print("EMA is flat or increasing for " + stock + ". Buying...")


                        


                        #
                        if tradingAlpaca == True:
                            try:
                                
                                api.submit_order(stock, alpacaSharesOwned, side='buy', type='market', time_in_force='day')
                                messageType = "stockBuy"

                                stockBoughtToday = True

                                try:
                                    initBuy = False


                                except:
                                    fo.write("Buy variable assignment/ writing failed.")
                                    print("Buy variable assignment/ writing failed.")


                                ### MESSAGING ###
                                messageBody = 'Alpaca - Bought ' + str(alpacaSharesOwned) + ' shares of ' + stock + ' -- RSI @ {0}, BBP @ {1} - PRICE @ {2}'.format(stock_rsi, stock_bbp, stock_price)
                                messageTitle = 'Alpaca Bought {}'.format(stock)
                        

                                ###

                                
                            except Exception as e:
                                messageTitle = "Alpaca Trading Failed"
                                messageBody = "Alpaca buying " + stock + " has failed. Continuing. Error: " + str(e)
                                messageType = "error"
                                

                            fo.write('\n\n' + messageBody)
                            wp_api.sendMessage(messageTitle, messageBody, messageType)
                            print(messageBody)


                        break


                    time.sleep(15)
                
            
            
            #
            elif (avgPrice_stock < stock_price and avgPrice_stock != 1) and stockBoughtToday == False: #SEEKING TO SELL stocks
                
                percentGain = float(((stock_price - avgPrice_stock)/avgPrice_stock)*100)
                pGain = "{:.3}".format(percentGain)
                fo.write("Seeking to sell " + stock + "for " + pGain + "percent gain." )



                if (stock_rsi >= 60 and stock_bbp >= .9) or (stock_rsi >= 67):
                    print("Can sell " + stock)
                    initSell = True



            
                if initSell == True and percentGain >= .5:
                    while initSell == True and not stopEvent.is_set():
                        # try:
                        #     stock_data = getData(stock)
                        # except:
                        #     print("Failed to get data for " + stock + ". Retrying 20 times...")
                        #     fo.write("Failed to get data for " + stock + ". Retrying 20 times...")
                        #     dataTries = 0
                        #     while dataTries < 20:
                        #         try:
                        #             stock_data = getData(stock)
                        #             print("Successfully got data for " + stock + ".")
                        #             break
                        #         except:
                        #             dataTries += 1
                        #             time.sleep(.25)

                        #     print("20  retries failed... Continuing...")
                        #     fo.write("20  retries failed... Continuing...")
                        #     continue

                        # print("Checking EMA to find a good time to sell " + stock)
                        # fo.write("\nChecking EMA to find a good time to sell " + stock)
                        # check = checkEMAslope(stock_data)
                    
                    
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
                                messageType = "stockSell"

                                initSell = False

                                messageBody = 'Alpaca - Sold ' + stock + ' ' + pGain + ' Percent Gain -- RSI @ {0}, BBP @ {1} - PRICE @ {2}'.format(stock_rsi, stock_bbp, stock_price)
                                messageTitle = 'Aplaca Sold {}'.format(stock)

                            except Exception as e:
                                messageTitle = "Alpaca Trading Failed"
                                messageBody = "Alpaca selling " + stock + " has failed. Continuing. Error: " + str(e)
                                messageType = "error"


                            ### MESSAGING ###
                            fo.write('\n\n' + messageBody)
                            wp_api.sendMessage(messageTitle, messageBody, messageType)
                            print(messageBody)
                            ###


                    


            fo.close()
        time.sleep(3)


        


def main():
    now = datetime.datetime.now()
    print("Starting up! Current time is :" + str(now))

    clock = api.get_clock()
    morningMessage = 'The market is {}'.format('open.' if clock.is_open else 'closed.')
    print(morningMessage)
    wp_api.sendMessage("Good Morning!", morningMessage, "goodMorning")

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