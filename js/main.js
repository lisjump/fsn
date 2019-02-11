patronlist = new Array()
secondsort = false
eventlist = new Array()
eventindex = ""
visitlist = new Array()
visitindex = ""
cancelindex = 0
newsessionindex = 0
currentsort = ""
priorsort = ""
reversesort = false
date = ""
showallevents = false
showallinstances = false
var today = new Date();
var dd = today.getDate();
var mm = today.getMonth()+1; //January is 0!
lastmonth = mm - 1
var yyyy = today.getFullYear();
if(dd<10) {
    dd='0'+dd
} 
if(mm<10) {
  mm='0'+mm
} 
if(lastmonth<10) {
  lastmonth='0'+lastmonth
} 
today = yyyy + "-" + mm + "-" + dd
if(lastmonth<1) {
  lastmonth=12
  year =  year - 1 
} 
lastmonth = yyyy + "-" + lastmonth + "-" + dd
recurringtabindex = 1

// ------------- Table Functions ------------------

function DeletePatron(span) {
  cell = span.parentNode;
  row = cell.parentNode;
  table = row.parentNode;
  index = row.rowIndex;

  deletes = document.getElementsByName("delete");
  firsts = document.getElementsByName("first");
  lasts = document.getElementsByName("last");
  xs = document.getElementsByName("x");
  
  if (deletes[index-1].value == "True") {
    firsts[index-1].setAttribute('class', 'normalrow');
    lasts[index-1].setAttribute('class', 'normalrow');
    xs[index-1].innerHTML = "&#10006;";
    deletes[index-1].value = "False";
  } else {
    firsts[index-1].setAttribute('class', 'deletedrow');
    lasts[index-1].setAttribute('class', 'deletedrow');
    xs[index-1].innerHTML = "undo";
    deletes[index-1].value = "True";
  }
}

function DeleteEventInstance(span) {
  cell = span.parentNode;
  row = cell.parentNode;
  table = row.parentNode;
  index = row.rowIndex;

  deletes = document.getElementsByName("ideleted");
  dates = document.getElementsByName("idate");
  starts = document.getElementsByName("istarttime");
  ends = document.getElementsByName("iendtime");
  instructors = document.getElementsByName("iinstructor");
  costs = document.getElementsByName("icost");
  notess = document.getElementsByName("inotes");
  
  if (deletes[index-1].value == "True") {
    dates[index-1].setAttribute('class', 'normalrow');
    starts[index-1].setAttribute('class', 'normalrow');
    ends[index-1].setAttribute('class', 'normalrow');
    instructors[index-1].setAttribute('class', 'normalrow');
    costs[index-1].setAttribute('class', 'normalrow');
    notess[index-1].setAttribute('class', 'normalrow');
    span.innerHTML = "&#10006;";
    deletes[index-1].value = "False";
  } else {
    dates[index-1].setAttribute('class', 'deletedrow');
    starts[index-1].setAttribute('class', 'deletedrow');
    ends[index-1].setAttribute('class', 'deletedrow');
    instructors[index-1].setAttribute('class', 'deletedrow');
    costs[index-1].setAttribute('class', 'deletedrow');
    notess[index-1].setAttribute('class', 'deletedrow');
    span.innerHTML = "undo";
    deletes[index-1].value = "True";
  }
}

function ToggleHidden(input) {
  sessionhidden = document.getElementById("hidden" + input.id);
  
  if (sessionhidden.value == 1) {
    sessionhidden.value = 0;
    if (sessionhidden.name == "icancel") { input.innerHTML = "Cancel" }
  } else {
    sessionhidden.value = 1;
    if (sessionhidden.name == "icancel") { input.innerHTML = "Restore" }
  }
}

function AddRows(tableid, num) {
  table = document.getElementById(tableid);
  if (table.style.display = "None") {
    table.style.display = "table";
  }
  for (i = 0; i < num; i++) { 
    newRow = table.rows[1].cloneNode(true);
    if (table.tBodies[0] ) {
      table.tBodies[0].appendChild(newRow);    
    }
    else {
      table.appendChild(newRow);    
    }
    newRow.style.display = "table-row";
  }
}


// ------------- Submitting ------------------

function EditHousehold(id) {
  var xmlhttp, url;
  var address1 = document.getElementById("address1").value;
  var address2 = document.getElementById("address2").value;
  var city = document.getElementById("city").value;
  var state = document.getElementById("state").value;
  var zip = document.getElementById("zip").value;
  var phone = document.getElementById("phone").value;
  var income = document.getElementById("income").value;
  var photo = document.getElementById("photo").value;
  
  var post = "id=" + id 
    + "&address1=" + address1;

  url = "/addhousehold?" + post;
    
  if (window.XMLHttpRequest) {// code for IE7+, Firefox, Chrome, Opera, Safari
    xmlhttp=new XMLHttpRequest();
  }
  else {// code for IE6, IE5
    xmlhttp=new ActiveXObject("Microsoft.XMLHTTP");
  }
  
  xmlhttp.open("POST", url, true);
  xmlhttp.send();
  
}

function VisitSubmit(){
  var patronboxes = document.getElementById('patroncell').querySelectorAll('input[type="checkbox"]');
  var checkedpatron = Array.prototype.slice.call(patronboxes).some(x => x.checked);
  var eventboxes = document.getElementById('eventcell').querySelectorAll('input[type="checkbox"]');
  var checkedevent = Array.prototype.slice.call(eventboxes).some(x => x.checked);
  var deletevisit = document.getElementById("deletevisit");

  if (deletevisit && deletevisit.checked) {
    if (confirm("Are you sure you want to delete the visit?")) {
      return true
    } else {
      return false
    }
  } else if (checkedpatron && checkedevent) {
    return true;
  } else if (checkedpatron) {
    alert("Please select at least one Event.")
    return false;
  } else if (checkedevent) {
    alert("Please select at least one Patron.")
    return false;
  } else {
    alert("Please select at least one Patron and one Event.")
    return false;
  }
}

function RegisterSubmit(){
  var form = document.getElementById('registration');
  var submitbutton = document.getElementById('submitbutton');
  var errordiv = document.getElementById('submiterrors');
  var firsts = document.getElementsByName('first');  
  var income = document.getElementById('income');  
  var email = document.getElementById('email');  
  var email2 = document.getElementById('email2');  
  var lanl = document.getElementById('lanl');  
  var birthyears = document.getElementsByName('birthyear');  
  var ethnicities = document.getElementsByName('ethnicity');  
  
  if (submitbutton.innerHTML == "Resubmit") {
    return true
  }
  
  submiterrors = ""
  please = "Please consider filling in some additional information: <br>"
  
  if (email.value == "" && email2.value == "" && (document.querySelector('input[name="communication2"]:checked') || document.querySelector('input[name="communication3"]:checked'))) {
    submiterrors = submiterrors + "* You've requested email communication, but have not provided and email address <br>"
  }
  
  if (income.value == "1") {
    submiterrors = submiterrors + "* Household Income: Many of our grants require this demographic information. <br>"
  }
  
  if (!document.querySelector('input[name="lanl"]:checked')) {
    submiterrors = submiterrors + "* LANL employment: This helps when we apply for funding from the lab. <br>"
  }
  
  if (!document.querySelector('input[name="photo"]:checked')) {
    submiterrors = submiterrors + "* Photo Waiver: We'd like to post photos of our programs online and in our newsletter. <br>"
  }
  
  for (index in firsts){
    if (firsts[index].value){
      if (!birthyears[index].value || birthyears[index].value == "select") {
        submiterrors = submiterrors + "* " + firsts[index].value +  "'s birthyear:  We use birthyears to differentiate children from adults. <br>"
      }
      if (!ethnicities[index].value || ethnicities[index].value == "select") {
        submiterrors = submiterrors + "* " + firsts[index].value +  "'s ethnicity:  Many of our grants require this demographic information. <br>"
      }
    }
  }

  if (submiterrors){
    errordiv.innerHTML = please + submiterrors
    submitbutton.innerHTML = "Resubmit"
    return false; 
  }
  
  return true

}

