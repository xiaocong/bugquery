#!/usr/bin/env python
from pymongo import MongoReplicaSetClient
from pymongo import MongoClient   
from pymongo.read_preferences import ReadPreference
import redis

from suds.client import Client
from suds import WebFault
from suds.mx.appender import ListAppender

import hashlib
import uuid

import smtplib
import random

'''
Library for Authentication and Authorization.

Author: Chen Jiliang
Core ID: b099

'''

###########Web API supported##############
#@app.route('/auth',method='POST')
def authAPI(username,password):
    '''
    Parameters:
    {username:name,password:pass}
    
    Return:
    {"error":{"code":11,"msg":"Authentication fail"}}
    or:
    {"token":"12345"}
    
    '''
    #print "authAPI()"
    if "@" in username:#mantis account
        #print "Mantis account"
        index=username.find("@")
        server=username[index+1:]        
        try:
            projects=getProjectList(server,username[:index],password)
            #print "projects:%s"%projects
            if projects==None:
                return {"error":{"code":17,"msg":"Accessible project list is empty"}}
            else:
                ret=getUser(name=username)
                if ret!=None:
                    uid=ret['_id']
                    pids=getRight(uid=uid)
                    if pids!=None:
                        for pid in pids:
                            removeRight(uid=uid,pid=pid)
                    else:
                        print "pids is None"
                    setUser(uid=uid,password=password)
                else:
                    uid=addUser(name=username,password=password,email="Unknown",priviledge='external',visible=False)
                    if uid==-1:
                        return {"error":{"code":16,"msg":"Add user fail!"}}
                for project in projects:
                    ret=getMapping(project='%s@%s'%(project,server))
                    if ret!=None:
                        addRight(uid=uid,pid=ret[0]['p_id'])
                token=str(uuid.uuid4())
                addToken(token,uid)
                return {"token":token}
        except Exception,e:#Encounter network issue, use local info to auth.
            print str(e)
            ret=auth(username,password)
            if ret==None:
                return {"error":{"code":11,"msg":"Authentication fail"}}
            else:
                uid=ret['_id']
                token=str(uuid.uuid4())
                addToken(token,uid)
                return {"token":token}
    else:#BugReporter account
        ret=auth(username,password)
        if ret==None:
            return {"error":{"code":11,"msg":"Authentication fail"}}
        else:
            uid=ret['_id']
            token=str(uuid.uuid4())
            addToken(token,uid)
            return {"token":token}
    
    
#@app.route('/accessible_products')
def accessible_products(token):#TODO: Interface change when return empty list, be careful.
    '''
    Parameters:
    token:
    
    Return:
    {"error":{"code":12,"msg":"Token invalid."}}
    or:
    {"error":{"code":18,"msg":"No accessible products."}}
    or:
    {"products":["P1","P2"]}
    '''
    uid=validateToken(token)
    if uid==-1:
        return {"error":{"code":12,"msg":"Token invalid."}}
    else:
        user=getUser(uid=uid)
        pids=getRight(user['priviledge'],uid)
        products=[]
        if pids!=None:
            for pid in pids:
                ret=getProduct(pid=pid)
                if ret!=None:
                    products.append(ret['name'])
        return {"products":products}
    
#@app.route('/is_accessible')
def is_accessible(token,product):
    '''
    Parameters:
    token:
    product:
    
    Return:
    {"error":{"code":12,"msg":"Token invalid."}}
    or:
    {"result":false}/{"result":true}    
    '''
    uid=validateToken(token)
    if uid==-1:
        return {"error":{"code":12,"msg":"Token invalid."}}
    else:
        pids=getRight(uid=uid)
        if pids==None:
            return False
        ret=getProduct(name=product)
        if ret==None:
            return False
        return (ret['_id'] in pids)

###########Utilities###################

def getDB(name):
    if name=='mongo':
        #conn=MongoReplicaSetClient('dbserver-3:27017', replicaSet='ats_rs')
        #conn.read_preference = ReadPreference.SECONDARY_PREFERRED
        #conn.read_preference = ReadPreference.PRIMARY
        conn = MongoClient('mongodb://192.168.5.60:27017')
        return conn.brauth
    elif name=='redis':
        return redis.Redis(connection_pool = redis.ConnectionPool(host='192.168.7.218', port=6379, db=6))
    else:
        return None  
    
