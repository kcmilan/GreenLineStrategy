from flask import Flask, render_template,request
import csv
import pandas as pd
from azure.storage.blob import ContainerClient
from io import StringIO

app = Flask(__name__)

#sasurl = 'https://mkccsvs.blob.core.windows.net/shortlist/shortlist.csv?sp=r&st=2021-11-22T23:00:39Z&se=2024-11-23T07:00:39Z&spr=https&sv=2020-08-04&sr=b&sig=2aJhwcOrqbG0DVe0iArmgaBGCiUpPbSCl6d0%2ByUeVl0%3D'

conn_str = 'DefaultEndpointsProtocol=https;AccountName=mkccsvs;AccountKey=N33wcyz+gndJj/laNFLy4mdG7yhE+5TTkuBD9DCCnXN5F4v/bAz71hrn2+UZNtvIsx1nkS2VPw8rJI/IZnfBmA==;EndpointSuffix=core.windows.net'
container = 'shortlist'
blob_name = 'shortlist.csv'

container_client = ContainerClient.from_connection_string(
    conn_str=conn_str, 
    container_name=container
    )

@app.route('/')
def index():
    
    # Download blob as StorageStreamDownloader object (stored in memory)
    downloaded_blob = container_client.download_blob(blob_name)

    stocks = {}
    #shortlistdf = pd.read_csv(sasurl)
    downloaded_blob = container_client.download_blob(blob_name)
    df = pd.read_csv(StringIO(downloaded_blob.content_as_text()))
    shortlistdf = pd.DataFrame(df)
    shortlistdf.set_index('Stock', drop=True, inplace=True)
    shortlistdf = shortlistdf.drop(shortlistdf.columns[[0]], axis=1)  # df.columns is zero-based pd.Index
    
    #print(shortlistdf)
    #change to dictionary
    records = shortlistdf.to_records(index=True)
    shortlist = list(records)

    print(shortlist)

    for item in shortlist:
        stocks[item[0]] = {'CurrentPrice':item[1],'PriceBeforeConsolidation':item[2],'PriceDiff':item[3],'Breakout_Reversal':item[4]}
    print (stocks)


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
    #create a dictionary to hold stock ticker, status(breakout/bounceoff),chart
    breakoutdict = {}
    with open('shortlist.csv') as f:
        stocks = f.read().splitlines()
        #print(stocks)
        for ticker in stocks:
            ticker = ticker.split(',')[1]
            breakoutdict[ticker] = {'status':'breakout'}
    print(breakoutdict)
    return render_template('breakout.html',breakoutdict=breakoutdict)