// ------------- Overlay ------------------

function Overlay(url, prefix) {

   var overlay = document.createElement("div");
   overlay.setAttribute("id","overlay");
   overlay.setAttribute("class", "overlay");
   document.body.appendChild(overlay);
   
   var overlayform = document.createElement("div");
   overlayform.setAttribute("id","overlayform");
   overlayform.setAttribute("class", prefix + "overlayform");
   document.body.appendChild(overlayform);

   if (window.XMLHttpRequest) {// code for IE7+, Firefox, Chrome, Opera, Safari
     var xmlhttp=new XMLHttpRequest();
   }
   else {// code for IE6, IE5
     var xmlhttp=new ActiveXObject("Microsoft.XMLHTTP");
   }
  
   xmlhttp.open("GET", url, true);
   xmlhttp.send();
   
   xmlhttp.onreadystatechange=function() {
     if (xmlhttp.readyState==4 && xmlhttp.status==200) {
       overlayform.innerHTML = xmlhttp.responseText;
       if (url.substring(0, 14) == '/adminaddevent') {
         LoadSessions(url.substring(23))
         if (url.substring(23)) {
           for (rindex in eventlist[eventindex]['recurrences']) {
             CreateRecurringTab(rindex)
           }
         }
       }
       if (url.substring(0, 11) == '/adminvisit') {
         LoadEvents(visit = true, date = date) 
       }
      }
    }
       overlayform.innerHTML = "Loading...";
}

function ClearOverlay() {
  var overlay = document.getElementById("overlay");
  document.body.removeChild(overlay);

  var overlayform = document.getElementById("overlayform");
  document.body.removeChild(overlayform);

  cancelindex = 0
  newsessionindex = 0
  recurringtabindex = 1
}


// ------------- Patrons Admin ------------------

function LoadPatrons() {
  var xmlhttp,xmldoc,patrons,i,j;
  
  if (window.XMLHttpRequest) {// code for IE7+, Firefox, Chrome, Opera, Safari
    xmlhttp=new XMLHttpRequest();
  }
  else {// code for IE6, IE5
    xmlhttp=new ActiveXObject("Microsoft.XMLHTTP");
  }
  
  xmlhttp.onreadystatechange=function() {
    if (xmlhttp.readyState==4 && xmlhttp.status==200) {
      response = JSON.parse(xmlhttp.responseText);
      patronlist = response
      FillPatronTable();
    }
  }

  xmlhttp.open("GET","/getpatrons.json",true, sortby = 'ID');
  xmlhttp.send();
}

function FillPatronTable() {
      var table = document.getElementById("patronlist");

      for (var i = table.rows.length-1; i>0; i--) {
        table.deleteRow(i);
      }
            
      secondsort = false;
      if (currentsort) patronlist.sort(eval(currentsort));
      if (reversesort) {
        patronlist.reverse()
      }
      
      for (patron in patronlist) {
          var row = table.insertRow(-1);
          var idcell = row.insertCell(0);
          var hidcell = row.insertCell(1);
          var firstcell = row.insertCell(2);
          var lastcell = row.insertCell(3);
          
          if (patron % 2 == 0) {
            row.setAttribute("class", "odd");
          }
          else {
            row.setAttribute("class", "even");
          }

          
          idcell.innerHTML = patronlist[patron]['id'];
          for (var index in patronlist[patron]['households']){
            hid = patronlist[patron]['households'][index]
            if (hidcell.innerHTML == "") {
              hidcell.innerHTML = "<span class='blacklink' id=" + hid + " onclick='LoadHousehold(" + hid + ")'>" + hid + "</span>"
            }
            else {
              hidcell.innerHTML = hidcell.innerHTML + "<br>" + "<span class='blacklink' id=" + hid + " onclick='LoadHousehold(" + hid + ")'>" + hid + "</span>"
            }
          }
          firstcell.innerHTML = patronlist[patron]['first'];
          lastcell.innerHTML = patronlist[patron]['last'];
      }
}

function LoadHousehold(id) {
  Overlay('/adminhousehold?householdid=' + id, "patron")
}

function LoadHouseholdFromVisit(id) {
  Overlay('/visithousehold?householdid=' + id, "patron")
}

// ------------- Events Admin ------------------

function EventShowAll(){
  var button = document.getElementById("showall");
  showallevents = !showallevents
  if (showallevents) {
    button.value = "Show Active"
  } else {
    button.value = "Show All"
  }
  FillEventTable()
}

function ExpandAll(span) {
  if (span.innerHTML == '[+]'){
    for (event in eventlist) {
      eventlist[event]['expanded'] = true;
    }
    FillEventTable();
    span.innerHTML = '[-]'
  } else {
    for (event in eventlist) {
      eventlist[event]['expanded'] = false;
    }
    FillEventTable();
    span.innerHTML = '[+]'
  }
  return;
}

function LoadEvents(visit = false, date = "", visitid = "", reload = "") {
  var xmlhttp,xmldoc,patrons,i,j;
  
  if (window.XMLHttpRequest) {// code for IE7+, Firefox, Chrome, Opera, Safari
    xmlhttp=new XMLHttpRequest();
  }
  else {// code for IE6, IE5
    xmlhttp=new ActiveXObject("Microsoft.XMLHTTP");
  }
  
  xmlhttp.onreadystatechange=function() {
    if (xmlhttp.readyState==4 && xmlhttp.status==200) {
      response = JSON.parse(xmlhttp.responseText);
      eventlist = response
      if (visit){
        FillVisitTD(date);
      } else {
        FillEventTable();
        if (reload) {
          LoadEvent(reload)
        }
      }
    }
  }

  xmlhttp.open("GET","/getevents.json",true, sortby = 'ID');
  xmlhttp.send();
}

