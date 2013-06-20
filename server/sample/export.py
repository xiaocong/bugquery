#!/usr/bin/python
# -*- coding: utf-8 -*-
import json
import urllib2


user="intel"
password="intel@beijing"

def getRecords():
    url="http://ats.borqs.com/api/brquery/record/export"
    req = urllib2.Request(url)
    req.add_header("Content-Type","application/json")
    data={"user":user,"password":password,"product":"AZ210A","start_date":"20120724","end_date":"20120725"}    
    data=json.dumps(data)
    req.add_data(data)
    
    f=urllib2.urlopen(req)
    data=json.loads(f.readline())["results"]
    if 'error' in data:
        print "Encounter error:%s"%data['error']
        return
    else:
        total=len(data)
        ec=0
        ewol=0
        for record in data:
            if record['category']=='ERROR':
                ec+=1
            if 'log' in record:
                try:
                    log=getLog(record['log'])
                    if log!=None:
                        fp=open('%s.zip'%record['_id'],'w')
                        allLines=log.readlines()
                        fp.writelines(allLines)
                        log.close()
                        fp.close()
                    else:
                        print "Read log for %s fail."%record['_id']
                except Exception, e:
                    print e
            else:
                if record['category']=='ERROR':
                    ewol+=1
                    
        print 'total:%s,ec:%s,ewol:%s'%(total,ec,ewol)     

def getLog(fileId):
    url="http://ats.borqs.com/api/brquery/record/get_file"
    req = urllib2.Request(url)
    req.add_header("Content-Type","application/json")
    data={"user":user,"password":password,"file_id":fileId}    
    data=json.dumps(data)
    req.add_data(data)
    
    f=urllib2.urlopen(req)
    m=f.info()    
    contentType=m.getheader("Content-Type")
    
    if contentType=="application/x-download":
        return f
    elif contentType=="application/json":
        error=json.loads(f.readline())
        print "Error:%s"%error
        return None
    else:
        print "Unknown return info:%s"%f.readline()
        return None
        



if __name__ == '__main__':
    getRecords()

    
