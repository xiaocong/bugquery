#!/usr/bin/env python
from bottle import Bottle, route, run, get, post, put, delete, request, response, abort, debug
from reporter import Reporter
from viewer import Viewer
import uuid

import dcrator

'''
Author: Chen Jiliang
Core ID: b099

'''
app=Bottle()
viewer=Viewer()

######################################################################Reporter API###################################################################


###########API for add data###################
@app.route('/report',method='POST')
def report_post():
    '''
    HTTP POST to upload a report string or data file
    '''
    reporter=Reporter()
    contentType=request.get_header('Content-Type')
    if contentType==None:
        abort(500,'missing Content-Type')
    dataTypes = contentType.split(';')
    recordId=request.get_header('record-id')        
    result=reporter.report_post(dataTypes,recordId,request.body,request.json)
    
    return result

@app.route('/report',method='PUT')
def report_put():
    '''
    HTTP PUT to upload a data file
    '''    
    contentType=request.get_header('Content-Type')
    if contentType==None:
        abort(500,'missing Content-Type')
    dataTypes = contentType.split(';')
    recordId=request.get_header('record-id') 
    reporter=Reporter()       
    result=reporter.report_put(dataTypes,recordId,request.body)
    
    return result

'''    
@app.route('/record/<record_id>/log',method='PUT')
def upload_put(record_id):
    
    return reporter.upload_put(record_id)
''' 
###########Retrieve related routing###################
@app.route('/record/<record_id>',method='GET')
#@brdecorator.check_user(brdecorator.auth,"brquery")
def get_report(record_id):   
    reporter=Reporter() 
    data=reporter.get_report(record_id)
    return data

@app.route('/record/<record_id>/log',method='GET')
####@check_user(auth)#mantis soap attachment issue
def get_log(record_id=None): 
    ##print 'get_log()'

    if not record_id or record_id is None:
        abort(500,"Invalid record_id")
    else:
        reporter=Reporter()    
        return reporter.get_log(record_id)
        
@app.route('/record/<record_id>/ticket_url',method='POST')
#@brdecorator.check_user(brdecorator.auth,"brquery")
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
    #print 'set_ticket_url(%s,%s)'%(record_id,url)
    reporter=Reporter()
    return reporter.set_ticket_url(record_id,url)
        
@app.route('/record',method='POST')
@app.route('/record/',method='POST')
#@brdecorator.check_user(brdecorator.auth,"brquery")
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
            reporter=Reporter()
            return reporter.get_batch_report(ids) 
    else:
        return {'error':"Invalid Content-Type!"}
        
@app.route('/record/export/',method='POST')        
@app.route('/record/export',method='POST')
#@brdecorator.check_user(brdecorator.auth,"brquery")
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
            reporter=Reporter()
            return reporter.export(ids)
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
    reporter=Reporter()
    return reporter.sync()#TODO: update the return data
    
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
    reporter=Reporter()    
    return reporter.ids()

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
    reporter=Reporter()
    return reporter.latest()

###########Delete related routing###################

#@app.route("/delete/<record_id>", method='GET')
#@brdecorator.check_user(brdecorator.auth,"brquery")
def delete_report(record_id=None):
    ##print 'delete_report()'
    reporter=Reporter()
    return reporter.delete_report(record_id)

#@app.route("/delete/<record_id>/log", method='GET')
#@brdecorator.check_user(brdecorator.auth,"brquery")
def delete_log(record_id=None):
    ##print 'delete_report()'
    reporter=Reporter()
    return reporter.delete_log(record_id)



######################################################################Viewer API#####################################################################


#Return all the sys_info keys in json string
@app.route('/query/keys')
@app.route('/query/keys/')
def keys():
    return wrapResults(viewer.info_keys())

#Return all the values for special sys_info key in json string
'''
involve permission checking, and not necessary, so comment it out
@app.route('/query/keys/<key>')
def values(key):
    return wrapResults(brquery.info_values(key))
'''
@app.route('/query/platforms')
def platforms():
    return wrapResults(viewer.platforms())

@app.route('/query/error_types')
def platforms():
    return wrapResults(viewer.errorTypes())
        
#Return all the android.os.build.RELEASE.VERSION and the relative products in json string
#@app.route('/query/products')
'''
?Who use?
'''
def release_products():
    token=request.params.get("token")
    results=brquery.info_release_product(token)
    return wrapResults(results)

@app.route('/query/swversion')
@app.route('/query/swversion/')
def release_products():
    '''
    Intel request
    '''
    #token=request.params.get("token")
    imei=request.params.get("imei")
    ret=viewer.getLatestId(imei)
    if ret is None:
        return '-1'
    else:
        reporter=Reporter()
        for id in ret:
            data=reporter.getData(id)
            if 'ro:build:revision' in data['sys_info']:
                if not 'unknown' in data['sys_info']['ro:build:revision'].lower():
                    return data['sys_info']['ro:build:revision']
    return '-1'

@app.route('/query/apps')
def release_products():
    return wrapResults(viewer.appList())

#Return the summary rate with the conditions and groupby
#url?key1=xxx&key2=xxx...&groupby=g1+g2+g3
@app.route('/query/rate')
@app.route('/query/rate/')
def rate():
    conds = getFilterConditions()
    #print "conds:%s" % conds
    group = getGroupKey()
    return wrapResults(viewer.rate_summary(conds, group))

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
    return wrapResults(viewer.errors(conds,paging))

#download excel for error list by condistions
@app.route('/query/error/download')
@app.route('/query/error/download/')
def download():
    print "Received requet from:%s"%request.remote_addr
    paging=getPagingParameters()
    conds = getFilterConditions()
    data = wrapResults(viewer.errors(conds,paging))
    if len(data)==0:
        print 'empty set.'
    return viewer.error_list_excel(data)
  
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
        data = viewer.summary(conditions)
        if 'phonenumber' in conditions or 'imsi' in conditions:
            if 'error' in data:
                return wrapResults(data)
            else:
                if 'phonenumber' in conditions:
                    user=conditions['phonenumber']
                    linkTemplate="errors?phoneNumber=%s&date=%s"
                else:
                    user=conditions['imsi']
                    linkTemplate="errors?imsi=%s&date=%s"
                result=getUserData(user,linkTemplate,data)
                return wrapResults(result)
        else:
            return wrapResults(data)
    else:
        return wrapResults({"error":"No valid parameter!"})

@dcrator.timeit
def getUserData(user,linkTemplate,ids):
    '''
    Paramenters:
    user: phonenumber or imsi
    linkTemplate: "errors?phoneNumber=%s&date=%s" or "errors?imsi=%s&date=%s"
    '''
    idList=[]
    for id in ids:
        idList.append(int(id))        
    spec={"_id":{"$in":idList}}
    fields=['category','receive_time']
    reporter=Reporter()
    records=reporter.getDatas(spec,fields)

    data={}
    for record in records:
        recTime=record['receive_time']
        category=record['category']
        key=recTime.strftime('%Y%m%d')
        if not key in data:
            data[key]={"live": 0, "link": linkTemplate%(user,key), "error": 0}            
        if category=='ERROR':
            data[key]['error']+=1
        else:
            data[key]['live']+=1
    return data

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



 
if (__name__ == '__main__'):
    ##print 'Run bugreport server in main mode!'
    #debug(True)
    #run(app,host='0.0.0.0', port=8080, reloader=True)
    user='460001010203114'
    linkTemplate="errors?imsi=%s&date=%s"
    conditions={'imsi':user}
    data = viewer.summary(conditions)
    print data
    if not 'error' in data:
        result=getUserData(user,linkTemplate,data)
        print "result:\n%s"%result