function FillEventTable() {
      var table = document.getElementById("eventlist");

      for (var i = table.rows.length-1; i>0; i--) {
        table.deleteRow(i);
      }
            
      secondsort = false;
      if (currentsort) eventlist.sort(eval(currentsort));
      if (reversesort) {
        eventlist.reverse()
      }
      
      for (event in eventlist) {
        if (showallevents || !eventlist[event]['archive']) {
          var row = table.insertRow(-1);
          var idcell = row.insertCell(0);
          var namecell = row.insertCell(1);
          var instructorcell = row.insertCell(2);
          var costcell = row.insertCell(3);
          var expandcell = row.insertCell(4);
          var expandspan = document.createElement("SPAN");
          expandcell.appendChild(expandspan)
          
          if (event % 2 == 0) {
            row.className = "odd";
          }
          else {
            row.className = "even";
          }

          
          idcell.innerHTML = "<span class='blacklink' id=" + eventlist[event]['id'] + " onclick='LoadEvent(" + eventlist[event]['id'] + ")'>" + eventlist[event]['id'] + "</span>";
          namecell.innerHTML = eventlist[event]['name'];
          instructorcell.innerHTML = eventlist[event]['instructor'];
          costcell.innerHTML = eventlist[event]['cost'];
          expandspan.innerHTML = "[+]"
          expandspan.className = "blacklink"
          expandspan.setAttribute('onclick', "expandEvent(this, " + event + ")")
          if (eventlist[event]['expanded']) { expandEvent(expandspan, event) }
        }
      }
}

function expandEvent(span, event) {
    var table = document.getElementById("eventlist");
    var row = span.parentNode.parentNode;
    var idcell = row.cells[0];
    var expandall = document.getElementById("expandall");
    expandall.innerHTML = "[*]"
    if (span.innerHTML == "[+]") {
      var newrow = table.insertRow(row.rowIndex + 1);
      var descriptioncell = newrow.insertCell(0);
      
      newrow.className = row.className;
      span.innerHTML = "[-]";
      descriptioncell.colSpan = row.cells.length - 1
      descriptioncell.innerHTML = eventlist[event]['description']
      
      idcell.rowSpan = 2;
      eventlist[event]['expanded'] = true;
    } else {
      idcell.rowSpan = 1
      table.deleteRow(row.rowIndex + 1)
      span.innerHTML = "[+]";
      eventlist[event]['expanded'] = false;
    }
}

// ------------- Add Events Admin ------------------

function InstanceShowAll(){
  var button = document.getElementById("instanceshowall");
  var id = document.getElementById("id");
  showallinstances = !showallinstances
  if (showallinstances) {
    button.value = "Show Active"
  } else {
    button.value = "Show All"
  }
  LoadSessions(id.value)
}

function LoadEvent(id) {
  showallinstances = false
  Overlay('/adminaddevent?eventid=' + id, "event")
}

function LoadSessions(eventid){
  sessionsdiv = document.getElementById("sessionsdiv");
  while (sessionsdiv.hasChildNodes()) {
      sessionsdiv.removeChild(sessionsdiv.lastChild);
  }
  
  eventindex = ""
  for (index in eventlist) {
    if (eventlist[index]['id'] == eventid) {
      eventindex = index
      break
    }
  }
  LoadSession("")
  if (eventindex) {
    for (sessionindex in eventlist[eventindex]['sessions']) {
      LoadSession(sessionindex)
    }
  }
}

function LoadSession(sessionindex){
  var sessionsdiv = document.getElementById("sessionsdiv");
  var table = ""
  
  if (sessionindex == "") {
    session = {}
    session['id'] = ""
  } else if (sessionindex == "new") {
    session = {}
    sessionindex = "new" + newsessionindex
    newsessionindex = newsessionindex + 1
    session['id'] = sessionindex
  } else {
    session = eventlist[eventindex]['sessions'][sessionindex]
  }
  
  if (sessionindex){
    table = CreateSessionTable(eventindex, session)
  }
      
  if (sessionindex.substr(0,3) != "new") {
    instancesexist = LoadInstances(eventindex, session['id']);
  }
  
  if (sessionindex && !instancesexist  && sessionindex.substr(0,3) != "new" && !showallinstances) {
    table.style.display = "None"
    return
  }
  
  var addinstance = document.createElement("BUTTON");

  addinstance.type = "button";
  addinstance.name = "addrows";
  addinstance.className = "button";
  addinstance.innerHTML = "Add Instance";
  addinstance.setAttribute('onclick', "AddInstance('" + session['id'] + "')")
  sessionsdiv.appendChild(document.createElement("BR"))
  sessionsdiv.appendChild(addinstance)
  sessionsdiv.appendChild(document.createElement("BR"))

}

function CreateSessionTable(eventindex, session) { 
  var sessiontable = document.createElement("TABLE");
  sessiontable.id = "sessiontable"
  sessiontable.className = "eventsession"
  sessionsdiv.appendChild(sessiontable)
  
  var head = sessiontable.createTHead()
  head.className = "datasheet"
  var headerrow = head.insertRow()
  
  var body = sessiontable.createTBody()
  body.className = "datasheet"
  var row2 = body.insertRow()
  row2.className = "even"
  
  var idhead = document.createElement("TH")
  idhead.innerHTML = "ID"
  idhead.className = "sessiondatasheet"
  headerrow.appendChild(idhead)

  idtextcell = document.createElement("TH");
  idtextcell.innerHTML = session['id'];
  idtextcell.className = "sessiondatasheet"
  row2.appendChild(idtextcell)
  
  idhidden = document.createElement("INPUT")
  idhidden.type = "hidden"
  idhidden.value = session['id']
  idhidden.name = "sessionid"
  idtextcell.appendChild(idhidden);

  var namehead = document.createElement("TH")
  namehead.innerHTML = "Name"
  namehead.className = "sessiondatasheet"
  headerrow.appendChild(namehead)

  nametextcell = row2.insertCell(1);
  nametext = document.createElement("INPUT")
  nametext.type = "textbox"
  nametext.value = ((session['name'])?session['name']:"")
  nametext.id = "sessionname"
  nametext.name = "sname"
  nametextcell.appendChild(nametext)

  var instructorhead = document.createElement("TH")
  instructorhead.innerHTML = "Instructor"
  instructorhead.className = "sessiondatasheet"
  headerrow.appendChild(instructorhead)

  instructortextcell = row2.insertCell(2);
  instructortext = document.createElement("INPUT")
  instructortext.type = "textbox"
  instructortext.value = ((session['instructor'])?session['instructor']:"")
  instructortext.id = "sessioninstructor"
  instructortext.name = "sinstructor"
  instructortextcell.appendChild(instructortext)

  var locationhead = document.createElement("TH")
  locationhead.innerHTML = "Location"
  locationhead.className = "sessiondatasheet"
  headerrow.appendChild(locationhead)

  locationtextcell = row2.insertCell(3);
  locationtext = document.createElement("INPUT")
  locationtext.type = "textbox"
  locationtext.value = ((session['location'])?session['location']:"")
  locationtext.id = "sessionlocation"
  locationtext.name = "slocation"
  locationtextcell.appendChild(locationtext)

  var costhead = document.createElement("TH")
  costhead.innerHTML = "Cost"
  costhead.className = "sessiondatasheet"
  headerrow.appendChild(costhead)

  costtextcell = row2.insertCell(4);
  costtext = document.createElement("INPUT")
  costtext.type = "textbox"
  costtext.value = ((session['cost'])?session['cost']:"")
  costtext.id = "sessioncost"
  costtext.name = "scost"
  costtextcell.appendChild(costtext)

  var noteshead = document.createElement("TH")
  noteshead.innerHTML = "Notes"
  noteshead.className = "sessiondatasheet"
  headerrow.appendChild(noteshead)

  notestextcell = row2.insertCell(5);
  notestext = document.createElement("TEXTAREA")
  notestext.type = "textbox"
  notestext.innerHTML = ((session['notes'])?session['notes']:"")
  notestext.id = "sessionnotes"
  notestext.name = "snotes"
  notestextcell.appendChild(notestext)
  
  
  return sessiontable

}

