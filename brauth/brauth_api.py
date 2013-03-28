#!/usr/bin/env python
from bottle import Bottle, route, run, get, post, put, delete, request, response, abort, debug,HTTPError

import json

import brauth

'''
Application for BugReporter Server Authentication and Authorization.

Author: Chen Jiliang
Core ID: b099

'''
app=Bottle()

'''
Design notes:
1. It is better to use unified error code for the whole application.
Error code and msg:
11: Authentication fail
12: Invalid token
13: Parameter missing.
14: Can not find the user.
15: Insufficient right. 
16: Add fail.
17: Accessible project list is empty
18: No accessible products.
19: Caller priviledge needed.
20: Can not find the product.
21: Remove product fail.
22: Remove user fail.
23: Can not find the target user.
24: Can not find the target product.
25: Duplicate record.
26: No priviledge data in user info


'''

#Global constant
PRIVILEDGE_LEVEL_PM=20

#Decorator#
def validate():
    '''
    Validate the caller's token and priviledge.
    '''
    def decorator(func):
        def wrapper(*a, **ka):
            token=request.params.get("token")
            if token==None:
                return {"results":{"error":{"code":12,"msg":"Invalid token"}}}
            else:
                uid=brauth.validateToken(token)
                #print "token:%s"%token
                #print "uid:%s"%uid
                if uid==-1:
                    return {"results":{"error":{"code":12,"msg":"Invalid token"}}}
                else:
                    user=brauth.getUser(uid=uid)
                    if user==None:
                        return {"results":{"error":{"code":14,"msg":"Can not find the user."}}}
                    else:
                        if 'priviledge' in user:
                            priviledge=user['priviledge']
                            if priviledge>PRIVILEDGE_LEVEL_PM:
                                return {"results":{"error":{"code":15,"msg":"Insufficient right."}}}
                            else:
                                return func(callerPriv=priviledge, *a, **ka)
                        else:
                            return {"results":{"error":{"code":26,"msg":"No priviledge data in user info."}}}
        return wrapper
    return decorator



############Use API######################
     
@app.route('/auth',method='POST')
def auth():
    '''
    Parameters:
    Content-Type: application/json
    
    {username:name,password:pass}
    
    Return:
    {"error":{"code":11,"msg":"Authentication fail"}}
    or:
    {"token":"12345"}

    test:
    curl -H "Content-Type:application/json" -d "{\"username\":name,\"password\":pass}" http://localhost/api/brauth/auth
    
    '''
    #print "api.auth()"
    data=request.json
    username=data["username"]
    password=data["password"]
    response.set_header("Content-Type","application/json")
    return {'results':brauth.authAPI(username,password)}
    
@app.route('/accessible_products')
def accessible_products():
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
    token=request.params.get("token")
    response.set_header("Content-Type","application/json")
    return {'results':json.dumps(brauth.accessible_products(token))}
    

@app.route('/is_accessible')
def is_accessible():
    '''
    Parameters:
    token:
    product:
    
    Return:
    {"error":{"code":12,"msg":"Token invalid."}}
    or:
    {"result":false}/{"result":true}    
    '''
    token=request.params.get("token")
    product=request.params.get("product")
    response.set_header("Content-Type","application/json")
    return {'results':brauth.is_accessible(token)}
    
#############Manage API####################

@app.route('/user/')
@validate()
def getUser(callerPriv):    
    '''
    List all user.
    
    parameters:
    token
    
    return:
    {results:{"user":[{_id:int,name:string,email:string,priviledge:int},{}],"priviledge":[""]}}
    or:
    {"results":[]}
    ...    
    '''   
    user=brauth.getVisibleUser(callerPriv=callerPriv)
    priviledges=brauth.getPriviledges(callerPriv=callerPriv)
    if user==None:
        user=[]
    for item in user:
        priv=item['priviledge']
        if(priv==0):
            item['priviledge']='admin'
        elif(priv==10):
            item['priviledge']='internal'
        elif(priv==20):
            item['priviledge']='pm'
        elif(priv==30):
            item['priviledge']='user'
        elif(priv==40):
            item['priviledge']='external'


    return {"results":{'user':user,'priviledge':priviledges}}  
  
@app.route('/user/add')
@validate()
def addUser(callerPriv):
    '''
    Add a user.
    
    parameters:
    token
    name
    email
    priviledge# Should be more readable
    
    return:
    {results:userid} 
    or
    {"results":{"error":{"code":16,"msg":"Add user fail."}}}
    ...
    '''
    name=request.params.get("name")
    #password=request.params.get("password")
    email=request.params.get("email")
    priviledge=request.params.get("priviledge")
    password=brauth.randomPass(6)

    userId=brauth.addUser(callerPriv=callerPriv,name=name,password=password,email=email,priviledge=priviledge,visible=True)
    if userId==-1:
        return {"results":{"error":{"code":16,"msg":"Add fail."}}}
    else:
        brauth.sendMail(email,name,password)
        return {"results":userId}    
  
