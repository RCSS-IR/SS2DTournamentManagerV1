
// --------- table-sort-search-json -----------

var table_full = document.getElementById('admin-table');
var table_body = document.getElementById('admin-table-body');
var search_input = document.getElementById('team-search');
let tableColumns = document.getElementsByClassName('table-column');
var def_tableData = tableToJson(table_full);
var tableData = def_tableData;

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
  tableData.sort(sort_by(field, reverse));

  populateTable();
}

function populateTable() {
  table_body.innerHTML = '';

  for (let data of tableData) {
    let row = table_body.insertRow(-1);
    let name = row.insertCell(0);
    name.outerHTML = "<th>" + data.teamname + "</th>";

    let username = row.insertCell(1);
    username.innerHTML = data.username;

    let password = row.insertCell(2);
    password.innerHTML = data.password;

    let email = row.insertCell(3);
    email.innerHTML = data.email;

    let type = row.insertCell(4);
    type.innerHTML = data.type;
    
    let last_upload = row.insertCell(5);
    last_upload.innerHTML = data.lastupload;

    let status = row.insertCell(6);
    status.innerHTML = data.status;

    let action = row.insertCell(7);
    action.innerHTML = data.action;
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
