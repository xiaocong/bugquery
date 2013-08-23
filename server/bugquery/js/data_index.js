var 
    platfcondition = "",
    productcondition = "",
    timecondition="",
    timeconditions="",
    timeconditiona="",    
    ggroupname="",
    grates=[],
    glinkbuffer=[],
    glinkprdbuffer=[],
    tabcnt = 0,
    tabindex = 0,
    ratecondition = "",
    summarycondition = "",
    livecondition = "";
    
var groups =[
           {text: "ro.build.revision", value:"ro.build.revision"},
           {text: "android.os.Build.FINGERPRINT", value:"android.os.Build.FINGERPRINT"},
           {text: "android.os.Build.TYPE", value:"android.os.Build.TYPE"},
           {text: "deviceId", value:"deviceId"},
           {text: "gsm.version.baseband", value:"gsm.version.baseband"},
           {text: "kernelVersion", value:"kernelVersion"},
           {text: "phoneNumber", value:"phoneNumber"}
          ];
                                                              
    
var colums=[
            {field: "g_value",width:180,title:"GroupValue"}, 
            {field: "e_count",width: 90,title: "Error_Count"},
            {field: "livetime",width: 90,title: "Live_Time(Hour)"},
            {field: "error_rate",width: 90,title: "Error_Rate(%)"},
            {field: "link",width: 1,title: ""},        // record key query string    
            {command: { text: "List", className: "details-button" }, title: "", width:90}
           ];
           
var columsdrop=[
            {field: "g_value",width:180,title:"GroupValue"}, 
            {field: "e_count",width: 90,title: "Drop_Count"},
            {field: "livetime",width: 90,title: "Call_Count"},
            {field: "error_rate",width: 90,title: "Drop_Rate(%)"},
            {field: "link",width: 1,title: ""},        // record key query string    
            {command: { text: "List", className: "details-button" }, title: "", width:90}
           ];           
           

var detailcolums=[
                  {field: "e_type",width: 90,title:"Error_Type"}, 
                  {field: "e_count",width: 90,title: "Error_Count"},
                  {field: "livetime",width: 90,title: "Live_Time(Hour)"},
                  {field: "error_rate",width: 90,title: "Error_Rate(%)"},
                  {field: "link",width: 1,title: ""},    //   record key query string             
                  {command: { text: "List", className: "subdetails-button" }, title: "", width:90}
                 ];
                  
                  
var livecolums=[ 
                 {field: "name",width: 90,title: "Month",footerTemplate: "Total Count: #=count#"},                 
                 {field: "error",width: 90,title: "Error_Count"},
                 {field: "live",width: 90,title: "Live_Time(circles)"},                 
                 {field: "link",width: 1,title: ""}
               ];                  
                  
                  
var livecolumdetails=[
                  {field: "name",width: 90,title: "Day",footerTemplate: "Total Count: #=count#"},
                  {field: "error",width: 90,title: "Error_Count"},                  
                  {field: "live",width: 90,title: "Live_Time(circles)"},
                  {field: "link",width: 1,title: ""},           
                  {command: { text: "Details", className: "links-button" }, title: "", width:90}
                  ];  
                  
var livecolumsummary=[
                  {field: "product",width: 90,title: "Product"},
                  {field: "count",width: 90,title: "Error_Count"},                  
                  {field: "base",width: 90,title: "Live_Time"},                  
                  {field: "rate",width: 90,title: "Error_Rate"},                  
                  {field: "link",width: 1,title: "",visible:false},             
                  {command: { text: "More...", className: "details-button" }, title: "", width:90}
                  ];  
                  
                                    
var livecolumrevision=[
                  {field: "revision",width: 90,title: "Revision"},
                  {field: "count",width: 90,title: "Error_Count"},                  
                  {field: "base",width: 90,title: "Live_Time"},                  
                  {field: "rate",width: 90,title: "Error_Rate"},                  
                  {field: "link",width: 1,title: "",visible:false},           
                  {command: { text: "List", className: "subdetails-button" }, title: "", width:90}
                  ];  
                  
var livecolumsummarydrop=[
                  {field: "product",width: 90,title: "Product"},
                  {field: "count",width: 90,title: "Drop_Count"},                  
                  {field: "base",width: 90,title: "Call_Count"},                  
                  {field: "rate",width: 90,title: "Drop_Rate"},                  
                  {field: "link",width: 1,title: "",visible:false},             
                  {command: { text: "More...", className: "details-button" }, title: "", width:90}
                  ];  
                  
                                    
