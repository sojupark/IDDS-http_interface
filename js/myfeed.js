function setURL(evt, tabnm, tabact, myServ) {
        document.getElementById('mysel').src = myServ+"/tab/"+tabnm;
        
        console.log("thist site is "+ myServ+"/tab/"+tabnm);

        tablinks = document.getElementsByClassName("tablinks");
        for (i = 0; i < tablinks.length; i++) {
                tablinks[i].className = tablinks[i].className.replace(" active", "");
        }
        evt.currentTarget.className += " active";
}
