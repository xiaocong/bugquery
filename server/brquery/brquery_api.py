#!/usr/bin/env python

from bottle import Bottle, route, run, get, post, put, delete, request, response, abort, debug
import brquery
import mantis
#import config
#from proxy import auth,record,records,export,sync,ids
import proxy

from pymongo import Connection
import gridfs
import mimetypes
import json
import datetime,time
from bson.timestamp import Timestamp 
from bson.objectid import ObjectId

app=Bottle()

################################################
#By b037
################################################
@app.route('/ping')
def ping():
    s = 'pong: '
    for key in request.params.keys():
        s += key + ', '
    return s

#Return all the sys_info keys in json string
@app.route('/query/keys')
@app.route('/query/keys/')
def keys():
    return wrapResults(brquery.info_keys())

#Return all the values for special sys_info key in json string
'''
involve permission checking, and not necessary, so comment it out
@app.route('/query/keys/<key>')
def values(key):
    return wrapResults(brquery.info_values(key))
'''
@app.route('/query/platforms')
def platforms():
    #token=request.params.get("token")
    results=brquery.platforms()
    return wrapResults(results)

@app.route('/query/error_types')
def platforms():
    #token=request.params.get("token")
    results=brquery.errorTypes()
    return wrapResults(results)
        
#Return all the android.os.build.RELEASE.VERSION and the relative products in json string
@app.route('/query/products')
def release_products():
    token=request.params.get("token")
    results=brquery.info_release_product(token)
    return wrapResults(results)

@app.route('/query/swversion')
@app.route('/query/swversion/')
def release_products():
    #token=request.params.get("token")
    imei=request.params.get("imei")
    print "imei:%s"%imei
    return brquery.revision(imei)

#Return all the apps in json string, add by Ma Ying
@app.route('/query/apps')
def release_products():
    return wrapResults(brquery.info_release_app())

#Return the summary rate with the conditions and groupby
#url?key1=xxx&key2=xxx...&groupby=g1+g2+g3
@app.route('/query/rate')
@app.route('/query/rate/')
def rate():
    conds = getFilterConditions()
    #print "conds:%s" % conds
    group = getGroupKey()
    return wrapResults(brquery.rate_summary(conds, group))

#Get error list by conditions
@app.route('/query/error')
@app.route('/query/error/')
def error():
    '''
    About paging:
    request:query/error?conditions&page=1&records=25&paging_token=xxx-xxx
    response: {"results":{"paging":{"totalrecords":100,"totalpages":10,"records":10,"page":1,"paging_token":"xxx-xxx"},"data":[{},{}]}}
    '''
    paging=getPagingParameters()    
    conds = getFilterConditions()
    return wrapResults(brquery.errors(conds,paging))

#download excel for error list by condistions
@app.route('/query/error/download')
@app.route('/query/error/download/')
def download():
    print "Received requet from:%s"%request.remote_addr
    paging=getPagingParameters()
    conds = getFilterConditions()
    data = wrapResults(brquery.errors(conds,paging))
    if len(data)==0:
        print 'empty set.'
    return brquery.error_list_excel(data)
  
@app.route('/summary')
@app.route('/summary/')
def summary():
    '''
    Get the summary by time or by user.
    ''' 
    conditions={}
    legalParams=("year","month","phonenumber","imsi")    
    for key in request.params.keys():
        if key in legalParams:
            conditions[key] = request.params[key]
    if len(conditions)>0:
        data = wrapResults(brquery.summary(conditions))
        return data
    else:
        return wrapResults({"error":"No valid parameter!"})
    
@app.route('/product_summary')
@app.route('/product_summary/')
def product_summary():
    '''
    Get the product_summary
    ''' 
    keyToken='token'
    keyPlatform='platform'
    keyMode='mode'
    token=None
    platform=None    
    mode='error'
    callDropMode=False        
    
    if keyToken in request.params.keys():
        token=request.params.get(keyToken)
    else:
        return wrapResults({"error":"No token provided!"})
    
    if keyPlatform in request.params.keys():
        platform=request.params.get(keyPlatform)
    if platform==None:
        platform='4.0.4'
        
        
    if keyMode in request.params.keys():
        mode=request.params.get(keyMode)
    if mode=='drop':
        callDropMode=True
        
    return wrapResults(brquery.product_summary(token,platform,callDropMode))
    

