import os
import time
import requests
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# This class will create a graph of either the 1 or 2 standard deviation 
# expected moves for each options expiration for a given ticker


class OPTIONS_PROBABILITY_CONE:

    def __init__(self, ticker, stdv):
        self.ticker = ticker.upper()
        self.stdv = str(stdv)

    def get_dictionary(self):
        self.API_KEY = os.getenv('KEY')
        self.get_request = requests.api.get(f'https://api.tdameritrade.com/v1/marketdata/chains?apikey={self.API_KEY}&symbol={self.ticker}&strikeCount=1')
        self.dictionary = self.get_request.json()

    def expiration_dates_dict(self):
        OPTIONS_PROBABILITY_CONE.get_dictionary(self)
        self.exp_date_dict = self.dictionary['callExpDateMap'].keys()
        self.exp_date_list = list(self.exp_date_dict)

    def atm_strikes(self):
        # This method creates a list of the At the money strikes for each 
        # options expiration date. We are looping through the list of expiration
        # dates we have and are using that to get the next item in the dictionary
        # which are the strikes. Once thats done we save that to a new list
        OPTIONS_PROBABILITY_CONE.expiration_dates_dict(self)
        self.atm_strike_list = []
        for i in self.exp_date_list:
            self.atm_strike_dict = self.dictionary['callExpDateMap'][i]
            self.atm_strike_list.append(list(self.atm_strike_dict.keys()))
        self.flattened_strike_list = [i[0] for i in self.atm_strike_list]

    def call_implied_volatility(self):
        # here we are grabbing the atm call's implied volatilty for each 
        # expiration date. We use the zip class in order to iterate through
        # the expiration date and the strikes at the same time to reach the
        # nested dictionary in our main dictionary and then saving that to a
        # pandas dataframe
        OPTIONS_PROBABILITY_CONE.atm_strikes(self)
        self.calls_iv_df = pd.DataFrame()
        for i, x in zip(self.exp_date_list, self.flattened_strike_list):
            self.calls_df = pd.DataFrame(self.dictionary['callExpDateMap'][i][x])
            self.calls_iv_df[i] = self.calls_df['volatility']

        self.calls_iv_transposed = pd.DataFrame()
        self.calls_iv_transposed = self.calls_iv_df.transpose().reset_index()
        self.calls_iv_transposed = self.calls_iv_transposed.rename(
            columns={'index': 'exp_dates', 0: 'implied volatility'})

        self.calls_iv_sliced = pd.DataFrame()
        self.calls_iv_sliced = self.calls_iv_transposed.copy()
        self.calls_iv_sliced['exp_dates'] = self.calls_iv_transposed[
            'exp_dates'].str.slice(0,10)

    def put_implied_volatility(self):
        # we are implementing the same method for the calls except this time
        # we are callling the puts expiration date map from the dictionary to 
        # iterate through
        OPTIONS_PROBABILITY_CONE.call_implied_volatility(self)
        self.puts_iv_df = pd.DataFrame()
        for i, x in zip(self.exp_date_list, self.flattened_strike_list):
            self.puts_df = pd.DataFrame(self.dictionary['putExpDateMap'][i][x])
            self.puts_iv_df[i] = self.puts_df['volatility']

        self.puts_iv_transposed = pd.DataFrame()
        self.puts_iv_transposed = self.puts_iv_df.transpose().reset_index()
        self.puts_iv_transposed = self.puts_iv_transposed.rename(
            columns={'index': 'exp_dates', 0: 'implied volatility'})

        self.puts_iv_sliced = pd.DataFrame()
        self.puts_iv_sliced = self.puts_iv_transposed.copy()
        self.puts_iv_sliced['exp_dates'] = self.puts_iv_transposed[
            'exp_dates'].str.slice(0,10)

    def days_to_expiration(self):
        # here we slice the expiration dates we have since they contain the 
        # days from today at the end and we could use that later on when 
        # calculating the expected move
        OPTIONS_PROBABILITY_CONE.put_implied_volatility(self)
        self.calls_dte = pd.DataFrame()
        self.calls_dte['exp_dates'] = self.calls_iv_transposed[
            'exp_dates'].str.slice(11)

    def fix_values(self):
        # This method is used for NaN values that appear when using TD Ameritrades
        # API. Typically caused by expiration dates that are on the same day and 
        # have null values for option greeks 
        OPTIONS_PROBABILITY_CONE.days_to_expiration(self)
        self.calls_iv_str = self.calls_iv_sliced.copy()
        self.calls_iv_str['implied volatility'] = self.calls_iv_sliced[
            'implied volatility'].astype(str)
        self.calls_iv_str = self.calls_iv_str.replace('NaN', '0')

        self.puts_iv_str = self.puts_iv_sliced.copy()
        self.puts_iv_str['implied volatility'] = self.puts_iv_sliced[
            'implied volatility'].astype(str)
        self.puts_iv_str = self.puts_iv_str.replace('NaN', '0')
        #print(self.puts_iv_str)

    def implied_volatility(self):
        # Here we are are taking the average of the calls and puts implied
        # volatilty in order to get a more accurate implied volatilty estimate
        OPTIONS_PROBABILITY_CONE.fix_values(self)
        self.calls_iv_float = self.calls_iv_str.copy()
        self.calls_iv_float['implied volatility'] = self.calls_iv_str[
            'implied volatility'].astype(float)
        self.puts_iv_float = self.puts_iv_str.copy()
        self.puts_iv_float['implied volatility'] = self.puts_iv_str[
            'implied volatility'].astype(float)
        self.iv= self.calls_iv_float.copy()
        self.iv['implied volatility'] = (self.calls_iv_float[
            'implied volatility'] + self.puts_iv_float['implied volatility']) / 2

    def after_hours_fix(self):
        OPTIONS_PROBABILITY_CONE.implied_volatility(self)
        self.iv_fix = self.iv.copy()
        self.iv_fix = self.iv_fix[self.iv_fix['implied volatility'] == -999.0]
        self.iv_fix = self.iv_fix.reset_index()
        self.wrong_list = self.iv_fix['index'].to_list()

        self.fix_list = []
        for i in self.wrong_list:
            self.index_up = i + 1
            self.index_down = i - 1
            self.value_up = self.iv['implied volatility'].loc[self.index_up]
            self.value_down = self.iv['implied volatility'].loc[self.index_down]
            self.average_val = (self.value_up + self.value_down) / 2
            self.fix_list.append(self.average_val)

        for i, x in zip(self.wrong_list, self.fix_list):
            self.iv.loc[i, 'implied volatility'] = x

    def expected_move(self):
        # we calculate the expected move by taking the stock price multiplied by
        # implied volatilty and then multiplied by the square root of the days
        # to expiration divided by 365
        OPTIONS_PROBABILITY_CONE.after_hours_fix(self)
        self.stock_price = self.dictionary['underlyingPrice']
        self.exp_move_calc = self.iv.copy()
        self.exp_move_calc['dte'] = self.calls_dte['exp_dates']
        self.exp_move_calc['dte'] = self.exp_move_calc['dte'].astype(float)
        self.exp_move_calc['exp_move'] = self.stock_price * (
            self.exp_move_calc['implied volatility'] / 100) * (np.sqrt(
                self.exp_move_calc['dte'])/np.sqrt(365.0))
        #print(self.exp_move_calc)


    def graph(self):
        # Now this just graphs out our 1 standard deviation expected move of 
        # our underlying price. But we have also added some code for grabbing
        # the 2 standard deviation expected move in case it becomes useful
        OPTIONS_PROBABILITY_CONE.expected_move(self)
        self.exp_move_calc['1 stdv higher'] = self.stock_price + (
            self.exp_move_calc['exp_move'])
        self.exp_move_calc['1 stdv lower'] = self.stock_price - (
            self.exp_move_calc['exp_move'])
        self.exp_move_calc['2 stdv higher'] = self.stock_price +  (
            2 * self.exp_move_calc['exp_move'])
        self.exp_move_calc['2 stdv lower'] = self.stock_price -  (
            2 * self.exp_move_calc['exp_move'])
        self.exp_move_calc['3 stdv higher'] = self.stock_price + (
            3 * self.exp_move_calc['exp_move'])
        self.exp_move_calc['3 stdv lower'] = self.stock_price - (
            3 * self.exp_move_calc['exp_move'])

        #self.one_stdv_higher = self.exp_move_calc[['exp_dates', '1 stdv higher']].copy()
        #self.one_stdv_lower = self.exp_move_calc[['exp_dates', '1 stdv lower']].copy()
        #self.two_stdv_higher = self.exp_move_calc[['exp_dates', '2 stdv higher']].copy()
        #self.two_stdv_lower = self.exp_move_calc[['exp_dates', '2 stdv lower']].copy()
        #print(self.exp_move_calc.loc[:1])
        self.exp_move_calc = self.exp_move_calc.round(2)

        self.one_stdv = pd.DataFrame()
        self.two_stdv = pd.DataFrame()
        self.three_stdv = pd.DataFrame()
        self.one_stdv[['exp_dates', 'higher', 'lower']] = self.exp_move_calc[['exp_dates', '1 stdv higher', '1 stdv lower']]
        self.two_stdv[['exp_dates', 'higher', 'lower']] = self.exp_move_calc[['exp_dates', '2 stdv higher', '2 stdv lower']]
        self.three_stdv[['exp_dates', 'higher', 'lower']] = self.exp_move_calc[['exp_dates', '3 stdv higher', '3 stdv lower']]
        #print(self.three_stdv['exp_dates'])
        #print(self.exp_move_calc)
        if self.stdv == 'None':
            return self.one_stdv
        elif self.stdv == '2':
            return self.two_stdv
        elif self.stdv == '3':
            return self.three_stdv
        #return self.one_stdv_higher, self.one_stdv_lower, self.two_stdv_higher, self.two_stdv_lower

    def quotes(self):
        self.API_KEY = os.getenv('KEY')
        self.quote_request = requests.api.get(f'https://api.tdameritrade.com/v1/marketdata/{self.ticker}/quotes?apikey={self.API_KEY}')
        self.quote_dict = self.quote_request.json()
        self.quote_list = []
        self.quote_list.append(self.quote_dict[self.ticker]['lastPrice'])
        self.quote_list.append(self.quote_dict[self.ticker]['bidPrice'])
        self.quote_list.append(self.quote_dict[self.ticker]['askPrice'])
        self.quote_list.append(self.quote_dict[self.ticker]['regularMarketPercentChangeInDouble'])
        self.quote_list.append(self.quote_dict[self.ticker]['openPrice'])
        self.quote_list.append(self.quote_dict[self.ticker]['highPrice'])
        self.quote_list.append(self.quote_dict[self.ticker]['lowPrice'])
        self.quote_list.append(self.quote_dict[self.ticker]['closePrice'])
        self.quote_list.append(self.quote_dict[self.ticker]['totalVolume'])
        self.quote_list.append(self.quote_dict[self.ticker]['52WkHigh'])
        self.quote_list.append(self.quote_dict[self.ticker]['52WkLow'])
        
        return self.quote_list

#init = OPTIONS_PROBABILITY_CONE('qqq', 'None')
#init = init.graph()
