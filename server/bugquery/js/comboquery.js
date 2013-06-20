       
        var propertyList=[],errorTypeList=[];
        var idIndex=0;
          
        function addCondition(){
            var condList=document.getElementById("cond_list");
            idIndex++;
            
            var div=document.createElement("div");
            div.setAttribute("class","comboitem");
            div.setAttribute("id","item"+idIndex);
                    
            var removeBtn=document.createElement("input");
            removeBtn.setAttribute("class","comboval");
            removeBtn.setAttribute("id","btn"+idIndex);
            removeBtn.setAttribute("type","button");
            removeBtn.setAttribute("value","-");
            removeBtn.setAttribute("onClick","removeCondition(event)");
            
            var typeSelect=document.createElement("select");
            typeSelect.setAttribute("class","combotype");
            typeSelect.setAttribute("id","type"+idIndex);
            typeSelect.selectedIndex=0;
            typeSelect.setAttribute("onChange","setSub(event)");

            var subSelect=document.createElement("select");
            subSelect.setAttribute("id","sub"+idIndex);
            subSelect.options.length = 0;
            var value=document.createElement("input");
            value.setAttribute("class","comboval");
            value.type="text";          
            value.id="val"+idIndex;

            div.appendChild(removeBtn);
            div.appendChild(typeSelect);
            div.appendChild(subSelect);
            div.appendChild(value);
            condList.appendChild(div);

            var opt1=new Option("Device Property","property");
            var opt2=new Option("Error Type","eType");
            typeSelect.options.add(opt1);
            typeSelect.options.add(opt2);

            var i;
            for (i in propertyList){
                //var opt=document.createElement("option");
                //opt.text=propertyList[i]["text"];
                //opt.value=propertyList[i]["value"];
                //subSelect.appendChild(opt);
                var opt = new Option(propertyList[i]["text"],propertyList[i]["value"]);
                subSelect.options.add(opt);
            }
            
        }

        function removeCondition(event){
            var id=(event.target)?event.target.id:event.srcElement.id;
            var index=id.substring(3);

            var condList=document.getElementById("cond_list");
            var div=document.getElementById("item"+index);
            condList.removeChild(div);
        }

        function setSub(event){
            var target=(event.target)?event.target:event.srcElement;
            var id=target.id;
            var index=id.substring(4);

            var div=document.getElementById("item"+index);
            switch(target.value){
                case "property":{
                    var subSelect=document.getElementById("sub"+index);
                    var value=document.getElementById("val"+index);

                    var i;
                    subSelect.options.length = 0;
                    for (i in propertyList){
                        var opt = new Option(propertyList[i]["text"],propertyList[i]["value"]);
                        subSelect.options.add(opt);
                    }
                    value.style.display="inline";
                    break;
                }
                case "eType":{
                    var subSelect=document.getElementById("sub"+index);
                    var value=document.getElementById("val"+index);
                    var i;
                    subSelect.options.length = 0;

                    for (i in errorTypeList){
                        var opt = new Option(errorTypeList[i]["text"],errorTypeList[i]["value"]);
                        subSelect.options.add(opt);                
                    }
                    value.style.display="none";
                    break;
                }            
            }
        }