@app.route('/user/delete')
@validate()
def removeUser(callerPriv):    
    '''
    Delete a user specified by uid or name.
    
    parameters:
    token
    uid
    name
    
    return:
    {results:OK}
    '''
    uid=request.params.get("uid")
    user=None
    ret=None

    if uid==None:
        user=request.params.get("name")
        if user==None:
            return {"results":{"error":{"code":13,"msg":"Parameter missing."}}}
        else:
            ret=brauth.removeUser(callerPriv=callerPriv,name=user)
    else:
        ret=brauth.removeUser(callerPriv=callerPriv,uid=uid)
    if ret==-1:
        return {"results":{"error":{"code":22,"msg":"Remove user fail."}}}
    else:
        return {"results":'OK'}

@app.route('/user/changepass',method='POST')
def changePassword():
    '''
    User can change their password themselves.

    Parameters:
    Content-Type: application/json
    
    {username:name,oldpass:pass,newpass:pass}
    
    Return:
    {"error":{"code":11,"msg":"Authentication fail"}}
    or:
    {"token":"12345"}
    
    '''
    data=request.json
    username=data["name"]
    oldpass=data["oldpass"]
    newpass=data["newpass"]
    info=brauth.auth(username,oldpass)
    if info==None:
        return {'results':{"error":{"code":11,"msg":"Authentication fail"}}}
    else:
        #print "name:%s,pass:%s"%(username,newpass)
        brauth.setPass(username,newpass)
        #response.set_header("Content-Type","application/json")
        return {'results':'OK'}

@app.route('/user/resetpass')
@validate()
def resetPass(callerPriv):
    '''
    Parameters:
    name

    '''
    user=request.params.get("name")
    if user==None:
        return {"results":{"error":{"code":13,"msg":"Parameter missing."}}}
    else:
        info=brauth.getUser(name=user)
        if info==None:
            return {"results":{"error":{"code":14,"msg":"Can not find the user."}}}
        else:
            if callerPriv>info['priviledge']:
                return {"results":{"error":{"code":15,"msg":"Insufficient right."}}}
            else:
                newpass=brauth.randomPass(6)
                brauth.setPass(user,newpass)
                brauth.sendMail(info['email'],user,newpass)
                return {'results':'OK'}




@app.route('/rights/')
@validate()
def getRight(callerPriv):    
    '''
    List rights items.
    
    parameters:
    name
    token
    
    return:
    {user:string,products:[p1,p2]}
    '''
    user=request.params.get("name") 
    if user==None:
            return {"results":{"error":{"code":13,"msg":"Parameter missing."}}}   
    userInfo=brauth.getUser(name=user)
    if userInfo==None:
        return {"results":{"error":{"code":21,"msg":"Can not find the user."}}}
    pids=brauth.getRight(callerPriv=callerPriv,uid=userInfo['_id'])
    products=[]
    if pids!=None:
        for pid in pids:
            product=brauth.getProduct(pid)
            if product!=None:
                products.append(product['name'])        
    return {"results":{"user":user,"products":products}}

@app.route('/rights/add')
@validate()
def addRight(callerPriv):    
    '''
    Add a right item.
    
    parameters:
    token
    name: such as b999
    product: 
    
    
    ''' 
    user=request.params.get("name")    
    product=request.params.get("product")
    if user==None or product==None:
            return {"results":{"error":{"code":13,"msg":"Parameter missing."}}}

    uInfo=brauth.getUser(name=user)
    if uInfo==None:
        return {"results":{"error":{"code":23,"msg":"Can not find the target user."}}}
    elif "error" in uInfo:
        return {"results":uInfo}
    pInfo=brauth.getProduct(name=product)
    if pInfo==None:
        return {"results":{"error":{"code":24,"msg":"Can not find the target product."}}}
    elif "error" in pInfo:
        return {"results":pInfo}                
    try:
        brauth.addRight(callerPriv=callerPriv,uid=uInfo["_id"],pid=pInfo["_id"])
        return {"results":'OK'}                
    except Exception,e:
        print str(e)
        return {"results":{"error":{"code":16,"msg":"Add fail."}}}
    

@app.route('/rights/delete')
@validate()
def delete_right(callerPriv):
    '''
    Delete a right item.
    
    parameters:
    token
    name
    product
    
    return:
    {results:OK}
    '''
    user=request.params.get("name")    
    product=request.params.get("product")
    if user==None or product==None:
            return {"results":{"error":{"code":13,"msg":"Parameter missing."}}}
    uInfo=brauth.getUser(name=user)
    if uInfo==None:
        return {"results":{"error":{"code":23,"msg":"Can not find the target user."}}}
    elif "error" in uInfo:
        return {"results":uInfo}
    pInfo=brauth.getProduct(name=product)
    if pInfo==None:
        return {"results":{"error":{"code":24,"msg":"Can not find the target product."}}}
    elif "error" in pInfo:
        return {"results":pInfo}
    brauth.removeRight(callerPriv=callerPriv,uid=uInfo['_id'],pid=pInfo['_id'])
    return {"results":"OK"}

