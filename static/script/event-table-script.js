
// --------- table-sort-search-json -----------

var table_full = document.getElementById('event-table');
var table_body = document.getElementById('event-table-body');
var search_input = document.getElementById('event-search');
let tableColumns = document.getElementsByClassName('table-column');
var load_more = document.getElementById('load-more');
var def_tableData = tableToJson(table_full);
var tableData = def_tableData;

const loadBtn = document.getElementById('btn');
const spinner = document.getElementById('spinner');
const total = JSON.parse(document.getElementById('json-total').textContent);
const alert = document.getElementById('alert');

function loadmorePost() {
  var _current_item = $('.event-row').length
  const content_container = document.getElementById("event-table-body");
  $.ajax({
    url: 'event_viewer/load',
    type: 'GET',
    data: {
      'offset': _current_item
    },
    beforeSend: function () {
      loadBtn.classList.add('not-visible');
      spinner.classList.remove('not-visible');
    },
    success: function (response) {
      const data = response.events
      spinner.classList.add('not-visible')
      data.map(event => {
        console.log(event.id);
        content_container.innerHTML += `<tr class="event-row">
                                            <td> #${event.id} </td>
                                            <td> #${event.BaseID == -1 ? '0' : event.BaseID} </td>
                                            <td> ${event.Name} </td>
                                            <!-- <td> ${event.Type} </td> -->
                                            <td> ${event.User} </td>
                                            <td> ${event.IP} </td>
                                            <td> ${event.Date} </td>
                                            <td> ${event.Request_Type} </td>
                                            <td> ${event.Status} </td>
                                            <td> ${event.Features} </td>
                                          </tr>
                                        `
      })
      if (_current_item == total) {
        alert.classList.remove('not-visible');
      } else {
        loadBtn.classList.remove('not-visible');
      }
      setTimeout(function () { tableData = tableToJson(table_full); }, 500);
    },
    error: function (err) {
      console.log(err);
    },
  });
}

var carretDefaultClassName = 'fa-solid fa-arrows-up-down';
var caretUpClassName = 'fa-solid fa-arrow-up-wide-short';
var caretDownClassName = 'fa-solid fa-arrow-down-short-wide';


function tableToJson(table) {
  var data = [];

  // first row needs to be headers
  var headers = [];
  for (var i = 0; i < table.rows[0].cells.length; i++) {
    headers[i] = table.rows[0].cells[i].innerText.replace(/ /gi, '').toLowerCase();
  }

  // go through cells
  for (var i = 1; i < table.rows.length; i++) {

    var tableRow = table.rows[i];
    var rowData = {};

    for (var j = 0; j < tableRow.cells.length; j++) {

      rowData[headers[j]] = tableRow.cells[j].innerHTML;

    }

    data.push(rowData);
  }

  return data;
}

const sort_by = (field, reverse, primer) => {

  const key = primer ?
    function (x) {
      return primer(x[field]);
    } :
    function (x) {
      return x[field];
    };

  reverse = !reverse ? 1 : -1;

  return function (a, b) {
    return a = key(a), b = key(b), reverse * ((a > b) - (b > a));
  };
};

function sharpRemover(str){
  if (str.length > 0 && str[1] == '#'){
    str = str.substr(2, str.length);
    if (parseInt(str))
      str = parseInt(str);
  }
  return str;
};

function clearArrow() {
  let carets = document.getElementsByClassName('caret');
  for (let caret of carets) {
    caret.className = `caret ${carretDefaultClassName} `; //  
  }
}

function toggleArrow(event) {
  let element = event.target;
  let caret, field, reverse;
  if (element.tagName === 'SPAN') {
    caret = element.getElementsByClassName('caret')[0];
    field = element.innerText.replace(/ /gi, '').toLowerCase()
  }
  else {
    caret = element;
    field = element.parentElement.innerText.replace(/ /gi, '').toLowerCase()
  }


  let iconClassName = caret.className;
  clearArrow();
  if (iconClassName.includes(caretUpClassName)) {
    caret.className = `caret ${caretDownClassName}`;
    reverse = false;
  } else {
    reverse = true;
    caret.className = `caret ${caretUpClassName}`;
  }
  tableData.sort(sort_by(field, reverse, sharpRemover));

  populateTable();
}


function populateTable() {
  table_body.innerHTML = '';

  for (let data of tableData) {
    let row = table_body.insertRow(-1);
    row.className = 'event-row'
    let id = row.insertCell(0);
    id.innerHTML = data.id;

    let baseid = row.insertCell(1);
    baseid.innerHTML = data.baseid;

    let name = row.insertCell(2);
    name.innerHTML = data.name;

    let user = row.insertCell(3);
    user.innerHTML = data.user;

    let ip = row.insertCell(4);
    ip.innerHTML = data.ip;

    let date = row.insertCell(5);
    date.innerHTML = data.date;

    let request_type = row.insertCell(6);
    request_type.innerHTML = data.request_type;
  
    let status = row.insertCell(7);
    status.innerHTML = data.status;
  
    let features = row.insertCell(8);
    features.innerHTML = data.features;
  }

  filterTable();
}


function filterTable() {
  let filter = search_input.value.toUpperCase();
  rows = table_body.getElementsByTagName("tr");
  let flag = false;

  for (let row of rows) {
    let cells = row.getElementsByTagName("td");
    for (let cell of cells) {
      if (cell.textContent.toUpperCase().indexOf(filter) > -1) {
        if (filter) {
          cell.style.backgroundColor = 'yellow';
        } else {
          cell.style.backgroundColor = '';
        }

        flag = true;
      } else {
        cell.style.backgroundColor = '';
      }
    }

    if (flag) {
      row.style.display = "";
    } else {
      row.style.display = "none";
    }

    flag = false;
  }
}

for (let column of tableColumns) {
  column.addEventListener('click', function (event) {
    toggleArrow(event);
  });
}

search_input.addEventListener('keyup', function (event) {
  filterTable();
});


$(document).ready(function(){
	setTimeout(function(){ clearArrow(); });
});

loadBtn.addEventListener('click', () => {
  loadmorePost()
});
