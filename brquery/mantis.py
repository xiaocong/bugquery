#!/usr/bin/env python
from bottle import Bottle, route, run, get, post, put, delete, request, response, abort, debug

import pymongo# import Connection
from pymongo import *
import gridfs
import mimetypes
import json
import datetime,time
from bson.timestamp import Timestamp 
from bson.objectid import ObjectId

from suds.client import Client
from suds import WebFault
from suds.mx.appender import ListAppender



'''
Library for communicating with Mantis by SOAP API.

Author: Chen Jiliang
Core ID: b099

'''

mantis_server={"borqsbt":"https://borqsbt.borqs.com","borqsbt2":"https://borqsbt2.borqs.com","borqsbtx":"https://borqsbtx.borqs.com"}
    
#@app.route("/mantis/projects", method='POST')
def get_project_list():
    '''
    Get available project list for a specific user.
    Content-Type:application/json
    @param JSON format string: e.g: {"server":"borqsbt","username":"b999","password":"123456"}
    @return JSON format array: e.g: {result:[{id:1,name:ART-ICS,subproj:[{id:3,name:p1}]},{id:2,name:MOD}]}
    '''
      
    contentType=request.headers.get('Content-Type')
    if not contentType:
        abort(500,'missing Content-Type')
    datatype = request.headers.get('Content-Type').split(';')[0]
    if datatype=='application/json':
        data=request.json    
        if not data:
            abort(500,"No report data provided.")
            
        if "server" in data.keys():
            server_name=data['server']
        else:
            abort(500,"Missing server name")
            
        if server_name in mantis_server.keys():
            server_url=mantis_server[server_name]            
        else:
            abort(500,"Unknown mantis server name")
            
        if "username" in data.keys():
            username=data['username']
        else:
            abort(500,"Missing user name")
        
        if "password" in data.keys():
            password=data['password']
        else:
            abort(500,"Missing password")
                
        api_url = server_url+"/api/soap/mantisconnect.php?wsdl"
        client = Client(api_url)
        try:
            project_data_array=client.service.mc_projects_get_user_accessible(username,password)
            result=[]
            for project_data in project_data_array:
                project={"id":project_data.id,"name":project_data.name}
                if (len(project_data.subprojects)>0):
                    sub_project_array=[]
                    for sub_project_data in project_data.subprojects:
                        sub_project={"id":sub_project_data.id,"name":sub_project_data.name}
                        sub_project_array.append(sub_project)
                    project["subproj"]=sub_project_array                    
                result.append(project)
            return json.dumps({"results":result})
        except WebFault, e:
            abort(500,str(e))
        
    else:
        abort(500,'Invalid Content-Type:'+contentType)
    
    

