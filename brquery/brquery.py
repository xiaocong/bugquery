#!/usr/bin/env python

import redis
import time
#from brconfig import getMongoDB
#from brconfig import getRedis
#from brconfig import BRSTORE
#from brconfig import BRAUTH
import brconfig
import string
import json
from pyExcelerator import *  
from bottle import response
from datetime import datetime,date

import urllib2
import time
import uuid

import proxy

#Decorator for timing the function execution.
def timeit(func):
    def wrapper(*a, **ka):
        start = time.time()
        ret=func(*a, **ka)
        end =time.time()
        print 'Function %s() cost: %s s.'%(func.__name__,end - start)
        return ret
    return wrapper

# keys list of phone properties
def info_keys():
    return list(brconfig.getRedis().smembers('i:k'))

# values list of a specified key of phone property
def info_values(key):
    return list(brconfig.getRedis().smembers('i:k:%s'%key))

def platforms():
    return list(brconfig.getRedis().sort('set:platform:names'))

def revision(imei):
    print "revision(%s)"%imei
    redis = brconfig.getRedis()
    ret=list(redis.sort('ids:i:deviceId:%s'%imei,desc=True,start=0,num=1))
    print "ret:%s"%ret
    if len(ret)==0:
        return "-1"
    else:
        record_id=ret[0]
        url=brconfig.BRSTORE+"/record/%s" % record_id
        #print "url:%s"%url
        msg=json.loads(proxy.access(url))
        msg=msg['results']
        if 'sys_info' in msg:
            sysInfo=msg['sys_info']
            if 'ro:build:revision' in sysInfo:
                return sysInfo['ro:build:revision']
            else:
                return "-1"
        else:
            return "-1"


def errorTypes():
    return list(brconfig.getRedis().sort('b:t'))

@timeit
def info_release_product(token):
    redis = brconfig.getRedis()
    pipe = redis.pipeline(transaction=True)
    
    #Get accessible product list    
    result=getAccessibleProducts(token)
    if result==None:
        print "No accessible products!"
        return {"error":"No accessible products!"}
    if ('error' in result):
        print "Error in result:%s"%result['error']
        return result
    products=result
    platforms=redis.sort('set:platform:names',alpha=True)
    
    for platform in platforms:
        pipe.smembers('set:%s:products'%platform)
    ret=pipe.execute()
    
    results={}
    i=0
    for platform in platforms:
        l=list(set(products)&set(ret[i]))
        if (len(l)>0):
            results[platform]=l
        i+=1
    
    return results
       

#add by Ma Ying, list of all the apps
def info_release_app():
    red = brconfig.getRedis()

    #Get all apps in type
    sets = []
    sets.append('b:t')
    sets.append('b:t:FORCE_CLOSE')
    sets.append('b:t:ANR')
    sets.append('b:t:CORE_DUMP')
    results = list(set(red.sunion(sets))) 
    results.remove('FORCE_CLOSE')
    results.remove('ANR')
    results.remove('CORE_DUMP')
    return results


#Get all the ids matching the conditions
#@timeit
#def getTagetSet(conditions):
    