var livecolumrevisiondrop=[
                  {field: "revision",width: 90,title: "Revision"},
                  {field: "count",width: 90,title: "Drop_Count"},                  
                  {field: "base",width: 90,title: "Call_Count"},                  
                  {field: "rate",width: 90,title: "Drop_Rate"},                  
                  {field: "link",width: 1,title: "",visible:false},           
                  {command: { text: "List", className: "subdetails-button" }, title: "", width:90}
                  ];                   
                    
//clone object variable
function clone(obj){
    if(obj == null || typeof(obj) != 'object'){
        return obj;
    }

    var temp = new obj.constructor();
    for(var key in obj){
        temp[key] = clone(obj[key]);
    }
    return temp;
}

function getKeys(data) {
    var keys =[];
    var tmpdata = data.results;
    for(var k=0;k<tmpdata.length;k++){
         keys.push({text:tmpdata[k],value:tmpdata[k]});
    } 
    return keys;
}


function getPlatforms(data){
    var plts = [];
    var datav = data.results;
    for(var i=datav.length-1; i>=0; i--)
       plts.push({text:datav[i],value:datav[i]});

    plts.sort(function(a,b){ return a.value < b.value })

    return plts;
}

function getETypes(data){
    var apps =[];
    var tmpdata = data.results;
    for(var i=0;i<tmpdata.length;i++) {
       apps.push({'text':tmpdata[i],'value':tmpdata[i]});
    }
    return apps;
}


function createSearchApplication(){
    
    var funcApps = function(data) {
	    $("#application").kendoAutoComplete({
	        dataSource: data,
	        filter: "startswith",
	        placeholder: "Input apps...",
	    });    	
    }

    ajaxRequest("/api/brquery/query/apps?"+ticketcondition(),
                {},
                function(data) {return data.results},
                funcApps
              );

}

function createTimeFilter(){            

    $('#start, #end').daterangepicker();
    $('#starts, #ends').daterangepicker();    
    $('#starta, #enda').daterangepicker();
        
    $('#start').val(new Date().toLocaleDateString());  
    $('#end').val(new Date().toLocaleDateString()); 
    $('#starts').val(new Date().toLocaleDateString());     
    $('#ends').val(new Date().toLocaleDateString());     
    $('#starta').val(new Date().toLocaleDateString()); 
    $('#enda').val(new Date().toLocaleDateString()); 
                 
    /*$("#datevalue").kendoDatePicker({
        value: new Date(2012, 0, 1),
        start: "decade",
        depth: "decade",
    });*/    
    
}

/*
 * Get Time filter condition
 */ 
function getTimeCondition() {
    var startTime=Date.parse($("#start").val() + ' 00:00:00 ')/1000;          
    var endTime=Date.parse($("#end").val() + ' 23:59:59 ')/1000;    
    timecondition="&starttime="+startTime+"&endtime="+endTime; 
}  

/*
 * Get platform condition
 */ 
function getPlatformCondition(){  	
	
	var platlist = $("#platlist").data("kendoDropDownList"); 
	if(platlist !== undefined) {
	    var pltValue = platlist.value();
        platfcondition = "&platform=" + pltValue;		
	} else platfcondition = "&platform=4.0.4"; 
 
}  

/*
 * Get simple search production condition.
 */
function getProductCondition(){  	
	var prodlist = $("#prodlists").data("kendoDropDownList"); 
	var prdValue = prodlist.value();
	var posi = prdValue.indexOf('/');	
	var bOk = false;	 
    if(posi > 0) {
	   bOk = true;    
       productcondition= "&android.os.Build.VERSION.RELEASE=" 
                         + prdValue.substring(0,posi)
                         +"&android.os.Build.PRODUCT="
                         + prdValue.substring(posi+1,prdValue.length);    	
    } else alert('Please select a ProductName first!');
      
	return bOk;
}  
/*
 * Get advanced search production condition.
 */
function getProductConditionEx(){  	
	var prodlist = $("#prodlista").data("kendoDropDownList"); 
	var prdValue = prodlist.value();
    var posi = prdValue.indexOf('/');  
 	var bOk = false;  
    if(posi > 0) {
 	   bOk = true;
       productcondition= "&android.os.Build.VERSION.RELEASE="
                         +prdValue.substring(0,posi)
                         +"&android.os.Build.PRODUCT="
                         +prdValue.substring(posi+1,prdValue.length);     	
    }  else alert('Please select a ProductName first!');
        
    return bOk;
}  

