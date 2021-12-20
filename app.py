from flask import Flask, render_template,request
import csv
import pandas as pd
from azure.storage.blob import ContainerClient
from io import StringIO
import yfinance as yf
from azure.cosmosdb.table.tableservice import TableService
from decimal import Decimal
from collections import OrderedDict

app = Flask(__name__)

#sasurl = 'https://mkccsvs.blob.core.windows.net/shortlist/shortlist.csv?sp=r&st=2021-11-22T23:00:39Z&se=2024-11-23T07:00:39Z&spr=https&sv=2020-08-04&sr=b&sig=2aJhwcOrqbG0DVe0iArmgaBGCiUpPbSCl6d0%2ByUeVl0%3D'

conn_str = 'DefaultEndpointsProtocol=https;AccountName=mkccsvs;AccountKey=N33wcyz+gndJj/laNFLy4mdG7yhE+5TTkuBD9DCCnXN5F4v/bAz71hrn2+UZNtvIsx1nkS2VPw8rJI/IZnfBmA==;EndpointSuffix=core.windows.net'

#csv containers
container = 'shortlist'

gap_container = 'gapstocks'

#blobs inside containers
blob_name1 = 'shortlist1.csv'
blob_name2 = 'shortlist2.csv'

gap_blob1 = 'gaplist1.csv'
gap_blob2 = 'gaplist2.csv'

account_name = 'mkccsvs'
account_Key = 'N33wcyz+gndJj/laNFLy4mdG7yhE+5TTkuBD9DCCnXN5F4v/bAz71hrn2+UZNtvIsx1nkS2VPw8rJI/IZnfBmA=='

table_service = TableService(account_name=account_name, account_key=account_Key)

#container clients
container_client = ContainerClient.from_connection_string(
    conn_str=conn_str, 
    container_name=container
    )

container_client_gap = ContainerClient.from_connection_string(
    conn_str=conn_str, 
    container_name = gap_container
    )

breakouts = []

def isapproachinggap(ticker):

    try:

        fivemindata = round(yf.download(ticker, period='20m', interval='5m'),2)

        current_price = fivemindata.tail(1)['Close'].item()

    except:
        pass
    




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
    #print(shortlistdf2)

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


@app.route('/putgap')
def putgap():

       # Download blob as StorageStreamDownloader object (stored in memory)
    downloaded_blob1 = container_client_gap.download_blob(gap_blob1)
    downloaded_blob2 = container_client_gap.download_blob(gap_blob2)

    df1 = pd.read_csv(StringIO(downloaded_blob1.content_as_text()))
    df2 = pd.read_csv(StringIO(downloaded_blob2.content_as_text()))


    blob_list = container_client_gap.list_blobs()

    blobs_list =[]

    for blob in blob_list:
       
        blobs_list.append(blob.name)
   
    main_dataframe = pd.DataFrame(pd.read_csv(StringIO((container_client_gap.download_blob(blobs_list[0])).content_as_text())))

    main_dataframe.set_index('Ticker', drop=True, inplace=True)
    main_dataframe = main_dataframe.drop(main_dataframe.columns[[0]], axis=1)

    for i in range(1,len(blobs_list)):

        dta = 'dta' + str(i)
        dta  = pd.DataFrame(pd.read_csv(StringIO((container_client_gap.download_blob(blobs_list[i])).content_as_text())))

        dta.set_index('Ticker', drop=True, inplace=True)
        dta = dta.drop(dta.columns[[0]], axis=1)
        main_dataframe = pd.concat([main_dataframe,dta])

    main_dataframe.dropna().drop_duplicates()
           
    print(main_dataframe)

    gapdf1 = pd.DataFrame(df1)
    gapdf2 = pd.DataFrame(df2)

    gapdf = pd.concat([gapdf1, gapdf2])

    gapdf.set_index('Ticker', drop=True, inplace=True)
    gapdf = gapdf.drop(gapdf.columns[[0]], axis=1)  # df.columns is zero-based pd.Index

    gaps_dict = {}

    records = main_dataframe.to_records(index = True)
    gaplist = list(records)

    #print(gaps_list)

    for gap in gaplist:

        ticker = gap[0][:-1]
        
        try:
            fivemindata = round(yf.download(ticker, period='20m', interval='5m'),2)

            current_price = fivemindata.tail(1)['Close'].item()

            current_price = round(Decimal(current_price),2)

            gap_top = round(Decimal(gap[2]),2)

            gap_bottom = round(Decimal(gap[3]),2)

            # how far is current price from the gap top
            dist_from_top = round(((current_price - gap_top) / current_price ) * 100 ,2)

            gaps_dict[ticker] = {'gap_bottom':gap_bottom,'gap_top':gap_top,'current_price':current_price,'dist_from_top':dist_from_top}

            gaps_dict = OrderedDict(sorted(gaps_dict.items(), key=lambda i: i[1]['dist_from_top']))
     
        except:
            pass

    return render_template('putgap.html',gaps_dict=gaps_dict)

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

