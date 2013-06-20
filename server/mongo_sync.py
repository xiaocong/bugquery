#!/usr/bin/python
# -*- coding: utf-8 -*-

import MySQLdb as mdb
from pymongo import Connection
import sys, time, datetime, json


def sync():
    con = mdb.connect('bugreport1.borqs.com', 'bugreporter', 'Borqs1234', 'bugreporter');
    mongodb = Connection()['bugreport']

    with con:
        minid = get_stored_max_id(mongodb)
        print 'minid = %d' % minid
        maxid = get_db_max_id(con)
        print 'maxid = %d' % maxid
        import_data1(con, mongodb, minid, maxid)
        #import_data1(con, mongodb, 1054599, 1054619)

def get_stored_max_id(mongodb):
    if mongodb.config.find({'_id':'max_id'}).count() == 0:
        mongodb.config.insert({'_id':'max_id', 'value':-1})
    return mongodb.config.find_one({'_id':'max_id'})['value']

def update_stored_max_id(mongodb, value):
    mongodb.config.update({'_id':'max_id'}, {'value':value})

def get_db_max_id(con):
    cur = con.cursor()
    sql = 'select max(_id) from original_data'
    cur.execute(sql)
    return int(cur.fetchone()[0])

def import_data1(con, mongodb, minid, maxid):
    cur = con.cursor()
    rowcount = 1000
    startnum, endnum = minid, minid+rowcount
    if endnum > maxid:
        endnum = maxid
    
    while startnum < maxid:
        print 'Import data between %d and %d...' % (startnum, endnum)
        sql = 'select _id, json_str, receive_time, uuid from original_data where _id>%d and _id<=%d' % (startnum, endnum)
        cur.execute(sql)
        for _id, json_str, _receive_time, _uuid in cur.fetchall():
            mongo_obj = {'_id':_id, 'received_time':_receive_time, 'uuid':_uuid}

            try:
                json_str = validatejson(json_str)
                json_obj = json.loads(json_str)
                if json_obj.has_key('category'): #new format
                    mongo_obj['category'] = json_obj['category']
                    if json_obj.has_key('bug_info') and type(json_obj['bug_info']) is type({}):
                        bug_info = json_obj['bug_info']
                        for key in bug_info.keys():
                            if key == 'bug_type':
                                mongo_obj['type'] = bug_info[key]
                            elif key == 'name':
                                mongo_obj['name'] = bug_info[key]
                            elif key == 'info':
                                if json_obj['category'] == 'STATISTIC':
                                    mongo_obj['info'] = float(bug_info[key])
                                else: # ERROR
                                    mongo_obj['info'] = bug_info[key]
                            elif key == 'time':
                                mongo_obj['occurred_time'] = todatetime(bug_info[key])
                elif json_obj.has_key('bug_type'): #old format
                    t = json_obj['bug_type']
                    if t == 'LIVE_TIME' or t == 'CALL_COUNT':
                        mongo_obj['category'] = 'STATISTIC'
                        mongo_obj['type'] = 'com.borqs.bugreporter'
                        mongo_obj['name'] = t
                        if json_obj.has_key('bug_info'):
                            mongo_obj['info'] = float(json_obj['bug_info'])
                    else:
                        mongo_obj['category'] = 'ERROR'
                        mongo_obj['type'] = t
                        if json_obj.has_key('bug_info') and type(json_obj['bug_info']) is type({}):
                            bug_info = json_obj['bug_info']
                            for key in bug_info.keys():
                                if key == 'bug_id':
                                    mongo_obj['name'] = bug_info[key]
                                elif key == 'summary':
                                    mongo_obj['info'] = bug_info[key]
                                elif key == 'time':
                                    mongo_obj['occurred_time'] = todatetime(bug_info[key])
                if json_obj.has_key('sys_info') and type(json_obj['sys_info']) is type({}):
                    sys_info = json_obj['sys_info']
                    si = [{k.replace('.','_'):v} for k,v in sys_info.items()]
                    mongo_obj['sys_info'] = si
            except Exception, e:
                print '_id=%d,  '%_id, e.message
            mongodb.bugs.update({'_id':_id}, mongo_obj, True, False)
        update_stored_max_id(mongodb, endnum)
        startnum = endnum
        endnum = startnum + rowcount
        if endnum > maxid:
            endnum = maxid

def validatejson(sjson):
    return sjson.replace('""""', '""').replace('\r','').replace('\n','').replace('""OPhone" ', '"OPhone ').replace('\\', '/')

def todatetime(stime):
    dt = None
    try:
        dt = datetime.datetime.strptime(stime, '%Y-%m-%d %H:%M:%S')
    except ValueError, e:
        dt = datetime.datetime.strptime(stime, '%Y.%m.%d %H:%M:%S')
    return dt

def import_data(con, mongodb, minid, maxid):
    cur = con.cursor()
    rowcount = 100
    startnum, endnum = minid, minid+rowcount
    if endnum > maxid:
        endnum = maxid
    
    while startnum < maxid:
        print 'Import data between %d and %d...' % (startnum, endnum)
        print 'sys_info',
        sql = 'select * from sys_info where _id>%d and _id<=%d' % (startnum, endnum)
        cur.execute(sql)
        for _id, _key, _value in cur.fetchall():
            mongodb.bugs.update({'_id':_id}, {'_id':_id, '$addToSet': {'info':{_key:_value}}}, True, False)

        print ', bug_date',
        sql = 'select * from bug_data where _id>%d and _id<=%d' % (startnum, endnum)
        cur.execute(sql)
        for _id, _type, _name, _sum, _time, _uuid in cur.fetchall():
            mongodb.bugs.update({'_id':_id}, 
                                {'_id':_id,
                                 'category':'bug',
                                 'type':_type, 
                                 'name':_name,
                                 'occurred_time':_time,
                                 'summary':_sum },
                                True, False)

        print ', statistic_data',
        sql = 'select * from statistic_data where _id>%d and _id<=%d' % (startnum, endnum)
        cur.execute(sql)
        for _id, _type, _name, _value in cur.fetchall():
            mongodb.bugs.update({'_id':_id}, 
                                {'_id':_id,
                                 'category':'statistics',
                                 'type':_type, 
                                 'name':_name,
                                 'value':_value },
                                True, False)

        print ', original_data'
        sql = 'select _id, receive_time, uuid from original_data where _id>%d and _id<=%d' % (startnum, endnum)
        cur.execute(sql)
        for _id, _receive_time, _uuid in cur.fetchall():
            mongodb.bugs.update({'_id':_id}, 
                                {'_id':_id,
                                 'received_time':_receive_time,
                                 'uuid':_uuid },
                                True, False)

        startnum = endnum
        endnum = startnum + rowcount
        if endnum > maxid:
            endnum = maxid

if __name__ == '__main__':
    sync()