def getUserId():
    db=getDB('mongo')
    ret=db.id_user.find_one() 
    if ret!=None:
        ret=db.id_user.find_and_modify(query={"name":"user"},update={"$inc":{"next":1}},new=True,upsert=False)
        return int(ret["next"]) 
    else:
        db.id_user.insert({"_id":1,"name":"user","next":1})
        return int(1) 
    
def getProductId():
    db=getDB('mongo')
    ret=db.id_product.find_one() 
    if ret!=None:
        ret=db.id_product.find_and_modify(query={"name":"product"},update={"$inc":{"next":1}},new=True,upsert=False)
        return int(ret["next"]) 
    else:
        db.id_product.insert({"_id":1,"name":"product","next":1})
        return int(1)
        
###---User related API---###
'''
user:{_id:int,name:string,password:string,email:string,priviledge:int,visible:boolean}
_id: interger value, unique for every user.
name: user name, string value, unique for every user.
password: string, encrypted with md5, hexdigit form.
email: string, used for account initialize or password reset.
priviledge: integer value, admin:0, internal: 10, pm:20, user: 30, external:40
visible: boolean value. If false, only used for authentication, not for management.

CRUD:
addUser()
getUser()
setUser()
removeUser()

'''
priviledges={'admin':0,'internal':10,'pm':20,'user':30,'external':40}

def addUser(name,password,email,priviledge,visible,callerPriv=0):
    '''
    Add user.
    name: User name.
    password: password.
    email: Email.
    priviledge: Priviledge level value.
    visible: External user is invisible.
    
    Return: user id for the added user or -1 if add fail.
    '''
    print 'addUser(%s,%s,%s,%s,%s,%s)'%(name,password,email,priviledge,visible,callerPriv)
    if callerPriv==None:
        #raise Exception("Caller priviledge needed.")
        return -1
    if name==None or len(name)==0:
        #raise Exception('Missing name!')
        return -1
    if password==None or len(password)==0:
        #raise Exception('Missing password!')
        return -1
    if email==None or len(email)==0:
        #raise Exception('Missing email!')
        return -1
    if priviledge==None:
        #raise Exception('Missing priviledge!')
        return -1
    elif priviledge not in priviledges:
        return -1
    else:
        privValue=priviledges[priviledge]
        if callerPriv>=privValue:
            #raise Exception("Insufficient right.")
            return -1
    if visible==None:
        #raise Exception('Missing visible!')
        return -1
    db=getDB('mongo')
    #print db    
    m=hashlib.md5()
    m.update(password)
    record=db.user.find_one({"name":name})
    #print record
    if record==None:
        uid=getUserId()
        db.user.insert({"_id":int(uid),"name":name,"password":m.hexdigest(),"email":email,"priviledge":privValue,"visible":visible})
        return uid
    else:
        return -1

    
def getUser(callerPriv=0,uid=None,name=None):
    '''
    Get user info for the given uid or name.
    callerPriv: caller priviledge.
    uid: user id
    name: user name
    
    Return: A document contains the user info or a document list if no specific user info given.
    '''
    #print 'getUser()'
    if callerPriv==None:
        raise Exception("Caller priviledge needed.")
    db=getDB('mongo')
    if uid!=None:
        return db.user.find_one({"_id":int(uid),"priviledge":{"$gte":callerPriv}},{"_id":1,"name":1,"email":1,"priviledge":1})        
    elif name!=None:
        return db.user.find_one({"name":name,"priviledge":{"$gte":callerPriv}},{"_id":1,"name":1,"email":1,"priviledge":1})
    else:
        cursor=db.user.find({"priviledge":{"$gte":callerPriv}},{"_id":1,"name":1,"email":1,"priviledge":1})
        if cursor.count()==0:
            return None
        else:
            ret=[]
            for record in cursor:
                ret.append(record)
            return ret