function getTimeConditionA(){  	
	timeconditiona="";	
	if($('#chka').attr('checked')) {	
        var startTime=Date.parse($("#starta").val() + ' 00:00:00 ')/1000;          
        var endTime=Date.parse($("#enda").val() + ' 23:59:59 ')/1000;    
        timeconditiona="&starttime="+startTime+"&endtime="+endTime; 
    }
} 


function getTimeConditionS(){  	
	timeconditions="";
	if($('#chks').attr('checked')) {
        var startTime=Date.parse($("#starts").val() + ' 00:00:00 ')/1000;          
        var endTime=Date.parse($("#ends").val() + ' 23:59:59 ')/1000;    
        timeconditions="&starttime="+startTime+"&endtime="+endTime;		
	}
} 

function getAccountbyGroup(data){	
    var dataRes = data.results;
    grates = clone(dataRes);
    for (var i = 1; i < dataRes.length; i++) {
        for (var j = dataRes.length - 1; j >= i; j--) {
            if (dataRes[j]["g_value"] > dataRes[j-1]["g_value"]) {
                temp = dataRes[j - 1];
                dataRes[j - 1] = dataRes[j];
                dataRes[j] = temp;
            }
        }
    } 

    var dataOut=[];
    var tmpFlag=-1;
    for(var i=0;i<dataRes.length;i++){
        var tmpData=dataRes[i];
        for(var j=0;j<dataOut.length;j++){
            if(dataOut[j].g_value == tmpData.g_value){
                tmpFlag=j;
                break;
            }
        }
        if(tmpFlag < 0){
        	tmpData["e_type"]="";
            dataOut.push(tmpData);
        } else {
            dataOut[tmpFlag].e_count += tmpData.e_count;
        }
        tmpFlag=-1;
    }
    return dataOut; 
}
       
function getRateData(datatmp){
    var newData = [];
    var linkAct = "";
    for (var i=0; i<datatmp.length; i++){
        var row=datatmp[i];
        row["livetime"]=(row["livetime"]/1).toFixed(2);
        var rate=(row["e_count"]/row["livetime"]*100).toFixed(2);
        row["error_rate"]=rate;
        linkAct = ggroupname + "=" + row["g_value"];
        if(row["e_type"] !== "") {
           linkAct = linkAct + "&e_type="+ row["e_type"];        	
        }   
        row["link"] = '#url#' + glinkprdbuffer.push(linkAct); 
        
        newData.push(row);
    }
    return newData;
}

/*
 * Simple condition Query - UserID - Phone Number 
 */
function goToPhoneNumberSearch(){
	
	if(!getProductCondition()) return;
	
	getTimeConditionS();	
    var id=$("#phonenumber").val();
    if(id==''){
        alert("please input PhoneNumber for query first!");
    } else {
        var querycondition = "phoneNumber="+id+productcondition+timeconditions;
        createSearchTab(querycondition);
    }
}
/*
 * Simple condition Query - IMEI 
 */
function goToPhoneIMEISearch(){
	
	if(!getProductCondition()) return;
	
	getTimeConditionS();	
    var id=$("#imsinumber").val();
    if(id==''){
        alert("please input IMEI number for query first!");
    } else {
        var querycondition = "deviceId="+id+productcondition+timeconditions;
        createSearchTab(querycondition);
    }
}
/*
 * Simple condition Query - ErrorType
 */
function goToErrorTypeSearch(){
	
	if(!getProductCondition()) return;
	
	getTimeConditionS();	
	
	var elist = $("#etypelist").data("kendoDropDownList"); 
    var id=elist.value();
    
    if(id==''){
        alert("please input ErrorType for query first!");
    } else {
        var querycondition = "e_type="+id+productcondition+timeconditions;
        createSearchTab(querycondition);
    }
}

/*
 * Simple condition Query - App Name
 */
function goToApplicationSearch(){
	
	if(!getProductCondition()) return;
	
	getTimeConditionS();	
	
    var application=$("#application").val();
    if(application==''){
        alert("please input application for query first!");
    } else {     
        var querycondition = "name="+application+productcondition+timeconditions;    
        createSearchTab(querycondition);        
    }
}

/*
 * Combo condition Queries - ErrorType / Product Property
 */
