var test_type = 0;

/*
 *  * type
 *   *      0 : mytalk
 *    *      1 : othertalk
 *     */
function jstalktheme_addmsg(type, name, time, msg)
{
        var ocontainer = document.getElementById("jstalktheme_test");
        var ocontainer_msg = ocontainer.getElementsByClassName("msg")[0];
        
        var onewmsg = document.createElement("div");
        var onewblank = document.createElement("div");
        
        if(type)
        {
                onewmsg.className="othertalk";
                onewmsg.innerHTML = 
                "<div class=\"profile_image\" style=\"background: url(./profile_image.png) no-repeat;\">\n"+
                "</div>\n"+
                "<div class=\"box\">\n"+
                "<div class=\"profile_name\">\n"+
                name+"\n"+
                "</div>\n"+
                "<div class=\"a\">\n"+
                "</div>\n"+
                "<div class=\"b\">\n"+
                msg+"\n"+
                "</div>\n" +
                "<div class=\"time\">\n"+
                time+"\n"+
                "</div>\n"+
                "</div>\n";
        }else{
                onewmsg.className="mytalk";
                onewmsg.innerHTML = 
                "<div class=\"b\">\n"+
                "</div>\n"+
                "<div class=\"a\">\n"+
                msg+"\n"+
                "</div>\n"+
                "<div class=\"time\">\n"+
                time+"\n"+
                "</div>\n" +
                "";
        }
        
        onewmsg.innerHTML +=
    "<div class=\"clear\">\n"+
    "</div>";

       
        onewblank.className="blank";
        
        ocontainer_msg.appendChild(onewmsg);
        ocontainer_msg.appendChild(onewblank);
        
        ocontainer_msg.scrollTop = ocontainer_msg.scrollHeight;
}


function jstalktheme_testfunc(mydata, myname)
{
	//var otxtmsg = JSON.stringify(mydata);
	var otxtmsg = JSON.stringify(JSON.parse(mydata));
	var d = new Date();
	var ampm = (d.getHours()>12 ?  "PM" : "AM");
	var h = (d.getHours()>12 ? d.getHours()-12 : d.getHours()).toString().padStart(2,'0');
	var m = d.getMinutes().toString().padStart(2,'0');

	//test_type ^= 0x01;
	test_type = 0x01;
	jstalktheme_addmsg(test_type, myname, ampm+" "+h+":"+m, otxtmsg+"<br />\n");	
}
