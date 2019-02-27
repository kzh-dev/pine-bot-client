# coding=utf-8

import json

from util.parameters import save_parameters
from util.comm import call_api

def do_init (params, pine_fname, pine_str):
    res = call_api(params, '/scan-input', code=pine_str)
    if 'error' in res:
        raise Exception('Pine rejected: {}'.format(res['error']))

    # Generate template w/default values
    save_parameters(res['params'], pine_fname)
