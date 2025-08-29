from apache_data import fetch_data_to_csv

stock_ticker_list = ["PYPL",
                     "CRCL",
                     "NVDA",
                     "VOO",
                     "RUM",
                     "COIN"]

for stock_ticker in stock_ticker_list:
    fetch_data_to_csv(stock_ticker, interval="60min", outputsize="full")