@timeit
def errors(conditions, paging):
    print 'brquery.errors()'
    print "conditions:"
    for k in conditions:
        print "%s=%s"%(k,conditions[k])
        
    print "paging:"
    for k in paging:
        print "%s=%s"%(k,paging[k])
    
        
    #Check token
    if 'token' in conditions:
        token=conditions.pop('token')
    else:
        return {"error":{"code":12,"msg":"Invalid token"}}

    redis = brconfig.getRedis()
    pipe = redis.pipeline(transaction=True)
    
    pagingCached=False
    pagingSet=None
    page=int(paging['page'])
    records=int(paging['records'])
    totalRecords=None
    paging_token=None
    if 'paging_token' in paging:
        paging_token=paging['paging_token']
        pagingSet="tmp_paging_%s"%paging_token
        if redis.exists(pagingSet):
            pagingCached=True

    ret = []    
    
    if not pagingCached:
        print "not paging!"
        sets = []
        
        #temporary set names
        accessibleSet='tmp_%s'%str(uuid.uuid4())
        timeFilteredSet='tmp_%s'%str(uuid.uuid4())
        appSet='tmp_%s'%str(uuid.uuid4())
        resultIdsSet='tmp_%s'%str(uuid.uuid4())
        paging_token=str(uuid.uuid4())
        pagingSet="tmp_paging_%s"%paging_token
        
        redis.hset("paging_token",paging_token,int(time.time())+30*60)
        
        #Get accessible set    
        accessibleSet=getAccessibleSet(token,accessibleSet)
        if accessibleSet==None:
            print "Accessible Set is None!"
            return ret
        else:
            sets.append(accessibleSet)
        
        print "accessible sets[]:%s"%sets
        #Get time filtered set    
        starttime=0
        endtime=0
        ntf=False
        if 'starttime' in conditions:
            starttime=conditions.pop('starttime')
            ntf=True        
        if 'endtime' in conditions:
            endtime=conditions.pop('endtime')
            ntf=True    
        if ntf:        
            timeFilteredSet=getTimeFilteredSet(starttime,endtime,timeFilteredSet)        
            if timeFilteredSet==None:
                print "Time Filtered Set is None!"
                return ret
            else:
                sets.append(timeFilteredSet)
        
        print "filtered sets[]:%s"%sets
        
        #For error type
        if 'e_type' in conditions:
            sets.append('ids:b:%s' % conditions.pop('e_type'))
        else:
            sets.append('ids:e')#All errors without call crop.
            
        #Other query conditions
        for k, v in conditions.items():
            if k == 'name':
                sets_app = []
                sets_app.append('ids:b:FORCE_CLOSE:%s' % v)
                sets_app.append('ids:b:ANR:%s' % v)
                sets_app.append('ids:b:CORE_DUMP:%s' % v)
                sets_app.append('ids:b:MANUALLY_REPORT:%s' % v)
                pipe.sunionstore(appSet,sets_app)
                result=pipe.execute()
                if result[0]==0:
                    return []
                else:
                    sets.append(appSet)                
            else:
                sets.append('ids:i:%s:%s' % (k,v))        
        
        print "last sets[]:%s"%sets
        #Intersect all the sets
        #TODO: Is here the best place to retrieve all the set members?
        pipe.sinterstore(pagingSet,sets)
        pipe.sort(pagingSet,desc=True,start=(page-1)*records,num=records)
        result=pipe.execute()
        totalRecords=result[0]
        ret=list(result[1])
        print "totalRecords:%s"%totalRecords
        print "pagingSet:%s"%pagingSet
        
        #Delete all temporary set
        pipe.delete(accessibleSet)
        pipe.delete(timeFilteredSet)
        pipe.delete(appSet)
        pipe.delete(resultIdsSet)
        pipe.execute()
    else:
        print "has paging!"
        pipe.hset("paging_token",paging_token,int(time.time())+30*60)
        pipe.card(pagingSet)
        pipe.sort(pagingSet,desc=True,start=(page-1)*records,num=records)
        result=pipe.execute()
        totalRecords=result[1]
        ret=list(result[2])
    
    if len(ret)==0:
        print "Return set is empty!"
        return {}
        
    
    recordList=proxy.records(ret,token)
    print "Records:%s"%recordList
    
    paging['totalrecords']=totalRecords
    remainder=totalRecords%records
    if remainder>0:
        paging['totalpages']=totalRecords/records+1
    else:
        paging['totalpages']=totalRecords/records
    paging['paging_token']=paging_token
    
    results={'paging':paging,'data':recordList}
      
    return results