@app.route('/product/')
@validate()
def list_products(callerPriv):    
    '''
    List products.
    
    parameters:
    token
    
    return:
    {results:[{_id:int,name:string},{_id:int,name:string}]}
    '''
    ret=[]
    products=brauth.getProduct()
    if products!=None:
        ret=products 
    return {"results":ret}  

@app.route('/product/add')
@validate()
def add_product(callerPriv):
    '''
    Add product.
    
    parameters:
    token
    product
    
    return:
    {results:productId}
    or
    {results:{error info}}}
    '''    
    product=request.params.get("product") 
    if product==None:
        return {"results":{"error":{"code":13,"msg":"Parameter missing."}}}
    pid=brauth.addProduct(product)
    if pid==-1:
        return {"results":{"error":{"code":16,"msg":"Add fail."}}}
    else:
        return {"results":pid}
  
@app.route('/product/delete')
@validate()
def delete_product(callerPriv):
    '''
    Delete product by the give pid or product name.
    
    parameters:
    token
    pid
    product
    
    return:
    {results:OK} or {results:{error:Invalid id}} or {results:{error: Delete fail}}
    '''
    pid=request.params.get("pid")
    product=None
    ret=None

    if pid==None:
        product=request.params.get("product")
        if product==None:
            return {"results":{"error":{"code":13,"msg":"Parameter missing."}}}
        else:
            ret=brauth.removeProduct(name=product)
    else:
        ret=brauth.removeProduct(pid=pid)

    if ret==-1:
        return {"results":{"error":{"code":21,"msg":"Remove product fail."}}}
    else:
        return {"results":'OK'}

@app.route('/mapping/')
@validate()
def list_mappings(callerPriv):
    '''
    List mapping items.
    
    parameters:
    token
    product
    
    return:
    {results:{product:string,projects:[]}}
    '''
    product=request.params.get("product")
    if product==None:
        return {"results":{"error":{"code":13,"msg":"Parameter missing."}}}
    pInfo=brauth.getProduct(name=product)
    if pInfo==None:
        return {"results":{"product":product,"projects":[]}}
    mappings=brauth.getMapping(pid=pInfo['_id'])
    if mappings==None:
        return {"results":{"product":product,"projects":[]}}
    ret=[]
    for item in mappings:
        ret.append(item['project_at_server'])
    return {"results":{"product":product,"projects":ret}}

@app.route('/mapping/add')
@validate()
def add_mapping(callerPriv):
    '''
    Add mapping item.
    
    parameters:
    token
    product
    server
    project    
    
    return:
    
    '''
    product=request.params.get("product")
    server=request.params.get("server")
    project=request.params.get("project")
    if product==None or server==None or project==None:
        return {"results":{"error":{"code":13,"msg":"Parameter missing."}}}
    if server not in brauth.mantis_server:
        return {"results":{"error":"Unknown server name!"}}
    pInfo=brauth.getProduct(name=product)
    if pInfo==None:
        return {"results":{"error":{"code":16,"msg":"Add fail."}}}
    brauth.addMapping(pid=pInfo['_id'],project='%s@%s'%(project,server))
    return {"results":"OK"}
    
@app.route('/mapping/delete')
@validate()
def delete_mapping(callerPriv):    
    '''
    Delete a mapping item.
    
    parameters:
    token
    product
    project

    return:
    {results:OK}
    '''
    product=request.params.get("product")
    project=request.params.get("project")
    if product==None or project==None:
        return {"results":{"error":{"code":13,"msg":"Parameter missing."}}}
    pInfo=brauth.getProduct(name=product)
    if pInfo==None:
        return {"results":{"error":{"code":24,"msg":"Can not find the target product."}}}
    brauth.removeMapping(pid=pInfo['_id'],project=project)
    return {"results":"OK"}
   
###############Local invoked API################

@app.route('/auth/user')
#@local_invoked()
def auth_user():    
    user=request.params.get("user")
    password=request.params.get("password")
    if user==None or password==None:
        return {"results":{"error":{"code":13,"msg":"Parameter missing."}}}
    ret=brauth.auth(user,password)
    if ret==None:
        return {"results":False}
    else:
        return {"results":True}
   

if (__name__ == '__main__'):
    #print 'Run bugreport server in main mode!'
    debug(True)
    run(app,host='0.0.0.0', port=8080, reloader=True)


