import pandas as pd
from pandas.core.dtypes.inference import is_complex
from pandas.core.indexes.base import Index
import yfinance as yf
import numpy as np
import pandas_datareader as pdr
import seaborn as sb
sb.set()
import matplotlib.pyplot as plt
import datetime as dt
from sklearn.linear_model import LinearRegression
import csv
import os

#Read Ticker list for S&P 500
column_name = ['Ticker']
tickerdf = pd.read_csv('SNP.csv', names=column_name)
print (tickerdf)
tickers =  tickerdf.Ticker.to_list()
print(tickers)

start = dt.datetime.now() + dt.timedelta(days= -90)
now = dt.datetime.now()

lol_stocks = []

# return consolidating stocks
def ret_cons_stocks(ticker):

    data = pd.DataFrame(pdr.get_data_yahoo(ticker,start,now)['Close'])

    data['day_of_week'] = data.index.dayofweek
    
    ## TODO: Deal when Fridays are holidays later
    ## Find closing prices for each friday
    
    data = data.loc[(data['day_of_week'] == 4)| ( data.index.date == data.index.date.max())]
    rowno = np.arange(1, len(data) + 1)
    data['Rowno'] = rowno
    data = data[['Rowno','Close']]
    data = round(data,2)
    print(data)
    
    #recent high close if today is not friday else friday's close
    h1 = data.loc[data['Rowno'] == data['Rowno'].max()]['Close'].values[0]
    h2 = data.loc[data['Rowno'] == data['Rowno'].max() - 1]['Close'].values[0]
    h3 = data.loc[data['Rowno'] == data['Rowno'].max() - 2]['Close'].values[0]
    
    # check if closing price are near enough
    if max(h1,h2,h3) * 0.97 < min(h1,h2,h3):
        is_consolidating = True
    else:
        is_consolidating = False
    
    print(is_consolidating)

    #find how low or high it was before consolidation 
    val_bef_consolidation = 0

    breakout_reversal = ''

    pricediff = 0

    #create a list of lists to hold records for output
    

    if(is_consolidating):
        
        # find forth from last close, find better way to do this
        rowno = data['Rowno'].max() - 3
        
    
        while(rowno > 0) :
            
            val_bef_consolidation = data.loc[data['Rowno'] == rowno]['Close'].values[0]
            
            if (abs(val_bef_consolidation - min(h1,h2,h3)) / min(h1,h2,h3)) > 0.03:
                print(abs(val_bef_consolidation - min(h1,h2,h3)) / min(h1,h2,h3))
                break
            rowno = rowno - 1

        if(val_bef_consolidation > max(h1,h2,h3)):
            breakout_reversal = 'reversal'
        else:
            breakout_reversal = 'breakout'

        pricediff = abs(val_bef_consolidation - min(h1,h2,h3)) / min(h1,h2,h3) * 100

        lol_stocks.append([ticker,h1,val_bef_consolidation,pricediff,breakout_reversal])
        print(lol_stocks)

      
for ticker in tickers:
    try:
        ret_cons_stocks(ticker)
    except:
        print ('Could not run for ' + ticker)

try:
    if os.path.exists('shortlist.csv'):
        os.remove('shortlist.csv')
    shortlistdf = pd.DataFrame(lol_stocks, columns = ['Stock','CurrentPrice','PriceBeforeConsolidation','PriceDiff','Breakout_Reversal'])
    shortlistdf.sort_values(by=['PriceDiff'], inplace=True,ascending=False)
    shortlistdf.to_csv('shortlist.csv')
except:
    print ('Nothing to write to file')




