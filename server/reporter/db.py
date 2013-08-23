#!/usr/bin/env python

from config import Config
from pymongo import MongoReplicaSetClient
from pymongo import MongoClient
from pymongo.read_preferences import ReadPreference
from pymongo.errors import AutoReconnect
import gridfs

import redis

class DBHelper(object):
    '''
    '''
    
    def __init__(self):
        self.mongoDB=self.getMongoDB()
        self.gridFS=self.getFS(self.mongoDB)
        self.redisDB=self.getRedisDB()
        if self.redisDB is not None:
            self.redisPipe=self.redisDB.pipeline(transaction=True)
        else:
            self.redisPipe=None


    def getMongoDB(self):
        #conn=MongoReplicaSetClient(Config['ReplicaSetServer'], replicaSet=Config['ReplicaSetName'])
        #conn.read_preference = ReadPreference.PRIMARY
        conn=MongoClient(Config['MongoServer'])
        return conn.bugreporter
        
    def getRedisDB(self):
        #r=None
        try:
            r=redis.Redis(connection_pool = redis.ConnectionPool(host=Config['RedisServer'], port=int(Config['RedisPort']), db=int(Config['RedisDB'])))
        except:
            r=None
        return r
        
    def getFS(self,db):
        return gridfs.GridFS(db, collection='fs')


dbHelper=DBHelper()


