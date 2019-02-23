# coding=utf-8

from logging import getLogger
logger = getLogger(__name__)

import json

from util.parameters import sanitize_parameters
from util.comm import call_api
from util.time import utcnowtimestamp
from vm.vm import BotVM
from exchange import get_market
import exchange.cryptowatch as cryptowatch

from util.logging import notify, enable_discord

def do_run (params, pine_fname, pine_str):

    ## Prelude (dump info)
    logger.info(f"Pine script: {pine_fname}")
    logger.info(f"[Parameters]")
    for line in json.dumps(sanitize_parameters(params), indent=2).splitlines():
        logger.info(line)
    
    # make market/exchange
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
    market = get_market(exchange, symbol, resolution, params)

    ## Install pine script
    res = call_api(params, '/install-vm', inputs=params['inputs'], code=pine_str)
    error = res.get('error', None)
    if error:
        raise Exception(f'Fail to process Pine script: {error}')
    markets = res.get('markets', [])
    if markets:
        raise Exception('security() is not supported')

    server_clock = res.get('server_clock')
    jitter = utcnowtimestamp() - server_clock
    logger.info("VM has been initialized: id=%s jitter=%.2f", res['vm'], jitter)

    # make VM
    bot = BotVM(params, **res)
    # TODO make broker

    # start
    enable_discord(params)
    notify("PINE Bot starts!!")
    bot.run_forever()