###################Utilities####################
def wrapResults(results):
    callback = getCallback()
    if len(callback) > 0:
        return '%s(%s);'%(callback, json.dumps({'results':results}))
    else:
        return {'results':results}

def getCallback():
    callback = ''
    try:
        for key in request.params.keys():
            if key == 'callback' or key == 'jsonp' or key == 'jsonpcallback':
                callback = request.params[key]
    except:
        pass
    return callback

def getFilterConditions():
    cond = {}
    try:
        keys = brquery.info_keys()
        for key in request.params.keys():
            if (key in keys) or (key in ('e_type','name','starttime','endtime','token','imsi','date','mode')):
                if key=='imsi':
                    cond['phoneNumber'] = "IMSI:%s"%request.params[key]
                elif key=='date':#like:20120612
                    datestr=request.params[key]
                    if len(datestr)==8:
                        year=int(datestr[0:4])
                        month=int(datestr[4:6])
                        day=int(datestr[6:8])
                        start=datetime.date(year,month,day)
                        end=datetime.date.fromtimestamp(int(start.strftime("%s"))+3600*24)
                        starttime=start.strftime("%s")
                        endtime=end.strftime("%s")
                        cond['starttime'] = starttime
                        cond['endtime'] = endtime       
                    else:
                        print "Value error for parameter date:%s"%datestr                    
                else:
                    cond[key] = request.params[key]
    except Exception, e:
        print 'getFilterConditions():%s'%e
        pass
    return cond

def getGroupKey():
    group = ''
    try:
        valid_values = brquery.info_keys()
        for key in request.params.keys():
            if key == 'groupby' and request.params[key] in valid_values:
                group = request.params[key]
    finally:
        pass
    return group
    
def getPagingParameters():
    paging={}
    if 'page' in request.params:
        paging['page']=request.params['page']
    else:
        paging['page']='1'
        
    if 'records' in request.params:
        paging['records']=request.params['records']
    else:
        paging['records']='100'
        
    if 'paging_token' in request.params:
        paging['paging_token']=request.params['paging_token']
    
    return paging
        

#################Mantis Related API###################
@app.route("/mantis/projects", method='POST')
def get_project_list():
    '''
    Get available project list for a specific user.
    Content-Type:application/json
    @param JSON format string: e.g: {"server":"borqsbt","username":"b999","password":"123456"}
    @return JSON format array: e.g: {result:[{id:1,name:ART-ICS,subproj:[{id:3,name:p1}]},{id:2,name:MOD}]}
    '''
    return mantis.get_project_list()
    
    
@app.route("/mantis/options", method='POST')
def get_option_list():
    '''
    Get available option list for a specific project and user.
    Content-Type:application/json
    @param JSON format string: e.g: {"server":"borqsbt","project":{"id":7,"name":"ART-T2-Acer"},"username":"b999","password":"123456"}
    @return JSON format array: e.g: {result:{category:[apps,OEM]],reproducibility:[{id:1,name:always},{id:2,name:random}],severity:[{id:1,name:1-block},{id:5,name:5-minor}],priority:[],customfield:[{id:1,name:Phase,values:[unit,feature]},{id:2,name:"Sub Categories",values:[app1,app2]},{id:3,name:Type,values:[defect,enhansment]}]}
    '''
    return mantis.get_option_list()
    
@app.route("/mantis/submit", method='POST')
def submit():
    '''
    Submit a ticket into mantis with the given issue data.
    Content-Type:application/json
    If submit successful, attach the ticket url to the issue data.
    @param JSON format string: e.g: {"record_id":88888,"server":"borqsbt","project":{"id":7,"name":"ART-T2-Acer"},"username":"b999","password":"123456","category":"Unknown","reproducibility":{"id":50,"name":"random"},"severity":{"id":40,"name":"5-minor"},"priority":{"id":20,"name":"5-low"},"summary":"[BugReporter]Update test code","description":"Update test code","customfield":[{"id": 1, "name": "Phase","value":"Unit Test"},{"id": 2, "name": "Sub Categories","value":"TestFramewrok-Testware"},{"id": 4, "name": "Type","value":"enhancement"}]}
    @return If successful,return a url point to the ticket,otherwise, return error info.
    '''
    record_id,url=mantis.submit()
    print "record_id=%s,url=%s"%(record_id,url)
    proxy.set_ticket_url(record_id,url)    
    return json.dumps({"results":{"url":url}})

