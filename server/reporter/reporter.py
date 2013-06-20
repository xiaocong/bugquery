#!/usr/bin/env python
import json
import datetime,time

from db import dbHelper
import dcrator

'''
Author: Chen Jiliang
Core ID: b099
'''

class Reporter(object):
    '''
    Class mainly for storing bug report data, containing some basic data restrieve function. 
    '''
    def __init__(self):
        self.db=dbHelper.mongoDB
        if self.db==None:
            raise Exception('Get DB fail!')        
        self.fs=dbHelper.gridFS
        if self.fs==None:
            raise Exception('Get GridFS fail!')
        #self.redis=dbHelper.redisDB

#################################################################################################################
    '''
    def getMongoDB(self):
        conn=ReplicaSetConnection(Config['ReplicaSetServer'], replicaSet=Config['ReplicaSetName'])
        conn.read_preference = ReadPreference.SECONDARY_PREFERRED
        return conn.bugreporter
        
    def getRedis(self):
        try:
            r=redis.Redis(connection_pool = redis.ConnectionPool(host=Config['RedisServer'], port=int(Config['RedisPort']), db=int(Config['RedisDB']))
        except:
            r=None
        return r
    '''

    def getFS(self,db):
        return gridfs.GridFS(db, collection='fs')
        
    def getCounter(self,db):    
        ret=db.counter.find_and_modify(query={"_id":"userId"},update={"$inc":{"next":1}},new=True,upsert=True)
        return int(ret["next"]); 

    def getMaxId(self,db):    
        ret=db.counter.find_one({"_id":"userId"})
        if ret!=None:
            return int(ret["next"]);
        else:
            return int(-1)
            
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
            document['receive_time']=document['receive_time'].strftime("%Y-%m-%d %H:%M:%S")
        if document.has_key('info'):
            document['info']=document["info"][:37]
        if 'sys_info' in document:
            si=document.pop('sys_info')
            sysInfo={}
            for key in si:
                rKey=key.replace(':','.')
                sysInfo[rKey]=si[key]
            document['sys_info']=sysInfo
        #return json.dumps(document)
        return document

#################################################################################################################
    ###########Add related routing###################
    
    def report_post(self,dataTypes,recordId,body,json_data):
        '''
        HTTP POST to upload a report string or data file
        '''  
        result={'error':'Illegal data'}
        if 'application/json' in dataTypes:        
            if json_data!=None:
                result=self.addReport(json_data)
        elif 'text/plain' in dataTypes:
            data = json.loads(body.read())
            if data!=None:
                result=self.addReport(data)            
        elif 'application/zip' in dataTypes:
            if recordId!=None:
                result=self.uploadFile(recordId,body)            
        return result

    
    def report_put(self,dataTypes,recordId,body):
        '''
        HTTP PUT to upload a data file
        '''
        result={'error':'Illegal data'}
        if recordId!=None:
            result=self.uploadFile(recordId,body)            
        return result
    
    @dcrator.timeit
    def addReport(self,info):
        '''
        Add report
        ''' 
        original_data=self.db['original_data']
        report_data=self.db['report_data']        

        record=report_data.find_one({'uuid':info['uuid']})
        if record!=None:
            return {'id':int(record['_id'])}
        
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

        recordId=self.getCounter(self.db)            
        original_data.insert({"_id":recordId,"json_str":json.dumps(info),"receive_time":receive_time,"uuid":info['uuid']})
        report_data.insert({"_id":recordId,"category":info['category'],"type":info['bug_info']['bug_type'],"name":name_value,"info":info_value,"occur_time":info['bug_info']['time'],"uuid":info['uuid'],"receive_time":receive_time,"sys_info":sysInfo})
                    
        return {'id':int(recordId)}

    @dcrator.timeit
    def uploadFile(self,recordId,body):
        '''
        Upload file
        '''
        result={'error':'Fail to upload file.'}
        report_data=self.db['report_data']
        record=report_data.find_one({'_id':int(recordId)})
        if record==None:
            result={'error':'No record found for the given record id!'}
        else:
            fileId=None
            try:       
                fileId=self.fs.put(body)
                report_data.update({"_id":int(recordId)},{'$set':{'log':fileId}})
                result={'id':int(recordId)}
            except Exception,e:
                print e
        return result
        
    ###########Retrieve related routing###################
    #@app.route('/record/<record_id>',method='GET')
    
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
        return self.serialize(record)

    def getData(self,record_id):
        '''
        Get a single report data. 
        '''        
        report=self.db["report_data"]
        return report.find_one({"_id":int(record_id)}) 

    def getDatas(self,spec,fields):
        '''
        Get batch report data. 
        '''
        report=self.db["report_data"]
        return report.find(spec,fields)    

    #@app.route('/record/<record_id>/log',method='GET')
    def get_log(self,record_id): 
        '''
        Get log file for report.
        '''        
        report=self.db["report_data"]    
        record=report.find_one({"_id":int(record_id)});
        if not record is None:
            if 'log' in record:
                if self.fs.exists(record['log']):
                    return self.fs.get(record['log'])
        return None        
    
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
    @dcrator.timeit
    def get_batch_report(self,record_ids):
        '''
        Retrieve a batch of report data for the given id array.
        '''
        report_data=self.db["report_data"]
        ids=[]
        for id in record_ids:
            try:
                ids.append(int(id))
            except:
                pass
        records=report_data.find({"_id":{"$in":ids}},{"_id":1,"type":1,"name":1,"info":1,"receive_time":1,"sys_info.ro:build:revision":1,"sys_info.phoneNumber":1,"ticket_url":1})
        ret=[] 
        for record in records:
            ret.append(self.brief(record))
            
        #return json.dumps(ret)#TODO dumps() or not dumps() is a problem!
        return ret

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
        
    def latest(self,limit):
        '''
        '''
        count=limit
        if not count:
            count=20
        else:
            count=int(count)
            if(count<=0):
                count=1
            elif(count>100):
                count=100
                    
        report=self.db.report_data
        cursor=report.find().sort("_id",-1).limit(count)
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
        return ret
        
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
        
    
        
        
        
        

    