def getVisibleUser(callerPriv=0,uid=None,name=None):
    '''
    Get user info for the given uid or name.
    callerPriv: caller priviledge.
    uid: user id
    name: user name
    
    Return: A document contains the user info or a document list if no specific user info given.
    '''
    #print 'getUser()'
    if callerPriv==None:
        raise Exception("Caller priviledge needed.")
    db=getDB('mongo')
    if uid!=None:
        return db.user.find_one({"_id":int(uid),"priviledge":{"$gte":callerPriv},"visible":True},{"_id":1,"name":1,"email":1,"priviledge":1})        
    elif name!=None:
        return db.user.find_one({"name":name,"priviledge":{"$gte":callerPriv},"visible":True},{"_id":1,"name":1,"email":1,"priviledge":1})
    else:
        cursor=db.user.find({"priviledge":{"$gte":callerPriv},"visible":True},{"_id":1,"name":1,"email":1,"priviledge":1})
        if cursor.count()==0:
            return None
        else:
            ret=[]
            for record in cursor:
                ret.append(record)
            return ret
        
def setUser(callerPriv=0,uid=None,name=None,password=None,email=None,priviledge=None,visible=None):#TODO How to provide parameter?
    '''
    Set user info(password,email,priviledge or visible)
    uid
    name
    
    Return: A document contains the info updated or None if fail.
    '''
    #print 'setUser()'
    if callerPriv==None:
        raise Exception("Caller priviledge needed.")
    db=getDB('mongo')
    query={}
    if uid!=None:
        query['_id']=int(uid)        
    elif name!=None:
        query['name']=name
    else:
        return None
    document={}
    if password!=None and len(password)!=0:
        document['password']=password
    if email!=None and len(email)!=0:
        document['email']=email
    if priviledge!=None:
        if callerPriv>=priviledge:
            raise Exception("Insufficient right.")
        else:
            document['priviledge']=priviledge
    if visible!=None:
        document['visible']=visible
    if len(document)>0:
        ret=db.user.find_and_modify(query,document,upsert=False,new=True)
    else:
        ret=db.user.find_one(query)
    return ret
    
def randomPass(length):
    candidate='ABCDEDGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz1234567890'
    password=''
    for i in range(length):
        index=random.randint(0,len(candidate)-1)
        password=password+candidate[index:index+1]
    return password

def setPass(username,password):
    '''
    Set password for given user. Maybe called when user change password.
    '''
    #print 'setPass()'
    db=getDB('mongo')
    m=hashlib.md5()
    m.update(password)
    db.user.update({'name':username},{'$set':{'password':m.hexdigest()}})


def sendMail(receiver,user,password):  
    sender = 'bugquery@borqs.com'  
    subject = 'Your account for BugReporter server has been initialized'  
    mailuser = 'bugquery@borqs.com'
    mailpass = '!QAZ2wsx3edc'
      
    msg = ("From: %s\r\nTo: %s\r\nSubject: %s\r\n\r\n" % (sender, receiver,subject))
    msg=msg+'Hi:\r\n'
    msg=msg+'\r\nThis mail send from BugReporter automatically, do not reply this mail.\r\n'
    msg=msg+'\r\nYour account has been initialized.\r\nusername: %s\r\npassword: %s\r\n'%(user,password)
    msg=msg+'\r\nBugReporter server: http://ats.borqs.com/bugquery/\r\n'
    msg=msg+'\r\nBest Regards!\r\n'
    msg=msg+'BugReporter Admin\r\n'

    smtp=None
    try:
        smtp = smtplib.SMTP_SSL()  
        smtp.connect('smtp.bizmail.yahoo.com')
        smtp.login(mailuser, mailpass)  
        smtp.sendmail(sender, receiver, msg)       
    except Exception, e:
        print e
    smtp.quit()

