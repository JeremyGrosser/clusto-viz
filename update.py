#!/usr/bin/env python
from gevent.wsgi import WSGIServer
from webob import Request, Response
from webob.exc import *

from pprint import pprint
from traceback import format_exc
from time import strftime, localtime
from os import stat
import sqlite3
import time
import re

from clusto.scripthelpers import init_script
import clusto
import simplejson as json

def update_racks():
    result = {}

    for datacenter in clusto.get_entities(clusto_types=['datacenter']):
        for rack in datacenter.contents(clusto_types=['rack']):
            devices = []
            for ru in range(42, 0, -1):
                device = rack.get_device_in(ru)
                if device:
                    devices.append((ru, device.name, device.type, ' '.join([x.name for x in device.parents(clusto_types=['pool'])])))
                else:
                    devices.append((ru, None, None, ''))

            if not datacenter.name in result:
                result[datacenter.name] = []
            result[datacenter.name].append((rack.name, devices))
        result[datacenter.name].sort(key=lambda x: x[0])

    result = json.dumps(result)
    file('/home/synack/src/clusto-viz/result.json', 'w').write(result)

def update_count():
    conn = sqlite3.connect('/home/synack/src/clusto-viz/pools.db')
    c = conn.cursor()
    now = int(time.time())

    for pool in clusto.get_entities(clusto_types=['pool']):
        c.execute('INSERT INTO counts(name, ts, count) VALUES (?, ?, ?)', (pool.name, now, len(pool.contents())))
    conn.commit()
    c.close()

if __name__ == '__main__':
    init_script()
    update_racks()
    update_count()
