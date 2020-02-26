# QuantTrading

A quantatative trading program, written in python 3. Uses the Alpaca.markets API, currently set for paper trading, and the unnofficial Robinhood API. The same trading strategies are executed on both platforms.

Uses multithreading to simultaneous track and trade as many stocks as your computer can handle.

To trade with Alpaca, simply create a python file called alpaca_api with a variable containing your key id called keyID, and a variable containing your secret key called secretKey. 

To trade with Robinhood, create a python file called rh_api, containing a variable with your username called username, a variable with your password called password, and a variable called qr containg the 2FA QR code. For more information on how to get the qr code, please refer to this repository: https://github.com/aamazie/Robinhood.