def removeUser(callerPriv=0,uid=None,name=None):
    '''
    Remove user.
    
    Return: user id for the removed item or -1 if fail.
    '''
    #print 'removeUser()'
    if callerPriv==None:
        raise Exception("Caller priviledge needed.")
    db=getDB('mongo')
    record=None    
    if uid!=None:
        record=db.user.find_one({"_id":int(uid)})
    elif name!=None:
        record=db.user.find_one({"name":name})
    if record!=None:
        priviledge=record['priviledge']
        if callerPriv>=priviledge:
            return -1
        else:
            userid=record['_id']
            db.user.remove({"_id":int(userid)})
            db.right.remove({"u_id":int(userid)}) 
            return userid       
    else:
        return -1

def auth(name,password):
    '''
    Authentication for a user.
    Return: A document contains the user info if authenticate pass, otherwise return None.    
    '''
    #print 'auth()'
    db=getDB('mongo')
    m=hashlib.md5()
    m.update(password)
    return db.user.find_one({"name":name,"password":m.hexdigest()},{"_id":1,"name":1,"email":1,"priviledge":1,"visible":1})
    
def getPriviledges(callerPriv):
    '''
    Get the available priviledges for the caller.
    '''
    callerPriv=int(callerPriv)
    values=[]
    if callerPriv==20:
        values=['user']
    elif callerPriv==0:
        values=priviledges.keys()
        values.remove('external')
        values.remove('admin')
    return values


###---Rights related API---###
'''
rights:{u_id:int,p_id:int}
CRUD:
add
remove 
set(unnecessary)
get
'''
def addRight(callerPriv=0,uid=None,pid=None):
    '''
    Add one right item for a specific user with the given uid.
    uid: user id.
    pid: product id.
    '''
    #print 'addRight()'
    db=getDB('mongo')
    user=getUser(uid=uid)
    if user==None:
        raise Exception('No user found for the given id')
    product=getProduct(pid=pid)
    if product==None:
        raise Exception('No product found for the given id.')
    if callerPriv>user['priviledge']:
        raise Exception('Insufficient right.')
    if db.rights.find_one({"u_id":uid,"p_id":pid})==None:
        db.rights.insert({"u_id":uid,"p_id":pid}) 
    
def getRight(callerPriv=0,uid=None):
    '''
    Get all rights for the given uid.
    uid: user id.
    
    Return: A list contains pid or None if no any right. 
    '''
    #print 'getRight(%s,%s)'%(callerPriv,uid)         
    db=getDB('mongo')
    user=getUser(uid=uid)
    #print "user:%s"%user
    if user==None:
        return None
    elif callerPriv>user['priviledge']:
        return None
    else:
        cursor=db.rights.find({"u_id":uid})
        if cursor.count()==0:
            return None
        else:
            ret=[]
            for record in cursor:
                ret.append(record['p_id'])
            return ret

def removeRight(callerPriv=0,uid=0,pid=0):
    '''
    Remove a single access right for a specific user with the given uid.
    uid: user id
    pid: product id 
    '''
    #print 'removeRight()'    
    db=getDB('mongo')
    user=getUser(uid=uid)
    if user==None:
        db.rights.remove({"u_id":uid,"p_id":pid})
    elif callerPriv>user['priviledge']:
        pass
    else:
        db.rights.remove({"u_id":uid,"p_id":pid})            
 
###---Product Related API---###
'''
product:{_id:int,name:string}
CRUD:
addProduct()
getProduct()
removeProduct()
'''       
def addProduct(name):
    '''
    Add product.    
    Return: product id or -1 if product exists.
    '''
    print 'addProduct()'    
    db=getDB('mongo')
    if db.product.find_one({"name":name})==None:
        pid=getProductId()
        db.product.insert({"_id":int(pid),"name":name})
        return pid
    else:
        return -1
    
def getProduct(pid=None,name=None):
    '''
    Get product info for the given uid or name.
    pid: product id
    name: product name    
    Return: A document contains the product info.
    '''
    #print 'getProduct()'    
    db=getDB('mongo')
    if pid!=None:
        return db.product.find_one({"_id":int(pid)})        
    elif name!=None:
        return db.product.find_one({"name":name})
    else:
        ret=[]
        cursor=db.product.find({})
        if cursor.count()==0:
            return None
        for record in cursor:
            ret.append(record)
        return ret
        
