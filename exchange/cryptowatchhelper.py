# coding=utf-8


def init_bitmex (symbols, pair):
    if pair.endswith('-perpetual-futures'):
        symbols[pair.split('-')[0]] = pair
    symbols['xbtusd'] = 'btcusd-perpetual-futures'

def init_bitflyer (symbols, pair):
    if pair == 'btcfxjpy':
        symbols['fxbtcjpy'] = pair
