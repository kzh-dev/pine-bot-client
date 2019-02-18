# coding=utf-8

import json
import requests
from collections import OrderedDict

class BadResponse (Exception):
    pass

def do_init (params, pine_fname, pine_str):
    data = {"code": pine_str}
    headers = {"content-type": 'application/json'}
    server = params['API_SERVER_URL']
    r = requests.post(server + '/scan-input', data=json.dumps(data), headers=headers)
    if not r.ok:
        raise BadResponse('Bad status code: {}'.format(r))
    res = json.loads(r.text, object_pairs_hook=OrderedDict)
    if 'error' in res:
        raise BadResponse('Pine rejected: {}'.format(res['error']))

    # Generate template w/default values
    with open(pine_fname + '.param', 'w') as f:
        f.write(json.dumps(res['params'], indent=4)+"\n")
