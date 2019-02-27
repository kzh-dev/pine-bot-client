# coding=utf-8

import os
import json
import collections

from logging import getLogger
logger = getLogger(__name__)

from copy import deepcopy

from util.dict_merge import dict_merge

default = collections.OrderedDict(
    api_server_url = 'http://pine-api.kzh-crypto.net',
)

def load_param_file (fname):
    with open(fname) as f:
        return json.loads(f.read(), object_pairs_hook=collections.OrderedDict)

def load_parameters (user_params=None, pine_fname=None):
    params = deepcopy(default)

    # global parameters
    try:
        dict_merge(params, load_param_file('global-parameters.json'))
    except FileNotFoundError:
        pass

    # Pine parameters
    if pine_fname:
        dict_merge(params, load_param_file(pine_fname+'.json'))

    # User defined parameters
    if user_params:
        dict_merge(params, deepcopy(user_params))

    return params

def save_parameters (params, pine_fname):
    param_fname = pine_fname + '.json'
    with open(param_fname, 'w') as f:
        f.write(json.dumps(params, indent=4)+"\n")
    logger.info(f"Generate a new paramter file: {param_fname}")

def _sanitize_dict (dct):
    for k, v in dct.items():
        if isinstance(v, dict) and isinstance(v, collections.Mapping):
            _sanitize_dict(v)
        elif (k == 'apiKey' or k == 'secret') and v and isinstance(v, str):
            dct[k] = '*' * len(v)

def sanitize_parameters (params):
    dest = deepcopy(params)
    _sanitize_dict(dest)
    return dest