function LoadInstances(eventindex, sessionid) {
  var sessionsdiv = document.getElementById("sessionsdiv");
  var table = document.createElement("TABLE");
  table.id = "session".concat(sessionid)
  table.className = "eventinstance"
  sessionsdiv.appendChild(table)

  var head = table.createTHead()
  head.className = "datasheet"
  var headerrow = head.insertRow()
  
  var idhead = document.createElement("TH")
  idhead.innerHTML = "ID"
  idhead.className = "datasheet"
  headerrow.appendChild(idhead)
  
  var namehead = document.createElement("TH")
  namehead.innerHTML = "Name"
  namehead.className = "datasheet"
  headerrow.appendChild(namehead)
  
  var datehead = document.createElement("TH")
  datehead.innerHTML = "Date"
  datehead.className = "datasheet"
  headerrow.appendChild(datehead)
  
  var starthead = document.createElement("TH")
  starthead.innerHTML = "Start Time"
  starthead.className = "datasheet"
  headerrow.appendChild(starthead)
  
  var endhead = document.createElement("TH")
  endhead.innerHTML = "End Time"
  endhead.className = "datasheet"
  headerrow.appendChild(endhead)
  
  var instrhead = document.createElement("TH")
  instrhead.innerHTML = "Instructor"
  instrhead.className = "datasheet"
  headerrow.appendChild(instrhead)
  
  var costhead = document.createElement("TH")
  costhead.innerHTML = "Cost"
  costhead.className = "datasheet"
  headerrow.appendChild(costhead)
  
  var noteshead = document.createElement("TH")
  noteshead.innerHTML = "Notes"
  noteshead.className = "datasheet"
  headerrow.appendChild(noteshead)
  
  var signinhead = document.createElement("TH")
  signinhead.innerHTML = "Sign-in"
  signinhead.className = "datasheet"
  headerrow.appendChild(signinhead)
  
  var cancelhead = document.createElement("TH")
  cancelhead.innerHTML = "Cancel"
  cancelhead.className = "datasheet"
  headerrow.appendChild(cancelhead)
  
  nosessions = true
  if (eventindex) {
    eventlist[eventindex]['instances'].sort(eval(compareDate))
    for (index in eventlist[eventindex]['instances']){
      if (eventlist[eventindex]['instances'][index]['sessionid'] == sessionid && (showallinstances || eventlist[eventindex]['instances'][index]['date'] > lastmonth)) {
        addInstanceRow(eventlist[eventindex]['instances'][index], sessionid, table)
        nosessions = false
      }
    }
  }
  if (nosessions) { table.style.display = "None"; return false}
  
  return true
  
}

function addInstanceRow(instance, sessionid, table) {
  var row = table.insertRow(-1);
  var idcell = document.createElement("TH")
  row.appendChild(idcell)
  var namecell = row.insertCell(1);
  var datecell = row.insertCell(2);
  var startcell = row.insertCell(3);
  var endcell = row.insertCell(4);
  var instructorcell = row.insertCell(5);
  var costcell = row.insertCell(6);
  var notescell = row.insertCell(7);
  var signincell = row.insertCell(8);
  var cancelcell = row.insertCell(9);
  
  row.className = "even";

  idcell.innerHTML = ((instance['id'])?(instance['id']):(''))
  idcell.className = "datasheet"
  var idinput = document.createElement("INPUT");
  idinput.type = "hidden";
  idinput.name = "instanceid";
  idinput.value = ((instance['id'])?(instance['id']):(''));  //This is an inline if statement (if a then b else c) == a?b:c
  idcell.appendChild(idinput);

  var sessionidinput = document.createElement("INPUT");
  sessionidinput.type = "hidden";
  sessionidinput.name = "isessionid";
  sessionidinput.value = sessionid
  idcell.appendChild(sessionidinput);
  
  var nameinput = document.createElement("INPUT");
  nameinput.type = "text";
  nameinput.name = "iname";
  nameinput.value = ((instance['name'])?(instance['name']):(''));
  namecell.appendChild(nameinput);
  
  var dateinput = document.createElement("INPUT");
  dateinput.type = "date";
  dateinput.className = "datasheet";
  dateinput.name = "idate";
  dateinput.value = ((instance['date'])?(instance['date']):(''));
  datecell.appendChild(dateinput);
  
  var startinput = document.createElement("INPUT");
  startinput.type = "time";
  startinput.name = "istarttime";
  startinput.value = ((instance['starttime'])?(instance['starttime']):(''));
  startcell.appendChild(startinput);
  
  var endinput = document.createElement("INPUT");
  endinput.type = "time";
  endinput.name = "iendtime";
  endinput.value = ((instance['endtime'])?(instance['endtime']):(''));
  endcell.appendChild(endinput);
  
  var instructorinput = document.createElement("INPUT");
  instructorinput.type = "text";
  instructorinput.name = "iinstructor";
  instructorinput.value = ((instance['instructor'])?(instance['instructor']):(''));
  instructorcell.appendChild(instructorinput);
  
  var costinput = document.createElement("INPUT");
  costinput.type = "text";
  costinput.name = "icost";
  costinput.value = ((instance['cost'])?(instance['cost']):(''));
  costcell.appendChild(costinput);
  
  var notesinput = document.createElement("TEXTAREA");
  notesinput.name = "inotes";
  notesinput.innerHTML = ((instance['notes'])?(instance['notes']):(''));
  notescell.appendChild(notesinput);
    
  signincell.innerHTML = "<a href='eventsignin?iid=" + instance['id'] + "'> Sign In Sheet </a>"
  
  var cancelspan = document.createElement("SPAN");
  cancelspan.id = "instancecancel" + cancelindex;
  
  cancelspan.className = "cursor";
  cancelspan.setAttribute('onclick', "ToggleHidden(this)")
  var cancelhidden = document.createElement("INPUT");
  cancelhidden.type = "hidden";
  cancelhidden.name = "icancel";
  cancelhidden.id = "hiddeninstancecancel" + cancelindex;
  if (instance['cancel']) {
    cancelhidden.value = 1;
    cancelspan.innerHTML = 'Restore';
  } else {
    cancelhidden.value = 0;
    cancelspan.innerHTML = 'Cancel';
  }
  cancelcell.appendChild(cancelspan);
  cancelcell.appendChild(cancelhidden);

  cancelindex = cancelindex + 1
  
  return;
}

