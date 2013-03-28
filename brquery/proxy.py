#!/usr/bin/env python
from bottle import request, response, abort

import brquery
import brconfig
#from brconfig import BRSTORE
#from brconfig import BRAUTH

import json
import urllib2
import urllib

import time

'''
We have some interface defined here, but real implemented in other app, such as
brauth and brstore. For unified and convenient access to those real implemented 
API, we implement this module, cause it works like a proxy, so name it as proxy.

'''

def timeit(func):
    def wrapper(*a, **ka):
        start = time.time()
        ret=func(*a, **ka)
        end =time.time()
        print 'Function %s() cost: %s s.'%(func.__name__,end - start)
        return ret
    return wrapper

@timeit
def access(url,headers=None,data=None):
    print "access():url=%s"%url    
    print 't1:%s'%time.time()
    req = urllib2.Request(url)
    print 't2:%s'%time.time()
    if data != None:
        #print "data:%s"%data
        data=json.dumps(data)
        req.add_data(data)
    if headers != None:
        for key in headers:
            req.add_header(key,headers[key])
    req.add_header("x-user","brquery")
    req.add_header("x-password","Redis123") 
    print 't3:%s'%time.time()   
    f=urllib2.urlopen(req)
    print 't4:%s'%time.time()
    return f.readline()    
    
    
def raw_access(url,headers=None,data=None):
    req = urllib2.Request(url)
    if data != None:
        req.add_data(data)
    if headers != None:
        for key in headers:
            req.add_header(key,headers[key])
    req.add_header("x-user","brquery")
    req.add_header("x-password","Redis123")
    
    f=urllib2.urlopen(req)
    m=f.info()
    contentType=m.getheader("Content-Type")
    response.set_header("Content-Type",contentType)
    if contentType=="application/x-download":    
        d=m.getheader("Content-Disposition")
        if d!=None:
            response.set_header("Content-Disposition",d)
        return f
    else:
        return f.readline()
    
    
def auth(data):
    if data == None:
        return {"error":{"code":14,"msg":"No user info"}}
    url=brconfig.BRAUTH+"/auth"
    headers={"Content-Type":"application/json"}
    ret=access(url,headers=headers,data=data)
    msg=json.loads(ret)
    response.set_header("Content-Type","application/json")
    return msg
 
@timeit   
def record(record_id,token):
    ret=brquery.isAccessible(token,record_id)
    if ret:
        url=brconfig.BRSTORE+"/record/%s" % record_id
        #print "url:%s"%url
        print 'r1:%s'%time.time()
        msg=json.loads(access(url))
        print 'r2:%s'%time.time()
        #print "msg:%s"%msg
        return msg
    else:
        #print "error:15"
        return {"error":{"code":15,"msg":"You have insufficient right."}}

#TODO: Fix upload attachment issue.
def record_log(record_id,token=None):
    url=brconfig.BRSTORE+"/record/%s/log" % record_id
    return raw_access(url)
    
def records(record_ids,token):
    #print "proxy.records()"
    #ids=brquery.get_accessible_ids(token,record_ids)#TODO: unnecessary check here
    url=brconfig.BRSTORE+"/record/"
    headers={"Content-Type":"application/json"}
    #print "data:%s"%ids
    msg=json.loads(access(url,headers=headers,data=list(record_ids)))
    response.set_header("Content-Type","application/json")
    return msg
    
    
def export(record_ids):
    '''
    
    '''
    url=brconfig.BRSTORE+"/record/export"
    headers={"Content-Type":"application/json"}
    msg=json.loads(access(url,headers=headers,data=list(record_ids)))
    return msg
    
def getFile(fileId):
    '''
    '''
    url=brconfig.BRSTORE+"/record/get_file?file_id=%s"%fileId
    return raw_access(url)
    
def sync(start_id,count):
    '''
    Data sync interface for other database.Should be invoked locally.
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
    brstore_url=brconfig.BRSTORE+"/record/sync?startid=%d&count=%d" % (start_id,count)
    data=json.loads(access(brstore_url))
    response.set_header("Content-Type","application/json")
    return data
    
def ids(starttime,endtime):
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
    brstore_url=brconfig.BRSTORE+"/record/ids?starttime=%s&endtime=%s" % (starttime,endtime)
    data=json.loads(access(brstore_url))
    response.set_header("Content-Type","application/json")
    return data

def set_ticket_url(record_id,ticket_url):
    '''
    Set ticket url for the record after submit ticket to mantis.
    '''
    url=brconfig.BRSTORE+"/record/%s/ticket_url" % record_id
    headers={"Content-Type":"application/json"} 
    data={"url":ticket_url}   
    access(url,headers=headers,data=data)
            
def latest():
    pass
    



