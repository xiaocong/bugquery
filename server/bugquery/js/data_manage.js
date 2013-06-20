var tmp = [];

var serverlist = [{'server':''},{'server':'borqsbt'},{'server':'borqsbt2'},{'server':'borqsbtx'}]; 
var productlist = [{'product':''}];
var userlist = [{'user':''}];

var privList=[];

var userCols=[ 
            { field: "name",title:"Name" },                  
            { field: "email",title:"Email",width: "180px" },
            { field: "priviledge",title:"Priviledge",editor: PriviledgeDropdown},             
            { command: "destroy", title: " ", width: "110px" },
            //{ command: "ResetPass", title: " ", width: "100px" },
            {command: { text: "ResetPass", className: "resetpass-button" }, title: "", width:100}];

                 		

function GetGridUsers() {
    $('#tabusr').addClass('active');
    $('#tabprd').removeClass('active');
    
    $("#divuser").show();
    $("#divproduct").hide();

    // $("#divuser").undelegate();   
    // $("#diveuser").empty();

    $("#usergrid").undelegate();    
    $("#usergrid").empty();

    $("#rightsgrid").undelegate();    
    $("#rightsgrid").empty();
                    
    var dataSource = new kendo.data.DataSource({    
       pageSize: 20,
       data: getBQUsers(),
       schema: {
           model: {
             id:"_id",
             fields: { 
                _id: { editable: false, nullable: true  }, 
                name: { validation: { required: true}  },
                email: { validation: { required: true}  },
                priviledge: { validation: { required: true}}                
                
             }
           }
       }
    });

    $("#usergrid").kendoGrid({
        dataSource: dataSource,
        sortable: true,
        pageable: true,
        selectable: "row",
        toolbar: [{ name: "create", text: "Add user account " }], 
        columns: userCols,
        // [ 
        //     { field: "name",title:"Name" },                  
        //     { field: "email",title:"Email",width: "180px" },
        //     { field: "priviledge",title:"Priviledge",editor: PriviledgeDropdown},             
        //     { command: "destroy", title: " ", width: "110px" },
        //     { command: "ResetPass", title: " ", width: "100px" }],
        editable: "popup",        
        remove: function(e) {
           delBQUser(e.model.id); 
        },
        save: function(e) {
           addBQUser(e);
        },
        change: function(e) {
            var errorId;
            var tmpStart=0;
            var selected =this.select(); 
            $(selected).find("td").each(function(){
                if(tmpStart++ ==0){
                    username=$(this).text();
                    return false;
                }
            }); 
            //var url="http://"+window.location.host+"/bugquery/detail.html?"+errorId;
            //window.open(url,'detaillist');
            //alert(username);
            GetsubGridRights(username)
        }                
    });

    $("#usergrid").delegate(".resetpass-button", "click", function(e) {
            var tmpStart=0;
            var selected =$(this).select(); 
            $(selected).find("td").each(function(){
                if(tmpStart++ ==0){
                    username=$(this).text();
                    return false;
                }
            }); 
            resestPass(username)
                      
        });
     
    
    //GetsubGridRights('');
}    

function GetsubGridRights(username) {
    
      $("#rightsgrid").undelegate();    
      $("#rightsgrid").empty();
      $("#rightsgrid").kendoGrid({
         dataSource: {
             data:getBQRights(username),
             //filter: { field: "user", operator: "eq", value: name },
             pageSize:20,
             schema: {
                 model: {
                 id:"user",
                 fields: {
                        //user: {validation: { required: true } },
                        product: {validation: { required: true } }            
                     }
                 }
            }           
         },                     
         sortable: true,
         pageable: true,  
         selectable: "row",
         toolbar: [{ name: "create", text: "Add Rights" }],        
         columns: [
            //{ field: "user", title:"UserName", editor: UserDropdown,width:"1px"},
            { field: "product", title:"Product", editor: ProductDropdown },
            { command: "destroy", title: " ", width: "110px" }],
          editable: "popup",
          remove: function(e) {
              delBQRights(username,e.model.product);          
          },
          save: function(e) {
              addBQRights(username,e.model.product);
          }    
       });
}



