
$(function(){
    if(window.location.href.indexOf("login.html") < 0) {
        setlogname();
        //$('.dropdown-toggle').dropdown();
    }
});

function setlogname() {
	 var server = $.cookie('btActiveServerName');
    if(server === null || server === '' || server === 'bqserver' )
       $('#loggedid').html('['+$.cookie('bqUserName')+']')    
    else
       $('#loggedid').html('['+$.cookie('btUserName_'+server)+']');
}

function dochnpswd() {

     var oldpswd,newpswd,cnfpswd;
     oldpswd = $('#txtoldpswd').val();
     newpswd = $('#txtnewpswd').val();
     cnfpswd = $('#txtcfmpswd').val();
     
     if($.cookie('btActiveServerName') !== 'bqserver' && $.cookie('btActiveServerName') !== '') { 
         alert('Only bugquery account can change password!'); 
         return;
     };
     if(oldpswd === '') { alert('Please input old password!'); return;};
     if(newpswd === '') { alert('Please input new password!'); return;};
     if(cnfpswd === '') { alert('Please input confirmed password!'); return;};   
     if(newpswd !== cnfpswd) { alert('New password and confirmed password are not identical!'); return;}  

     var data = {'name':$.cookie('bqUserName'),
                 'oldpass':oldpswd,
                 'newpass':newpswd,
                };

     ajaxRequestEx("/api/brauth/user/changepass",             
                    data,
                    function(ret){return ret.results;},
                    function(ret){
                       $.cookie('bqUserPswd',newpswd,{expires:999});
                       alert('Change password successfully!');
                       $('#dlgpswd').dialog("close");
                    });
}

function changepswd() {
    $('#dlgpswd').dialog({title: 'change password',
                          resizable:false,
                          modal: true});
}

function getRequestParam(src,name){
      var params=src;
      var paramList=[];
      var param=null;
      var parami;
      if(params.length>0) {
             if(params.indexOf("&") >=0) {  // >=2 parameters
                paramList=params.split( "&" );
             } else {                       // 1 parameter
                paramList[0] = params;
             }
             for(var i=0,listLength = paramList.length;i<listLength;i++) {
                 parami = paramList[i].indexOf(name+"=" );
                 if(parami>=0) {
                     param =paramList[i].substr(parami+(name+"=").length); //get value
                     break;
                 }
             }
      }
      return param;
}

function gotoRecord(){
    var id=document.getElementById("searchTextBox").value;
    var queryid="id="+id;
    var url=window.location.protocol+"//"+window.location.host+"/bugquery/detail.html?"+queryid;
    window.open(url,'_blank');
}

var ticketcondition = function() {
    return "token=" + $.cookie('bqticket');
}

var baseURL = function() {
    return window.location.protocol+"//"+window.location.host;	
}

var ajaxstart=function() {
		var winWidth=0;
		var winHeight=0;
		//获取窗口宽度	
	    if(window.innerWidth) winWidth = window.innerWidth;	
	    else if((document.body) && (document.body.clientWidth))	winWidth = document.body.clientWidth;
	
	    //获取窗口高度
	    if(window.innerHeight) winHeight = window.innerHeight;	
	    else if((document.body) && (document.body.clientHeight)) winHeight = document.body.clientHeight;
	
	    //通过深入Document内部对body进行检测，获取窗口大小
	    if(document.documentElement && document.documentElement.clientHeight && document.documentElement.clientWidth) {
		   winHeight = document.documentElement.clientHeight;
		   winWidth = document.documentElement.clientWidth;
	    }

        if(document.getElementById('img') !== undefined && document.getElementById('img') !== null ) {
	        document.getElementById('img').style.left=""+(winWidth/2-70)+"px";
	        document.getElementById('img').style.top=""+(winHeight/2)+"px";
	        document.getElementById('img').innerHTML = "<a><img style='BORDER:none' src='styles/images/loading.gif'></a>";   	
        }	    		    
}; 

var ajaxend = function(){
	if(document.getElementById('img') !== undefined && document.getElementById('img') !== null )
        document.getElementById('img').innerHTML = '';
};

/*
 * Http Get Request by Jquery Ajax
 */
