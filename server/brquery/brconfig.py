#!/usr/bin/env python

import redis
#from pymongo import Connection
import pymongo
from pymongo import ReplicaSetConnection
from pymongo.read_preferences import ReadPreference
from pymongo import ReadPreference
from pymongo.errors import AutoReconnect

pool = [redis.ConnectionPool(host='192.168.7.218', port=6379, db=5), redis.ConnectionPool(host='192.168.7.218', port=6379, db=5)]
#pool = [redis.ConnectionPool(host='localhost', port=6379, db=5), redis.ConnectionPool(host='localhost', port=6379, db=5)]

def getRedis(server='slave'):
    global pool
    if server == 'master':
        return redis.Redis(connection_pool = pool[0])
    else:
        return redis.Redis(connection_pool = pool[1])
'''
def getMongoDB():
    #connection = Connection('192.168.7.201', 27017)
    connection = Connection('192.168.7.205', 27017)
    db = connection['bugreporter']
    collection = db['original_data']
    return collection
'''
def getMongoDB():
    conn=ReplicaSetConnection("192.168.5.60:27017,192.168.7.52:27017,192.168.5.156:27017", replicaSet='ats_rs')
    conn.read_preference = ReadPreference.SECONDARY_PREFERRED
    db = conn['bugreporter']
    collection = db['original_data']
    return collection

def getRSConn():
    conn=ReplicaSetConnection("192.168.5.60:27017,192.168.7.52:27017,192.168.5.156:27017", replicaSet='ats_rs')
    conn.read_preference = ReadPreference.SECONDARY_PREFERRED
    return conn
    

def getDB(conn,dbname):
    db=conn[dbname]    
    return db

BRSTORE='http://localhost/api/brstore'
BRAUTH='http://localhost/api/brauth'