function goToComboSearch(){
	
	if(!getProductConditionEx()) return;
	
	getTimeConditionA();
	
    var combostrings="";
    $('#cond_list').children('.comboitem').each(function(){
    	var itemtype = $(this).children(".combotype");
    	var itemname = itemtype.next();
    	var itemvalue = itemtype.next().next();
    	if(itemtype.val() === 'eType') {     	//error Type
    		if(itemname.val() !== undefined && itemname.val() !== '') 
               combostrings += "&e_type=" + itemname.val();            	
    	} else {     	                        //product property
            if(itemvalue.val() !== undefined && itemvalue.val() !== '')  
               combostrings += "&" + itemname.val() + "=" + itemvalue.val();        	
        }                     	
    })


    if(combostrings === "") {
    	alert('At least one condition for advanced query required!')
    	return;
    }
    var querycondition = combostrings+productcondition+timeconditiona;  
    querycondition = querycondition.substring(1,querycondition.length)   
    createSearchTab(querycondition);        
}

function createPlatfDropdown() {	
       
    var renderingPlatform = function(data){
	    $("#platlist").undelegate();	
	    $("#platlist").empty();	          	                  	        	         	              
	    $("#platlist").kendoDropDownList({
	                        dataTextField: "text",
	                        dataValueField: "value",
	                        dataSource: data,
	                        change:function(e) {
	                        	createSummaryGrid();
	                        }
	                   });   
	    var prodlist = $("#platlist").data("kendoDropDownList");
	    if(prodlist !== undefined) prodlist.select(0);
    }
     
  var prodlist = $("#platlist").data("kendoDropDownList"); 	    
	if(prodlist === null || prodlist === undefined) {  
        ajaxRequest("/api/brquery/query/platforms?"+ticketcondition(),
                    {},
                    getPlatforms,
                    function(data) {
                    	renderingPlatform(data);
                    	createSummaryGrid();
                    }
                   );  
  } else createSummaryGrid();  
}

function createGroupDropdown() {

    $("#grouplist").undelegate();
    $("#grouplist").empty();
    var prodlist = $("#grouplist").data("kendoDropDownList");
    if(prodlist === null || prodlist === undefined) {     	                  	        	         	              
        $("#grouplist").kendoDropDownList({
                        dataTextField: "text",
                        dataValueField: "value",
                        dataSource: groups,
                        change:function(e) {
                        	createErrorRateGrid();
                        }                        
        });
    } else prodlist.select(0);
}

function createEtypeDropdown() {
			
    var createEDrop = function(data) {
    	var prodlist = $("#etypelist").data("kendoDropDownList");  
        if(prodlist === null || prodlist === undefined) {  
    	    $("#etypelist").undelegate();	
            $("#etypelist").empty();             	                  	        	         	              
            $("#etypelist").kendoDropDownList({
                        dataTextField: "text",
                        dataValueField: "value",
                        dataSource: data,                  
            });
            
        } else prodlist.select(0); 
    }
    ajaxRequest("/api/brquery/query/keys?"+ticketcondition(),
                {},
                getKeys,
                function(data){
                    propertyList=data;
                }
               );
              
    ajaxRequest("/api/brquery/query/error_types?"+ticketcondition(),
                {},
                getETypes,
                function(data){
                    errorTypeList=data;
                	createEDrop(data);
                }
               );                       
}

function getProducts(data){	
    var retdata = data.results;
    var products = [];                     
    var keys = []; 
                         
    if(retdata !== null && retdata !== undefined) {
         for(var t in retdata)
             keys.push(t);    
         keys.sort(function(a, b){ return a < b ? 1 : a > b ? -1 : 0;});                         	
    } 
                                                          
    for(var d=0;d<keys.length;d++){     
         k=keys[d];                   
         products.push({text:'======'+k+'======',value:k});
         for(var i=0;i<retdata[k].length;i++){
             products.push({text:retdata[k][i],value:k+'/'+retdata[k][i]});
         }
    }                        
    return products;
}

function createProductDropdown(){    
       
    //rendering                
    var funProduct = function(data) {  	
    	$("#prodlists").undelegate();	
        $("#prodlists").empty();	                
        var prodlist = $("#prodlists").data("kendoDropDownList"); 
        if(prodlist === null || prodlist === undefined) {
             $("#prodlists").kendoDropDownList({
                   dataTextField: "text",
                   dataValueField: "value",
                   index:0,
                   dataSource: data
                 });    	
        }
  
        $("#prodlista").undelegate();	
        $("#prodlista").empty();	
                       
        var prodlist = $("#prodlista").data("kendoDropDownList"); 
        if(prodlist === null || prodlist === undefined) {
             $("#prodlista").kendoDropDownList({
                   dataTextField: "text",
                   dataValueField: "value",
                   index:0,
                   dataSource: data
                 });    	
          }              
      };
      
      //ajax request  
      ajaxRequest("/api/brquery/query/products?"+ticketcondition(),
                {},
                getProducts,
                funProduct
              );                              
}