function AddInstance(sessionid) {
  table = document.getElementById("session".concat(sessionid))
  table.style.display = "table"
  addInstanceRow([], sessionid, table)
}

function ChangeSubTab(li){
  var oldtab = document.getElementsByClassName("subactivetab");
  for (tab = 0; tab < oldtab.length; tab++) {
    var oldtabtable = document.getElementById(oldtab[tab].id + "table");
    if (oldtabtable) {
      oldtabtable.style.display = "None"
    }
    oldtab[tab].className = "subtab"
  }
  li.className = "subactivetab"
  var newtabtable = document.getElementById(li.id + "table");
    if (newtabtable) {
      newtabtable.style.display = "table"
    }
}

function ChangeRecurringSubTab(input){
  index = input.id.substr(6)
  weekofmonthrow = document.getElementById("weekofmonthrow" + index)
  
  if (input.value == "monthly") {
    weekofmonthrow.style.display = "table-row"
  } else if (input.value == "weekly") {
    weekofmonthrow.style.display = "None"
  }
}

function CreateRecurringTab(rindex) {
  index = recurringtabindex
  recurringtabindex++
  var eventmenu = document.getElementById("eventmenu");  
  var tablediv = document.getElementById("menuframe");
  
  var listitem = document.createElement("LI");
  listitem.className = "subtab";
  listitem.id = "recurring" + index
  listitem.setAttribute('onclick', "ChangeSubTab(this)")
  eventmenu.appendChild(listitem)
  
  var listspan = document.createElement("SPAN");
  if (rindex) {
    listspan.innerHTML = eventlist[eventindex]['recurrences'][rindex]['name']
  } else {
    listspan.innerHTML = "Recurrence" + index
  }
  listitem.appendChild(listspan)
  
  var table = document.createElement("TABLE");
  table.className = "addeventmenu";
  table.id = "recurring" + index + "table"
  table.style.display = "None"
  tablediv.appendChild(table)
  
  namerow = table.insertRow()
  namerow.id = "namerow" + index
  namelabelcell = namerow.insertCell()
  namelabelcell.className = "label"
  namelabelcell.style.width = "20%"
  
  var namelabel = document.createElement("LABEL");
  namelabel.htmlFor = "rname" + index
  namelabel.innerHTML = "Name:"
  namelabelcell.appendChild(namelabel)
  
  nameinputcell = namerow.insertCell()
  nameinputcell.className = "textbox"
  nameinputcell.style.width = "20%"
  
  var nameinput = document.createElement("INPUT");
  nameinput.id = "rname" + index
  nameinput.name = "rname" + index
  nameinput.type = "textbox"
  if (rindex) {
    nameinput.value = eventlist[eventindex]['recurrences'][rindex]['name']
  } 
  nameinputcell.appendChild(nameinput)
  
  var idinput = document.createElement("INPUT");
  idinput.type = "hidden";
  idinput.name = "rid" + index
  if (rindex) {
    idinput.value = eventlist[eventindex]['recurrences'][rindex]['id']
  } 
  nameinputcell.appendChild(idinput);

  if (eventindex && eventlist[eventindex]['sessions'].length > 0 ) {
    sessionrow = table.insertRow()
    sessionrow.id = "sessionrow" + index
    sessionlabelcell = sessionrow.insertCell()
    sessionlabelcell.className = "label"
    sessionlabelcell.style.width = "20%"
  
    var sessionlabel = document.createElement("LABEL");
    sessionlabel.htmlFor = "rsession" + index
    sessionlabel.innerHTML = "Session:"
    sessionlabelcell.appendChild(sessionlabel)
  
    sessioninputcell = sessionrow.insertCell()
    sessioninputcell.className = "textbox"
    sessioninputcell.style.width = "20%"
  
    var sessionselect = document.createElement("SELECT");
    sessionselect.id = "rsession" + index
    sessionselect.name = "rsession" + index
  
    sessionoption = document.createElement("OPTION");
    sessionoption.text = "None"
    sessionoption.value = 0
    sessionselect.add(sessionoption)

    for (sessionindex in eventlist[eventindex]['sessions']) {
      sessionoption = document.createElement("OPTION");
      sessionoption.text = eventlist[eventindex]['sessions'][sessionindex]['name']
      sessionoption.value = eventlist[eventindex]['sessions'][sessionindex]['id']
      if (rindex  && eventlist[eventindex]['recurrences'][rindex]['sessionid'] == eventlist[eventindex]['sessions'][sessionindex]['id']) {
        sessionoption.selected = true; 
      }
      sessionselect.add(sessionoption)
    }
    sessioninputcell.appendChild(sessionselect)
  }

  
  stylerow = table.insertRow()
  stylerow.id = "stylerow" + index
  stylelabelcell = stylerow.insertCell()
  stylelabelcell.className = "label"
  stylelabelcell.style.width = "20%"
  
  var stylelabel = document.createElement("LABEL");
  stylelabel.htmlFor = "rstyle" + index
  stylelabel.innerHTML = "Repeats:"
  stylelabelcell.appendChild(stylelabel)
  
  styleinputcell = stylerow.insertCell()
  styleinputcell.className = "textbox"
  styleinputcell.style.width = "20%"
  
  var styleselect = document.createElement("SELECT");
  styleselect.id = "rstyle" + index
  styleselect.name = "rstyle" + index
  styleselect.setAttribute('onchange', "ChangeRecurringSubTab(this)")
  
  monthlyoption = document.createElement("OPTION");
  monthlyoption.text = "Monthly"
  monthlyoption.value = "monthly"
  
  weeklyoption = document.createElement("OPTION");
  weeklyoption.text = "Weekly"
  weeklyoption.value = "weekly"
  
  if (rindex  && eventlist[eventindex]['recurrences'][rindex]['style'] == "weekly") {
    weeklyoption.selected = true; 
  } else {
    monthlyoption.selected = true;
  }
  styleselect.add(monthlyoption)
  styleselect.add(weeklyoption)
  styleinputcell.appendChild(styleselect)
  
  weekofmonthrow = table.insertRow()
  if (rindex  && eventlist[eventindex]['recurrences'][rindex]['style'] == "weekly") {
    weekofmonthrow.style.display = "None"; 
  }
  weekofmonthrow.id = "weekofmonthrow" + index
  weekofmonthlabelcell = weekofmonthrow.insertCell()
  weekofmonthlabelcell.className = "label"
  weekofmonthlabelcell.style.width = "20%"
  
  var weekofmonthlabel = document.createElement("SPAN");
  weekofmonthlabel.innerHTML = "Week of Month"
  weekofmonthlabelcell.appendChild(weekofmonthlabel)
  
  weekofmonthcell = weekofmonthrow.insertCell()
  weekofmonthcell.className = "textbox"
  weekofmonthcell.style.width = "20%"
  
  weekofmonthcheckbox = []
  weekofmonthlabel = []
  for (checkindex=1; checkindex<6; checkindex++) {
    weekofmonthcheckbox[checkindex] = document.createElement("INPUT");
    weekofmonthcheckbox[checkindex].type = "checkbox"
    weekofmonthcheckbox[checkindex].name = "rweekofmonth" + index
    weekofmonthcheckbox[checkindex].className = "ignore"
    weekofmonthcheckbox[checkindex].id = "rwom" + checkindex + index
    weekofmonthcheckbox[checkindex].value = "rwom" + checkindex + index
    if (rindex && eventlist[eventindex]['recurrences'][rindex]['weekofmonth'].match(checkindex)) {
      weekofmonthcheckbox[checkindex].checked = true
    }
    weekofmonthcell.appendChild(weekofmonthcheckbox[checkindex])
  
    weekofmonthlabel[checkindex] = document.createElement("LABEL");
    weekofmonthlabel[checkindex].htmlFor = "rwom" + checkindex + index
    weekofmonthlabel[checkindex].className = "ignore"
    weekofmonthlabel[checkindex].innerHTML = " " + checkindex + " "
    weekofmonthcell.appendChild(weekofmonthlabel[checkindex])
  }
  
  dayofweekrow = table.insertRow()
  dayofweekrow.id = "dayofweekrow" + index
  dayofweeklabelcell = dayofweekrow.insertCell()
  dayofweeklabelcell.className = "label"
  dayofweeklabelcell.style.width = "20%"
  
  var dayofweeklabel = document.createElement("SPAN");
  dayofweeklabel.innerHTML = "Day of Week"
  dayofweeklabelcell.appendChild(dayofweeklabel)
  
  dayofweekcell = dayofweekrow.insertCell()
  dayofweekcell.className = "textbox"
  dayofweekcell.style.width = "20%"
  
  dayofweekcheckbox = []
  dayofweeklabel = []
  
  dayofweekarray = ["S", "M", "T", "W", "R", "F", "S"]
  
  for (checkindex=0; checkindex<7; checkindex++) {
    dayofweekcheckbox[checkindex] = document.createElement("INPUT");
    dayofweekcheckbox[checkindex].type = "checkbox"
    dayofweekcheckbox[checkindex].name = "rdayofweek" + index
    dayofweekcheckbox[checkindex].className = "ignore"
    dayofweekcheckbox[checkindex].id = "rdow" + checkindex + index
    dayofweekcheckbox[checkindex].value = "rdow" + checkindex + index
    if (rindex && eventlist[eventindex]['recurrences'][rindex]['dayofweek'].match(checkindex)) {
      dayofweekcheckbox[checkindex].checked = true
    }
    dayofweekcell.appendChild(dayofweekcheckbox[checkindex])
  
    dayofweeklabel[checkindex] = document.createElement("LABEL");
    dayofweeklabel[checkindex].htmlFor = "rdow" + checkindex + index
    dayofweeklabel[checkindex].className = "ignore"
    dayofweeklabel[checkindex].innerHTML = " " + dayofweekarray[checkindex] + " "
    dayofweekcell.appendChild(dayofweeklabel[checkindex])
  }
  
  
  daterow = table.insertRow()
  daterow.id = "daterow" + index
  startdatelabelcell = daterow.insertCell()
  startdatelabelcell.className = "label"
  startdatelabelcell.style.width = "20%"
  
  var startdatelabel = document.createElement("LABEL");
  startdatelabel.htmlFor = "rstartdate" + index
  startdatelabel.innerHTML = "Start Date:"
  startdatelabelcell.appendChild(startdatelabel)
  
  startdateinputcell = daterow.insertCell()
  startdateinputcell.className = "textbox"
  startdateinputcell.style.width = "20%"
  
  var startdateinput = document.createElement("INPUT");
  startdateinput.id = "rstartdate" + index
  startdateinput.name = "rstartdate" + index
  startdateinput.type = "date"
  if (rindex) {
    startdateinput.value = eventlist[eventindex]['recurrences'][rindex]['startdate']
  }
  startdateinputcell.appendChild(startdateinput)
  
  enddatelabelcell = daterow.insertCell()
  enddatelabelcell.className = "label"
  enddatelabelcell.style.width = "20%"
  
  var enddatelabel = document.createElement("LABEL");
  enddatelabel.htmlFor = "renddate" + index
  enddatelabel.innerHTML = "End Date:"
  enddatelabelcell.appendChild(enddatelabel)
  
  enddateinputcell = daterow.insertCell()
  enddateinputcell.className = "textbox"
  enddateinputcell.style.width = "20%"
  
  var enddateinput = document.createElement("INPUT");
  enddateinput.id = "renddate" + index
  enddateinput.name = "renddate" + index
  enddateinput.type = "date"
  if (rindex) {
    enddateinput.value = eventlist[eventindex]['recurrences'][rindex]['enddate']
  }
  enddateinputcell.appendChild(enddateinput)
  
  timerow = table.insertRow()
  timerow.id = "timerow" + index
  starttimelabelcell = timerow.insertCell()
  starttimelabelcell.className = "label"
  starttimelabelcell.style.width = "20%"
  
  var starttimelabel = document.createElement("LABEL");
  starttimelabel.htmlFor = "rstarttime" + index
  starttimelabel.innerHTML = "Start Time:"
  starttimelabelcell.appendChild(starttimelabel)
  
  starttimeinputcell = timerow.insertCell()
  starttimeinputcell.className = "textbox"
  starttimeinputcell.style.width = "20%"
  
  var starttimeinput = document.createElement("INPUT");
  starttimeinput.id = "rstarttime" + index
  starttimeinput.name = "rstarttime" + index
  starttimeinput.type = "time"
  if (rindex) {
    starttimeinput.value = eventlist[eventindex]['recurrences'][rindex]['starttime']
  }
  starttimeinputcell.appendChild(starttimeinput)
  
  endtimelabelcell = timerow.insertCell()
  endtimelabelcell.className = "label"
  endtimelabelcell.style.width = "20%"
  
  var endtimelabel = document.createElement("LABEL");
  endtimelabel.htmlFor = "rendtime" + index
  endtimelabel.innerHTML = "End Time:"
  endtimelabelcell.appendChild(endtimelabel)
  
  endtimeinputcell = timerow.insertCell()
  endtimeinputcell.className = "textbox"
  endtimeinputcell.style.width = "20%"
  
  var endtimeinput = document.createElement("INPUT");
  endtimeinput.id = "rendtime" + index
  endtimeinput.name = "rendtime" + index
  endtimeinput.type = "time"
  if (rindex) {
    endtimeinput.value = eventlist[eventindex]['recurrences'][rindex]['endtime']
  }
  endtimeinputcell.appendChild(endtimeinput)
  
  applyrow = table.insertRow()
  applyrow.id = "applyrow" + index
  applyrow.insertCell()
  applyrow.insertCell()
  applyrow.insertCell()
  applybuttoncell = applyrow.insertCell()
  applybuttoncell.className = "label"
  
  var applybutton = document.createElement("INPUT");
  applybutton.type = "button"
  applybutton.className = "button"
  applybutton.value = "Apply"
  applybuttoncell.appendChild(applybutton)
  
  applybutton.setAttribute('onclick', "ApplyRecurrence(" + index + ");")
  
}