function getBQUsers() {
    var retdata =null;
    $.ajax({ 
            async: false,
            type: "GET",
            url: window.location.protocol+"//"+window.location.host+"/api/brauth/user/",
            timeout:5000,
            dataType:"json",
            data:{"token":$.cookie("bqticket")},
            success: function(data){
                retdata = data.results;
                if(retdata['error'] !== undefined){
                    if (retdata['error']['msg']!=undefined){
                        alert(retdata['error']['msg']);
                    }else{
                        alert(retdata['error']);
                    }
                }else {                    
                    user=retdata.user                    
                    //alert(privList)
                    userlist = [{'user':''}];
                    for(var t in user) {                     
                       userlist.push({'user':user[t]['name']});
                    }                     
                    pl=retdata.priviledge;
                    privList=[{'priviledge':''}];
                    for(var i in pl){
                        privList.push({'priviledge':pl[i]})
                    } 
                    //alert(privList)             
                    retdata=user
                }                 
            },
            error: function(){
                alert("Server internal error");
            }
    });
    return retdata;  /**/                                    
}      


function getBQRights(username) {
    var retdata =null;
    $.ajax({ 
            async: false,
            type: "GET",
            url: window.location.protocol+"//"+window.location.host+"/api/brauth/rights/",
            timeout:5000,
            dataType:"json",
            data: {"token":$.cookie("bqticket"),"name":username},
            success: function(data){
                retdata = data.results;  
                if(retdata['error'] !== undefined){
                    if (retdata['error']['msg']!=undefined){
                        alert(retdata['error']['msg']);
                    }else{
                        alert(retdata['error']);
                    }
                }else {
                    tmp = [];                                       
                    for(var i=0;i<retdata.products.length;i++){
                        tmp.push({'user':retdata['user'],'product':retdata['products'][i]}); 
                    }                   
                    retdata = tmp;
                }                     
            },
            error: function(){
                alert("get rights for user failed");
            }
    });
    return retdata;  /**/                                    
}   

function addBQUser(e) {
    var retdata =null;
    $.ajax({ 
            async: false,
            type: "GET",
            url: window.location.protocol+"//"+window.location.host+"/api/brauth/user/add",
            timeout:5000,
            dataType:"json",
            data:{"token":$.cookie("bqticket"),'name':e.model.name,'email':e.model.email,'priviledge':e.model.priviledge},
            success: function(data){
                 retdata = data.results; 
                 if (retdata.error!=undefined){
                    if (retdata.error.msg!=undefined){
                        alert(retdata.error.msg);
                    }else{
                        alert(retdata.error);    
                    }                    
                 }
                GetGridUsers();                                       
            },
            error: function(){
                 alert("Add User failed!");
            }
    });
    return retdata;             
}

function delBQUser(uid) {
    var retdata =null;
    $.ajax({ 
            async: false,
            type: "GET",
            url: window.location.protocol+"//"+window.location.host+"/api/brauth/user/delete",
            timeout:5000,
            dataType:"json",
            data: {"token":$.cookie("bqticket"),'uid':uid},          
            success: function(data){
                retdata = data.results; 
                 GetGridUsers();          
            },
            error: function(){
                alert("Delete User failed!");
            }
    });
    return retdata;          
} 
   
function addBQRights(usr,product){
    var retdata =null;
    $.ajax({ 
            async: false,
            type: "GET",
            url: window.location.protocol+"//"+window.location.host+"/api/brauth/rights/add",
            timeout:5000,
            dataType:"json",
            data: {"token":$.cookie("bqticket"),"name":usr,"product":product},
            success: function(data){
                 retdata = data.results;                             
            },
            error: function(){
                 alert("Add User failed!");
            }
    });
    return retdata;             
}

function delBQRights(usr,product) {
    var retdata =null;
    $.ajax({ 
            async: false,
            type: "GET",
            url: window.location.protocol+"//"+window.location.host+"/api/brauth/rights/delete",
            timeout:5000,
            dataType:"json",
            data: {"token":$.cookie("bqticket"),"name":usr,"product":product},          
            success: function(data){
                retdata = data.results;        
            },
            error: function(){
                alert("Delete User failed!");
            }
    });
    return retdata;          
}

