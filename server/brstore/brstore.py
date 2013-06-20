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
#from bson.timestamp import Timestamp 
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
        start = time.time()
        ret=func(*a, **ka)
        end =time.time()
        print 'Request from %s, Function %s() cost: %s s.'%(request.remote_addr,func.__name__,end - start)
        return ret
    return wrapper


class BugReportStore(object):
    '''
    Class mainly for storing bug report data, containing some basic data restrieve function. 
    '''
    def __init__(self):
        '''
        Do some initial works.
        '''
        #self.conn = Connection('192.168.7.201',27017)
        #self.conn = self.getConn()
        #if not self.conn:
        #    pass#TODO How to report this?        
        #self.db = self.conn['bugreporter']
        self.db = self.getDB()
        self.fs=self.getFS()
        if not self.fs:
            pass#TODO How to report this?

    ###########Add related routing###################
    #@app.route('/report',method='POST')
    def report_post(self):
        '''
        HTTP POST to upload a report string or data file
        '''
        ##print 'report_post()'
        #db = self.getDB()        
        contentType=request.headers.get('Content-Type')
        print 'content-type: ' + contentType
        if not contentType:
            abort(500,'missing Content-Type')
        ##print 'Content-Type:',contentType
        datatype = request.headers.get('Content-Type').split(';')[0]
        print 'dataType: ' + datatype
        if datatype=='application/json':#upload report string 
            ##print 'json:',request.json
            ##print 'upload report string with POST'
            info=request.json
            if not info:
                abort(500,"No report data provided.")
            return self.add_report(info)
        elif datatype=='text/plain':#(For Compatible Reason)
            info = json.loads(request.body.read())
            if not info:
                abort(500,"No report data provided.")
            return self.add_report(info)
        elif datatype=='multipart/form-data':
            ##print 'upload data file with POST'
            record_id=request.headers.get('record-id')
            if not record_id:
                abort(500,"No record id provided.")
            return self.upload_file(record_id)
        elif datatype=='application/zip':#(For Compatible Reason)
            ##print 'upload data file with POST'
            record_id=request.headers.get('record-id')
            if not record_id:
                abort(500,"No record id provided.")
            return self.upload_file(record_id)
        else:
            abort(500,'Invalid Content-Type:'+contentType)

    #@app.route('/report',method='PUT')
    def report_put(self):
        '''
        HTTP PUT to upload a data file
        '''
        ##print 'report_put()'
        record_id=request.headers.get('record-id')
        if not record_id:
                abort(500,"No record id provided.")
        return self.upload_file(record_id)
    
    #@app.route('/record/<record_id>/log',method='PUT')
    def upload_put(self,record_id):
        '''
        HTTP PUT to upload a data file
        '''
        ##print 'upload_data_put()'
        return self.upload_file(record_id)

    ###########Retrieve related routing###################
    #@app.route('/record/<record_id>',method='GET')
    @timeit
    def get_report(self,record_id):
        '''
        Get a single report data. 
        '''
        #print 'brstore.get_report(%s)'%record_id        
        #db=self.getDB()
        report=self.db["report_data"]
        record=report.find_one({"_id":int(record_id)})
        if record==None:
            record={}
        return {"results":self.serialize(record)}

    #@app.route('/record/<record_id>/log',method='GET')
    def get_log(self,record_id): 
        '''
        Get log file for report.
        '''        
        ##print 'querylog()'                
        #db=self.getDB()
        report=self.db["report_data"]    
        record=report.find_one({"_id":int(record_id)});
        if not record:
            abort(400,'No record found!') 
        elif ("log" not in record):
            abort(400,"No log file!")
        else: 
            #fs=self.getfs()
            if not self.fs.exists(record['log']):
                abort(400,'File not found!')
            else:
                log=self.fs.get(record['log'])
                response.set_header('Content-Type','application/x-download')
                response.set_header('Content-Disposition','attachment; filename=log_'+record_id+'.zip',True)
                return log 
    
    def get_file(self,fileId): 
        '''
        Get file.
        '''
        objId=ObjectId(fileId)
        exists=self.fs.exists(objId)
        if exists:
            log=self.fs.get(objId)
            response.set_header('Content-Type','application/x-download')
            response.set_header('Content-Disposition','attachment; filename='+fileId+'.zip',True)
            return log
        else:
            response.set_header('Content-Type','application/json')
            return {"error":"File doesn't exists for the given file id."}
                
    #TODO: How about when the set is extremly large?>1000
    def get_batch_report(self,record_ids):
        '''
        Retrieve a batch of report data for the given id array.
        '''
        report_data=self.db["report_data"]
        ids=[]
        for id in record_ids:
            ids.append(int(float(id)))
        records=report_data.find({"_id":{"$in":ids}},{"_id":1,"type":1,"name":1,"info":1,"receive_time":1,"sys_info.ro:build:revision":1,"sys_info.phoneNumber":1,"ticket_url":1})
        ret=[] 
        for record in records:
            ret.append(self.brief(record))
            
        return json.dumps(ret)#TODO dumps() or not dumps() is a problem!
    

    def old_export(self):
        '''
        '''
        COUNT_PER_PAGE=100
        
        params=request.params
        product=params.get('product')
        startid=params.get('startid')
        pageno=params.get('pageno')
        
        if not product or not startid:
            abort(500,"product and startid must be provided")
        startid=int(startid)
        if not pageno:
            pageno=1
        else:
            pageno=int(pageno)
            if pageno<=0:
                pageno=1
        original=self.db.original_data
        report=self.db.report_data
        
        cursor=report.find({"sys_info.android:os:Build:PRODUCT":product,"_id":{"$gte":startid}}).sort("_id",pymongo.ASCENDING).skip(COUNT_PER_PAGE*(pageno-1)).limit(COUNT_PER_PAGE)
        totalrecord=cursor.count(with_limit_and_skip=True)
        ##print "totalrecord:%d"%totalrecord
        if totalrecord==0:
            totalpage=0
        else:
            totalpage=int(totalrecord/COUNT_PER_PAGE)+1
        recordperpage=COUNT_PER_PAGE
        currentpage=pageno
        
        ids=[]
        ret=[]
        if(totalrecord!=0):
            for record in cursor:
                ids.append({"_id":int(record["_id"])})                
            records=original.find({"$or":ids},["_id","receive_time","json_str"])                    
            for doc in records:
                ret.append({"_id":int(doc["_id"]),"receive_time":int(doc["receive_time"].strftime("%s")),"json_str":doc["json_str"]})
                
        response.set_header("Content-Type","application/json")
        response.set_header("totalrecord",str(totalrecord))
        response.set_header("totalpage",str(totalpage))
        response.set_header("recordperpage",str(recordperpage))
        response.set_header("currentpage",str(currentpage))
            
        return json.dumps(ret)
    
    def export(self,record_ids):
        '''
        '''
        report_data=self.db["report_data"]
        ids=[]
        for id in record_ids:
            ids.append(int(float(id)))
        records=report_data.find({"_id":{"$in":ids}})
        ret=[] 
        for record in records:
            ret.append(self.serialize(record))
            
        return json.dumps(ret)
            
    def sync(self):
        '''
        '''
        params=request.params
        startid=params.get('startid')
        count=params.get('count')
        if not startid:
            abort(500,"Please specify the start id.")
        if not count:
            count=100
        report_data=self.db.report_data
        ret=[]
        records=report_data.find({"_id":{"$gt":int(startid)}}).sort("_id",pymongo.ASCENDING).limit(int(count))
        for record in records:
            ret.append({"_id":int(record["_id"]),"category":record["category"],"type":record["type"],"name":record["name"],"info":record["info"],"occur_time":record["occur_time"],"uuid":record["uuid"],"receive_time":record["receive_time"],"sys_info":record["sys_info"]})
            
        response.set_header("Content-Type","application/json")
        
        return json.dumps(ret)
        
    def ids(self):
        '''
        Retrieve the min and max id pair for the given starttime and endtime. 
        '''
        params=request.params
        if(not params.get("starttime") and not params.get("endtime")):
            abort(500,"No parameter provided.")
        start=params.get("starttime")
        end=params.get("endtime")
        
        dtstart=0
        if start:
            dtstart=datetime.datetime.fromtimestamp(float(start))
            if(dtstart>datetime.datetime.now()):
                abort(500,"Start time later than now!")
            report=self.db.report_data
            cursor=report.find({"receive_time":{"$gt":dtstart}}).sort("_id",pymongo.ASCENDING).limit(1)
            if(cursor.count()==0):
                idstart=-1
            else:
                idstart=int(cursor.next()["_id"])
        else:
            report=self.db.report_data
            cursor=report.find({}).sort("_id",pymongo.ASCENDING).limit(1)
            if(cursor.count()==0):
                idstart=-1
            else:
                idstart=int(cursor.next()["_id"])
        
        if end:
            dtend=datetime.datetime.fromtimestamp(float(end))
            if dtstart:
                if(dtend<dtstart):
                    abort(500,"End time before start time!")
                    
            report=self.db.report_data
            cursor=report.find({"receive_time":{"$lt":dtend}}).sort("_id",pymongo.DESCENDING).limit(1)
            if(cursor.count()==0):
                idend=-1
            else:
                idend=int(cursor.next()["_id"])
        else:
            report=self.db.report_data
            cursor=report.find({}).sort("_id",pymongo.DESCENDING).limit(1)
            if(cursor.count()==0):
                idend=-1
            else:
                idend=int(cursor.next()["_id"])
        
        if idend<idstart:
            idstart=-1        
        response.set_header("Content-Type","application/json")
        return {"start":idstart,"end":idend}
        
    def latest(self):
        '''
        '''
        count=request.params.get("count")
        if not count:
            count=20
        else:
            count=int(count)
            if(count<=0):
                count=1
            elif(count>100):
                count=100
                    
        report=self.db.report_data
        cursor=report.find({}).sort("_id",pymongo.DESCENDING).limit(count)
        ret=[]
        for doc in cursor:
            product="Unknown"
            if('android:os:Build:PRODUCT' in doc['sys_info']):
                product=doc['sys_info']['android:os:Build:PRODUCT']
            phone_number="Unknown"
            if('phoneNumber' in doc['sys_info']):
                phone_number=doc['sys_info']['phoneNumber']
            ret.append({"_id":int(doc['_id']),"category":doc['category'],"type":doc['type'],"name":doc['name'],"info":doc['info'],"receive_time":doc['receive_time'].strftime("%Y-%m-%d %H:%M:%S"),"product":product,"phone_no":phone_number})
        ##print "Not dumps result"
        return {'results':ret}
        
    ###########Delete related routing###################

    #@app.route("/delete/<record_id>", method='GET')
    #@app.route("/record/<record_id>", method='DELETE')
    def delete_report(self,record_id=None):
        '''
        Delete report data.
        '''
        #db = self.getDB()
        report=self.db['report_data']
        #fs=self.getfs()
        data=report.find_one({'_id':int(record_id)})
        if not data or data.count()==0:
            return None
        else:
            report.remove({'_id':int(record_id)})
            if "log" in data:
                fileId=data['log']
                fs.delete(fileId)
            return 'DELETE_OK'
  

    #@app.route("/record/<record_id>/log", method='DELETE')
    def delete_log(self,record_id=None):
        '''
        Delete log file.
        '''
        ##print 'delete_log()'
        if record_id is None or record_id == '':
            abort(500, "Invalid record_id")
        #db = self.getDB()
        report=self.db['report_data']
        #fs=self.getfs()
        data=report.find_one({'_id':int(record_id)})
        if not data or data.count()==0:
            return None
        else:            
            if "log" in data:
                fileId=data['log']
                fs.delete(fileId)
                return 'DELETE_OK'
            else:
                return None

    def set_ticket_url(self,record_id,url):
        '''
        Set Mantis ticket url for the issue.
        '''
        report_data=self.db['report_data']
        exists=report_data.find({'_id':int(record_id)})
        if not exists.count()==1:
            abort(500,'No record found for the given record id!')        
        report_data.update({"_id":int(record_id)},{'$set':{'ticket_url':url}})
        #data=report_data.find_one({'_id':int(record_id)})
        #return data 
        
    ###########Utilities###################    

    def getDB(self):        
        #return Connection('192.168.7.201',27017)['bugreporter']
        #return Connection('localhost',27017)['bugreporter']
        conn=ReplicaSetConnection("192.168.5.60:27017,192.168.7.52:27017,192.168.5.156:27017", replicaSet='ats_rs')
        conn.read_preference = ReadPreference.SECONDARY_PREFERRED
        return conn['bugreporter']
    
    def getFS(self):
        return gridfs.GridFS(self.db, collection='fs')
        
    def counter(self):    
        ret=self.db.counter.find_and_modify(query={"_id":"userId"},update={"$inc":{"next":1}},new=True,upsert=True)
        return int(ret["next"]); 

    def getConn(self):
        #return Connection('192.168.7.201',27017)
        conn=ReplicaSetConnection("192.168.5.60:27017,192.168.7.52:27017,192.168.5.156:27017", replicaSet='ats_rs')
        conn.read_preference = ReadPreference.SECONDARY_PREFERRED
        return conn

    def myCounter(self,db):    
        ret=db.counter.find_and_modify(query={"_id":"userId"},update={"$inc":{"next":1}},new=True,upsert=True)
        return int(ret["next"]);

    def getMaxId(self,db):    
        ret=db.counter.find_one({"_id":"userId"})
        if ret!=None:
            return int(ret["next"]);
        else:
            return int(-1)

    @timeit
    def add_report(self,info):
        '''
        Add report
        '''
        print 'info: ' + str(info)
        conn=self.getConn()
        db=conn['bugreporter']        
        
        original_data=db['original_data']
        report_data=db['report_data']

        '''
        exists=report_data.find({'uuid':info['uuid']})
        print 'find count: ' + str(exists.count())
        if exists.count()==1:#count>0 vs count ==1; how about count>1
            return {'id':int(exists[0]['_id'])}
        '''
        maxId=self.getMaxId(self.db)
        exists=None
        if maxId!=-1:
            exists=report_data.find_one({'uuid':info['uuid'],'_id':{'$gt':maxId-100000,'$lt':maxId}})
        else:
            exists=report_data.find_one({'uuid':info['uuid']})
            
        if exists!=None:
            return {'id':int(exists['_id'])}

        record_id=self.myCounter(db)
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
                    
        original_data.insert({"_id":record_id,"json_str":json.dumps(info),"receive_time":receive_time,"uuid":info['uuid']})
        report_data.insert({"_id":record_id,"category":info['category'],"type":info['bug_info']['bug_type'],"name":name_value,"info":info_value,"occur_time":info['bug_info']['time'],"uuid":info['uuid'],"receive_time":receive_time,"sys_info":sysInfo})
        
        #conn.end_request()

        return {'id':int(record_id)}

    @timeit
    def upload_file(self,record_id):
        '''
        Upload file
        '''
        ##print 'upload_file()'            
        conn=self.getConn()
        db=conn['bugreporter']        
        
        report_data=db['report_data']
        exists=report_data.find({'_id':int(record_id)})
        if not exists.count()==1:
            abort(500,'No record found for the given record id!') 
        fileId=None
        try:       
            fileId=self.fs.put(request.body)        
        except Exception,e:
            print "upload file fail!"
            abort(500,"upload file fail!")
        report_data.update({"_id":int(record_id)},{'$set':{'log':fileId}})

        #conn.end_request()

        return {'id':int(record_id)} 

    def serialize(self,document):  
        #print "serialize()"      
        if not document:
            return None
        if 'log' in document:
            document['log']=str(document['log'])
        if 'occur_time' in document:
            document['occur_time']=str(document['occur_time'])
        if 'receive_time' in document:
            document['receive_time']=document['receive_time'].strftime("%Y-%m-%d %H:%M:%S")
        return document
        
    def brief(self,document):  
        ##print "brief()"      
        if not document:
            return None
        #ret=document
        if document.has_key('log'):
            document['log']=str(document['log'])
        if document.has_key('occur_time'):
            document['occur_time']=str(document['occur_time'])
        if document.has_key('receive_time'):
            document['receive_time']=document['receive_time'].strftime("%m-%d %H:%M:%S")
        if document.has_key('info'):
            document['info']=document["info"][:37]
        #return json.dumps(document)
        return document

