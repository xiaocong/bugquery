#!/usr/bin/python
# -*- coding: utf-8 -*-

#from pymongo import Connection
import redis, json
import sys, time, datetime
#from brconfig import getRedis
#from brconfig import getMongoDB
import string
import datetime,time
import uuid

import urllib2
#import brconfig

'''
ids:min
ids:max             Key to store the max ID of record. We used it when creating new record in redis.
ids:i               Set of IDs which contain sys info.
ids:i:<key>:<value> Set of IDs which contain specified key and value in sys info.
ids:b               Set of IDs which contain all errors.
ids:b:<type>        Set of IDs which contain all errors with <type>, e.g. FORCE_CLOSE.
ids:b:<type>:<name> Set of IDs which contain all errors with <type> and <name>. 
                    e.g. type = FORCE_CLOSE name = and com.borqs.home
ids:s               Set of IDs which contain all statistic records.
ids:s:<type>:<name> Set of IDs which contain all statistic records with <type> and <name>,
                    e.g. type = com.borqs.bugreporter, and name = LIVE_TIME
ids                 Set of all IDs in the DB
i:k                 Set of keys in sys info.
i:k:<key>           Set of values of the <key> in sys info.
b:t                 Set of error types, e.g. FORCE_CLOSE, KERNEL_PANIC
b:t:<type>          Set of error names with specified type.
s:t                 Set of statistic types
s:t:<type>          Set of statistic names with specified type.
s:values            HashSet of id/value pairs, which contains all statistic record id and its value.
'''



'''
ids:data:<YYYYMMDD>
ids:live:<YYYYMMDD>
ids:error:<YYYYMMDD>

set:platform:names #all android platform list
set:product:names #all products list
set:$PLATFORM:products #all products list on specific platform

ids:e                           #all error set (without call drop)
ids:$PLATFORM:$PRODUCT:$REVISION          #The id set of the $PRODUCT on $REVISION.
set:$PLATFORM:$PRODUCT:error:revisions    #Set of revisions which has error data.
set:$PLATFORM:$PRODUCT:calldrop:revisions #Set of revisions which has call drop data.
    
'''

def timeit(func):
    def wrapper():
        start = time.time()
        func()
        end =time.time()
        print 'Function %s() cost: %s s.'%(func.__name__,end - start)
    return wrapper

def getRedis():
    return redis.Redis(connection_pool = redis.ConnectionPool(host='192.168.7.210', port=6379, db=5))

@timeit    
def genSetByTime():
    red=getRedis()
    pipe = red.pipeline(transaction=True)  
    #ids
    aday=3600*24
    current=int(time.time())
    todaystart=(current/aday)*aday#Get today start   
    
    enday=int(datetime.date(2012,1,1).strftime("%s"))
    start=current
    end=current
    
    i=0
    while(start>enday):
        start=todaystart-i*aday
        end=start+aday        
        timestr=datetime.date.fromtimestamp(start).strftime("%Y%m%d")
        
        tmp=red.zrangebyscore("ids",start,end)
        for item in tmp:
            pipe.sadd("ids:date:%s"%timestr,item)
        pipe.execute()
        
        #red.delete("ids:date:%s"%timestr)
        i+=1
@timeit            
def genErrorSetByTime():
    
    redis=getRedis()
    pipe = redis.pipeline(transaction=True)  
    #ids
    aday=3600*24
    current=int(time.time())
    todaystart=(current/aday)*aday#Get today start
    enday=int(datetime.date(2012,1,1).strftime("%s"))
    start=current
    end=current
    
    errorSet="ids:e"
    redis.sdiffstore(errorSet,['ids:b','ids:b:CALL_DROP'])
    i=0
    while(start>enday):
        start=todaystart-i*aday
        end=start+aday        
        timestr=datetime.date.fromtimestamp(start).strftime("%Y%m%d")        
        ret=redis.exists("ids:date:%s"%timestr)
        
        if ret:                     
            pipe.sinterstore("ids:error:%s"%timestr,[errorSet,"ids:date:%s"%timestr])
        pipe.execute()
        
        i+=1 