function resestPass(usr) {
    var retdata =null;
    $.ajax({ 
            async: false,
            type: "GET",
            url: window.location.protocol+"//"+window.location.host+"/api/brauth/user/resetpass",
            timeout:5000,
            dataType:"json",
            data: {"token":$.cookie("bqticket"),"name":usr},
            success: function(data){
                retdata = data.results; 
                if(retdata['error'] !== undefined){
                    if (retdata['error']['msg']!=undefined){
                        alert(retdata['error']['msg']);
                    }else{
                        alert(retdata['error']);
                    }
                }       
            },
            error: function(){
                alert("Reset password failed!");
            }
    });
    return retdata;          
}



function GetGridProducts() {
	$('#tabprd').addClass('active');
    $('#tabusr').removeClass('active');
    
    $("#divproduct").show();
    $("#divuser").hide();

    $("#productgrid").undelegate();    
    $("#productgrid").empty();

    $("#mappinggrid").undelegate();    
    $("#mappinggrid").empty();
    
    var dataSource = new kendo.data.DataSource({     	
       pageSize: 20,
       data: getBQProducts(),
       schema: {
           model: {
             id:"_id",
             fields: {
             	_id:{ editable: false, nullable: true },
                name: {validation: { required: true } }              
             }
           }
       }
    });

    $("#productgrid").kendoGrid({
        dataSource: dataSource,
        sortable: true,
        pageable: true,
        selectable: "row",        
        toolbar: [{ name: "create", text: "Add new product" }],
        columns: [
            { field: "name", title:"ProductName" },
            { command: "destroy", title: " ", width: "110px" }],     
        editable: "popup",
        //change: subGridInit,	        
        save: function(e) {
           //alert(JSON.stringify(e));
           addBQProduct(e);
        },
        remove: function(e) {
           delBQProduct(e.model.id);          
        },
        change: function(e) {
            var errorId;
            var tmpStart=0;
            var selected =this.select(); 
            $(selected).find("td").each(function(){
                if(tmpStart++ ==0){
                    product=$(this).text();
                    return false;
                }
            }); 
            GetsubGridMappings(product);
        }      
    });    
    //GetsubGridMappings('');   	
} 
   
function GetsubGridMappings(product) {
   	  $("#mappinggrid").undelegate();	
      $("#mappinggrid").empty();   
      	
      $("#mappinggrid").kendoGrid({
         dataSource: {
             data: getBQMapping(product),
             //filter: { field: "product", operator: "eq", value: name },           
             pageSize:20,
             schema: {
                 model: {
                 id:"_id",
                 fields: {
             	        //product: {validation: { required: true } },
                        project: {validation: { required: true } },
                        server: {validation: { required: true } }                                    
                     }
                 }
            }           
         },                   
         sortable: true,
         pageable: true,  
         selectable: "row",
         toolbar: [{ name: "create", text: "Add mapping to BorqsBT" }],        
         columns: [
            //{ field: "_id", title:"Id" , width: "110px"},    
            //{ field: "product", title:"ProductName",editor: ProductDropdown },                
            { field: "project", title:"MantisProject" },
            { field: "server", title:"MantisServer", editor:ServerDropdown},
            { command: "destroy", title: " ", width: "110px" }],
          editable: "popup",
          remove: function(e) {
              delBQMapping(product,e.model.project,e.model.server);          
          },
          save: function(e) {
              addBQMapping(product,e.model.project,e.model.server);
          }    
       });
}    

          
function getBQProducts() {
    var retdata =null;
    $.ajax({ 
            async: false,
            type: "GET",
            url: window.location.protocol+"//"+window.location.host+"/api/brauth/product/",
            timeout:5000,
            dataType:"json",
            data:{"token":$.cookie('bqticket')},
            success: function(data){
                retdata = data.results; 
                if(retdata['error'] !== undefined){
                	if (retdata['error']['msg']!=undefined){
                        alert(retdata['error']['msg']);
                    }else{
                        alert(retdata['error']);
                    }
                }  else {
                	productlist = [{'product':''}];
                 	for(var t in retdata) {               		
                 	   productlist.push({'product':retdata[t]['name']});
                 	}              	
                }                         
            },
            error: function(){
                alert("get products error");
            }
    });
    return retdata;             	 	 
}

