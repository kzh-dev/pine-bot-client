# coding=utf-8

from logging import getLogger
logger = getLogger(__name__)

import json

from util.parameters import sanitize_parameters
from util.comm import call_api
from util.time import utcnowtimestamp
from bot.vm import BotVM
from exchange import get_market
import exchange.cryptowatch as cryptowatch

from util.logging import notify, enable_discord

def _prepare_market (params):
    exchange = params.get('exchange', None)
    symbol = params.get('symbol', None)
    resolution = params.get('resolution', None)
    if exchange is None:
        raise Exception("missing 'exchange'")
    if symbol is None:
        raise Exception("missing 'symbol'")
    if resolution is None:
        raise Exception("missing 'resolution'")
    cryptowatch.initialize()
    return get_market(exchange, symbol, resolution, params)


def _install_vm (params, pine_str, market):
    res = call_api(params, '/install-vm',
                code=pine_str, inputs=params['inputs'], market=market.info) 
                
    error = res.get('error', None)
    if error:
        raise Exception(f'Fail to process Pine script: {error}')
    markets = res.get('markets', [])
    if markets:
        raise Exception('security() is not supported')

    vmid = res['vm']
    server_clock = res.get('server_clock')

    bot = BotVM(params, ident=vmid, market=market)
    jitter = bot.update_jitter(server_clock)
    logger.info("VM has been installed: id=%s jitter=%.2f", vmid, jitter)

    return bot

def do_run (params, pine_fname, pine_str):

    ## Prelude (dump info)
    logger.info(f"Pine script: {pine_fname}")
    logger.info(f"[Parameters]")
    for line in json.dumps(sanitize_parameters(params), indent=2).splitlines():
        logger.info(line)
    
    # make market/exchange
    market = _prepare_market(params)

    ## Install pine script
    bot = _install_vm(params, pine_str, market)

    ## Load initialize OHLCV data
    bot.boot()

    ## start
    enable_discord(params)
    notify(logger, f"PINE Bot has started!! {market.info}")
    bot.run_forever()