function ApplyRecurrence(rindex) {
  document.getElementById("reload").value = document.getElementById("id").value;
  document.getElementById("applyrindex").value = rindex;
  document.getElementById("addevent").submit();
  return
}

// ------------- Visit Admin ------------------

function LoadVisits() {
  var xmlhttp,xmldoc,patrons,i,j;
  
  if (window.XMLHttpRequest) {// code for IE7+, Firefox, Chrome, Opera, Safari
    xmlhttp=new XMLHttpRequest();
  }
  else {// code for IE6, IE5
    xmlhttp=new ActiveXObject("Microsoft.XMLHTTP");
  }
  
  xmlhttp.onreadystatechange=function() {
    if (xmlhttp.readyState==4 && xmlhttp.status==200) {
      response = JSON.parse(xmlhttp.responseText);
      visitlist = response
      reversesort = true;
      FillVisitTable();
    }
  }

  xmlhttp.open("GET","/getvisits.json",true, sortby = 'vid');
  xmlhttp.send();
}

function FillVisitTable() {
      var table = document.getElementById("visitlist");

      for (var i = table.rows.length-1; i>0; i--) {
        table.deleteRow(i);
      }
            
      secondsort = false;
      if (currentsort) visitlist.sort(eval(currentsort));
      if (reversesort) {
        visitlist.reverse()
      }
      
      for (visit in visitlist) {
          var row = table.insertRow(-1);
          var vidcell = row.insertCell(0);
          var datecell = row.insertCell(1);
          var hidcell = row.insertCell(2);
          var patroncell = row.insertCell(3);
          var eventcell = row.insertCell(4);
          
          if (visit % 2 == 0) {
            row.className = "odd";
          }
          else {
            row.className = "even";
          }

          vidcell.innerHTML = "<span class='blacklink' id=" + visitlist[visit]['vid'] + " onclick='LoadVisit(" + visitlist[visit]['vid'] + ", \"" + visitlist[visit]['date'] + "\");'>" + visitlist[visit]['vid'] + "</span>";
          datecell.innerHTML = visitlist[visit]['date'];
          hidcell.innerHTML = "<span class='blacklink' id=" + visitlist[visit]['hid'] + " onclick='LoadHousehold(" + visitlist[visit]['hid'] + ")'>" + visitlist[visit]['hid'] + "</span>";
          for (patron in visitlist[visit]['patronnames']) {
            if (patroncell.innerHTML == ""){
              patroncell.innerHTML = patron + ": " + visitlist[visit]['patronnames'][patron];
            } else {
              patroncell.innerHTML = patroncell.innerHTML + "<br>" + patron + ": " + visitlist[visit]['patronnames'][patron];
            }
          }
          for (event in visitlist[visit]['eventnames']) {
            var eventidspan = document.createElement("SPAN")
            if (eventcell.innerHTML != ""){
              eventcell.innerHTML = eventcell.innerHTML + "<br>";
            }
            eventidspan.innerHTML = event+ ": " + visitlist[visit]['eventnames'][event];
//             eventidspan.className = "blacklink";
            eventcell.appendChild(eventidspan)
         }
      }
}

