# coding=utf-8

import os
import json

default = dict(
    API_SERVER_URL = 'http://pine-api.kzh-crypto.net',
)

def _load_one_file (fname):
    with open(fname) as f:
        return json.load(f.read())

def load_parameters (user_params, pine_fname=None):
    params = dict(default)
    # global parameters
    try:
        params = dict(params, _load_one_file('global-parameters.json'))
    except FileNotFoundError:
        pass

    # Pine parameters
    if pine_fname:
        params = dict(params, _load_one_file(pine_fname))

    # User defined parameters
    if user_params:
        params = dict(params, user_params)

    return params