@timeit
def export(user, password,product,start_date=None,end_date=None):
    '''
    Data exporting interface for manufacturer.
    Parameters:
    user=username
    password=password
    product=like: BKB
    start_date=like: 20120701
    end_date=like: 20120715(not included)
    
    Return:
    Headers:
    Content-Type:application/json    
    Body:
    {"results":[{},{},...]}
    A json array and every element in the array is a json document.
    array:[{},{}]
    document:{"_id":id,"receive_time":time,"json_str":original} 
    '''
    print 'export(),user=%s,product=%s,start=%s,end=%s'%(user,product,start_date,end_date)
    
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
            return {"error":"Unknown error"}
    
    redis = brconfig.getRedis()
    pipe = redis.pipeline(transaction=True)
    
    ret =[] 
    sets=[]    
    #accessibleSet='tmp_%s'%str(uuid.uuid4())
    timeFilteredSet='tmp_%s'%str(uuid.uuid4())
    resultIdsSet='tmp_%s'%str(uuid.uuid4())
        
    #Get accessible set    
    result=getAccessibleProducts(token)
    if result==None:
        print "No accessible products!"
        return {"error":"No accessible products!"}
    if ('error' in result):
        print "Error in result:%s"%result['error']
        return result
    products=result
    if product not in products:
        return {'error':'The given product is not in the accessible products list.'}
    sets.append('ids:i:android.os.Build.PRODUCT:%s'%product)
    
    #Get time filtered set    
    starttime=0
    endtime=0
    ntf=False
    if start_date!=None:
        try:
            starttime=int(datetime.strptime(start_date,"%Y%m%d").strftime('%s'))
            ntf=True
        except ValueError,e:
            print "start_date:%s"%e
            return {'error':'Invalid format for start_date:%s'%start_date}
    if end_date!=None: 
        try:
            endtime=int(datetime.strptime(end_date,"%Y%m%d").strftime('%s'))
            ntf=True
        except ValueError,e:
            print "end_date:%s"%e
            return {'error':'Invalid format for end_date:%s'%end_date}
    if ntf:        
        timeFilteredSet=getTimeFilteredSet(starttime,endtime,timeFilteredSet)        
        if timeFilteredSet==None:
            print "Time Filtered Set is None!"
            return []
        else:
            sets.append(timeFilteredSet)
    
    pipe.sinter(sets)
    pipe.delete(timeFilteredSet)
    result=pipe.execute()
    
    retset=list(result[0])
    if len(retset)==0:
        print 'The result set is empty!'
        return []
    
    result=proxy.export(retset)    
    response.set_header("Content-Type","application/json")
    return result

#@timeit
def getTimeFilteredSet(start,end,tmpSetName):
    start=int(start)
    end=int(end)
    if start==0:
        start=int(datetime.date(2012,1,1).strftime("%s"))
    if end==0:
        end=int(time.time())
    aday=3600*24
    sets=[]
    
    redis = brconfig.getRedis()
    pipe = redis.pipeline(transaction=True)
    
    i=0
    day=start
    while(day<=end):
        day=start+i*aday
        datestr=date.fromtimestamp(day).strftime("%Y%m%d")
        sets.append("ids:date:%s"%datestr)
        i+=1
    
    if len(sets)>0:
        pipe.sunionstore(tmpSetName,sets)
        pipe.execute()
        return tmpSetName
    else:
        return None   
        
