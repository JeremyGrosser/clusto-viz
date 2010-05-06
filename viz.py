#!/usr/bin/env python
from gevent.wsgi import WSGIServer
from webob import Request, Response
from webob.exc import *

from pprint import pprint
from traceback import format_exc
from time import strftime, localtime
from os import stat
import sqlite3
import re

from clusto.scripthelpers import init_script
import clusto
import simplejson as json

from jinja2 import Environment, FileSystemLoader
env = Environment(loader=FileSystemLoader('/home/synack/src/clusto-viz/templates'))

class Application(object):
    def __init__(self, urls):
        self.urls = [(re.compile(k), v) for k, v in urls]

    def __call__(self, environ, start_response):
        req = Request(environ)

        response = None
        for pattern, handler in self.urls:
            match = pattern.match(req.path_info)
            if match:
                obj = handler()
                method = req.method.lower()
                if hasattr(obj, method):
                    method = getattr(obj, method)
                    response = method(req, **match.groupdict())
                else:
                    response = HTTPMethodNotAllowed()
        if not response:
            response = HTTPNotFound()

        return response(environ, start_response)

class RackViewHandler(object):
    def get(self, request):
        st = stat('result.json')
        result = json.load(file('result.json'))

        keywords = []
        for datacenter, racks in result.items():
            for rack, contents in racks:
                for ru, device, devicetype, pools in contents:
                    keywords += pools.split(' ')

        template = env.get_template('rack.html')
        return Response(status=200, body=template.render(result=result.items(), keywords=set(keywords), last_updated=strftime('%Y-%m-%d %I:%M:%S %p', localtime(st.st_mtime))))

class SpaceViewHandler(object):
    def get(self, request):
        template = env.get_template('space.html')
        return Response(status=200, body=template.render())

class PoolViewHandler(object):
    def get(self, request, pool):
        template = env.get_template('pool_count.html')

        conn = sqlite3.connect('/home/synack/src/clusto-viz/pools.db')
        c = conn.cursor()
        c.execute('SELECT * FROM counts WHERE name=? ORDER BY ts ASC', (pool,))
        counts = c.fetchall()
        c.close()
        conn.close()

        counts = [(x[2] * 1000, x[3]) for x in counts]

        return Response(status=200, body=template.render(pool=pool, counts=json.dumps(counts)))

def main():
    urls = [
        ('^/pool/(?P<pool>[-\w]+)/*$',  PoolViewHandler),
        ('^/*$',    RackViewHandler),
    ]

    app = Application(urls)
    server = WSGIServer(('0.0.0.0', 9660), app)
    server.serve_forever()

if __name__ == '__main__':
    init_script()
    main()
