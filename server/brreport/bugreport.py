#!/usr/bin/env python
from bottle import Bottle, route, run, get, post, put, delete, request, response, abort, debug
from brstore import BugReport
import uuid


'''
Application for collect issue report.

Author: Chen Jiliang
Core ID: b099

'''
app=Bottle()
store=BugReport()

###########Add related routing###################
@app.route('/report',method='POST')
def report_post():
    '''
    HTTP POST to upload a report string or data file
    '''
    sid=str(uuid.uuid4())
    #print '%s|POST from %s.'%(sid,request.remote_addr)
    
    return store.report_post(session=sid)

@app.route('/report',method='PUT')
def report_put():
    '''
    HTTP PUT to upload a data file
    ''' 
    sid=str(uuid.uuid4()) 
    print '%s|PUT from %s.'%(sid,request.remote_addr)  
    return store.report_put(session=sid)
 
if (__name__ == '__main__'):
    ##print 'Run bugreport server in main mode!'
    debug(True)
    run(app,host='0.0.0.0', port=8080, reloader=True)