@timeit
def product_summary(token,platform='4.0.4',callDropMode=False):
    '''
    Give a summary for all the accessible products. The summary data can be error
    rate or call drop rate.
    @param token access token
    @platform android platform version, like: 2.3.3, 2.3.7, 4.0.3 or 4.0.4 
    @param mode work mode flag, whether error rate or call drop rate.
    '''    
    
    #TODO: To optimize, error count, live time, call drop and call count can be computed before query.        
      
    #Get accessible product list    
    result=getAccessibleProducts(token)
    print "result:%s"%result
    if result==None:
        print "No accessible products!"
        return {"error":"No accessible products!"}
    if ('error' in result):
        print "Error in result:%s"%result['error']
        return result
    products=result
    
    MAX_REVISION_COUNT=5    
    redis = brconfig.getRedis()
    pipe = redis.pipeline(transaction=True)
        
    errorSet='ids:e'#all errors without call drop
    liveTimeSet='ids:s:com.borqs.bugreporter:LIVE_TIME'
    callDropSet='ids:b:CALL_DROP'
    callCountSet='ids:s:com.borqs.bugreporter:CALL_COUNT'
    
    tmp='tmp_%s'%uuid.uuid4()    
    
    #Get revision list for every products
    platProducts=redis.smembers('set:%s:products'%platform)
    products=set(products)&set(platProducts)
    products=list(products)
    products.sort()    
    
    if callDropMode:
        mode="calldrop"
        sumKey="drop"
        countSet=callDropSet
        baseSet=callCountSet
    else:
        mode="error"
        sumKey="error"
        countSet=errorSet
        baseSet=liveTimeSet
    
    revisions={}
    pLength=len(products)
    if pLength==0:
        return []
        
    for product in products:        
        revisionList=redis.sort('set:%s:%s:%s:revisions'%(platform,product,mode),alpha=True,desc=True)#why alpha=True?
        #TODO: revisionList has at least one item, otherwise the product name will not be listed here.
        sub=[]
        length=min(MAX_REVISION_COUNT,len(revisionList))
        for j in range(length):
            sub.append(revisionList[j])
            pipe.sinterstore(tmp,['ids:%s:%s:%s'%(platform,product,revisionList[j]),countSet])
            pipe.sinter(['ids:%s:%s:%s'%(platform,product,revisionList[j]),baseSet])
        revisions[product]=sub
    pipe.delete(tmp)
    ret=pipe.execute()
    
    #Get the count data; And save the part result to a temporary result set.
    #TODO: Why use temporary result?
    summary={} 
    k=0
    for product in products: 
        sub=revisions[product]
        total=0
        subSummary={}
        subSummary["product"]=product
        subSummary["mode"]=sumKey
        subSummary["sublist"]={}
        length=min(MAX_REVISION_COUNT,len(sub))
        for j in range(length):            
            revision=sub[j]
            subSummary["sublist"][revision]={}
            subSummary["sublist"][revision]["revision"]=revision
            errorOrDropCount=ret[k]
            subSummary["sublist"][revision]["count"]=int(errorOrDropCount)
            total+=errorOrDropCount
            if callDropMode:
                listLink="/api/brquery/query/error?android.os.Build.VERSION.RELEASE=%s&sandroid.os.Build.PRODUCT=%s&ro.build.revision=%s&e_type=CALL_DROP"%(platform,product,revision)
            else:
                listLink="/api/brquery/query/error?android.os.Build.VERSION.RELEASE=%s&android.os.Build.PRODUCT=%s&ro.build.revision=%s"%(platform,product,revision)
            subSummary["sublist"][revision]["link"]=listLink
            callOrLiveIdSet=list(ret[k+1])
            if len(callOrLiveIdSet)==0:
                pipe.scard("ThisKeyWillNeverExist")#always return 0
            else:
                pipe.hmget('s:values',callOrLiveIdSet)
            k+=2        
        subSummary["count"]=total
        subSummary["link"]="/api/brquery/query/rate?groupby=ro.build.revision&android.os.Build.VERSION.RELEASE=%s&android.os.Build.PRODUCT=%s&mode=%s"%(platform,product,sumKey)
        summary[product]=subSummary
    ret=pipe.execute()
    
    #Get the base data(livetime or callcount), and compute rate.
    k=0
    for product in products: 
        sub=revisions[product]
        total=0
        length=min(MAX_REVISION_COUNT,len(sub))
        for j in range(length):
            revision=sub[j]
            valueSet=ret[k]
            count=0
            if valueSet:
                for value in valueSet:                    
                    count+=int(value)                   
            total+=count
            if not callDropMode:
                count=count/3600
            summary[product]["sublist"][revision]['base']=count
            
            if count==0:
                summary[product]["sublist"][revision]['rate']='N/A'
            else:
                summary[product]["sublist"][revision]['rate']='%s%%'%(summary[product]["sublist"][revision]['count']*100/count)            
            k+=1
        if not callDropMode:
            total=total/3600
        summary[product]['base']=total
        if total==0:
            summary[product]['rate']='N/A'
        else:
            summary[product]['rate']='%s%%'%(summary[product]['count']*100/total)        
    pipe.execute()
    
    #Format the result
    result=[]
    for product in products:
        subSummary={}
        subList=[]
        subSummary["product"]=summary[product]["product"]
        subSummary["mode"]=summary[product]["mode"]
        subSummary["count"]=summary[product]["count"]
        subSummary["base"]=summary[product]["base"]
        subSummary["rate"]=summary[product]["rate"]
        subSummary["link"]=summary[product]["link"]
        
        for revision in summary[product]["sublist"]:
            subList.append(summary[product]["sublist"][revision])
        subSummary["sublist"]=subList
        result.append(subSummary)
    
    return result  

