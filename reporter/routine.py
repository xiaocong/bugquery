#!/usr/bin/python
from db import dbHelper
import dcrator
import sys
import time,datetime



'''
Server routine
'''




''' MongoDB structure
db name: bugreporter
collections:
original_data: (int)_id,(ISODate)receive_time,(string)json_str,(string)uuid
report_data:
{
    "_id" : 50001,
    "category" : "STATISTIC",
    "info" : "21600",
    "name" : "LIVE_TIME",
    "occur_time" : "2012-03-31 07:33:41",
    "receive_time" : ISODate("2012-03-31T07:34:50.987Z"),
    "sys_info" : {
        "android:os:Build:DEVICE" : "T2",
        "android:os:Build:HOST" : "nataku09",
        "android:os:Build:PRODUCT" : "T2",
        "ro:build:revision" : "2050",
        "android:os:Build:TYPE" : "eng",
        "android:os:Build:HARDWARE" : "t2",
        "android:os:Build:FINGERPRINT" : "marvell/T2/T2:4.0.3/IML74K/eng.svnadmin.20120327.112725:eng/debug,test-keys",
        "android:os:Build:MODEL" : "AT390",
        "gsm:version:baseband" : "TTD_CP_01.06.056_P9:TTD_TVRTD_MSA_1.08.049_P4_ICS_L",
        "phoneNumber" : "13511035264",
        "bugreporter:version:name" : "4.8",
        "android:os:Build:VERSION:RELEASE" : "4.0.3",
        "kernelVersion" : "3.0.8 svnadmin@nataku09 #1 Tue Mar 27 11:29:06 CST 2012",
        "android:os:Build:USER" : "svnadmin",
        "bugreporter:version:code" : "4",
        "android:os:Build:TAGS" : "debug,test-keys",
        "deviceId" : "357218040002245",
        "android:os:Build:BRAND" : "marvell",
        "android:os:Build:DISPLAY" : "ART_M1-eng 4.0.3 IML74K eng.svnadmin.20120327.112725 debug,test-keys",
        "android:os:Build:MANUFACTURER" : "ACER",
        "android:os:Build:BOARD" : "unknown",
        "android:os:Build:TIME" : "1332818891000",
        "android:os:Build:VERSION:INCREMENTAL" : "eng.svnadmin.20120327.112725",
        "android:os:Build:ID" : "IML74K"
    },
    "type" : "com.borqs.bugreporter",
    "uuid" : "06b2dfc7-e0f4-4f34-9a4b-e528591b62bc"
}



'''


''' Redis structure
#id:min
id:max             Key to store the max ID of record. We used it when creating new record in redis.
#ids:i               Set of IDs which contain sys info.
ids:i:<key>:<value> Set of IDs which contain specified key and value in sys info.

ids:b               Set of IDs which contain all errors.
ids:b:<type>        Set of IDs which contain all errors with <type>, e.g. FORCE_CLOSE.
ids:b:<type>:<name> Set of IDs which contain all errors with <type> and <name>. 
                    e.g. type = FORCE_CLOSE name = and com.borqs.home
ids:s               Set of IDs which contain all statistic records.
ids:s:<type>:<name> Set of IDs which contain all statistic records with <type> and <name>,
                    e.g. type = com.borqs.bugreporter, and name = LIVE_TIME

ss:ids                 Set of all IDs in the DB
ss:ids:e
ss:ids:s
ss:revision

i:k                 Set of keys in sys info.
i:k:<key>           Set of values of the <key> in sys info.

b:t                 Set of error types, e.g. FORCE_CLOSE, KERNEL_PANIC
b:t:<type>          Set of error names with specified type.

s:t                 Set of statistic types
s:t:<type>          Set of statistic names with specified type.
s:values            HashSet of id/value pairs, which contains all statistic record id and its value.
'''


#filter data

def dataFilter(spec,fields):
    print 'dataFilter()'
    db=dbHelper.mongoDB
    cursor=db.report_data.find(spec,fields)
    return cursor

#process data

def dataProcessing(processors):
    print 'dataProcessing()'
    for processor in processors:
        pipe=processor()    