function createSummaryGrid(){
  
	$("#summarygrid").undelegate();	
	$("#summarygrid").empty();	  
       
    var renderingSummary = function(data) {		
	    $("#summarygrid").kendoGrid({
	         dataSource: {
	                data: data,
	                schema: {
	                        model: {
	                                    fields: {
	                                        product: { type: "string" },
	                                        count: { type: "number" },                                        
	                                        base: { type: "number" },
	                                        rate: { type: "string" },
	                                        link: { type: "string" }                                        
	                                    }
	                         }
	                }              
	        },
	        detailInit: detailInit,	              
	        sortable: true,	
	        //scrollable: false,
                selectable: "row",	
	        columns:cols
	    });
	    
	    $("#summarygrid").delegate(".details-button", "click", function(e) {
	        var dataselect=$(this).closest("tr");
	        var errorcondition = "";     
	        $(dataselect).find("td").each(function(){       	
	            if($(this).text().indexOf("#url#") === 0 ){
	            	var tmpurl = $(this).text();
	            	tmpurl = tmpurl.substring(5,tmpurl.length);            	           	
	                errorcondition=glinkbuffer[Number(tmpurl)-1];
	                var idx=errorcondition.indexOf("rate?");                
	                errorcondition=errorcondition.substr(idx+5,errorcondition.length);                
	                return false;
	            }
	        }); 
	        ratecondition = errorcondition;
	        timecondition = "";              
	        showProductRates();          
	    });  
	       
	    $("#summarygrid").delegate(".subdetails-button", "click", function(e) {
	        var dataselect=$(this).closest("tr");
	        var errorcondition = "";        
	        $(dataselect).find("td").each(function(){       	
	            if($(this).text().indexOf("#url#") === 0 ){
	            	var tmpurl = $(this).text();
	            	tmpurl = tmpurl.substring(5,tmpurl.length);            	           	
	                errorcondition=glinkbuffer[Number(tmpurl)-1];
	                var idx=errorcondition.indexOf("error?");
	                errorcondition=errorcondition.substr(idx+6,errorcondition.length);                
	                return false;
	            }
	        }); 
	 
	        var url=window.location.protocol+"//"+window.location.host+"/bugquery/list.html?"+errorcondition;
	        window.open(url,'_blank');      
	    });      
	 
	    function detailInit(e) {    	      	  
	        $("<div/>").appendTo(e.detailCell).kendoGrid({
	            dataSource: {
	                data: e.data.sublist,
	                pageSize:20,
	                schema: {
	                        model: {
	                                    fields: {
	                                        revision: { type: "string" },
	                                        base: { type: "number" },
	                                        count: { type: "number" },
	                                        rate: { type: "string" },
	                                        link: { type: "string" }                                      
	                                    }
	                         }
	                }, 
	                sort: {
	                     field: "revision",
	                     dir: "desc"
	                }              
	            },             
	            sortable: true,
	            resizable: true,
	            selectable: "row",
	            columns: subcols
	        });
	    }      	
    };
        	   	
	var cols,subcols;     
	if($('#radioerror').attr('checked')) {
	       summarycondition='mode=error';
	       cols=livecolumsummary;
	       subcols=livecolumrevision;    	
	}
	else if($('#radiodrop').attr('checked')){
	       summarycondition='mode=drop'; 
	       cols=livecolumsummarydrop;
	       subcols=livecolumrevisiondrop;             	
	}  
	getPlatformCondition();
	summarycondition += platfcondition;       
       $('#lnkplatform').html($("#platlist").val());

    //ajax request  
    ajaxRequest("/api/brquery/product_summary?" + summarycondition + "&"+ ticketcondition(),
                {},
                getProductSummaryData,
                renderingSummary
               );            
  
}

