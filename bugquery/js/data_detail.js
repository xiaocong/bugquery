var grecordId="",preHeader="";
var jsondata,url_ticket="N/A", url_log="Not available";

function InitDetailform(){

    var renderingDetail = function(data) {   		    
	    $("#data_info").empty();
	    $("#device_info").empty();	    
	    jsondata=data; 
	    if(jsondata === undefined || jsondata === null) {
	    	$('#mantis').hide();
	    	alert('The record id doesn\'t exist, please double check!');
	    } else $('#mantis').show();

		if(data.category==="ERROR"){
			var tid="";	
			if(data.ticket_url !== null && data.ticket_url !== undefined) {
				tid=data.ticket_url;
				tid=tid.substring(tid.indexOf("id=")+3,tid.length);
				url_ticket = "<a href=\""+data.ticket_url+"\">" + tid +"</a>";
			} 
			
			if(data.log !== null && data.log !== undefined) {
			    url_log = "<a href=\"http://"+window.location.host+"/api/brquery/record/"+data._id+"/log\">log</a>";		
			} else url_log="N/A";
			
            $("#data_info").append("<tr class='k-grid-header' style=\"background-color:#8c8c8c\"><td colspan='5'>Error Data</td></tr>");
            $("#data_info").append("<tr class='k-header1'><td class='category'>ID</td><td class='category'>Type</td>"
	                                +"<td class='category'>Name</td><td class='category'>Occur Time</td><td class='category'>Log</td>");
            $("#data_info").append("<tr class='row-2'><td>"+data._id+"</td><td>"+data.type+"</td><td>"+data.name+"</td><td>"+data.occur_time+"</td>"
			                      +"<td>"+url_log+"</td></tr>"
			                      +"<tr class='k-header1'><td class='category' colspan='4'>Description</td><td class='category'>MantisTicket</td></tr>"
			                      +"<tr class='row-2'><td colspan='4'>"+ data.info +"</td><td>"+url_ticket+"</td></tr>");
		 } else {
	        $("#data_info").append("<tr class='k-grid-header' style=\"background-color:#8c8c8c\" ><td colspan='5'>Statistic Data</td></tr>");		        
	        $("#data_info").append("<tr class='k-header1' ><th>ID</th><th>Type</th><th>Name</th><th>Value</th></tr>");
			$("#data_info").append("<tr class='row-2'> <td>"+data._id+"</td><td>"+data.type+"</td><td>"+data.name+"</td><td>"+data.info+"</td></tr>");
		 }
		 $("#device_info").append("<tr class='k-grid-header' style=\"background-color:#8c8c8c\"><td colspan='3'>Device Information</td></tr>");
		 for(i in data.sys_info){
			  $("#device_info").append("<tr class='row-2'><td class='k-header1'>"+i+"</td><td colspan='2'>"+data.sys_info[i]+"</td>></tr>");
		 }    	
    }

	grecordId=getRequestParam(window.location.search,'id');  
	 
	ajaxRequest("/api/brquery/record/"+grecordId+"?"+ticketcondition(),
                {},
                function(data){return data.results;},
                renderingDetail
               ); 
}

function InitDefaultValues()
{
    var actserver = $('#btServerName').val();
    var btuser = '';
    var btpswd = '';
    
    $('#btUserName').val('');
    $('#btUserPswd').val(''); 
	$('#btProjectlist').html("");
			
    if( $.cookie('btUserName_'+actserver) !== null && $.cookie('btUserPswd_'+actserver) !== null) {
        btuser = $.cookie('btUserName_'+actserver);
        btpswd = $.cookie('btUserPswd_'+actserver);            
        $('#btUserName').val(btuser);
        $('#btUserPswd').val(btpswd);                	
    }  
    showProjcetItems(actserver,btuser,btpswd);                           	    	                          	
}


