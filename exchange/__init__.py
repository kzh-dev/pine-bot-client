# coding=utf-8

from logging import getLogger
logger = getLogger(__name__)

import time
from copy import deepcopy

import ccxt
from ccxt.base.errors import ExchangeError, NetworkError
from ccxt.base.errors import NotSupported

import exchange.cryptowatch as cryptowatch

from util.dict_merge import dict_merge
from util.parameters import sanitize_parameters

def any_to_resolution (obj):
    try:
        return int(obj)
    except:
        pass
    s = str(obj).lower()

    try:
        num = int(s[:-1])
    except:
        raise NotSupported(f'unknown resolution: {obj}')

    sfx = s[-1]
    if sfx == 'm':
        pass
    elif sfx == 'h':
        num *= 60
    elif sfx == 'd':
        num *= 60 * 24
    elif sfx == 'w':
        num *= 60 * 24 * 7
    else:
        raise NotSupported(f'unknown timeframe string: {obj}')
    return num


class Exchange (object):

    def __init__ (self, name, ccxt_obj, options):
        self.name = name
        self.ccxt = ccxt_obj
        self.options = options
        # test net
        if options.get('testnet', False):
            self._swith_to_testnet()
        # market info
        self._initialize_markets()

    def _swith_to_testnet (self):
        if 'test' not in self.ccxt.urls:
            raise NotSupported('testnet is not supported')
        self.ccxt.urls['api'] = self.ccxt.urls['test']

    def _expand_ids (self, *args):
        rslt = set()
        for arg in args:
            for a in (arg, ''.join([c for c in arg if c.isalnum()])):
                rslt.add(a)
                rslt.add(a.upper())
                rslt.add(a.lower())
        return list(rslt)

    def _initialize_markets (self):
        self.markets = {}
        self.market_alias = {}
        for name, m in self.ccxt.load_markets().items():
            alias = self.market_alias.setdefault(m['id'], [])
            ids = self._expand_ids(name, m['id'], m['symbol'])
            for n in ids:
                self.markets[n] = m
            alias += ids

    def fetch_orders (self, oid_list, symbol):
        rslt = []
        for oid in oid_list:
            o = self.ccxt.fetchOrder(oid, symbol)
            rslt.append(o)
        return rslt

    def create_order (self, symbol, qty):
        if qty > 0:
            return self.ccxt.createMarketBuyOrder(symbol, qty)
        if qty < 0:
            return self.ccxt.createMarketSellOrder(symbol, -qty)
        raise Exchange('zero qty order')

from exchange.ohlcprovider import BaseOHLCVProvider
class CCXTOHLCVProvider (BaseOHLCVProvider):

    def __init__ (self, ccxt_obj, symbol):
        super().__init__()
        self.ccxt_obj = ccxt_obj
        self.symbol = symbol

    def resolutions (self):
        return [any_to_resolution(t) for t in self.ccxt_obj.timeframes.keys()]

    def _resolution_to_tf (self, resolution):
        if resolution > 60 * 24 * 7:
            n = int(resolution / (60 * 24 * 7))
            u = 'w'
        elif resolution > 60 * 24:
            n = int(resolution / (60 * 24))
            u = 'd'
        elif resolution > 60:
            n = int(resolution / 60)
            u = 'h'
        else:
            n = resolution
            u = ''
        return f'{n}{u}'

    def set_resolution (self, resolution):
        super().set_resolution(resolution)
        self._resolution = self._resolution_to_tf(self.resolution)


class Market (object):

    def __init__ (self, exchange, symbol, resolution, options):
        self.exchange = exchange
        self.symbol_ = symbol
        self.market = exchange.markets[symbol.lower()]
        self.symbol = self.market['symbol']
        self.resolution = any_to_resolution(resolution)
        self.options = options
        # ohlcv provider
        self._initialize_ohlcv_provider()
        self.ohlcv_provider.set_resolution(self.resolution)
        strategy = options.get('strategy', None)
        if strategy:
            max_bars_back = strategy.get('max_bars_back', None)
            if max_bars_back:
                self.ohlcv_provider.set_barcount(max_bars_back)

    @property
    def info (self):
        return (self.exchange.name, self.symbol, self.resolution)

    def _initialize_ohlcv_provider (self):
        provider = None
        # cryptowatch?
        for a in self.exchange.market_alias[self.market['id']]:
            xchg_name = self.exchange.name.lower()
            if cryptowatch.supports(xchg_name, a):
                provider = cryptowatch.OHLCVProvider(xchg_name, a)
                break

        # ccxt
        if provider is None:
            support = self.exchange.ccxt.has['fetchOHLCV']
            if support and support != 'emulated':
                provider = CCXTOHLCVProvider(self.exchange.ccxt, self.symbol)

        if provider is None:
            name = self.exchange.name
            symbol = self.symbol_
            raise NotSupported(f'market does not support OHLCV API: {name}:{symbol}')
                
        self.ohlcv_provider = provider

    def load_ohlcv (self, timestamp):
        return self.ohlcv_provider.load(self.resolution, timestamp)

    def fetch_ohlcv (self, timestamp):
        return self.ohlcv_provider.fetch(self.resolution, timestamp)
        
    def fetch_orders (self, oid_list):
        while True:
            try:
                return self.exchange.fetch_orders(oid_list, self.symbol)
            except (ExchangeError, NetworkError) as e:
                logger.error(f'fail to fetch orders: {e}: {oid_list}')
                time.sleep(5)

    def create_order (self, qty, max_trial=3):
        trial = 0
        if max_trial <= 0:
            max_trial = 2**16
        while trial < max_trial:
            try:
                return self.exchange.create_order(self.symbol, qty)
            except (ExchangeError, NetworkError) as e:
                logger.error(f'fail to make market order: {e}: {self.symbol} {qty}')
                time.sleep(5)
                trial += 1
        return None


## Factory
def get_exchange (name, params):
    name_ = name.lower()
    if name_ not in ccxt.exchanges:
        raise ExchangeError(f'Unsupported exchange: {name}')

    options = deepcopy(params.get('ccxt', {}))
    dict_merge(options, params.get(name, {}))
    dict_merge(options, params.get(name_, {}))
    # Tweak options
    if 'enableRateLimit' not in options:
        options['enableRateLimit'] = True

    ccxt_cls = getattr(ccxt, name_)
    ccxt_obj = ccxt_cls(options)
    
    logger.info(f'Initialize exchange: {name}')
    options_ = sanitize_parameters(deepcopy(options))
    
    return Exchange(name, ccxt_obj, options_)

def get_market (exchange, symbol, resolution, params):
    exchange = get_exchange(exchange, params)
    if symbol not in exchange.markets:
        raise ExchangeError(f'market not found: {symbol}')
    market = Market(exchange, symbol, resolution, params)
    logger.info(f'Initialize market: {symbol}, {resolution}')
    return market


if __name__ == '__main__':
    import sys
    import logging
    logging.basicConfig(level=logging.INFO)
    cryptowatch.initialize()
    market = get_market(sys.argv[1], sys.argv[2], {})
    print(market)
    print(market.ohlcv_provider)
    print(market.ohlcv_provider.resolutions())