function getProductSummaryData(data){
    var livedata = data.results;
    
    glinkbuffer = [];
    if(livedata !== null && livedata !== undefined) {
          for(var i=0;i<livedata.length;i++) {
               var tmprow=livedata[i]['link'];
               livedata[i]['link'] =  '#url#' + glinkbuffer.push(tmprow); 
               var subdata = livedata[i]['sublist'];
               for(var k=0;k<subdata.length;k++){
                   var subrow=subdata[k]['link'];
                   subdata[k]['link'] = '#url#' + glinkbuffer.push(subrow);                      		
               }
          }
     }
     return livedata;	
}

function gotoErrorFilter(){
	getTimeCondition();  		   
    createErrorRateGrid();   
}   

function gotoAllFilter(){
	timecondition = "";		   
    createErrorRateGrid();   
}   

    
function createErrorRateGrid() {  
	     
    $("#errorsgrid").undelegate();	
	$("#errorsgrid").empty();  
    var prodlist = $("#grouplist").data("kendoDropDownList"); 
    
    ratecondition = ratecondition.replace(/(&mode=error)/g,'')
                                 .replace(/(&mode=drop)/g,'')
                                 .replace(/(groupby=)/g,'v=');
                                                                  
    ratecondition += '&groupby='+prodlist.value();      
    ggroupname = prodlist.value();                           
    
    //for error rate results
    if($('#radioerror').attr('checked'))
       ratecondition +='&mode=error';      	
    else if($('#radiodrop').attr('checked'))
       ratecondition +='&mode=drop'; 
 		
	var renderingerrorRate = function(data) {    
	    var cols,subcols;
        var tmpInit;
        var dropextra="";    
	    
	    //for error rate results
	    if($('#radioerror').attr('checked')) {   
	       tmpInit=detailInit;       
	       cols=colums;
	       subcols=detailcolums;    	
	    }
	    //for drop rate results
	    else if($('#radiodrop').attr('checked')){ 
	       tmpInit=null;       
	       cols=columsdrop;
	       subcols=detailcolums; 
	       dropextra="&e_type=CALL_DROP";                   	
	    } 	    
	     
	    $("#errorsgrid").kendoGrid({
	        dataSource: {
	            data: data,
	            pageSize:20,
	            schema: {
	                        model: {
	                                    fields: {
	                                        g_value: { type: "string" },
	                                        e_count: { type: "number" },
	                                        livetime: { type: "number" },
	                                        error_rate: { type: "number" },
	                                        link: { type: "string" }
	                                    }
	                         }
	                    },            
	            aggregate:{ field: "g_value", aggregate: "count" }
	        },
	        filterable: true,              
	        sortable: true,
	        pageable: true,	
	        resizable: true,     
	        selectable: "row",
	        detailInit: tmpInit,		
	        columns:cols
	    }).data("kendoGrid");
	    
	    $("#errorsgrid").delegate(".details-button", "click", function(e) {
	        var datasours=$(this).closest("tr");
	        var errorcondition="";     
	        $(datasours).find("td").each(function(){
	            if($(this).text().indexOf("#url#") === 0 ){
	            	var tmpurl = $(this).text();
	            	tmpurl = tmpurl.substring(5,tmpurl.length);            	           	
	                errorcondition=glinkprdbuffer[Number(tmpurl)-1];               
	                return false;
	            }	        
	        });
	        var url=window.location.protocol+"//"+window.location.host+"/bugquery/list.html?"+errorcondition+productcondition+timecondition+dropextra;
	        window.open(url,'_blank');        
	    });
	    $("#errorsgrid").delegate(".subdetails-button", "click", function(e) {
	        var dataselect=$(this).closest("tr");
	        var errorcondition = "";        
	        $(dataselect).find("td").each(function(){       	
	            if($(this).text().indexOf("#url#") === 0 ){
	            	var tmpurl = $(this).text();
	            	tmpurl = tmpurl.substring(5,tmpurl.length);            	           	
	                errorcondition=glinkprdbuffer[Number(tmpurl)-1];                
	                return false;
	            }
	        }); 	 
	        var url=window.location.protocol+"//"+window.location.host+"/bugquery/list.html?"+errorcondition+productcondition+timecondition;
	        window.open(url,'_blank');      
	    });
	         
	    function detailInit(e) {
	        $("<div/>").appendTo(e.detailCell).kendoGrid({
	            dataSource: {
	                data: getRateData(grates),
	                filter: { field: "g_value", operator: "eq", value: e.data.g_value }
	                //pageSize:20
	            },  
	            sortable: true,
	            //pageable: true,
	            resizable: true,	            
	            selectable: "row",
	            columns: subcols
	        });
	    }		
	}
  
    ajaxRequest("/api/brquery/query/rate?"+ ratecondition + timecondition +"&"+ticketcondition(),
                {},
                function(data){ 
                	glinkprdbuffer = [];
                    return getRateData(getAccountbyGroup(data)) 
                },
                renderingerrorRate
              );
}



