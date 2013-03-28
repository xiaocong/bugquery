#!/usr/bin/python
# -*- coding: utf-8 -*-

from pymongo import Connection
import redis, json
import sys, time, datetime
from config import getRedis
from config import getMongoDB
import string

'''
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

def read_data(mgd, red, min_id):
    #The max number records to be imported
    rowcount = 33

    #The last imported _id saved in ids:max
    startnum = min_id
    endnum = startnum + rowcount

    #pipe for redis
    pipe = red.pipeline(transaction=True)

    #import the first #rowcount records which _id are from startnum to endnum 
    mgd_original_data = mgd.find({'_id':{'$gt':startnum, '$lte':endnum}}).sort('_id')
    record_count = mgd_original_data.count()

    #If there are records which need to import
    while record_count > 0: 
        print "Import %d records........" % record_count

        #Interate all the records
        for i in range(record_count): 
            item = mgd_original_data.next()
            _id = item.get('_id')
            json_str = item.get('json_str')
            _receive_time = item.get('receive_time')
            _uuid = item.get('uuid')

            obj = getJsonObj(_id, json_str, _receive_time, _uuid)

            if not obj.has_key('sys_info') or not obj.has_key('category') or (obj['category']=='STATISTIC' and not obj.has_key('info')) or not obj.has_key('name') or not obj.has_key('type'):
                print obj.keys(), 
                print '    bypass id: %s' % _id
                continue
            for _key, _value in obj['sys_info'].items():
                print "_key, _value = %s, %s" % (_key, _value)
                pipe.sadd('i:k', _key)
                pipe.sadd('i:k:%s'%_key, _value)
                pipe.sadd('ids:i:%s:%s' % (_key, _value), _id)
                pipe.sadd('ids:i', _id)

            #Set of products for special VERSION_RELEASE
            if obj['sys_info'].has_key('android.os.Build.VERSION.RELEASE') and obj['sys_info'].has_key('android.os.Build.PRODUCT'):
                pipe.sadd('i:p:%s'%obj['sys_info']['android.os.Build.VERSION.RELEASE'], obj['sys_info']['android.os.Build.PRODUCT'])

            if obj['category'] == 'ERROR':
                pipe.sadd('b:t', obj['type'])
                pipe.sadd('b:t:%s'%obj['type'], obj['name'])
                pipe.sadd('ids:b', _id)
                pipe.sadd('ids:b:%s:%s' % (obj['type'], obj['name']), _id)
                pipe.sadd('ids:b:%s' % obj['type'], _id)
            elif obj['category'] == 'STATISTIC':
                pipe.sadd('s:t', obj['type'])
                pipe.sadd('s:t:%s'%obj['type'], obj['name'])
                pipe.hset('s:values', _id, obj['info'])
                pipe.sadd('ids:s', _id)
                pipe.sadd('ids:s:%s:%s' % (obj['type'], obj['name']), _id)
            pipe.zadd('ids', _id, _receive_time.strftime('%s'))
        pipe.set('ids:max', _id)
        pipe.execute()

        startnum = _id
        endnum = startnum + rowcount
        mgd_original_data = mgd.find({'_id':{'$gt':startnum, '$lte':endnum}})
        record_count = mgd_original_data.count()

def testData():
    con = getMongoDB()
    red = getRedis('master')
    cur_id = get_stored_cur_id(red)
    print "Current id in redis is %d"%cur_id
    read_data(con, red, cur_id)

def get_stored_cur_id(red):
    if not red.exists('ids:max'):
        red.set('ids:max', '-1')
#    return int(red.get('ids:max'))
    return string.atof(red.get('ids:max'))

def getJsonObj(_id, json_str, _receive_time, _uuid):
    _obj = {'_id':_id, 'received_time':_receive_time, 'uuid':_uuid}
    key_convert = { 'time': 'android.os.Build.TIME',
                    'host': 'android.os.Build.HOST',
                    'device': 'android.os.Build.DEVICE',
                    'type': 'android.os.Build.TYPE',
                    'incremental': 'android.os.Build.VERSION.INCREMENTAL',
                    'tags': 'android.os.Build.TAGS',
                    'version_release': 'android.os.Build.VERSION.RELEASE',
                    'release': 'android.os.Build.DISPLAY',
                    'board': 'android.os.Build.BOARD',
                    'fingerprint': 'android.os.Build.FINGERPRINT',
                    'id': 'android.os.Build.ID',
                    'brand': 'android.os.Build.BRAND',
                    'user': 'android.os.Build.USER',
                    'manufacture': 'android.os.Build.MANUFACTURER',
                    'product': 'android.os.Build.PRODUCT',
                    'model': 'android.os.Build.MODEL',
                    'hardware': 'android.os.Build.HARDWARE',
                    'platformware': 'ro.build.revision',
                    'baseband': 'gsm.version.baseband',
                    'firmware': 'apps.setting.platformversion',
                    'rel': 'apps.setting.integrate.rel',
                    'kernel_version': 'kernelVersion',
                    'phone_number': 'phoneNumber',
                    'device_id': 'deviceId',
                    'bugreporter_version_name': 'bugreporter.version.name',
                    'bugreporter_version_code': 'bugreporter.version.code'
                  }
    old_keys = key_convert.keys()
    try:
        json_str = validatejson(json_str)
        json_obj = json.loads(json_str)
        if json_obj.has_key('category'): #new format
            _obj['category'] = json_obj['category']
            if json_obj.has_key('bug_info') and type(json_obj['bug_info']) is type({}):
                bug_info = json_obj['bug_info']
                for key in bug_info.keys():
                    if key == 'bug_type':
                        _obj['type'] = bug_info[key]
                    elif key == 'name':
                        _obj['name'] = bug_info[key]
                    elif key == 'info':
                        if json_obj['category'] == 'STATISTIC':
                            _obj['info'] = int(bug_info[key])
                        else: # ERROR
                            _obj['info'] = bug_info[key]
                    elif key == 'time':
                        _obj['occurred_time'] = todatetime(bug_info[key])
                if not _obj.has_key('name'):
                    _obj['name'] = ''
                if not _obj.has_key('info'):
                    _obj['info'] = ''
        elif json_obj.has_key('bug_type'): #old format
            t = json_obj['bug_type']
            if t == 'LIVE_TIME' or t == 'CALL_COUNT':
                _obj['category'] = 'STATISTIC'
                _obj['type'] = 'com.borqs.bugreporter'
                _obj['name'] = t
                if json_obj.has_key('bug_info'):
                    _obj['info'] = int(json_obj['bug_info'])
            else:
                _obj['category'] = 'ERROR'
                _obj['type'] = t
                if json_obj.has_key('bug_info') and type(json_obj['bug_info']) is type({}):
                    bug_info = json_obj['bug_info']
                    for key in bug_info.keys():
                        if key == 'bug_id':
                            _obj['name'] = bug_info[key]
                        elif key == 'summary':
                            _obj['info'] = bug_info[key]
                        elif key == 'time':
                            _obj['occurred_time'] = todatetime(bug_info[key])
                    if not _obj.has_key('name'):
                        _obj['name'] = ''
                    if not _obj.has_key('info'):
                        _obj['info'] = ''
        
        if json_obj.has_key('sys_info') and type(json_obj['sys_info']) is type({}):
            sys_info = dict(map(lambda t: t[0] in old_keys and (key_convert[t[0]],t[1]) or t ,json_obj['sys_info'].items()))
            #si = [{k.replace('.','_'):v} for k,v in sys_info.items()]
            _obj['sys_info'] = sys_info
    except Exception, e:
        print '_id=%d,  '%_id, e.message
    return _obj

def validatejson(sjson):
    return sjson.replace('""""', '""').replace('\r','').replace('\n','').replace('""OPhone" ', '"OPhone ').replace('\\', '/')

def todatetime(stime):
    dt = None
    try:
        dt = datetime.datetime.strptime(stime, '%Y-%m-%d %H:%M:%S')
    except ValueError, e:
        dt = datetime.datetime.strptime(stime, '%Y.%m.%d %H:%M:%S')
    return dt

if __name__ == '__main__':
#    sync()
    testData()

