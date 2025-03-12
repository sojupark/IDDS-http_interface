/*헬로월드*/

function openForm(myTr) {
        console.log("open form");
	if(document.getElementById("myForm").style.display == "block") {
		document.getElementById("myForm").style.display="none";	
		document.getElementById("myExeForm").style.display="none";	
	} else {	
		if(myTr) {
			for(var i = 0; i < myTr.childNodes.length; i++) {
				if(myTr.childNodes[i].tagName == 'TD') {
					if(document.getElementById(myTr.childNodes[i].className+"_input")) {
						document.getElementById(myTr.childNodes[i].className+"_input").value = myTr.childNodes[i].innerHTML.replace(/&lt;/g,'<').replace(/&gt;/g,'>').replace(/&quot;/g, '"').replace(/<br>/g,"").replace(/&amp;/g,"&").replace(/&#039;/,"'");
        					//console.log("-->"+ myTr.childNodes[i].innerHTML);
					}
				}
			}
		} else {
			var myTr = document.getElementsByTagName("textarea")
			for(var i = 0; i < myTr.length; i++) {
				myTr[i].value="";
			}

		}
		document.getElementById("myForm").style.display="block";
	}
}

function closeForm() {
	document.getElementById("myForm").style.display="none";
	document.getElementById("myExeForm").style.display="none";
}

function openExeForm() {
	let exe_form= document.getElementById("myExeForm");
	exe_form.style.display = "block";

	let myPDoc= document.getElementById("myForm");
	myPDoc.scrollTop = myPDoc.scrollHeight;

	
}

function mySearch() {
	var input, filter, table, tr, td, i;
	input = document.getElementById("myInput");
	const filters = input.value.split(" ");

	table = document.getElementById("mytablelist")

	mysinput = document.getElementById("mysearchstr")
	mysinput.value = filters.join(" ");

	tr = table.getElementsByTagName("tr");
	for(i = 1; i < tr.length; i++) {
		td = tr[i].getElementsByTagName("td");
		let isThere = 0;
		for(j = 0; j < td.length;j++) {
			if(td[j]) {
				if(td[j].innerHTML.indexOf(filters[isThere]) > -1) {
					isThere++;
				} 
			}
		}

		if(isThere == filters.length) {
			tr[i].style.display = "";
		} else {
			tr[i].style.display = "none";
		}
	}
}

var i = 0;
function move() {
  if (i == 0) {
    i = 1;
    var elem = document.getElementById("myBar");
    var width = 1;
    var id = setInterval(frame, 10);
    function frame() {
      if (width >= 100) {
        clearInterval(id);
        i = 0;
      } else {
        width++;
        elem.style.width = width + "%";
      }
    }
  }
}

/*function mySortTable(myClassNm) {
	var table, rows, switching, i, x, y, shouldSwitch;
	table = document.getElementById("mytablelist").;	
	switching = true;
	while (switching) {
		switching = false;
		;
}*/

const test1= document.getElementById("myInput");
const test2= document.getElementsByClassName("open-button");
console.log("myfeed_tab.js----->, urgent_exe.js---->", test1, test2);