function getLiveData(data){
    var livedata = [];
    var tmpdata = data.results;
    for (var key in tmpdata) {
        var row = tmpdata[key];
        row['name'] = key;
        livedata.push(row);
    };
    return livedata;	
}


function goToLivetimebyUser(){
    
    $("#livegrid").undelegate();	
    $("#livegrid").empty();
    $("#livechart").undelegate();	
    $("#livechart").empty();
      
    var phonevalue=$('#phoneuser').val();   
    if(phonevalue == '') {
    	alert("please input PhoneNumber before!");
    	return;
    }
    
    if($('#radphonenumber').attr('checked'))
        livecondition = 'phonenumber=' + phonevalue;    	
    else if($('#radimsi').attr('checked')) 
        livecondition = 'imsi=' + phonevalue;           
 
    var renderingLiveUser =  function(data) {
    	  
    	if(data.length === 0) return;  

    	var txtTitle = "";   
        if($('#radphonenumber').attr('checked')) 
            txtTitle = "Trends of PhoneNumber:" + phonevalue;
        else if($('#radimsi').attr('checked')) 
            txtTitle = "Trends of IMSI:" + phonevalue;
              
	    var sharedDatasource = new kendo.data.DataSource({
	            data: data,
	            pageSize:31,
	            schema: {
	                        model: {
	                                    fields: {
	                                        name: { type: "number" },
	                                        live: { type: "number" },
	                                        error: { type: "number" },
	                                        link: { type: "string" }
	                                    }
	                         }
	                    }, 
	            sort: {
	                     field: "name",
	                     dir: "asc"
	            },           
	            aggregate:{ field: "name", aggregate: "count" }
	     });
	                
	    $("#livechart").kendoChart({
	                        theme: $(document).data("kendoSkin") || "default",
	                        dataSource: sharedDatasource,
	                        autoBind: false,
	                        legend: {
	                            position: "top"
	                        },
	                        title: {
	                            text: txtTitle
	                        },                          
	                        series: [
	                           {
	                            type: "line",
	                            name: "error",                             
	                            field: "error"
	                           },
	                           {
	                            type: "line",
	                            name: "livetime",                             
	                            field: "live"
	                           }
	                        ],
	                        axisDefaults: {
	                            labels: {
	                                font: "11px Tahoma, sans-serif"
	                            }
	                        },
	                        valueAxis: {
	                            labels: {
	                                format: "{0:N0}"
	                            }
	                        },
	                        categoryAxis: {
	                            field: "name",
                              labels: {  
                                rotation: -45 
                              } 
	                        },
	                        tooltip: {
	                            visible: true,
	                            format: "{0:N0}"
	                        }
	                    });       
	    
	    
	    
	    $("#livegrid").kendoGrid({
	        dataSource: sharedDatasource,              
	        filterable: true,         
	        sortable: true,
	        pageable: true,	
	        selectable: "row",	
	        columns:livecolumdetails
	    }).data("kendoGrid");
	    
	    $("#livegrid").delegate(".links-button", "click", function(e) {
	        var dataselect=$(this).closest("tr");
	        var errorcondition = "";        
	        $(dataselect).find("td").each(function(){       	
	            if($(this).text().indexOf("errors?") === 0 ){
	                errorcondition=$(this).text();
	                errorcondition=errorcondition.substr(7,errorcondition.length);                
	                return false;
	            }
	        }); 
	        var url=window.location.protocol+"//"+window.location.host+"/bugquery/list.html?"+errorcondition;
	        window.open(url,'_blank');      
	    });                            
    }
    
    ajaxRequest("/api/brquery/summary?" + livecondition,
                {},
                getLiveData,      
                renderingLiveUser
               );             
}