@timeit
def rate_summary(conditions, group, show_error_type=True):
    print "rate_summary()" 
    t0=time.clock()
    
    if 'token' in conditions:
        token=conditions.pop('token')
    else:
        return {"error":{"code":12,"msg":"Invalid token"}}
    
    print "conditions:"
    for key in conditions:
        print "%s:%s"%(key,conditions[key]) 
    print "Group by:%s"%group
    #TODO: Filter result by access right.
    
    #Get work mode: drop/error
    mode='error'
    if 'mode' in conditions:
        mode=conditions.pop('mode')
    if mode!='drop':
        mode='error'
        
        
    r = brconfig.getRedis()
    pipe = r.pipeline(transaction=True)
    
    group_key = group

    pipe.smembers('i:k:%s' % group_key)
    pipe.smembers('b:t')
    group_values, types = pipe.execute()
    
    if mode=='drop':
        types=['CALL_DROP']
    else:
        types=list(types)
        types.remove('CALL_DROP')
        
    #Get time filtered set
    timeFilteredSet='tmp_%s'%str(uuid.uuid4())    
    starttime=0
    endtime=0
    ntf=False
    if 'starttime' in conditions:
        starttime=conditions.pop('starttime')
        ntf=True        
    if 'endtime' in conditions:
        endtime=conditions.pop('endtime')
        ntf=True    
    if ntf:        
        timeFilteredSet=getTimeFilteredSet(starttime,endtime,timeFilteredSet)        
        if timeFilteredSet==None:
            print "Get empty set after time filterd!"
            return []#return empty set
        #print "Item count in filterd set:%s"%r.scard(timeFilteredSet)    

    # get all data except uptimes...
    t1=time.clock()
    
    for v in group_values:
        conditions[group_key] = v        
        sets = []
        tmpSet='tmp_%s'%str(uuid.uuid4())
        
        for k, v in conditions.items():
            sets.append('ids:i:%s:%s' % (k,v))
            
        if ntf:
            sets.append(timeFilteredSet)
        pipe.sinterstore(tmpSet, sets)

        if mode=='error':
            pipe.sinter(tmpSet, 'ids:s:%s:%s'%('com.borqs.bugreporter', 'LIVE_TIME'))
        else:
            pipe.sinter(tmpSet, 'ids:s:%s:%s'%('com.borqs.bugreporter', 'CALL_COUNT'))
        
        if show_error_type:
            for t in types:
                pipe.sinter(tmpSet, 'ids:b:%s'%t)
        else:
            pipe.sinter(tmpSet, 'ids:e')
            
        pipe.delete(tmpSet)
    
    if ntf:    
        pipe.delete(timeFilteredSet)
        
    ret = pipe.execute()
    
    t2=time.clock()
        
    # go through all results and get uptime data
    cur_ret = ret
    for v in group_values:
        time_ids = cur_ret[1]
        if len(time_ids) > 0:
            pipe.hmget('s:values', time_ids) 
        cur_ret = show_error_type and cur_ret[3+len(types):] or cur_ret[4:]
    times = pipe.execute() # to get all uptimes in one execute.
    
    t3=time.clock()
    
    # go through all results and get the data
    results = []
    for v in group_values:
        inter_num = ret[0]
        time_ids = ret[1]
        if inter_num > 0: # not empty
            uptime = 0
            if len(time_ids) > 0:
                cur_times = times[0]
                if mode=="error":
                    uptime = sum(long(t) for t in cur_times)/3600.
                else:
                    uptime = sum(int(t) for t in cur_times)
        
            if show_error_type:
                cur_bugs = ret[2:2+len(types)]
                l = map(lambda t, s: {'g_value':v, 'livetime':uptime, 'e_type':t, 'e_count': len(s)}, types, cur_bugs)
            else:
                l = [{'g_value':v, 'livetime':uptime, 'e_count': len(ret[2])}]
            errors = filter(lambda o: o['e_count'] != 0, l)
            if uptime > 0 and len(errors) ==0: # we should return the non-zero uptime in case of errors is empty 
                if show_error_type:
                    errors.append({'g_value':v, 'livetime':uptime, 'e_count': 0, 'e_type':''})
                else:
                    errors.append({'g_value':v, 'livetime':uptime, 'e_count': 0})

            results += errors
        ret = show_error_type and ret[3+len(types):] or ret[4:]
        times = times[len(time_ids) and 1 or 0:]
    t4=time.clock()
    print "t1=%s,t2=%s,t3=%s,t4=%s"%(t1-t0,t2-t1,t3-t2,t4-t3)
    return results


