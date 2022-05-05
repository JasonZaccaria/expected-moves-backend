import yfinance as yf

#Here we will be geting out quotes from yfinance
#we are grabbing them from yahoo instaed of td because of api call limits

class Quotes:
    
    def __init__(self, ticker):
        self.ticker = ticker
        
    def get_data(self):
        data = yf.download(self.ticker, period='1d', interval='1d')
        return data

#instance = Quotes('SPY')
#instance.get_data()