function goToLivetimebyDate(){
	
    $("#livegrid").undelegate();	
    $("#livegrid").empty();
    $("#livechart").undelegate();	
    $("#livechart").empty();
            
    var datev = $("#datevalue").data("kendoDatePicker").value();    
    var arrMonth = ['01','02','03','04','05','06','07','08','09','10','11','12'];    

    if($('#radyear').attr('checked'))
    	livecondition = 'year=' + datev.getFullYear(); 
    else if($('#radmonth').attr('checked')) 
        livecondition = 'month=' + datev.getFullYear()+arrMonth[datev.getMonth()];	
 

    var renderingLiveDate = function(data) {
    	  
        var txtTitle = "";
        var txtUnit = "";    
        var tmpcolumns = null;
        var tmpInit = null;    	     	
    	if(data.length === 0) return;  
    	  	
	    if($('#radyear').attr('checked')) {
	    	tmpcolumns = livecolums;
	    	tmpInit = detailInit;
	    	txtTitle = "Trends of Year:" + datev.getFullYear();
	    	txtUnit = "Month";   	
	    }
	    else if($('#radmonth').attr('checked')) {
	    	tmpcolumns = livecolumdetails;   
	    	txtTitle = "Trends of Month: " + datev.getFullYear() + "-" +arrMonth[datev.getMonth()];    	 	
	    	txtUnit = "Day";            	
	    }  
    	   	
	    var sharedDatasource = new kendo.data.DataSource({
	            data: data,
	            pageSize:31,
	            schema: {
	                        model: {
	                                    fields: {
	                                        name: { type: "number" },
	                                        live: { type: "number" },
	                                        error: { type: "number" },
	                                        link: { type: "string" }
	                                    }
	                         }
	                    }, 
	            sort: {
	                     field: "name",
	                     dir: "asc"
	            },           
	            aggregate:{ field: "name", aggregate: "count" }
	     });
	                
	    $("#livechart").kendoChart({
	                        theme: $(document).data("kendoSkin") || "default",
	                        dataSource: sharedDatasource,
	                        autoBind: false,
	                        legend: {
	                            position: "top"
	                        },
	                        title: {
	                            text: txtTitle
	                        },                        
	                        series: [
	                        {
	                            type: "line",
	                            name: "error",
	                            field: "error"
	                        },{
	                            type: "line",
	                            name: "livetime",                            
	                            field: "live"
	                        }],
	                        axisDefaults: {
	                            labels: {
	                                font: "11px Tahoma, sans-serif"
	                            }
	                        },
	                        valueAxis: {
	                            labels: {
	                                format: "{0:N0}"
	                            }
	                        },
	                        categoryAxis: {
	                            field: "name"
	                        },
	                        tooltip: {
	                            visible: true,
	                            format: "{0:N0}"
	                        }
	                    });   
	
	 
	    $("#livegrid").kendoGrid({
	        dataSource:sharedDatasource,
	        detailInit: tmpInit,	        
	        filterable: true,       
	        sortable: true,
	        pageable: true,	
	        selectable: "row",	
	        columns:tmpcolumns
	    });
	    
	    
	    $("#livegrid").delegate(".links-button", "click", function(e) {
	        var dataselect=$(this).closest("tr");
	        var errorcondition = "";        
	        $(dataselect).find("td").each(function(){       	
	            if($(this).text().indexOf("errors?") === 0 ){
	                errorcondition=$(this).text();
	                errorcondition=errorcondition.substr(7,errorcondition.length);                
	                return false;
	            }
	        }); 
	 
	        var url=window.location.protocol+"//"+window.location.host+"/bugquery/list.html?"+errorcondition;
	        window.open(url,'_blank');      
	    });    
	    
	    function detailInit(e) {
	    	livecondition = e.data.link;
	    	livecondition = livecondition.replace(/(errors\?)/g,'');
	    	
	        var funcLiveSub = function (data) {
		        $("<div/>").appendTo(e.detailCell).kendoGrid({
		            dataSource: {
		                data: data,
		                pageSize:31,
		                schema: {
		                        model: {
		                                    fields: {
		                                        name: { type: "number" },
		                                        live: { type: "number" },
		                                        error: { type: "number" },
		                                        link: { type: "string" }
		                                    }
		                         }
		                },            
		                aggregate:{ field: "name", aggregate: "count" }                
		            },            
		            sortable: true,
		            pageable: true,
		            selectable: "row",
		            columns: livecolumdetails
		        });        	
	        }
	        
	        ajaxRequest("/api/brquery/summary?" + livecondition,
	                    {},
	                    getLiveData,      
	                    funcLiveSub
	        ); 		    	      	  
	    }    	
    	    	
    }
   
    ajaxRequest("/api/brquery/summary?" + livecondition,
                {},
                getLiveData,      
                renderingLiveDate
               );
}