#return a float value, sum for phone uptime filtered by param conditions
def live_time(conditions):
    r = brconfig.getRedis()
    sets = ['ids:i:%s:%s' % (k,v) for k, v in conditions.items()]
    sets.append('ids:s:%s:%s'%('com.borqs.bugreporter', 'LIVE_TIME'))
    time_ids = r.sinter(sets)
    if len(time_ids) > 0:
        uptimes = r.hmget('s:values', time_ids)
        return sum(long(t) for t in uptimes)/3600.
    else:
        return 0

#[{'e_type':'...', 'e_count':.}, {}, ...]
def error_count(conditions, show_error_type=True):
    r = brconfig.getRedis()
    sets = ['ids:i:%s:%s' % (k,v) for k, v in conditions.items()]
    if show_error_type:
        types = r.smembers('b:t')
        pipe = r.pipeline(transaction=True)
        for t in types:
            pipe.sinter(s for s in sets+['ids:b:%s'%t])
        errors = pipe.execute()
        l = map(lambda t, e: {'e_type':t, 'e_count': len(e)}, types, errors)
    else:
        l = [{'e_count': len(r.sinter(s for s in sets+['ids:b']))}]
    return filter(lambda o: o['e_count'] != 0, l)

#[{'e_type':'...', 'uptime':., 'e_count':.}, {}, ...]
def error_rate(conditions, show_error_type=True):
    errors = error_count(conditions, show_error_type)
    lt = live_time(conditions)
    for e in errors: e['uptime'] = lt
    if lt > 0 and len(errors) == 0:
        errors.append({'uptime':lt})
    return errors

# error types in a list
def error_types():
    return list(brconfig.getRedis().smembers('b:t'))

# error names of a specified error type in a list 
def error_names(error_type):
    return list(brconfig.getRedis().smemvers('b:t:%s'%error_type))

#generate excel for error list
def error_list_excel(data):
    datas=data['results']   
    w = Workbook() 
    ws = w.add_sheet('error_list')
    #set content font
    font = Font()
    font.name = "Arial"

    #set borders
    borders = Borders()
    borders.left = 1
    borders.right = 1
    borders.top = 1
    borders.bottom = 1

    al = Alignment()
    al.horz = Alignment.HORZ_CENTER
    al.vert = Alignment.VERT_CENTER
    style = XFStyle()
    style.font = font
    style.alignment = al
    style.borders = borders

    #set header font
    font1 = Font()
    font1.name = "Arial"
    font1.bold = True

    style1 = XFStyle()
    style1.font = font1
    style1.alignment = al
    style1.borders = borders

    ws.write(0,0,'ID',style1) 
    ws.write(0,1,'Receive_Time',style1)   
    ws.write(0,2,'Error_Type',style1)  
    ws.write(0,3,'Name',style1) 
    ws.write(0,4,'Description',style1) 
    ws.write(0,5,'PhoneNumber',style1) 
    ws.write(0,6,'Revision',style1)

    for key in datas[0].keys():
        print key
        
    j = 1    
    for record in datas:
        ws.write(j,0,record['_id'],style) 
        ws.write(j,1,record['receive_time'],style)   
        ws.write(j,2,record['type'],style)  
        ws.write(j,3,record['name'],style) 
        ws.write(j,4,record['info'],style) 
        ws.write(j,5,record['sys_info.phoneNumber'],style) 
        ws.write(j,6,record['sys_info.ro:build:revision'],style)
        j=j+1 
    
    response.set_header('Content-Type','application/vnd.ms-excel')
    response.set_header("Content-Disposition", "attachment;filename=errorlist.xls");
    return w.get_biff_data()


