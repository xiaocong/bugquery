var 
    record_id='',
    ticketServer='',
    ticketPrjName='',
    ticketPrjId='',
    ticketUsrName='',
    ticketUsrPswd='';

var KEYINFO=["android.os.Build.TYPE","ro.build.revision","android.os.Build.HARDWARE","android.os.Build.FINGERPRINT"];


function initFormData(){	
    var funcOptions = function(optiondata) {   	
	       if(optiondata !== undefined && optiondata !== null){ 
			   $.each(optiondata.category,
			   	      function(i,o){
			   	         $("<option value="+o+">"+o+"</option>").appendTo('#category');
			   });	   
			   
			   $.each(optiondata.reproducibility,
			   	      function(i,o){
			   	         $("<option value="+o.id+">"+o.name+"</option>").appendTo('#reproducibility');	   	         
			   });	   			  
			   $('#reproducibility').get(0).selectedIndex = 2;
			   
			   $.each(optiondata.severity,
			   	      function(i,o){
			   	         $("<option value="+o.id+">"+o.name+"</option>").appendTo('#severity');	   	         
			   });
			   $('#severity').get(0).selectedIndex = 2;
			   
			   $.each(optiondata.priority,
			   	      function(i,o){
			   	         $("<option value="+o.id+">"+o.name+"</option>").appendTo('#priority');	   	         
			   });	 
		       $('#priority').get(0).selectedIndex = 4;
			   
			   $.each(optiondata.customfield,
			   	      function(i,o){
			   	      	  var cid=o.id;
			   	      	  var cname=o.name;
			   	      	  var coptions=o.values.split('|');
			   	      	  $('#custom_field_' + cid).attr('name', cname);
			   	      	  for(var t=0;t<coptions.length;t++) {
			   	      	      $("<option value=\""+coptions[t]+"\">"+coptions[t]+"</option>").appendTo('#custom_field_' + cid);	   	      		
			   	      	  }		      	   	         
			   });		      	   	   	  	    	   	   	   
		}   	    	
    };
    
    var funcDesription = function(datadetail) {
	    var vsum = "[BugReporter]" + datadetail.type + ": " + datadetail.name;     
	    var vdetail="",vsysinfo="",vdesp=""; 
	    var reg=/(:)/g;          
	    vdetail="[Error Detail]\r\n";
	    vsysinfo="[Device Information]\r\n";
	    vdetail=vdetail
	            +"ID:"+ datadetail._id+"\r\n"
	            +"Type:"+ datadetail.type+"\r\n"
	            +"Name:"+ datadetail.name+"\r\n"
	            +"Occur Time:"+ datadetail.occur_time+"\r\n"
	            +"Description:"+ datadetail.info+"\r\n"
	            +" \r\n";
	   
		for(o in datadetail.sys_info){
			oo=o.replace(reg,'.');
			if (KEYINFO.indexOf(oo)>=0)
			   vdetail=vdetail+oo+":"+datadetail.sys_info[o]+"\r\n";		   
			else
			   vsysinfo=vsysinfo+oo+":"+datadetail.sys_info[o]+"\r\n";
		} 
		vdetail=vdetail+"\r\n"
		        +"Log:http://"+window.location.host+"/api/brquery/record/"+datadetail._id+"/log\r\n";
		
		vdesp = vdetail
		        +"\r\n=============================================================================\r\n"
		        +vsysinfo;
		   
		$('#summary').val(vsum);         
	    $('#description').val(vdesp);    	
    }
    
	//get record id from query string
    record_id=getRequestParam(window.location.search,'id'); 
    //restore data from cookies
    ticketServer=$.cookie('btMantisServerName');
    ticketUsrName=$.cookie('btUserName_'+ticketServer);
    ticketUsrPswd=$.cookie('btUserPswd_'+ticketServer);       
    ticketPrjName=$.cookie('btProjectName'+record_id);
    ticketPrjId=$.cookie('btProjectId'+record_id); 
    //clear the cookies			        
	$.cookie('btProjectId'+record_id, '',{ expires:-1 });				
	$.cookie('btProjectName'+record_id, '',{ expires: -1 });            
    //servername : project name
    $('#server_proj').html(ticketServer+ '->' + ticketPrjName);
               
    ajaxRequestEx("/api/brquery/mantis/options",    
                  {'server':ticketServer,
                    'project':{'id':ticketPrjId,'name':ticketPrjName},
                    'username':ticketUsrName,
                    'password':ticketUsrPswd,
                    'token':$.cookie('bqticket')
                  },         
                  function(data){ return data.results},
                  funcOptions
                 );
 
    //Request the data from server when the data size over cookie storage
    if($.cookie('hugedata'+record_id) !== null){
        ajaxRequest("/api/brquery/record/"+record_id+"?"+ticketcondition(),
                     {},
                     function(data){ return data.results;},
                     funcDesription
                    );
    	$.cookie('hugedata'+record_id,'',{ expires: -1 });         	
    } 
    //Read from cookie storage
    else if ($.cookie('jsondata'+record_id) !== null) {
    	var cjsondata = $.cookie('jsondata'+record_id);
    	var datadetail = eval('('+cjsondata +')');
    	funcDesription(datadetail); 
    	$.cookie('jsondata'+record_id,'',{ expires: -1 });   
	}
	    
}

function reportIssue() {	

    var userdata = {
    	            "record_id":record_id,
    	            "token":$.cookie('bqticket'),
                    'server':ticketServer,
                    'project':{'id':ticketPrjId,'name':ticketPrjName},
                    'username':ticketUsrName,
                    'password':ticketUsrPswd,
                    "category":$('#category').val(),
                    "reproducibility":{"id":$('#reproducibility').val(),"name":$('#reproducibility').find("option:selected").text()},
                    "severity":{"id":$('#severity').val(),"name":$('#severity').find("option:selected").text()},
                    "priority":{"id":$('#priority').val(),"name":$('#priority').find("option:selected").text()},
                    "summary":$('#summary').val(),
                    "description":$('#description').val(),
                    "customfield":[{"id": 1, "name": $('#custom_field_1').attr('name'),"value":$('#custom_field_1').val()},
                                   {"id": 2, "name": $('#custom_field_2').attr('name'),"value":$('#custom_field_2').val()},
                                   {"id": 4, "name": $('#custom_field_4').attr('name'),"value":$('#custom_field_4').val()}]
                    };
                     
    ajaxRequestEx("/api/brquery/mantis/submit",             
                  userdata,
                  function(data){ return data.results},
                  function(data){ 	
                  	 if(data !== undefined && data !== null) 
	                     window.location = data.url;
                  }
                 );	
}