#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
from gevent import monkey
monkey.patch_all()  # monkey patch for gevent

from gevent.pywsgi import WSGIServer
from bottle import Bottle, static_file, redirect
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
    port = os.getenv('WEB_PORT', 8010)
    print 'bugquery Serving on :%d...' % (port)
    WSGIServer(('', port), app).serve_forever()