function InitProjectlist()
{		
 	var actserver = '';
    var btuser = '';
    var btpswd = '';  	
	$('#btProjectlist').html("");
			
    if( $.cookie('btActiveServerName') === null || $.cookie('btActiveServerName') === '' || $.cookie('btActiveServerName') === 'bqserver') {
       $('#auth_info_bq').show();
       $('#auth_info').html(''); 
       
       if( $.cookie('btMantisServerName') !== null && $.cookie('btMantisServerName') !== '') {
           actserver = $.cookie('btMantisServerName');
           btuser = $.cookie('btUserName_'+actserver);
           btpswd = $.cookie('btUserPswd_'+actserver);          
           $('#btServerName').val(actserver);  
           $('#btUserName').val(btuser);
           $('#btUserPswd').val(btpswd);                	
       }                        	
    } 
    else {	
       $('#auth_info_bq').html('');
       $('#auth_info').show();             	
       $('#btServerName').html($.cookie('btActiveServerName'));            	
 	   actserver = $.cookie('btActiveServerName');
       btuser = $.cookie('btUserName_'+actserver);
       btpswd = $.cookie('btUserPswd_'+actserver); 
    }
    showProjcetItems(actserver,btuser,btpswd);                        	
}  

function GetProjectlist()
{       
 	var actserver = $('#btServerName').val();
    var btuser = $('#btUserName').val();
    var btpswd = $('#btUserPswd').val();
     
    showProjcetItems(actserver,btuser,btpswd);     		       	
}  


function showProjcetItems(actserver,btuser,btpswd)
{
    $('#btProjectlist').html("");  
		
	if(actserver === '' || btuser === '' || btpswd === '') return; 
      
    ajaxRequestEx("/api/brquery/mantis/projects?"+ticketcondition(),
        	       {"server":actserver,
                    "username":btuser,
                    "password":btpswd
                   },
                   function(data) {
                      $.cookie('btMantisServerName',actserver,{expires:999});
                      $.cookie('btUserName_'+actserver,btuser,{expires:999});
                      $.cookie('btUserPswd_'+actserver,btpswd,{expires:999}); 
                      return data.results;
                   },		  		
                   function(data) {			   
                      preHeader = "";	   
                      rescuProjectFormat(data,preHeader);
                   }
                 );   
}

function rescuProjectFormat(data,preHeader) {
	$.each(data,function(i,o) {	   	
	   	$("<option value="+o.id+">"+preHeader+o.name+"</option>").appendTo('#btProjectlist');
	   	if(o.subproj != undefined) {
	   		preHeader = preHeader + " >>";
	   		rescuProjectFormat(o.subproj,preHeader);
	   		preHeader = preHeader.substring(0,preHeader.length - 3);	
	   	}	   	
	}); 			
}


function gotoReportIssue() {

	 if(url_ticket !== "N/A"){
	 	if(!confirm("A ticket reported already,override it with an new one?"))
	 	   return;
	 }
	
	 if($('#btProjectlist').val() !== null &&  $('#btProjectlist').val() !== "") {	 		 		     		 	
         var prjId = $('#btProjectlist').val();
	     var prjName = $('#btProjectlist').find("option:selected").text();
	     while(prjName.indexOf(">>") >= 0)
	         prjName = prjName.substring(prjName.indexOf(">>")+2,prjName.length);
    
	     //cookies caches the data for report issue to mantis		        
	     $.cookie('btProjectId'+grecordId, prjId,{ expires: 1 });				
	     $.cookie('btProjectName'+grecordId, prjName,{ expires: 1 });	    
	     var cjsondata = JSON.stringify(jsondata);	   	    
	     if (cjsondata.length > 3000) //over the storage of cookies
             $.cookie('hugedata'+grecordId,'1',{ expires: 1 });   	  
         else  
             $.cookie('jsondata'+grecordId,cjsondata,{ expires: 1 });

         var url=window.location.protocol+"//"+window.location.host+"/bugquery/reportissue.html?id="+grecordId;
         window.open(url,'_blank');

	 } else alert('Please select a project to report issue!');
  	
}