@dcrator.timeit
def getFirstIdAfter(timestamp):
    someDay=datetime.datetime.fromtimestamp(timestamp)
    cursor=dbHelper.mongoDB.report_data.find({'_id':{'$gt':int(1000000)},"receive_time":{"$gt":someDay}}).sort("_id").limit(1)
    if(cursor.count()==0):
        id=None
    else:
        id=int(cursor[0]["_id"])
    return id

@dcrator.timeit
def processSync():
    print 'processSync()'
    reserveTime=int(time.time())-90*24*3600
    db=dbHelper.mongoDB
    redis=dbHelper.redisDB
    redisPipe=dbHelper.redisPipe

    startId=redis.get('id:max')
    if startId is None:
        startId=getFirstIdAfter(reserveTime)
        if startId is None:
            print 'Sync error: Can not get start id.'
            return
    print 'Sync starting, start id=%s'%startId
    
    spec={'_id':{'$gt':int(startId)}}

    fields={'occur_time':False,
            'sys_info.android:os:Build:HOST':False,
            'sys_info.android:os:Build:FINGERPRINT':False,
            'sys_info.kernelVersion':False,
            'sys_info.android:os:Build:USER':False,
            'sys_info.android:os:Build:DISPLAY':False,
            'sys_info.android:os:Build:BOARD':False,
            'sys_info.android:os:Build:VERSION:INCREMENTAL':False}
    
    cursor=db.report_data.find(spec,fields)
    
    counter=0
    for data in cursor:
        counter+=1
        oldCmdCount=redisPipe.command_stack.__len__()
        try:
            id=data['_id']
            category=data['category']
            type=data['type']
            name=data['name']
            info=data['info']
            uuid=data['uuid']
            receiveTime=data['receive_time'].strftime('%s')# in seconds
            sysInfo=data['sys_info']            
            
            platform=sysInfo['android:os:Build:VERSION:RELEASE']
            product=sysInfo['android:os:Build:PRODUCT']            
            revision=sysInfo['ro:build:revision']
            buildTime=sysInfo['android:os:Build:TIME'][:-3]# in seconds
            
            if 'unknown' in [platform.lower(),product.lower()]:
                #print 'id=%s,unknown value'%(data['_id'])
                continue

            if category=='ERROR':
                redisPipe.sadd('b:t', type)
                redisPipe.sadd('ids:b:%s' % type, id)                
                if(type=='CALL_DROP'):
                    redisPipe.sadd('set:%s:%s:calldrop:revisions'%(platform,product),revision)
                else:
                    redisPipe.sadd('b:t:%s'%type, name)#except call drop
                    redisPipe.sadd('ids:b', id)
                    redisPipe.sadd('ids:b:%s:%s' % (type, name), id)
                    redisPipe.sadd('set:%s:%s:error:revisions'%(platform,product),revision)
                redisPipe.zadd('ss:ids:e', id, receiveTime)
            elif category=='STATISTIC':
                redisPipe.sadd('s:t', type)
                redisPipe.sadd('s:t:%s'%type, name)
                redisPipe.hset('s:values', id, info)
                redisPipe.sadd('ids:s', id)
                redisPipe.sadd('ids:s:%s:%s' % (type, name), id)
                redisPipe.zadd('ss:ids:s:%s'%name, id, receiveTime)
            else:
                continue

            for key in sysInfo:
                rKey=key.replace(':','.')
                redisPipe.sadd('i:k', rKey)
                redisPipe.sadd('i:k:%s'%rKey, sysInfo[key])
                redisPipe.sadd('ids:i:%s:%s' % (rKey, sysInfo[key]), id)                
                #redisPipe.sadd('ids:i', id)
            redisPipe.zadd('ss:ids', id, receiveTime)
            redisPipe.zadd('ss:revision', revision, buildTime)
            redisPipe.set('id:max', id)
            #redisPipe.execute()#Should limit the commands in pipeline, better less than 10000
        except Exception, e:
            print 'id=%s,error:%s'%(data['_id'],e)
            try:
                newCmdCount=redisPipe.command_stack.__len__()
                for i in range(newCmdCount-oldCmdCount):
                    redisPipe.command_stack.pop()
            except:
                pass
        if (counter%150==0):
            redisPipe.execute()
    redisPipe.execute()
    return redisPipe#needed?

