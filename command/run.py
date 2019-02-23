# coding=utf-8

from util.logger import logger, report2, report3, info

from util.comm import call_api
from vm.vm import BotVM
from datetime import datetime, timezone

def do_run (params, pine_fname, pine_str):
    ## Prelude (dump info)
    api_key = params.pop('API_KEY')
    secret  = params.pop('SECRET')
    report2("  Pine script: %s", pine_fname)
    for k, v in params.items():
        report2("  %s: %s", k, v)
    report3("  API_KEY: %s", api_key)
    report3("  SECRET : %s", secret)

    # TODO make exchange

    ## Register pine script
    res = call_api(params, '/init-vm', params=params, code=pine_str)
    if 'error' in res:
        raise Exception('Fail to initialize pine script: {}'.format(res['error']))

    utcnow = datetime.now(timezone.utc).timestamp()
    jitter = utcnow - res['server_clock']
    to_next = res['next_clock'] - int(utcnow)
    report2("VM has been initialized: id=%s to_next=%s jitter=%.2f", res['vm'], to_next, jitter)

    # make VM
    vm = BotVM(params, **res)
    # TODO make broker

    report2("Bot start!!")
    vm.run_forever()