function addBQProduct(e) {
	//alert('Add Product');
    var retdata =null;
    $.ajax({ 
            async: false,
            type: "GET",
            url: window.location.protocol+"//"+window.location.host+"/api/brauth/product/add",
            timeout:5000,
            dataType:"json",
            data:{'product':e.model.name,"token":$.cookie('bqticket')},
            success: function(data){
                retdata = data.results; 
                GetGridProducts();
            },
            error: function(){
                alert("Add product failed!");
            }
    });
    return retdata;		 	   	
}

function delBQProduct(pid) {
	//alert('Remove Product');	
    var retdata =null;
    $.ajax({ 
            async: false,
            type: "GET",
            url: window.location.protocol+"//"+window.location.host+"/api/brauth/product/delete",
            timeout:5000,
            dataType:"json",
            data:{"token":$.cookie('bqticket'),'pid':pid},          
            success: function(data){
                retdata = data.results;    
                GetGridProducts();       
            },
            error: function(){
                alert("Server internal error");
            }
    });
    return retdata;		 	 
}


function getBQMapping(product) {
	
    var retdata =null;
    $.ajax({ 
            async: false,
            type: "GET",
            url: window.location.protocol+"//"+window.location.host+"/api/brauth/mapping/",
            timeout:5000,
            dataType:"json",
            data:{"token":$.cookie('bqticket'),'product':product},
            success: function(data){
                retdata = data.results;
                if(retdata['error'] !== undefined){
                    if (retdata['error']['msg']!=undefined){
                        alert(retdata['error']['msg']);
                    }else{
                        alert(retdata['error']);
                    }
                } else {
                    var tmp = [];
                    var pats=[];
                    for(var i=0;i<retdata.projects.length;i++){
                        pats=retdata.projects[i].split("@");
                        tmp.push({'project':pats[0],"server":pats[1]}); 
                    }                   
                    retdata = tmp;
                }        
            },
            error: function(){
                alert("Server internal error");
            }
    });
    return retdata;		               	 
	   	
	/*return mappings;*/ 
}  

function addBQMapping(product,project,server) {
	//alert('Add Mapping');
    var retdata =null;
    $.ajax({ 
            async: false,
            type: "GET",
            url: window.location.protocol+"//"+window.location.host+"/api/brauth/mapping/add",
            timeout:5000,
            dataType:"json",
            data:{"token":$.cookie('bqticket'),'product':product,'server':server,'project':project},
            success: function(data){
                retdata = data.results;        
            },
            error: function(){
                alert("Add product failed!");
            }
    });
    return retdata;		 	   	
}

function delBQMapping(product,project,server) {
	//alert('Remove Mapping');	
    var retdata =null;
    $.ajax({ 
            async: false,
            type: "GET",
            url: window.location.protocol+"//"+window.location.host+"/api/brauth/mapping/delete",
            timeout:5000,
            dataType:"json",  
            data:{"token":$.cookie('bqticket'),'product':product,'project':project+"@"+server},        
            success: function(data){
               retdata = data.results;
               if(retdata['error'] !== undefined){
                    if (retdata['error']['msg']!=undefined){
                        alert(retdata['error']['msg']);
                    }else{
                        alert(retdata['error']);
                    }
                }                         
            },
            error: function(){
               alert("Server internal error");
            }
    });
    return retdata;		 	 
}     


 
       


function ServerDropdown(container, options) {
    $('<input data-text-field="server" data-value-field="server" data-bind="value:' + options.field + '"/>')
        .appendTo(container)
        .kendoDropDownList({
            autoBind: false,
            dataSource:{
               data:serverlist	
            }
        });
}

function ProductDropdown(container, options) {
    $('<input data-text-field="product" data-value-field="product" data-bind="value:' + options.field + '"/>')
        .appendTo(container)
        .kendoDropDownList({
            autoBind: false,
            dataSource:{
               data:productlist	
            }
        });
}

function UserDropdown(container, options) {
    $('<input data-text-field="user" data-value-field="user" data-bind="value:' + options.field + '"/>')
        .appendTo(container)
        .kendoDropDownList({
            autoBind: false,
            dataSource:{
               data:userlist	
            }
        });
}

function PriviledgeDropdown(container, options) {
    $('<input data-text-field="priviledge" data-value-field="priviledge" data-bind="value:' + options.field + '"/>')
        .appendTo(container)
        .kendoDropDownList({
            autoBind: false,
            dataSource:{
               data:privList    
            }
        });
}