@timeit
def genLiveSetByTime():
     
    red=getRedis()
    pipe = red.pipeline(transaction=True)  
    #ids
    aday=3600*24
    current=int(time.time())
    todaystart=(current/aday)*aday#Get today start
    enday=int(datetime.date(2012,1,1).strftime("%s"))
    start=current
    end=current
    
    i=0
    while(start>enday):
        start=todaystart-i*aday
        end=start+aday        
        timestr=datetime.date.fromtimestamp(start).strftime("%Y%m%d")
        
        ret=red.exists("ids:date:%s"%timestr)
        
        if ret:
            pipe.sinterstore("ids:live:%s"%timestr,["ids:date:%s"%timestr,"ids:s:com.borqs.bugreporter:LIVE_TIME"])            
        pipe.execute()
        
        i+=1

@timeit
def genPlatformNameSet():
    '''
    Result:
    'set:platform:names'# all android platform list
    '''
    
    red=getRedis()
    pipe = red.pipeline(transaction=True)  
    
    ret=red.smembers('i:k:android.os.Build.VERSION.RELEASE')
    
    for platform in ret:
        pipe.sadd('set:platform:names',platform)
        
    pipe.execute()
    
    #print red.sort('set:platform:names',alpha=True)

'''
set:product:names
#set:product:revisions
set:$PRODUCT:error:revisions(has error data or live data)
set:$PRODUCT:calldrop:revisions(has call drop data or call count data)

'''
@timeit
def genProductNameSet():
    '''
    Result:
    'set:product:names'# all product list
    '''
    
    red=getRedis()
    pipe = red.pipeline(transaction=True)  
    
    ret=red.smembers('i:k:android.os.Build.PRODUCT')
    
    for product in ret:
        pipe.sadd('set:product:names',product)
        
    pipe.execute()
    
    #print red.sort('set:product:names',alpha=True)

@timeit
def genPlatformProductList():
    '''
    Result:
    'set:$PLATFORM:products'# all product list on specific platform
    '''
    
    red=getRedis()
    pipe = red.pipeline(transaction=True)  
    tmp="tmp_%s"%str(uuid.uuid4())
    
    platforms=red.smembers('set:platform:names')
    products=red.smembers('set:product:names')
    
    for platform in platforms:
        for product in products:
            pipe.sinterstore(tmp,['ids:i:android.os.Build.VERSION.RELEASE:%s'%platform,'ids:i:android.os.Build.PRODUCT:%s'%product])        
    ret=pipe.execute()
    i=0
    for platform in platforms:
        for product in products:
            if ret[i]>0:
                pipe.sadd('set:%s:products'%platform,product)
            i+=1
    pipe.delete(tmp)
    pipe.execute()
    
    #for platform in platforms:
    #    print "%s:%s"%(platform,list(red.smembers('set:%s:products'%platform)))
    
    #print red.sort('set:product:names',alpha=True)
    