@dcrator.timeit
def processTrim():
    print 'processTrim()'
    fields={'occur_time':False,
            'receive_time':False,
            'info':False,
            'sys_info.android:os:Build:HOST':False,
            'sys_info.android:os:Build:FINGERPRINT':False,
            'sys_info.kernelVersion':False,
            'sys_info.android:os:Build:USER':False,
            'sys_info.android:os:Build:DISPLAY':False,
            'sys_info.android:os:Build:BOARD':False,
            'sys_info.android:os:Build:VERSION:INCREMENTAL':False,
            'sys_info.android:os:Build:TIME':False}
    reserveTime=int(time.time())-90*24*3600
    ids=dbHelper.redisDB.zrangebyscore('ss:ids',0,reserveTime)
    if len(ids)>0:
        recordIds=[]
        for id in ids:
            recordIds.append(int(id))
        datas=dbHelper.mongoDB.report_data.find({"_id":{"$in":recordIds}},fields)

        redisPipe=dbHelper.redisPipe
        counter=0
        for data in datas:
            counter+=1
            oldCmdCount=redisPipe.command_stack.__len__()
            try:
                id=data['_id']
                category=data['category']
                type=data['type']
                name=data['name']
                #info=data['info']
                uuid=data['uuid']
                #receiveTime=data['receive_time'].strftime('%s')# in seconds
                sysInfo=data['sys_info']            
                
                platform=sysInfo['android:os:Build:VERSION:RELEASE']
                product=sysInfo['android:os:Build:PRODUCT']            
                revision=sysInfo['ro:build:revision']
                #buildTime=sysInfo['android:os:Build:TIME'][:-3]# in seconds
                
                if 'unknown' in [platform.lower(),product.lower()]:
                    #print 'id=%s,unknown value'%(data['_id'])
                    continue

                if category=='ERROR':
                    if 'log' in data:
                        log=data['log']
                        dbHelper.gridFS.delete(log)
                    #redisPipe.sadd('b:t', type)
                    redisPipe.srem('ids:b:%s' % type, id)                
                    if(type!='CALL_DROP'):
                        redisPipe.srem('ids:b', id)
                        redisPipe.srem('ids:b:%s:%s' % (type, name), id)
                    redisPipe.zrem('ss:ids:e', id)
                elif category=='STATISTIC':
                    #redisPipe.sadd('s:t', type)
                    #redisPipe.sadd('s:t:%s'%type, name)
                    redisPipe.hdel('s:values', id)
                    redisPipe.srem('ids:s', id)
                    redisPipe.srem('ids:s:%s:%s' % (type, name), id)
                    redisPipe.zrem('ss:ids:s:%s'%name, id)
                else:
                    continue

                for key in sysInfo:
                    rKey=key.replace(':','.')
                    #redisPipe.sadd('i:k', rKey)
                    #redisPipe.sadd('i:k:%s'%rKey, sysInfo[key])
                    redisPipe.srem('ids:i:%s:%s' % (rKey, sysInfo[key]), id)                
                    #redisPipe.sadd('ids:i', id)
                redisPipe.zrem('ss:ids', id)
                #redisPipe.zadd('ss:revision', revision, buildTime)
                #redisPipe.set('id:max', id)
                #redisPipe.execute()#Should limit the commands in pipeline, better less than 10000
            except Exception, e:
                print 'id=%s,error:%s'%(data['_id'],e)
                try:
                    newCmdCount=redisPipe.command_stack.__len__()
                    for i in range(newCmdCount-oldCmdCount):
                        redisPipe.command_stack.pop()
                except:
                    pass
            if (counter%150==0):
                redisPipe.execute()    
        redisPipe.execute() 

@dcrator.timeit
def clearRedisDB():
    keys=dbHelper.redisDB.keys('*')
    print len(keys)
    for key in keys:
        dbHelper.redisDB.delete(key)


def routine():
    print 'routine()'    
    #clearRedisDB()
    processSync()#80 mins for 1 million
    processTrim()

if __name__ == '__main__':
    '''
    Tasks:sync,redis_trim,mongo_trim
    '''    
    routine()