#@app.route("/mantis/options", method='POST')
def get_option_list():
    '''
    Get available option list for a specific project and user.
    Content-Type:application/json
    @param JSON format string: e.g: {"server":"borqsbt","project":{"id":7,"name":"ART-T2-Acer"},"username":"b999","password":"123456"}
    @return JSON format array: e.g: {result:{category:[apps,OEM]],reproducibility:[{id:1,name:always},{id:2,name:random}],severity:[{id:1,name:1-block},{id:5,name:5-minor}],priority:[],customfield:[{id:1,name:Phase,values:[unit,feature]},{id:2,name:"Sub Categories",values:[app1,app2]},{id:3,name:Type,values:[defect,enhansment]}]}
    '''
    contentType=request.headers.get('Content-Type')
    if not contentType:
        abort(500,'missing Content-Type')
    datatype = request.headers.get('Content-Type').split(';')[0]
    if datatype=='application/json':
        data=request.json
        if not data:
            abort(500,"No report data provided.")
            
        if "server" in data.keys():
            server_name=data['server']
        else:
            abort(500,"Missing server name")
            
        if server_name in mantis_server.keys():
            server_url=mantis_server[server_name]            
        else:
            abort(500,"Unknown mantis server name")
        
        if "project" in data.keys():
            project=data['project']
            if "id" in project.keys():
                project_id=project['id']
            else:
                abort(500,"Missing project id")
            
            if "name" in project.keys():
                project_name=project['name']
            else:
                abort(500,"Missing project name")
        else:
            abort(500,"Missing project")
                
        if "username" in data.keys():
            username=data['username']
        else:
            abort(500,"Missing user name")
        
        if "password" in data.keys():
            password=data['password']
        else:
            abort(500,"Missing password")
                
        api_url = server_url+"/api/soap/mantisconnect.php?wsdl"
        client = Client(api_url)
        try:
            result={}
            categories=client.service.mc_project_get_categories(username,password,int(project_id))
            c_list=list(set(categories))
            c_list.sort()
            #print c_list
            result["category"]=c_list
            
            reproducibility_array=client.service.mc_enum_reproducibilities(username,password)
            reproducibility=[]
            for item in reproducibility_array:
                reproducibility.append({"id":item.id,"name":item.name})
            result["reproducibility"]=reproducibility
            
            severity_array=client.service.mc_enum_severities(username,password)
            severity=[]
            for item in severity_array:
                severity.append({"id":item.id,"name":item.name})
            result["severity"]=severity
            
            priority_array=client.service.mc_enum_priorities(username,password)
            priority=[]
            for item in priority_array:
                priority.append({"id":item.id,"name":item.name})
            result["priority"]=priority
            
            custom_field_array=client.service.mc_project_get_custom_fields(username,password,int(project_id))
            custom_field=[]
            for item in custom_field_array:
                if item.field.name in ("Phase","Sub Categories","Type"):
                    custom_field.append({"id":item.field.id,"name":item.field.name,"values":item.possible_values})#TODO e.g: "defect|enhancement|integration"
            result["customfield"]=custom_field
            
            return json.dumps({"results":result})
        except WebFault, e:
            abort(500,str(e))
        
    else:
        abort(500,'Invalid Content-Type:'+contentType)

