# coding=utf-8

import requests
import exchange.cryptowatchhelper as helper

API_SERVER_URL = 'https://api.cryptowat.ch'
#URL_TMPL = "https://api.cryptowat.ch/markets/bitflyer/btcfxjpy/ohlc?" + \
#            "periods={resolution}&after={f}&before={t}"

class CryptoWatchError (Exception):
    pass

from exchange.ohlcprovider import BaseOHLCVProvider
class OHLCVProvider (BaseOHLCVProvider):

    def __init__ (self, exchange, pair):
        self.exchange = exchange
        self.pair = pair

    def resolutions (self):
        return (
            1, 3, 5, 15, 30,
            60, 60*2, 60*4, 60*6, 60*12,
            1440, 1440*3, 1440*7
        )

def supports (exchange, pair):
    return exchange in markets and pair in markets[exchange]


from collections import OrderedDict
markets = OrderedDict()
def initialize ():
    try:
        res = requests.get(API_SERVER_URL+'/markets')
        for m in res.json(object_pairs_hook=OrderedDict)['result']:
            exchange = m['exchange']
            pair = m['pair']
            symbols = markets.setdefault(exchange, OrderedDict())
            symbols[pair] = pair
            func = getattr(helper, f'init_{exchange}', None)
            if func:
                func(symbols, pair)
    except Exception as e:
        raise CryptoWatchError(f'fail to fetch markets: {e}') from e

if __name__ == '__main__':
    initialize()
    print(markets['bitmex'])