function LoadVisit(id, tdate){
  date = tdate
  for (visit in visitlist){
    if (visitlist[visit]['vid'] == id) {
      visitindex = visit
      break
    }
  }
  Overlay('/adminvisit?visitid=' + id, "visit")
}

function FillVisitTD(date) {
  var eventcell = document.getElementById("eventcell");
  eventcell.innerHTML = ""
  var eventchoices = []
  for (event in eventlist) {
    showevent = false
    if (visitindex && visitlist[visitindex]['eventids'].indexOf(eventlist[event]['id']) >= 0 ) {
      if (visitlist[visitindex]['instanceids'][eventlist[event]['id']].length == 0) {
        showevent = true
      }
    }
    if (eventlist[event]['alwaysshow'] || showevent) {
      var eventinput = document.createElement("INPUT");
      eventinput.type = "checkbox";
      eventinput.name = "event" + eventlist[event]['id'];
      eventinput.id = "event" + eventlist[event]['id'];
      if (visitindex) {
        if (visitlist[visitindex]['eventids'].indexOf(eventlist[event]['id']) >= 0) {
          eventinput.checked = true;
        }
      } else if (eventlist[event]['name'] == "Family Resource Center") {
        eventinput.checked = true;
      }

      var eventlabel = document.createElement("LABEL");

      var eventspan = document.createElement("SPAN");
      eventspan.innerHTML = eventlist[event]['name']
      eventspan.style.width = '80%';

      eventlabel.appendChild(eventinput);
      eventlabel.appendChild(eventspan);
      eventcell.appendChild(eventlabel);
      eventcell.appendChild(document.createElement("BR"));
    } else {
      eventchoices.push([eventlist[event]['name'], eventlist[event]['id']])
    }
  }
  for (event in eventlist) {
    for (instance in eventlist[event]['instances']) {
      cancel = false
      checked = false
      if (visitindex && visitlist[visitindex]['eventids'].indexOf(eventlist[event]['id']) >= 0 ) {
        if (visitlist[visitindex]['instanceids'][eventlist[event]['id']].indexOf(eventlist[event]['instances'][instance]['id']) >= 0) {
          checked = true
        }
      }
      if ((eventlist[event]['instances'][instance]['date'] == date || checked) && !eventlist[event]['instances'][instance]['cancel']) {
        sessionname = ""
        if (eventlist[event]['instances'][instance]['sessionid']) {
          for (session in eventlist[event]['sessions']){
            if (eventlist[event]['sessions'][session]['id'] == eventlist[event]['instances'][instance]['sessionid']) {
              if (eventlist[event]['sessions'][session]['cancel']) { cancel = true }         
              if (eventlist[event]['sessions'][session]['name']) { sessionname = eventlist[event]['sessions'][session]['name'] }
            }
          }
        }
        if (cancel) {
          continue
        }
        
        var eventinput = document.createElement("INPUT");
        eventinput.type = "checkbox";
        eventinput.name = "event" + eventlist[event]['id'];
        eventinput.id = "event" + eventlist[event]['id'];
        if (visitindex) {
          if (checked){
            eventinput.checked = true
          }
        }

        var eventlabel = document.createElement("LABEL");
        
        var eventspan = document.createElement("SPAN");
        eventspan.style.width = '80%';

        if (sessionname && eventlist[event]['instances'][instance]['name']) {
          eventspan.innerHTML = eventlist[event]['name'] + " (" + sessionname + ": " + eventlist[event]['instances'][instance]['name'] + ")"
        } else if (sessionname) {
          eventspan.innerHTML = eventlist[event]['name'] + " (" + sessionname + ")"
        } else if (eventlist[event]['instances'][instance]['name']) {
          eventspan.innerHTML = eventlist[event]['name'] + " (" + eventlist[event]['instances'][instance]['name'] + ")"
        } else {
          eventspan.innerHTML = eventlist[event]['name']
        }

        var iidinput = document.createElement("INPUT");
        iidinput.type = "hidden";
        iidinput.name = "instance" + eventlist[event]['id'];
        iidinput.value = ((eventlist[event]['instances'][instance]['id'])?(eventlist[event]['instances'][instance]['id']):(''));  //This is an inline if statement (if a then b else c) == a?b:c

        eventlabel.appendChild(eventinput);
        eventlabel.appendChild(eventspan);
        eventcell.appendChild(eventlabel);
        eventcell.appendChild(iidinput);
        eventcell.appendChild(document.createElement("BR"));
        

      }
    }
  }

  var events = new autoComplete({
      selector: '#eventsuggest',
      minChars: 0,
      source: function(term, suggest){
          term = term.toLowerCase();
          var choices = eventchoices;
          var suggestions = [];
          for (i=0;i<choices.length;i++)
              if (~(choices[i][0]+' '+choices[i][1]).toLowerCase().indexOf(term)) suggestions.push(choices[i]);
          suggest(suggestions);
      },
      renderItem: function (item, search){
          search = search.replace(/[-\/\\^$*+?.()|[\]{}]/g, '\\$&amp;');
          var re = new RegExp("(" + search.split(' ').join('|') + ")", "gi");
          return '<div class="autocomplete-suggestion" event="'+item[0]+'" eventid="'+item[1]+'" data-val="'+search+'"> '+item[0].replace(re, "<b>$1</b>")+'</div>';
      },
      onSelect: function(e, term, item){
          console.log('Item "'+item.getAttribute('event')+' ('+item.getAttribute('eventid')+')" selected by '+(e.type == 'keydown' ? 'pressing enter' : 'mouse click')+'.');
          document.getElementById('eventsuggest').value = "";
          document.getElementById('eventsuggest').focus();
          document.getElementById('eventsuggest').blur();
          var newcheck = document.createElement("INPUT");
          newcheck.type = "checkbox";
          newcheck.name = "event" + item.getAttribute('eventid');
          newcheck.id = "event" + item.getAttribute('eventid');
          newcheck.checked = true;

          var newlabel = document.createElement("LABEL");
          newlabel.htmlFor = "event" + item.getAttribute('eventid');
          newlabel.style.width = "80%";
          newlabel.innerHTML = item.getAttribute('event');

          document.getElementById('eventcell').appendChild(newcheck);
          document.getElementById('eventcell').appendChild(newlabel);
      }
  });


}