var ajaxRequest = function(apiUrl,dataj,filter,render) {
	
  //ajax options prepare
  var options = {}; 

	var funok=function(data) {
      if(data['results'] === undefined) {
          alert("Server Internal error!");
          ajaxend();
      } else if(data['results']['error'] !== undefined) {
         if(data['results']['error']['code'] === 12) {
             var oldt = ticketcondition();
             doAuth();
             var newt = ticketcondition();
             options['url'] = options['url'].replace(oldt,newt);
             $.ajax(options);
         } else {
             alert(data['results']['error']['msg']);
             ajaxend();
         }
      } else {
          render(filter(data));
		      ajaxend();
      }
	};
	
	  var funerror=function() {
       alert("Server Internal error!");
       ajaxend();
    };
    options['beforeSend'] = ajaxstart;
    options['url'] = baseURL() + apiUrl;	
    options['async'] = true;	
    options['type'] = 'GET';	
    options['dataType'] = 'json';    
    options['timeout'] = 25000;        
	  options['success'] = funok;
	  options['error'] = funerror;
			
    //invoke jquery ajax
    $.ajax(options);
}

/*
 * Http POST Request by Jquery Ajax
 */
var ajaxRequestEx = function(apiUrl,pdata,filter,render) {
	
	var funok = function(data) {
      if(data['results'] !== undefined) {
          if (data['results']['error'] !== undefined) {
             alert(data['results']['error']['msg']);
             ajaxend();
          } else {
             render(filter(data));
             ajaxend();
          }
      }
	};
	
	var funerror=function(){		
        alert("Server Internal error!");
        ajaxend();
    };
	
    var options = {};	
    options['beforeSend'] = ajaxstart;	
    options['url'] = baseURL() + apiUrl;		
    options['async'] = false;	
    options['type'] = 'POST';	
    options['dataType'] = 'json';
    options['data'] = JSON.stringify(pdata);    
    options['contentType']= 'application/json';          
    options['timeout'] = 25000;        
	  options['success'] = funok;
	  options['error'] = funerror;
	
	  //invoke jquery ajax	
    $.ajax(options);			
}



function loginauth(usr,pswd,server) {
	
     var blogin = false;
     var m_username = usr;
     if (server !== '' && server !== 'bqserver' ) {
         m_username += '@' + server;
     }
     var userdata = {'username':m_username,
                     'password':pswd
                    };
                         
     ajaxRequestEx("/api/brauth/auth",             
                    userdata,
                    function(ret){return ret.results;},
                    function(ret){          	      
                        if(ret["token"] !== undefined && ret["token"] !== null) {
                      	    $.cookie('bqticket',ret["token"], {expires:9});
                      	    if(server === '' || server === 'bqserver') {
                      	         $.cookie('btActiveServerName','bqserver',{expires:999});                    	 	
                      	         $.cookie('bqUserName',usr,{expires:999});
                      	         $.cookie('bqUserPswd',pswd,{expires:999});                  	 	
                      	    } else {
                      	         $.cookie('btActiveServerName',server,{expires:999});                  	 	
                      	         $.cookie('btUserName_'+server,usr,{expires:999});
                      	         $.cookie('btUserPswd_'+server,pswd,{expires:999});                       	 	
                      	    }
                      	    blogin = true;    
                      	                       	                      	                    	 	    	                                                         	 	
                         } else if(ret["error"] !== undefined && ret["error"] !== null){
                      	     alert(ret["error"]["msg"]);
                         }
                   });

    return blogin;
}

function logout()
{
    $.cookie('bqticket','',{expires:-1});
    $.cookie('url_redirect','',{expires:-1});
    window.location = "login.html";
}


function doAuth(){
    if($.cookie('btActiveServerName') !== null) {
       var server = $.cookie('btActiveServerName');
       var user = '';
       var pswd = '';
       if (server !== '' && server !== 'bqserver' ) {
          user =$.cookie('btUserName_'+server);
          pswd =$.cookie('btUserPswd_'+server);       
       } else {
          user =$.cookie('bqUserName');
          pswd =$.cookie('bqUserPswd');       
       }          
    
       if(!loginauth(user,pswd,server)) {
          $.cookie('bqticket','',{expires:-1});       
          window.location = "login.html"; 
       }                         
    } else {
      $.cookie('bqticket','',{expires:-1});     
      window.location = "login.html";
    }
}

/*
 *  Request for new access token with an interval 30m now
 */
function funcAuth(){
    var timer_timeout = null;
    doAuth();
    timer_timeout = setTimeout(funcAuth, 10*60*1000);		
}