def removeProduct(pid=None,name=None):
    '''
    Remove product by id or name.    
    Return: product id for the removed item or -1 if fail.
    '''
    #print 'removeProduct()'
    db=getDB('mongo')
    record=None
    if pid!=None:
        record=db.product.find_one({"_id":int(pid)})
    elif name!=None:
        record=db.product.find_one({"name":name})            
    if record!=None:
        productid=record['_id']
        db.product.remove({"_id":int(productid)})
        db.right.remove({"p_id":productid})
        db.mapping.remove({"p_id":productid})        

###---Mapping Related API---###
'''
mapping:{p_id,project_at_server}
p_id: prduct id
project_at_server: such as T2@borqsbt
CRUD:
addMapping()
getMapping()
removeMapping()
'''    
def addMapping(pid,project):
    '''
    Add a mapping item for mantis project to BugReporter server product.
    pid: product id
    project: project at server, such as: T2@borqsbt
    
    '''
    #print 'addMapping()'
    db=getDB('mongo')
    if db.mapping.find_one({"p_id":pid,"project_at_server":project})==None:
        db.mapping.insert({"p_id":pid,"project_at_server":project}) 

def getMapping(pid=None,project=None):
    '''
    Get mapping relation.    
    Return: A list contains mapping item or None.
    '''
    #print "getMapping(pid=%s,project=%s)"%(pid,project)    
    db=getDB('mongo')
    cursor=None    
    if pid!=None:
        cursor=db.mapping.find({"p_id":int(pid)})
    elif project!=None:
        cursor=db.mapping.find({"project_at_server":project})
    else:
        return None        
    if cursor.count()==0:
        return None
    ret=[]
    for record in cursor:
        ret.append({'p_id':record['p_id'],'project_at_server':record["project_at_server"]})
    return ret
   
def removeMapping(pid,project):
    '''
    Remove mapping.    
    '''
    #print 'removeMapping(%s,%s)'%(pid,project)
    
    db=getDB('mongo')
    db.mapping.remove({"p_id":pid,"project_at_server":project})

   
###---Token Related API---###
'''
Token stored in redis server, will expire automaticlly.
key:token value, maybe a uuid.
value: uid
expire_seconds: 30 mins
'''
EXPIRE_TIMEOUT=30*60 #seconds
    
def addToken(token,uid):
    '''
    Add token.
    token: token
    uid: user id
    expire_seconds: time in seconds
    '''
    #print 'addToken()'
    db=getDB('redis')
    pipe=db.pipeline(transaction=True)
    pipe.set(token,uid)
    pipe.expire(token,EXPIRE_TIMEOUT)
    pipe.execute()

def validateToken(token):
    '''
    Validate token.
    token: token
    Return: user id for the token if token valid or -1 if token invalid.
    '''
    #print 'validateToken()'
    db=getDB('redis')
    if db.exists(token):
        db.expire(token,EXPIRE_TIMEOUT) #Automaticlly renew the token 
        return int(db.get(token))
    else:
        return -1

###---Mantis related---###
mantis_server={"borqsbt":"https://borqsbt.borqs.com","borqsbt2":"https://borqsbt2.borqs.com","borqsbtx":"https://borqsbtx.borqs.com"}
    

def getProjectList(server,username,password):
    '''
    Get available project list for a specific user.    
    @return A list of projects: e.g: [ART-ICS,MOD]
    '''
      
    if server in mantis_server.keys():
        server_url=mantis_server[server]            
    else:
        raise Exception("Unknown mantis server name")
                
    api_url = server_url+"/api/soap/mantisconnect.php?wsdl"
    client = Client(api_url)
    try:
        project_data_array=client.service.mc_projects_get_user_accessible(username,password)
        result=[]
        for project_data in project_data_array:
            result.append(project_data.name)
            if (len(project_data.subprojects)>0):                
                for sub_project_data in project_data.subprojects:
                    result.append(sub_project_data.name)                
        if len(result)==0:
            return None
        else:
            return result
    except WebFault, e:
        #print "SOAP:%s" % str(e)
        raise Exception(str(e))
           
    
 
