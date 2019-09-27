async function reqJSON(method, url, data) {
  return new Promise((resolve, reject) => {
    let xhr = new XMLHttpRequest();
    xhr.open(method, url);
    xhr.responseType = 'json';
    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        resolve({status: xhr.status, data: xhr.response});
      } else {
        reject({status: xhr.status, data: xhr.response});
      }
    };
    xhr.onerror = () => {
      reject({status: xhr.status, data: xhr.response});
    };
    xhr.send(data);
  });
}


function addEvent(name, date) {
  $.ajax({
    type: 'POST',
    contentType: "application/json",
    url: '/event',
    data: JSON.stringify({Name: name,Date: date}),
    dataType: 'json',
    xhrFields: {
      withCredentials: true
    },
    success: buildPage
  });
}

/* {POST, /delete}
  Sends Event ID to delete event from database.  Arg: Event ID.
  Makes AJAX call to push JSON to server.  Rebuilds page upon success.
*/
function deleteEvent(id) {
    $.ajax({
      type: 'POST',
      contentType: 'application/json',
      url: '/delete',
      data: JSON.stringify({ID: id}),
      dataType: 'json',
      xhrFields: {
        withCredentials: true
      },
      success: buildPage
    });
}

/* {POST, /event}
  Takes inputs from form to create and add event to database.  Checks for empty
  input strings, then makes AJAX call to send event JSON.  Rebuilds pages on
  success.
*/
function validateSubmission() {
  name_value = document.getElementById('nameInput').value;
  date_value = document.getElementById('dateInput').value;

  if(name_value!=""&&date_value!=""){
    // Handle date inputs YYYY-MM-DD or MM-DD
    var new_date_value = handleDate(date_value);
    addEvent(name_value, new_date_value);
  }
  else{
    console.log("Submission ERROR: Empty form fields");
  }
  //Reset form fields
  document.getElementById('form').reset();
}

/*
  handleDate(DateStr). Arg: String from form input. Date. Returns new date string.
  If format is MM-DD, changes format to YYYY-MM-DD with proper year.
*/
function handleDate(dateStr) {
  const now = new Date().getTime();
  const year = new Date().getFullYear();
  const date = dateStr.split('-');

  if(date.length==2){
    var temp = new Date(year, Number.parseInt(date[0])-1, Number.parseInt(date[1]));
    if(temp-now<=0){
      var y = year+1;
      var new_date = y+'-'+date[0]+'-'+date[1];
      return new_date;
    }
    else{
      var new_date = year+'-'+date[0]+'-'+date[1];
      return new_date;
    }
  }
  else if (date.length==3) {
    return dateStr;
  }
  else {
    console.log("Invalid Date");
  }
}

/*
  Processes deletion from form submission.  Checks for all checkboxes.
  Each checkbox has an EventID as its value. Calls deleteEVent() for each
  checked event.
*/
function processDelete() {
  var check = document.getElementsByName("chkboxes");
  var del_select = [];

  for (i=0; i < check.length; i++) {
    if(check[i].checked) {
      del_select.push(check[i]);
    }
  }

  for (x=0; x < del_select.length; x++) {
    deleteEvent(del_select[x].value);
  }
}

/*
  Renders HTML page.  Gathers events from database and builds HTML string.
  Creates events table to inlcude checkboxes as input.  Then creates clock
  table for countdowns.
*/
function buildPage() {
  var clocks = [];
  reqJSON('GET','/events')
  .then(({status, data}) => {
    let html = '';
    index = 0;
    for (let event of data.events) {
      // Build HTML Form string with checkboxes per event
      html += '<tr><td><input type="checkbox" name="chkboxes" value="'+event.ID+'"></td><td>'+event.Name+'</td><td>'+ event.Date + '</td></tr>';
      clocks[index] = new Timer(event.Name, event.Date, event.ID);
      index++;
    }
    document.getElementById('event_table').innerHTML = html;

    // Build clocks and initiate timers
    // Check if clocks have begun.  If so, clear before rebuilding clocks.
    if (interval != 0) {
      clearInterval(interval);
      buildClocks(clocks);
    }
    else {
      buildClocks(clocks);
    }
  })
  .catch(({status, data}) => {
    // Display an error.
    document.getElementById('table_div').innerHTML = 'ERROR: ' +
      JSON.stringify(data);
  });
}

/*
  Called from buildPage() and builds clock table.  Arg: List of Timer objects.
  Initiates and sets interval for timer for each event.  Calls deleteEvent()
  when date passes.
*/
function buildClocks(clock_input) {
  interval = setInterval( function() {
    var clock_html = '';
    //iterate through clocks
    for (i=0; i<clock_input.length; i++) {
      var dateStr = clock_input[i].parseDate(clock_input[i].event_date);
      var current_time = new Date().getTime();
      var delta = dateStr - current_time;
      // if delta reaches below zero, delete event.
      if (delta <= 0) {
        //delete event and rebuild table
        deleteEvent(clock_input[i].event_id);
      }
      else{
        var timeStr = clock_input[i].updateTime(delta);
      }
      clock_html += '<tr><td>'+timeStr+'</td></tr>';
    }

    document.getElementById('clock_table').innerHTML = clock_html;
  }, 1000);
}

/*
  Timer object to store event name, date, and ID.  Used for initiating and
  updating timers.  Event data is used for deletion when necessary.
*/
class Timer {
  constructor(name, date, id) {
    this.event_name = name;
    this.event_date = date;
    this.event_id = id;
  }

  parseDate(datestr) {
    const [y, m, d] = datestr.split('-');
    return new Date(Number.parseInt(y), Number.parseInt(m)-1, Number.parseInt(d));
  }

  updateTime(diff) {
    var clock_str = '';

    // Calculate time.  1000ms/s. 60s/m. 60m/hr. 24hr/day.
    var days = Math.floor(diff / (1000*60*60*24));
    var hours = Math.floor((diff % (1000*60*60*24)) / (1000*60*60));
    var minutes = Math.floor((diff % (1000*60*60)) / (1000*60));
    var seconds = Math.floor((diff % (1000*60)) / 1000);

    // Return clock string
    clock_str = days+"d "+hours+"hr "+minutes+"min "+seconds+"s";
    return clock_str;
  }
}

var interval = 0;
document.addEventListener('DOMContentLoaded', () => {
  buildPage();
});