// ------------- Sorts ------------------

function SortTable(sortby) {
      priorsort = currentsort;
      currentsort = sortby;
      if (priorsort == currentsort) {
        reversesort = !reversesort;
      } else {
        reversesort = false;
      }
}
      
function compareLast(a,b) {
  if (a['last']) { 
    af = a['last'].toLowerCase() 
  } else { 
    af = "" 
  }
  if (b['last']) { 
    bf = b['last'].toLowerCase() 
  } else { 
    bf = "" 
  }
  if (af < bf) return -1;
  if (af > bf) return 1;

  if (priorsort && !(secondsort)) {
    secondsort = true;
    return eval(priorsort)(a, b);
  }
  return 0;
}

function compareFirst(a,b) {
  if (a['first']) { 
    af = a['first'].toLowerCase() 
  } else { 
    af = "" 
  }
  if (b['first']) { 
    bf = b['first'].toLowerCase() 
  } else { 
    bf = "" 
  }
  if (af < bf) return -1;
  if (af > bf) return 1;

  if (priorsort && !(secondsort)) {
    secondsort = true;
    return eval(priorsort)(a, b);
  }
  return 0;
}

function compareID(a,b) {
  if (parseInt(a['id'], 10) < parseInt(b['id'], 10)) return -1;
  if (parseInt(a['id'], 10) > parseInt(b['id'], 10)) return 1;
  if (priorsort && !(secondsort)) {
    secondsort = true;
    return eval(priorsort)(a, b);
  }
  return 0;
}

function compareVID(a,b) {
  if (parseInt(a['vid'], 10) < parseInt(b['vid'], 10)) return -1;
  if (parseInt(a['vid'], 10) > parseInt(b['vid'], 10)) return 1;
  if (priorsort && !(secondsort)) {
    secondsort = true;
    return eval(priorsort)(a, b);
  }
  return 0;
}

function compareHID2(a,b) {
  if (parseInt(a['hid'], 10) < parseInt(b['hid'], 10)) return -1;
  if (parseInt(a['hid'], 10) > parseInt(b['hid'], 10)) return 1;
  if (priorsort && !(secondsort)) {
    secondsort = true;
    return eval(priorsort)(a, b);
  }
  return 0;
}

function compareDate(a,b) {
  if (a['date'] < b['date']) return -1;
  if (a['date'] > b['date']) return 1;
  if (priorsort && !(secondsort)) {
    secondsort = true;
    return eval(priorsort)(a, b);
  }
  return 0;
}

function compareHID(a,b) {
  for (var index in a['households']){
    if (a['households'][index]) {
      ahid = parseInt(a['households'][index]);
    } else {
      ahid = 0;
    }
    if (b['households'][index]) {
      bhid = parseInt(b['households'][index]);
    } else {
      bhid = 0;
    }
    if (ahid < bhid) return -1;
    if (ahid > bhid) return 1;
  }
  
  if (a['households'].length < b['households'].length) return -1;
  
  if (priorsort && !(secondsort)) {
    secondsort = true;
    return eval(priorsort)(a, b);
  }
  return 0;
}

function compareName(a,b) {
  if (a['name']) { 
    af = a['name'].toLowerCase() 
  } else { 
    af = "" 
  }
  if (b['name']) { 
    bf = b['name'].toLowerCase() 
  } else { 
    bf = "" 
  }
  if (af < bf) return -1;
  if (af > bf) return 1;

  if (priorsort && !(secondsort)) {
    secondsort = true;
    return eval(priorsort)(a, b);
  }
  return 0;
}

function compareInstructor(a,b) {
  if (a['instructor']) { 
    af = a['instructor'].toLowerCase() 
  } else { 
    af = "" 
  }
  if (b['instructor']) { 
    bf = b['instructor'].toLowerCase() 
  } else { 
    bf = "" 
  }
  if (af < bf) return -1;
  if (af > bf) return 1;

  if (priorsort && !(secondsort)) {
    secondsort = true;
    return eval(priorsort)(a, b);
  }
  return 0;
}

function compareCost(a,b) {
  if (a['cost']) { 
    af = a['cost'].toLowerCase() 
  } else { 
    af = "" 
  }
  if (b['cost']) { 
    bf = b['cost'].toLowerCase() 
  } else { 
    bf = "" 
  }
  if (af < bf) return -1;
  if (af > bf) return 1;

  if (priorsort && !(secondsort)) {
    secondsort = true;
    return eval(priorsort)(a, b);
  }
  return 0;
}

