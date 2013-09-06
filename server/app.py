#!/usr/bin/python
# -*- coding: utf-8 -*-

from gevent import monkey
monkey.patch_all()  # monkey patch for gevent

from gevent.pywsgi import WSGIServer
from geventwebsocket import WebSocketHandler
from bottle import Bottle, static_file, redirect
import os

from brauth.brauth_api import app as auth_app
from reporter.api import app as report_app

app = Bottle()


@app.route("/bugquery/<filename:path>")
def assets(filename):
    return static_file(filename, root=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'bugquery'))


@app.route("/")
@app.route("/bugquery")
@app.route("/bugquery/")
def root():
    return redirect("/bugquery/index.html")

app.mount('/api/brauth', auth_app)
app.mount('/api/brquery', report_app)


if (__name__ == '__main__'):
    host = '127.0.0.1'
    port = 8010
    print 'bugquery Serving on %s:%d...' % (host, port)
    WSGIServer(("", port), app, handler_class=WebSocketHandler).serve_forever()