def getAccessibleSet(token,tmpSetName,ids=None):
    '''
    Generate the accessible set for the given token, and return the temperorary set name.
    The set should be remove after use. But if for the optimization reason, the 
    remove can be delay. 
    '''
    products=getAccessibleProducts(token)
    if ('error' in products):
        print "getAccessibleSet encounter error:%s"%products
        return products
        
    setName=generateSet(products,tmpSetName)
    if setName==None:
        print "Generate set fail!"
        return None
    
    if ids==None:
        return setName
    else:
        redis=brconfig.getRedis()
        pipe=redis.pipeline(transaction=True)
        
        tmpIds="tmp_%s" % str(uuid.uuid4())
        tmpResult="tmp_%s" % str(uuid.uuid4())
        
        for id in ids:
            pipe.sadd(tmpIds,id)
        
        pipe.sinterstore(tmpResult,setName,tmpIds)
        ret=pipe.execute()
        
        if (ret[-1]==0):
            pipe.delete(tmpResult)
            tmpResult=None
            
        pipe.delete(setName)
        pipe.delete(tmpIds)
        pipe.execute()
        
        return tmpResult
    
@timeit    
def getAccessibleProducts(token):
    '''
    Get accessible products for the given token.
    '''
    #print "getAccessibleProducts(%s)"%token
    
    url=brconfig.BRAUTH+"/accessible_products?token="+token
    f = urllib2.urlopen(url)
    msg=None
    try:
        msg=json.loads(f.readline())
        print "msg:%s"%msg 
    except Exception, e:
        return {"error":"%s"%e}
    
    print "msg:%s"%msg['results'] 
    msg=json.loads(msg['results'])
    if 'products' in msg:
        return msg["products"]
    elif 'error' in msg :
        return msg
    else:
        return {"error":"Unknown error!"}
        
def generateSet(products,tmpSetName):
    '''
    Generate a temporary union set for the given products list.
    '''
    print "generateSet()"
    
    if len(products)==0:
        print "Parameter(products) is empty!"
        return None
    
    redis = brconfig.getRedis()
    pipe = redis.pipeline(transaction=True)    
    
    sets=[]
    for p in products:
        sets.append("ids:i:android.os.Build.PRODUCT:%s"%p)
        
    pipe.sunionstore(tmpSetName,sets)
    ret=pipe.execute()
    
    if ret[0]==0:
        redis.delete(tmpSetName)
        print "Generated an empty set!"
        return None
    else:  
        return tmpSetName

@timeit
def isAccessible(token,record_id):
    '''
    Not a good implementation.
    '''
    tmpSetName='tmp_%s'%str(uuid.uuid4())
    tmpSetName=getAccessibleSet(token,tmpSetName)
    
    if tmpSetName == None:
        return False
    else:
        redis=brconfig.getRedis()
        pipe = redis.pipeline(transaction=True)
        pipe.sismember(tmpSetName,record_id)
        pipe.delete(tmpSetName)
        ret=pipe.execute()
        
        if ret[0]:
            return True
        else:
            return False

def get_accessible_ids(token,ids=None):
    tmpSetName='tmp_%s'%str(uuid.uuid4())
    tmpSetName=getAccessibleSet(token,tmpSetName,ids=ids)
    if tmpSetName==None:
        return None
    else:
        redis=brconfig.getRedis()
        ret_ids=redis.smembers(tmpSetName)
        redis.delete(tmpSetName)
        return ret_ids
    
