# coding=utf-8

from logging import getLogger
logger = getLogger(__name__)

import requests
import exchange.cryptowatchhelper as helper

from util.time import utcnowtimestamp

API_SERVER_URL = 'https://api.cryptowat.ch'
OHLCV_API_URL_TMPL = "https://api.cryptowat.ch/markets/{exchange}/{pair}/ohlc?" + \
                     "periods={resolution_sec}&after={f}"

class CryptoWatchError (Exception):
    pass

from exchange.ohlcprovider import BaseOHLCVProvider
class OHLCVProvider (BaseOHLCVProvider):

    def __init__ (self, exchange, symbol):
        super().__init__()
        self.exchange = exchange
        self.pair = symbol_to_pair(exchange, symbol)

    def resolutions (self):
        return (
            1, 3, 5, 15, 30,
            60, 60*2, 60*4, 60*6, 60*12,
            1440, 1440*3, 1440*7
        )

    def rows_to_udf (self, rows, resolution_sec):
        udf = {}
        t = udf.setdefault('t', [])
        o = udf.setdefault('o', [])
        h = udf.setdefault('h', [])
        l = udf.setdefault('l', [])
        c = udf.setdefault('c', [])
        v = udf.setdefault('v', [])
        for row in rows:
            t.append(int(row[0]) - resolution_sec)
            o.append(row[1])
            h.append(row[2])
            l.append(row[3])
            c.append(row[4])
            v.append(row[5])
        return udf

    def _load (self, resolution, f=None, t=None):
        resolution_sec = resolution * 60
        if t is None:
            if f is None:
                t = (int(utcnowtimestamp() / resolution_sec) + 1) * resolution_sec + 1
            else:
                t = f + resolution_sec * 2
        if f is None:
            f = t - resolution_sec * (self.barcount + 16)

        url = OHLCV_API_URL_TMPL.format(exchange=self.exchange, pair=self.pair,
                                    resolution_sec=resolution_sec, f=f)
        logger.debug(f'get OHLCV: url={url}')
        res = requests.get(url)
        if not res.ok:
            raise Exception(f'unexpected status code: {res}')
        rows = res.json().get('result', None).get(str(resolution_sec), None)
        if not rows:
            raise Exception(f'invalid replied contents: {res.text}')
        return self.rows_to_udf(rows[-self.barcount:], resolution_sec)

    def load (self, resolution, timestamp=None):
        import datetime
        ohlcv = self._load(resolution, None, timestamp)
        logger.debug('lastbar={} l2={} o={} c={}'.format(
            ohlcv['t'][-1], datetime.datetime.fromtimestamp(ohlcv['t'][-2]),
            ohlcv['o'][-2], ohlcv['c'][-2]
        ))
        return ohlcv

    def fetch (self, resolution, timestamp):
        pair = self._load(resolution, timestamp + resolution * 60)
        logger.debug(f'pair={pair}')
        return pair
                            

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

def symbol_to_pair (exchange, symbol):
    return markets[exchange][symbol]

if __name__ == '__main__':
    initialize()
    print(markets['bitmex'])
