#!/usr/bin/env python

from bottle import request, response, abort
import urllib2
import json
import time



#Decorator for timing the function execution.
def timeit(func):
    def wrapper(*a, **ka):
        start = time.time()
        ret=func(*a, **ka)
        end =time.time()
        print 'Function %s() cost: %s s.'%(func.__name__,end - start)
        return ret
    return wrapper



def check_user(check,expected_user):
    #print "brstore.check_user()"
    def decorator(func):
        def wrapper(*a, **ka):
            ###print "request path:%s"%request.path
            user=request.get_header("x-user")
            password=request.get_header("x-password") 
            ##print "expected_user:%s"%expected_user
            ##print "user:%s"%user
            ##print "password:%s"%password
            if user==None or password==None:
                pass
            elif user!=expected_user:
                pass
            elif not check(user, password):
                pass
            else:
                ##print "check_user:pass"
                return func(*a, **ka)
            ##print "check_user:fail"
            return {"results":{"error":{"code":11,"msg":"Authentication fail!"}}}            
        return wrapper
    return decorator


'''
from config import BRAUTH

def auth(user, pwd):
    
    Return True if username and password are valid. 
    
    #print "brstore.auth()"  
    url=BRAUTH+"/auth/user?user="+user+"&password="+pwd
    f = urllib2.urlopen(url)
    #content_type=f.info().gettype()
    #TODO ?check it or not
    msg=json.loads(f.readline())
    #print "auth:msg=%s"%msg
    if "results" in msg:
        return msg["results"]
    else:
        return False
    
'''   
