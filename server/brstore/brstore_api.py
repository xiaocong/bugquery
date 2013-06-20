#!/usr/bin/env python
from bottle import Bottle, route, run, get, post, put, delete, request, response, abort, debug
from pymongo import Connection
import gridfs
import mimetypes
import json
import datetime,time
from bson.timestamp import Timestamp 
from bson.objectid import ObjectId
from brstore import BugReportStore
import mantis
from config import BRAUTH
import urllib2

import brdecorator


'''
Application for BugReporter storage.

Author: Chen Jiliang
Core ID: b099

'''
app=Bottle()
store=BugReportStore()

###########Add related routing###################
@app.route('/report',method='POST')
def report_post():
    '''
    HTTP POST to upload a report string or data file
    '''
    print 'Request from %s.'%request.remote_addr
    #store=BugReportStore()
    print 'store created.'
    result = store.report_post()
    print 'result: ' + result
    return result

@app.route('/report',method='PUT')
def report_put():
    '''
    HTTP PUT to upload a data file
    '''    
    #store=BugReportStore()
    return store.report_put()
    
@app.route('/record/<record_id>/log',method='PUT')
def upload_put(record_id):
    '''
    HTTP PUT to upload a data file
    '''
    if not record_id:
        abort(500,"No record id provided.")
    store=BugReportStore()
    return store.upload_put(record_id)

###########Retrieve related routing###################
@app.route('/record/<record_id>',method='GET')
@brdecorator.check_user(brdecorator.auth,"brquery")
def get_report(record_id):
    print 'API:/record/%s,at: %s'%(record_id,time.time())
    #store=BugReportStore()
    print 't,at: %s'%(time.time())
    data=store.get_report(record_id)
    print 'Finished API:/record/%s,at: %s'%(record_id,time.time())
    return data

@app.route('/record/<record_id>/log',method='GET')
####@check_user(auth)#mantis soap attachment issue
def get_log(record_id=None): 
    ##print 'get_log()'                
    if not record_id or record_id is None:
        abort(500,"Invalid record_id")
    else:    
        store=BugReportStore()
        return store.get_log(record_id)

@app.route('/record/get_file',method='GET')
@app.route('/record/get_file/',method='GET')
@brdecorator.check_user(brdecorator.auth,"brquery")
def get_file(): 
    fileId=request.params.get('file_id')                
    if not fileId:
        return {"error":"No file_id provided!"}
    else:    
        store=BugReportStore()
        return store.get_file(fileId)
        
@app.route('/record/<record_id>/ticket_url',method='POST')
@brdecorator.check_user(brdecorator.auth,"brquery")
def set_ticket_url(record_id):  
    print "brstore_api.set_ticket_url(%s)"%record_id                   
    #url=request.params.get("url")
    datatype = request.headers.get('Content-Type').split(';')[0]
    if datatype=='application/json':
        print "json."
        data=request.json
        if "url" in data:
            url=data["url"]
            print "url=%s"%url
        else:
            pass
    if not url:
        abort(500,"No url parameter!")    
    print 'set_ticket_url(%s,%s)'%(record_id,url)
    store=BugReportStore()
    return store.set_ticket_url(record_id,url)
        
@app.route('/record',method='POST')
@app.route('/record/',method='POST')
@brdecorator.check_user(brdecorator.auth,"brquery")
def get_batch_report():
    '''
    Retrieve a batch of report data for the given id array.
    '''
    print "brsotre.getRecords()"
    contentType=request.headers.get('Content-Type')
    if not contentType:
        return {'error':'Missing Content-Type'}
    datatype = request.headers.get('Content-Type').split(';')[0]
    if datatype=='application/json':
        ids=request.json
        if not ids:
            return {'error':"Invalid parameter!"}
        elif(ids==None or len(ids)==0):
            return {'error':"Invalid parameter!"}
        else:
            store=BugReportStore()
            return store.get_batch_report(ids) 
    else:
        return {'error':"Invalid Content-Type!"}
        
@app.route('/record/export/',method='POST')        
@app.route('/record/export',method='POST')
@brdecorator.check_user(brdecorator.auth,"brquery")
def export():
    '''        
    '''
    contentType=request.headers.get('Content-Type')
    if not contentType:
        return {'error':'Missing Content-Type'}
    datatype = request.headers.get('Content-Type').split(';')[0]
    if datatype=='application/json':
        ids=request.json
        if not ids:
            return {'error':"Invalid parameter!"}
        elif(ids==None or len(ids)==0):
            return {'error':"Invalid parameter!"}
        else:
            store=BugReportStore()
            return store.export(ids)
    else:
        return {'error':"Invalid Content-Type!"}
    

#@app.route('/record/sync/',method='GET')
#@app.route('/record/sync',method='GET')
#@brdecorator.check_user(brdecorator.auth,"brquery")
def sync():
    '''
    Data sync interface for other database.
    Paramenters:
    startid=id(start from 1)
    count=count
    
    Return:
    Headers:
    Content-Type:application/json    
    Body:
    A json array and every element in the array is a json document.
    array:[{},{}]
    document:{_id,category,type,name,info,occur_time,receive_time,uuid,sys_info:{}}
    
    '''
    store=BugReportStore()
    return store.sync()#TODO: update the return data
    
@app.route('/record/ids',method='GET')
#@brdecorator.check_user(brdecorator.auth,"brquery")
def ids():
    '''
    Get the id(s) for the given creteria.
    Paramenters:
    starttime=seconds
    endtime=seconds
    
    Return:
    Headers:
    Content-Type:application/json    
    Body:
    A json document.    
    document:{"start":id,"end":id}
    If the start id is -1, that means error.
    '''
    store=BugReportStore()
    return store.ids()

#@app.route('/record/latest',method='GET')
#@brdecorator.check_user(brdecorator.auth,"brquery")
def latest():
    '''
    Get the latest n records.
    Paramenters:
    count=n(max=100,default=20)
    
    Return:
    Headers:
    Content-Type:application/json    
    Body:
    A json array and every element in the array is a json document.
    array:[{},{}]
    document:{"_id":id,"receive_time":time,"json_str":original}     
    
    '''
    store=BugReportStore()
    return store.latest()

###########Delete related routing###################

@app.route("/delete/<record_id>", method='GET')#test pass
#@brdecorator.check_user(brdecorator.auth,"brquery")
def delete_report(record_id=None):
    ##print 'delete_report()'
    store=BugReportStore()
    return store.delete_report(record_id)

@app.route("/record/<record_id>", method='DELETE')#test pass
#@brdecorator.check_user(brdecorator.auth,"brquery")
def delete_report(record_id=None):
    ##print 'delete_report()'
    store=BugReportStore()
    return store.delete_report(record_id)

@app.route("/record/<record_id>/log", method='DELETE')#test pass
#@brdecorator.check_user(brdecorator.auth,"brquery")
def delete_log(record_id=None):
    ##print 'delete_log()'
    store=BugReportStore()
    return store.delete_log(recored_id)


if (__name__ == '__main__'):
    ##print 'Run bugreport server in main mode!'
    debug(True)
    run(app,host='0.0.0.0', port=8080, reloader=True)


