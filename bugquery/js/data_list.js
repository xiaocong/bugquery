var listcolums=[
            {field:"_id",width:40, title:"Id"},
            {field:"ticket_url",width:30, title:"Ticket"},             
            {field:"receive_time",width:60, title:"Receive_Time"},
            {field:"type",width:70, title:"Error_Type"},
            {field:"name",width:80, title:"Name"},
            {field:"info",width:80, title:"Description"},
            {field:"phoneNumber",width:90, title:"PhoneNumber"},
            {field:"revision",width:30, title:"Revision"},
            {field:"url_id",width:1, title:""},            
            {command: { text: "Details", className: "details-button" }, title: " ", width:60}
           ];
                     
var gerrorcondition = '';  
var gpagingcondition = '&page=1&records=5000';   
var glistDataBuffer = [];

function createSearchTab(condition){

    gerrorcondition = condition;
    var renderingListtab = function(data) {  	
    	if(data === null){
            alert('Query result is null!');
            return;    		
    	}	    	
	    ++tabcnt; 
	    $tabs.tabs("add","#tabs-"+tabindex,condition,0);         
	    $("#errorlist"+tabindex).kendoGrid({
	        dataSource:{
	                       data: data,
	                       pageSize: 20,
	                       aggregate:{ field: "_id", aggregate: "count" },
	                       sort: {
	                          field: "_id",
	                          dir: "desc"
	                       }
	                   },    
	        sortable: true,
	        pageable: true,
	        resizable: true,	
	        selectable: "row",		
	        columns:listcolums
	    });
	
	    $("#errorlist"+tabindex).delegate(".details-button", "click", function(e) {
	        var tmpStart=0;
	        var recId;
	        var datasours=$(this).closest("tr");
	        $(datasours).find("td").each(function(){
	            if($(this).text().indexOf("#url#") === 0){
	                recId=$(this).text();
	                recId=recId.substr(5,recId.length);
	                return false;
	            }
	        });
	
	        var queryerrorId="id="+recId;
	        var url=window.location.protocol+"//"+window.location.host+"/bugquery/detail.html?"+queryerrorId;
	        window.open(url,'_blank');   
	    }); 
	    $tabs.tabs("select",0); 
	    tabindex += 1;    	
    }

    //invoke ajax request   
    ajaxRequest("/api/brquery/query/error?"+condition+gpagingcondition+"&"+ticketcondition(),
                {},                 
                getErrorList,
                renderingListtab); 
}


var renderingList = function(data) {

     if(data === null){
         alert('Query result is null!');
         return;
     }
     $("#errorlist").empty();
     $("#errorlist").undelegate();
     $("#errorlist").kendoGrid({
            dataSource: {
                             data: data,
                             pageSize: 20,
                             aggregate:{ field: "_id", aggregate: "count" },
                             sort: {
                               field: "_id",
                               dir: "desc"
                             }
                            },
            sortable: true,
            pageable: true,
            resizable: true,
            selectable: "row",
            columns:listcolums
     });

     $("#errorlist").delegate(".details-button", "click", function(e) {
            var tmpStart=0;
            var recId;
            var datasours=$(this).closest("tr");
            $(datasours).find("td").each(function(){
                    if($(this).text().indexOf("#url#") === 0){
                        recId=$(this).text();
                        recId=recId.substr(5,recId.length);
                        return false;
                    }
            });

            var queryerrorId="id="+recId;
            var url=window.location.protocol+"//"+window.location.host+"/bugquery/detail.html?"+queryerrorId;
            window.open(url,'_blank');
     });
}

function createListGrid(){	

    $("#summarylist").empty();  
    gerrorcondition = window.location.search.substring(1);       
    var listv=gerrorcondition.split("&");    
    for(i=0;i<listv.length;i++){
        $("#summarylist").append("<tr><td>"+listv[i]+"</td</tr>");    	
    }
    ajaxRequest("/api/brquery/query/error?" + gerrorcondition + gpagingcondition + "&" + ticketcondition(),
                {},                 
                getErrorList,
                renderingList); 
}
        
function getErrorList(json){
	      
   var data = json.results;	         
   if(data['paging'] === undefined || data['paging'] === null) return null;
   
   var pagingInfo = data['paging'];   
   var errordata = data['data'];  
   var totalrec = pagingInfo['totalrecords'];
   var records = parseInt(pagingInfo['records']);   
   var curpage = parseInt(pagingInfo['page']);
   var totalpage = pagingInfo['totalpages'];

   if(curpage === 1) {
       glistDataBuffer = [];
       for(var k=0;k<totalrec;k++)
   	     glistDataBuffer.push({"_id":"",
   	                          "ticket_url":"",
   	                          "receive_time":"",
   	                          "type":"",
   	                          "name":"",
   	                          "info":"",
   	                          "url_id":"",
   	                          "phoneNumber":"",
   	                          "revision":""
   	                         });
   }
   var startIdx = (curpage-1)*records;
   for (var i=0; i<errordata.length; i++){
        var datarow = errordata[i];
        glistDataBuffer[startIdx+i]["_id"] = datarow["_id"];
        glistDataBuffer[startIdx+i]["ticket_url"] = (datarow["ticket_url"]===undefined)?'-':'Y';
        glistDataBuffer[startIdx+i]["receive_time"] = datarow["receive_time"];
        glistDataBuffer[startIdx+i]["type"] = datarow["type"];
        glistDataBuffer[startIdx+i]["name"] = datarow["name"];               
        glistDataBuffer[startIdx+i]["info"] = datarow["info"];                
        glistDataBuffer[startIdx+i]["url_id"] = "#url#" + datarow["_id"];
        glistDataBuffer[startIdx+i]["phoneNumber"] = datarow["sys_info"]["phoneNumber"]
        glistDataBuffer[startIdx+i]["revision"] = datarow["sys_info"]["ro:build:revision"]
   }

   if(curpage < totalpage) {
        var pageno = curpage + 1;
        gpagingcondition = '&page=' + pageno.toString() +'&records=5000';
        ajaxRequest("/api/brquery/query/error?" + gerrorcondition + gpagingcondition+"&"+ticketcondition(),
                    {},
                    getErrorList,
                    renderingList); 
   }

   return glistDataBuffer; 	
}


function exportExcel(){
	
    $("#export").click(function(){
        //window.open(window.location.protocol+"//"+window.location.host+"/api/brquery/query/error/download?"+gerrorcondition+"&"+ticketcondition());      
    })  
}