#################Redirect API#####################3
@app.route('/auth',method='POST')
def auth():
    '''
    Parameters:
    Content-Type: application/json
    
    {username:name,password:pass}
    
    Return:
    {"error":{"code":11,"msg":"Authentication fail"}}
    or:
    {"token":"12345"}
    
    '''
    data=request.json
    return proxy.auth(data)

@app.route('/record/<record_id>',method='GET')
def record(record_id):
    t1=time.time()
    token=request.params.get("token")
    data=proxy.record(record_id,token)
    t2=time.time()
    print '/record/%s cost:%s'%(record_id,t2-t1)
    return data
    
@app.route('/record/<record_id>/log',method='GET')
def log(record_id):
    token=request.params.get("token")
    return proxy.record_log(record_id,token)
    
@app.route('/record/export/',method='POST')        
@app.route('/record/export',method='POST')
def export():
    '''
    Data exporting interface for manufacturer.
    Headers:
    Content-Type:application/json
    Parameters:
    json format data:
    {"user":user,"password":password,"product":product,"start_date":start_date,"end_date":end_date}
    user: username
    password: password
    product: like BKB
    start_date: like 20120701
    end_date: like 20120715(not included)
    
    Return:
    Headers:
    Content-Type:application/json    
    Body:
    {"results":[{},{},...]}
    A json array and every element in the array is a json document.
    array:[{},{}]
    document:{"_id":id,"receive_time":time,"json_str":original} 
    or error:    
    {"results":{"error":"error info"}}       
    '''
    info=None
    user=None
    password=None
    product=None
    start_date=None
    end_date=None
    
    result=None
    
    contentType=request.headers.get('Content-Type')
    if not contentType:
        result={'error':'Missing Content-Type'}
        return {"results":result}
    else:
        datatype = request.headers.get('Content-Type').split(';')[0]
        if datatype=='application/json':
            info=request.json
        else:
            result={'error':'Invalid Content-Type:%s'%datatype}
            return {"results":result}
    
    if info!=None:
        if 'user' in info:        
            user=info["user"]
        if 'password' in info:        
            password=info["password"]
        if 'product' in info:        
            product=info["product"]
        if 'start_date' in info:        
            start_date=info["start_date"]
        if 'end_date' in info:        
            end_date=info["end_date"]
        
        if (user==None or password==None or product==None):
            result={"error":"Parameter missing!"}
            return {"results":result}
        else:
            result=brquery.export(user,password,product,start_date,end_date)
            return {"results":result} 
    else:
        result={'error':'No info read.'}
        return {"results":result}
    

@app.route('/record/get_file',method='POST')
@app.route('/record/get_file/',method='POST')
def get_file():    
    '''
    Headers:    
    Content-Type:application/json
    Parameters:
    json format data:
    {"user":user,"password":password,"file_id":file_id}
    
    Return:
    Headers:
    Content-Type:application/x-download
    or:(when encounter error)
    Content-Type:application/json    
    Body:
    The file data.
    or:(when encounter error)
    {"error":"error info"}     
    '''
    info=None
    user=None
    password=None
    file_id=None    
    result=None
    
    contentType=request.headers.get('Content-Type')
    if not contentType:
        result={'error':'Missing Content-Type'}
        return result
    else:
        datatype = request.headers.get('Content-Type').split(';')[0]
        if datatype=='application/json':
            info=request.json
        else:
            result={'error':'Invalid Content-Type:%s'%datatype}
            return result
    
    if info!=None:
        if 'user' in info:        
            user=info["user"]
        if 'password' in info:        
            password=info["password"]
        if 'file_id' in info:        
            file_id=info["file_id"]        
        
        if (user==None or password==None or file_id==None):
            result={"error":"Parameter missing!"}
            return result
        else:            
            userInfo={"username":user,"password":password}
            authInfo=proxy.auth(userInfo)
            results=authInfo["results"]
            token=None
            error=None
            if 'token' in results:
                token=results["token"]
            if 'error' in results:
                error=results["error"]
            
            if (token==None):
                if error!=None:
                    return error 
                else:
                    result={"error":"Unknown error"}
                    return result 
            else:        
                result=proxy.getFile(file_id)
                return result 
    else:
        result={'error':'No info read.'}
        return result 
    
    
#TODO:
def hide():
    '''
    Hide some records.
    '''
    pass


if (__name__ == '__main__'):
    #print 'Run brquery server in main mode!'
    debug(True)
    run(app,host='0.0.0.0', port=8080, reloader=True)




