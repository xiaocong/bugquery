#!/usr/bin/env python
from bottle import Bottle, route, run, get, post, put, delete, request, response, abort, debug

import pymongo
from pymongo import ReplicaSetConnection
from pymongo.read_preferences import ReadPreference
from pymongo import ReadPreference
from pymongo.errors import AutoReconnect
import gridfs
import mimetypes
import json
import datetime,time
from bson.objectid import ObjectId



'''
Application for BugReporter storage.

Author: Chen Jiliang
Core ID: b099

Dev questions:
1. For result wraping, which place is the best?

'''

#Decorator for timing the function execution.
def timeit(func):
    def wrapper(*a, **ka):
        start = time.clock()
        ret=func(*a, **ka)
        end =time.clock()
        print 'Request from %s, Function %s() cost: %s s.'%(request.remote_addr,func.__name__,end - start)
        return ret
    return wrapper


class BugReport(object):
    '''
    Class mainly for storing bug report data, containing some basic data restrieve function. 
    '''
    def __init__(self):
        '''
        Do some initial works.
        '''
        self.conn=self.getConn()
        if self.conn==None:
            raise Exception('Get DB connection fail!')
        self.db=self.getDB(self.conn)
        if self.db==None:
            raise Exception('Get DB fail!')        
        self.fs=self.getFS(self.db)
        if self.fs==None:
            raise Exception('Get GridFS fail!')

    ###########Add related routing###################
    #@app.route('/report',method='POST')
    @timeit
    def report_post(self,session):
        '''
        HTTP POST to upload a report string or data file
        '''
        #print '%s|report_post()'%session
        contentType=request.headers.get('Content-Type')
        if not contentType:
            abort(500,'missing Content-Type')
        datatype = request.headers.get('Content-Type').split(';')[0]
        if datatype=='application/json':#upload report string 
            info=request.json
            if not info:
                abort(500,"No report data provided.")
            return self.add_report(info,session)
        elif datatype=='text/plain':#(For Compatible Reason)
            info = json.loads(request.body.read())
            if not info:
                abort(500,"No report data provided.")
            return self.add_report(info,session)
        elif datatype=='multipart/form-data':
            ##print 'upload data file with POST'
            record_id=request.headers.get('record-id')
            if not record_id:
                abort(500,"No record id provided.")
            return self.upload_file(record_id,session)
        elif datatype=='application/zip':#(For Compatible Reason)
            record_id=request.headers.get('record-id')
            if not record_id:
                abort(500,"No record id provided.")
            return self.upload_file(record_id,session)
        else:
            abort(500,'Invalid Content-Type:'+contentType)

    #@app.route('/report',method='PUT')
    @timeit
    def report_put(self,session):
        '''
        HTTP PUT to upload a data file
        '''
        print '%s|report_put()'%session
        record_id=request.headers.get('record-id')
        if not record_id:
                abort(500,"No record id provided.")
        return self.upload_file(record_id,session)
    
    
    

    def getConn(self):
        #return Connection('192.168.7.201',27017)
        conn=ReplicaSetConnection("192.168.5.60:27017,192.168.7.52:27017,192.168.5.156:27017", replicaSet='ats_rs')
        conn.read_preference = ReadPreference.SECONDARY_PREFERRED
        return conn

    def getDB(self,conn):
        return conn.bugreporter
    
    def getFS(self,db):
        return gridfs.GridFS(db, collection='fs')
        
    def counter(self,db):    
        ret=db.counter.find_and_modify(query={"_id":"userId"},update={"$inc":{"next":1}},new=True,upsert=True)
        return int(ret["next"]); 

    def getMaxId(self,db):    
        ret=db.counter.find_one({"_id":"userId"})
        if ret!=None:
            return int(ret["next"]);
        else:
            return int(-1)

    
    #@timeit
    def add_report(self,info,session):
        '''
        Add report
        ''' 
        #print '%s|add_report()'%session               
        original_data=self.db['original_data']
        report_data=self.db['report_data']

        maxId=self.getMaxId(self.db)
        exists=None
        if maxId!=-1:
            exists=report_data.find_one({'uuid':info['uuid'],'_id':{'$gt':maxId-50000,'$lt':maxId}})
        else:
            exists=report_data.find_one({'uuid':info['uuid']})

        if exists!=None:
            return {'id':int(exists['_id'])}
        
        receive_time=datetime.datetime.now()
        sysInfo={}
        for key in info['sys_info']:
            sysInfo[key.replace('.',':')]=info['sys_info'][key]
        
        if('name' in info['bug_info']):
            name_value=info['bug_info']['name']
        else:
            name_value='Unknown'

        if('info' in info['bug_info']):
            info_value=info['bug_info']['info']
        else:
            info_value='Unknown'

        record_id=self.counter(self.db)            
        original_data.insert({"_id":record_id,"json_str":json.dumps(info),"receive_time":receive_time,"uuid":info['uuid']})
        report_data.insert({"_id":record_id,"category":info['category'],"type":info['bug_info']['bug_type'],"name":name_value,"info":info_value,"occur_time":info['bug_info']['time'],"uuid":info['uuid'],"receive_time":receive_time,"sys_info":sysInfo})
        
        #conn.disconnect()

        return {'id':int(record_id)}

    #@timeit
    def upload_file(self,record_id,session):
        '''
        Upload file
        '''
        #print '%s|upload_file()'%session
        report_data=self.db['report_data']

        exists=report_data.find_one({'_id':int(record_id)})
        if exists==None:
            abort(500,'No record found for the given record id!') 
        fileId=None
        try:       
            fileId=self.fs.put(request.body)        
        except Exception,e:
            print "upload file fail!"
            abort(500,"upload file fail!")
        report_data.update({"_id":int(record_id)},{'$set':{'log':fileId}})

        #conn.disconnect()

        return {'id':int(record_id)} 

    
