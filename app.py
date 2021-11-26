from flask import Flask, render_template,request
import csv
import pandas as pd
from azure.storage.blob import ContainerClient
from io import StringIO
import yfinance as yf
#from azure.cosmosdb.table.tableservice import TableService

app = Flask(__name__)

#sasurl = 'https://mkccsvs.blob.core.windows.net/shortlist/shortlist.csv?sp=r&st=2021-11-22T23:00:39Z&se=2024-11-23T07:00:39Z&spr=https&sv=2020-08-04&sr=b&sig=2aJhwcOrqbG0DVe0iArmgaBGCiUpPbSCl6d0%2ByUeVl0%3D'

conn_str = 'DefaultEndpointsProtocol=https;AccountName=mkccsvs;AccountKey=N33wcyz+gndJj/laNFLy4mdG7yhE+5TTkuBD9DCCnXN5F4v/bAz71hrn2+UZNtvIsx1nkS2VPw8rJI/IZnfBmA==;EndpointSuffix=core.windows.net'
container = 'shortlist'

blob_name1 = 'shortlist1.csv'
blob_name2 = 'shortlist2.csv'

container_client = ContainerClient.from_connection_string(
    conn_str=conn_str, 
    container_name=container
    )

breakouts = []

def isbreakingout(candid,lastprice,breakrev):

    try:
        
        fivemindata = round(yf.download(candid, period='20m', interval='5m'),2)
        
        #last three 5 mins closing prices in list
        lastthreeclose = fivemindata.tail(3)['Close'].tolist()
        
        #print (lastthreeclose)

        currentprice = max(lastthreeclose)

        percentchange = round(abs(((currentprice - lastprice) / max(lastthreeclose) *100)),2)

        if percentchange > 1:

            if breakrev == 'reversal' and currentprice > lastprice:

                breakouts.append((candid,lastprice,currentprice,breakrev,percentchange))

                    

            if breakrev == 'breakout':
                if currentprice > lastprice:
                     breakouts.append((candid,lastprice,currentprice,breakrev,percentchange))
                else:
                    breakouts.append((candid,lastprice,currentprice,'Falloff',percentchange))

            #if abs(max(lastthreeclose) * 0.99 - lastprice): 
    except:
        print('Ok')


@app.route('/')
def index():
    
    # Download blob as StorageStreamDownloader object (stored in memory)
    downloaded_blob1 = container_client.download_blob(blob_name1)
    downloaded_blob2 = container_client.download_blob(blob_name2)

    stocks = {}
    #shortlistdf = pd.read_csv(sasurl)

    df1 = pd.read_csv(StringIO(downloaded_blob1.content_as_text()))
    df2 = pd.read_csv(StringIO(downloaded_blob2.content_as_text()))

    shortlistdf1 = pd.DataFrame(df1)
    shortlistdf2 = pd.DataFrame(df2)
    print(shortlistdf2)

    shortlistdf = pd.concat([shortlistdf1, shortlistdf2])
    shortlistdf.set_index('Stock', drop=True, inplace=True)
    shortlistdf = shortlistdf.drop(shortlistdf.columns[[0]], axis=1)  # df.columns is zero-based pd.Index
    
    #print(shortlistdf)
    #change to dictionary
    records = shortlistdf.to_records(index=True)
    shortlist = list(records)

    #print(shortlist)

    for item in shortlist:
        stocks[item[0]] = {'CurrentPrice':item[1],'PriceBeforeConsolidation':item[2],'PriceDiff':item[3],'Breakout_Reversal':item[4]}
    #print (stocks)


    return render_template('index.html',stocks=stocks)

# SAS URL for shortlisted consolidated stocks csv file shortlist.csv


@app.route('/snapshot')
def snapshot():
    with open('shortlist.csv') as f:
        stocks = f.read().splitlines()
        print(stocks)
        for ticker in stocks:
            ticker = ticker.split(',')[1]

    return {
        'code':'success'
    }



@app.route('/breakout')
def breakout():

    breakoutdict = {}

    downloaded_blob1 = container_client.download_blob(blob_name1)
    downloaded_blob2 = container_client.download_blob(blob_name2)

    
    #shortlistdf = pd.read_csv(sasurl)

    df1 = pd.read_csv(StringIO(downloaded_blob1.content_as_text()))
    df2 = pd.read_csv(StringIO(downloaded_blob2.content_as_text()))

    shortlistdf1 = pd.DataFrame(df1)
    shortlistdf2 = pd.DataFrame(df2)

    shortlistdf = pd.concat([shortlistdf1,shortlistdf2])

    #print(shortlistdf)

    shortlistdf.set_index('Stock', drop=True, inplace=True)
    shortlistdf = shortlistdf.drop(shortlistdf.columns[[0]], axis=1)  # df.columns is zero-based pd.Index

    records = shortlistdf.to_records(index=True)

    breakoutcandidates = list(records)
    
    #Dict of breakoutcandidates
    candidates =  {}

    for item in breakoutcandidates:
        candidates[item[0]] = {'CurrentPrice':item[1],'PriceBeforeConsolidation':item[2],'PriceDiff':item[3],'Breakout_Reversal':item[4]}
    
    #print(candidates)

    for key, value in candidates.items():
        #print(key,value['CurrentPrice'])
        isbreakingout(key,value['CurrentPrice'],value['Breakout_Reversal'])
    
    
    for item in breakouts:
        breakoutdict[item[0]] = {'ConsolidatedPrice':item[1],'CurrentPrice':item[2],'PercentChange':item[4],'Status':item[3]}
    print (breakoutdict)

    return render_template('breakout.html',breakouts = breakoutdict)

