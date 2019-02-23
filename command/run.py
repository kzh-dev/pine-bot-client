# coding=utf-8

from logging import getLogger
logger = getLogger(__name__)

from util.parameters import sanitize_parameters
from util.comm import call_api
from util.time import utcnowtimestamp
from vm.vm import BotVM

def do_run (params, pine_fname, pine_str):
    ## Prelude (dump info)
    logger.info(f"Pine script: {pine_fname}")
    logger.info(f"[Parameters]")
    for line in json.dumps(sanitize_parameters(params), indent=2).splitlines():
        logger.info(line)
    
    # TODO make exchange

    ## Register pine script
    res = call_api(params, '/init-vm', params=params, code=pine_str)
    error = res.get('error', None)
    if error:
        raise Exception(f'Fail to process Pine script: {error}')

    utcnow = utcnowtimestamp()
    jitter = utcnow - res['server_clock']
    to_next = res['next_clock'] - int(utcnow)
    logger.info("VM has been initialized: id=%s to_next=%s jitter=%.2f", res['vm'], to_next, jitter)

    # make VM
    bot = BotVM(params, **res)
    # TODO make broker

    # start
    bot.run_forever()
