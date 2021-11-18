from flask import Flask, render_template,request
import csv

app = Flask(__name__)

@app.route('/')
def index():
    stocks = {}
    with open('shortlist.csv') as f:
        for row in csv.reader(f):
            stocks[row[1]] = {'company': 'company'}

    print(stocks)


    return render_template('index.html',stocks=stocks)

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