@timeit
def genProductRevisionSet():
    '''
    Result:
    'ids:e'#all error set (without call drop)
    'ids:$PLATFORM:$PRODUCT:$REVISION'#The id set of the $PRODUCT on $REVISION.
    'set:$PLATFORM:$PRODUCT:error:revisions'#Set of revisions which has error data.
    'set:$PLATFORM:$PRODUCT:calldrop:revisions'#Set of revisions which has call drop data.
    
    
    #TODO:How frequently should this method be invoked?
        
    'set:product:names'#all product set
    'ids:i:android.os.Build.PRODUCT:<value> '#all ids for the given product 
    
    set:$PLATFORM:products
       
    
    'i:k:ro.build.revision'#all revision set
    'ids:i:ro.build.revision:<value> '#all ids for the given revision
    
    'ids:b'
    'ids:b:<type>'
    'ids:s:<type>:<name>e.g. type = com.borqs.bugreporter, and name = LIVE_TIME'
    
    's:values '#All statistic values stored here, hashset.    
    
    
    Error without call drop:
    sdiff('ids:b','ids:b:CALL_DROP')
    
    Call drop:
    'ids:b:CALL_DROP'
    
    
    Live time:
    'ids:s:com.borqs.bugreporter:LIVE_TIME'
    
    Call count:
    'ids:s:com.borqs.bugreporter:CALL_COUNT'
    
    '''    
    red=getRedis()
    pipe = red.pipeline(transaction=True)    
    
    errorSet='ids:e'
    liveTimeSet='ids:s:com.borqs.bugreporter:LIVE_TIME'
    callDropSet='ids:b:CALL_DROP'
    callCountSet='ids:s:com.borqs.bugreporter:CALL_COUNT'
    
    red.sdiffstore(errorSet,['ids:b','ids:b:CALL_DROP'])#overwritten
    
    platformList=red.sort('set:platform:names',alpha=True)#sort by ASCII
    #productList=red.sort('set:product:names',alpha=True)#sort by ASCII
    revisionList=red.sort('i:k:ro.build.revision',desc=True)#sort by integer value, descrease
    
    #tmpProductRevisionSet='tmp_%s'%uuid.uuid4()
    tmp1='tmp_%s'%uuid.uuid4()
    tmp2='tmp_%s'%uuid.uuid4()
    tmp3='tmp_%s'%uuid.uuid4()
    tmp4='tmp_%s'%uuid.uuid4()
            
    for platform in platformList:
        print 'Platform:%s'%platform
        productList=red.sort('set:%s:products'%platform,alpha=True)#sort by ASCII
        for product in productList:
            print 'Product:%s'%product        
            for revision in revisionList:
                try:
                    rev=int(revision)
                    if rev<1000000:
                        productRevisonSet='ids:%s:%s:%s'%(platform,product,revision)           
                        pipe.sinterstore(productRevisonSet,['ids:i:android.os.Build.VERSION.RELEASE:%s'%platform,'ids:i:android.os.Build.PRODUCT:%s'%product,'ids:i:ro.build.revision:%s'%revision])
                        pipe.sinterstore(tmp1,[productRevisonSet,errorSet])#The stored set will be overwirten.
                        pipe.sinterstore(tmp2,[productRevisonSet,liveTimeSet])
                        pipe.sinterstore(tmp3,[productRevisonSet,callDropSet])
                        pipe.sinterstore(tmp4,[productRevisonSet,callCountSet])
                except Exception:
                    pass
            ret=pipe.execute()
            i=0
            for revision in revisionList:
                try:
                    rev=int(revision)
                    if rev<1000000:
                        if (ret[i*5]==0):
                            pipe.delete('ids:%s:%s:%s'%(platform,product,revision))
                        else:
                            if (ret[i*5+1]>0 or ret[i*5+2]>0):
                                pipe.sadd('set:%s:%s:error:revisions'%(platform,product),revision)
                            if (ret[i*5+3]>0 or ret[i*5+4]>0):
                                pipe.sadd('set:%s:%s:calldrop:revisions'%(platform,product),revision)
                        i+=1
                except Exception:
                    pass
            
    #Remove all temporary set
    pipe.delete(tmp1)
    pipe.delete(tmp2)
    pipe.delete(tmp3)
    pipe.delete(tmp4)
    
    pipe.execute()
    
@timeit
def clearPagingCache():
    
    key='paging_token'    
    redis=getRedis()
    pipe = redis.pipeline(transaction=True) 
    
    now=time.time()
    tokens=redis.hkeys(key)
    for token in tokens:
        expireTime=int(redis.hget(key,token))
        if expireTime<now:            
            pipe.hdel(key,token)
            pipe.delete("tmp_paging_%s"%token)
            pipe.execute()

       
if __name__ == '__main__':
    genSetByTime()
    genErrorSetByTime()
    genLiveSetByTime()
    genPlatformNameSet()
    genProductNameSet()
    genPlatformProductList()
    #genProductRevisionSet()
    clearPagingCache()
    
    
