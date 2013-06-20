var colums=[            
            {field:"_id",width:25, title:"Id"},
            {field:"product",width:20, title:"Product"},
            {field:"phone_no",width:40, title:"PhoneNumber"},             
            {field:"category",width:35, title:"Category"},            
            {field:"type",width:45, title:"Type"},
            {field:"name",width:45, title:"Name"},
            {field:"info",width:80, title:"Info"},            
            {field:"receive_time",width:35, title:"Receive_Time"}         
           ];
           
function createGrid(){
    $("#monitorview").empty();
    columnDes=[];
    function onChange(arg) {
        var errorId;
        var tmpStart=0;
        var selected =this.select(); 
        $(selected).find("td").each(function(){
            if(tmpStart++ ==0){
                errorId=$(this).text();
                return false;
            }
        }); 
        var url=window.location.protocol+"//"+window.location.host+"/bugquery/detail.html?id="+errorId;
        window.open(url,'detaillist');
    } 
    $("#monitorview").kendoGrid({
        dataSource: {
                     data: getErrorList(),
                     pageSize: 25
                       },
        height: 640,
        scrollable: true,
        sortable: true,
        pageable: true,	
        change: onChange,
        selectable: "row",		
        columns:colums
    });    
}
function getErrorList(){
    var errordata = getErrorData();
    	
    for (var i=0; i<errordata.length; i++){
         var row=errordata[i]
         var info=row["info"]+""
         row["info"]=info.substring(0,(info.length>50?50:info.length));                            
    }
    setTimeout("createGrid()",5000);
     
    return errordata;	
}    
  
function getErrorData(){	
	var errordata=null;
	
    var errorcondition = window.location.search.substring(1);
    $.ajax({
            async: false,
            type: "GET",
            url: window.location.protocol+"//"+window.location.host+"/api/brstore/record/latest?count=20&"+ticketcondition(),             
            timeout:5000,
            dataType:"json",
            success: function(data){                   
                         errordata = checkerror(data.results,getErrorData);                    
                     },
            error: function(){
                       alert("error");
                   }
           });
           
    return errordata;
} 
