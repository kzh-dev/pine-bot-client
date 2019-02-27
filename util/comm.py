# coding=utf-8

import json
import requests
from collections import OrderedDict

class BadResponse (Exception):
    pass

def _call_api (ap_params, path, **kws):
    headers = {"content-type": 'application/json'}
    server = ap_params['api_server_url']
    r = requests.post(server + path, data=json.dumps(kws), headers=headers)
    if not r.ok:
        raise BadResponse('Bad status code: {}'.format(r))
    if r.text:
        obj = json.loads(r.text, object_pairs_hook=OrderedDict)
    else:
        obj = None
    return (r.status_code, obj)

def call_api (ap_params, path, **kws):
    _, json = _call_api(ap_params, path, **kws)
    return json

def call_api2 (ap_params, path, **kws):
    return _call_api(ap_params, path, **kws)