def summary(conditions):
    '''
    
    '''
    data={}
    if "year" in conditions:        
        return getYearData(conditions["year"])
    elif "month" in conditions:
        return getMonthData(conditions["month"])
    elif "phonenumber" in conditions:
        return getUserData(phonenumber=conditions["phonenumber"])
    elif "imsi" in conditions:
        return getUserData(imsi=conditions["imsi"])
    return data

def getMonthData(month):
    '''
    '''
    if len(month)!=6:
        return {"error":"Invalid parameter"}
    redis=brconfig.getRedis()
    #redis=getRedis()
    pipe = redis.pipeline(transaction=True)
    pipe.keys("ids:error:%s??"%month)
    pipe.keys("ids:live:%s??"%month)
    errorList,liveList=pipe.execute()
    
    dayList=[]
    for key in errorList:
        pipe.scard(key)
        pipe.scard("ids:live:%s"%key[10:18])
        dayList.append(key[16:18])
    result=pipe.execute()
    data={}
    retLen=len(result)/2
    for i in range(retLen):
        data[dayList[i]]={"error":result[i*2],"live":result[i*2+1],"link":"errors?date=%s%s"%(month,dayList[i])}
        
    return data
    
    
    
def getYearData(year):
    '''
    '''
    if len(year)!=4:
        return {"error":"Invalid parameter"}
    redis=brconfig.getRedis()
    #redis=getRedis()
    pipe=redis.pipeline(transaction=True)
    keyList=redis.keys("ids:date:%s????"%year)
    monthList=[]
    for key in keyList:
        monthList.append(key[9:15])#like:201206
    
        
    monthList=list(set(monthList))#remove duplicate
    yearData={}
    for month in monthList:
        monthData=getMonthData(month)
        errorCount=0
        liveCount=0
        for item in monthData:
            errorCount+=monthData[item]["error"]
            liveCount+=monthData[item]["live"]
        yearData[month[4:6]]={"error":errorCount,"live":liveCount,"link":"summary?month=%s"%month}
    return yearData 
    

def getUserData(phonenumber=None, imsi=None):
    if phonenumber==None and imsi==None:
        return None
    redis=brconfig.getRedis()
    #redis=getRedis()
    pipe=redis.pipeline(transaction=True)
    keyName=None
    backupKeyName=None
    
    if phonenumber != None:
        user=phonenumber
        queryUrl="errors?phoneNumber=%s&date="%user
        keyName="ids:i:phoneNumber:%s"%phonenumber
        backupKeyName="ids:i:phoneNumber:+86%s"%phonenumber
    elif imsi!=None:
        user=imsi
        queryUrl="errors?imsi=%s&date="%user
        keyName="ids:i:phoneNumber:IMSI:%s"%imsi
    else:
        return None
        
    ret=redis.exists(keyName)
    if not ret:
        keyName=backupKeyName        
        ret=redis.exists(keyName)
        if not ret:
            return None
    
    
    aday=3600*24
    current=int(time.time())
    current=(current/aday)*aday#Get today start    
    #enday=current-aday*30            
    start=current
    end=current
    
    #i=0
    print keyName
    data={}
    for i in range(30):
        start=current-i*aday
        timestr=date.fromtimestamp(start).strftime("%Y%m%d")
        
        errorList=redis.sinter(keyName,"ids:error:%s"%timestr)
        liveList=redis.sinter(keyName,"ids:live:%s"%timestr)
        data[timestr]={"error":len(errorList),"live":len(liveList),"link":queryUrl+timestr}
        
    return data
      

def main():
    cond = {'android.os.Build.VERSION.RELEASE':'2.3.7', 'android.os.Build.PRODUCT':'TAHITI', 'android.os.Build.TYPE':'eng'}
    cond2 = {'android.os.Build.VERSION.RELEASE':'2.3.7', 'android.os.Build.PRODUCT':'TAHITI', 'android.os.Build.TYPE':'eng', 'e_type':'ANR', 'ro.build.revision':'76565'}
    cond3 = {'android.os.Build.VERSION.RELEASE':'2.3.7', 'android.os.Build.PRODUCT':'AZ510', 'e_type':'FORCE_CLOSE'}


if __name__ == '__main__':
    main()