#@app.route("/mantis/submit", method='POST')
def submit():
    '''
    Submit a ticket into mantis with the given issue data.
    Content-Type:application/json
    If submit successful, attach the ticket url to the issue data.
    @param JSON format string: e.g: {"record_id":88888,"server":"borqsbt","project":{"id":7,"name":"ART-T2-Acer"},"username":"b999","password":"123456","category":"Unknown","reproducibility":{"id":50,"name":"random"},"severity":{"id":40,"name":"5-minor"},"priority":{"id":20,"name":"5-low"},"summary":"[BugReporter]Update test code","description":"Update test code","customfield":[{"id": 1, "name": "Phase","value":"Unit Test"},{"id": 2, "name": "Sub Categories","value":"TestFramewrok-Testware"},{"id": 4, "name": "Type","value":"enhancement"}]}
    @return If successful,return a url point to the ticket,otherwise, return error info.
    '''
    contentType=request.headers.get('Content-Type')
    if not contentType:
        abort(500,'missing Content-Type')
    datatype = request.headers.get('Content-Type').split(';')[0]
    if datatype=='application/json':        
        data=request.json
        #print "Submit dat:%s"%data
        if not data:
            abort(500,"No report data provided.")
        
        if "record_id" in data.keys():
            record_id=data['record_id']
        else:
            abort(500,"Missing user name")
                
        if "server" in data.keys():
            server_name=data['server']
        else:
            abort(500,"Missing server name")
            
        if server_name in mantis_server.keys():
            server_url=mantis_server[server_name]            
        else:
            abort(500,"Unknown mantis server name")
        
        if "project" in data.keys():
            project=data['project']
            if "id" in project.keys():
                project_id=project['id']
            else:
                abort(500,"Missing project id")
            
            if "name" in project.keys():
                project_name=project['name']
            else:
                abort(500,"Missing project name")
        else:
            abort(500,"Missing project")
                
        if "username" in data.keys():
            username=data['username']
        else:
            abort(500,"Missing user name")
        
        if "password" in data.keys():
            password=data['password']
        else:
            abort(500,"Missing password")
        
        #category,reproducibility,severity,priority,summary,description,customfield
        
        if "category" in data.keys():
            category=data['category']
        else:
            abort(500,"Missing category")
        
        if "reproducibility" in data.keys():
            reproducibility=data['reproducibility']
            if "id" in reproducibility.keys():
                reproducibility_id=reproducibility['id']
            else:
                abort(500,"Missing reproducibility id")
            
            if "name" in reproducibility.keys():
                reproducibility_name=reproducibility['name']
            else:
                abort(500,"Missing reproducibility name")
        else:
            abort(500,"Missing reproducibility")
        
        if "severity" in data.keys():
            severity=data['severity']
            if "id" in severity.keys():
                severity_id=severity['id']
            else:
                abort(500,"Missing severity id")
            
            if "name" in severity.keys():
                severity_name=severity['name']
            else:
                abort(500,"Missing severity name")
        else:
            abort(500,"Missing severity")
        
        if "priority" in data.keys():
            priority=data['priority']
            if "id" in priority.keys():
                priority_id=priority['id']
            else:
                abort(500,"Missing priority id")
            
            if "name" in priority.keys():
                priority_name=priority['name']
            else:
                abort(500,"Missing priority name")
        else:
            abort(500,"Missing priority")
        
        if "summary" in data.keys():
            summary=data['summary']
        else:
            abort(500,"Missing summary")
        
        if "description" in data.keys():
            description=data['description']
        else:
            abort(500,"Missing description")
        
        if "customfield" in data.keys():
            customfield=data['customfield']
        else:
            abort(500,"Missing customfield")
        
                    
        api_url = server_url+"/api/soap/mantisconnect.php?wsdl"
        client = Client(api_url)
        issue=client.factory.create('IssueData')
        
        view_state=client.factory.create('ObjectRef')
        view_state.id=10
        view_state.name='public'
        issue.view_state=view_state
        
        #print project_id
        #print project_name
        
        project_data=client.factory.create('ObjectRef')
        project_data.id=int(project_id)
        project_data.name=project_name
        issue.project=project_data
        
        issue.category=category
        
        reproducibility_data=client.factory.create('ObjectRef')
        reproducibility_data.id=int(reproducibility_id)
        reproducibility_data.name=reproducibility_name
        issue.reproducibility=reproducibility_data
        
        priority_data=client.factory.create('ObjectRef')
        priority_data.id=int(priority_id)
        priority_data.name=priority_name
        issue.priority=priority_data

        severity_data=client.factory.create('ObjectRef')
        severity_data.id=int(severity_id)
        severity_data.name=severity_name
        issue.severity=severity_data

        status=client.factory.create('ObjectRef')
        status.id=10
        status.name='new'
        issue.status=status

        issue.summary=summary

        issue.description=description

        resolution=client.factory.create('ObjectRef')
        resolution.id=10
        resolution.name='open'
        issue.resolution=resolution

        projection=client.factory.create('ObjectRef')
        projection.id=10
        projection.name='none'
        issue.projection=projection

        eta=client.factory.create('ObjectRef')
        eta.id=10
        eta.name='none'
        issue.eta=eta
        
        custom_field_array=client.factory.create('CustomFieldValueForIssueDataArray')
        #appender=ListAppender()
        field_list=[]
        for item in customfield:
            custom_field_data= client.factory.create('CustomFieldValueForIssueData') 
            field=client.factory.create('ObjectRef')
            field.id=int(item['id'])
            field.name=item['name']
            custom_field_data.field=field
            custom_field_data.value=item['value']
            field_list.append(custom_field_data)
            #custom_field_array.append(custom_field_data)
            #appender.append(custom_field_array,custom_field_data)
        custom_field_array=field_list
        issue.custom_fields=custom_field_array
        
        #print issue
        #print "username:%s"%username
        #print "password:%s"%password
        try:            
            result=client.service.mc_issue_add(username,password,issue)                        
            return (record_id,server_url+"/view.php?id=%d"%int(result))
        except WebFault, e:
            #print str(e)
            abort(500,str(e))
        
    else:
        abort(500,'Invalid Content-Type:'+contentType)


