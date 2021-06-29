function getSelectedOption(sel) {
  var opt;
  for ( var i = 0, len = sel.options.length; i < len; i++ ) {
      opt = sel.options[i];
      if ( opt.selected === true ) {
          break;
      }
  }
  return opt;
}

function validatePersonExists(pk) {
  var exists = false
  $("input[name='selectedUsersInput']").each(function(idx, elem) {
    if ($(elem).val() == pk)
      exists = true
  });
  return exists
}

function deleteRow(btn, pk) {
  var row = btn.parentNode.parentNode;
  row.parentNode.removeChild(row);

  $("input[name='selectedUsersInput']").each(function(idx, elem) {
    if ($(elem).val() == pk)
      $(elem).remove()
  });
}

function addPerson() {
  var selectedUser = getSelectedOption(document.getElementById('user_selected'))
  if (selectedUser === undefined || selectedUser.value == -1) {
    window.alert('Por favor seleccione el usuario a agregar')
    return
  }
  if (validatePersonExists(selectedUser.value)) {
    window.alert('la persona ya existe')
    return
  }
  let item = { user: {pk: selectedUser.value, username: selectedUser.text}, area: $("#interest_area").val()}
  var tableUsers = document.getElementById('people_list')
  if (tableUsers) {
    let row = tableUsers.insertRow(1)
    let cellUser = row.insertCell(0)
    let cellArea = row.insertCell(1)
    let cellActions = row.insertCell(2)
  
    cellUser.innerHTML = item.user.username
                  
    cellArea.innerHTML = item.area
  
    cellActions.innerHTML = '<input class="fas fa-minus-circle fa-2x" type="button" value="Delete" onclick="deleteRow(this, ' + selectedUser.value + ')"/>'
  }

  $('<input>', {
      type: 'hidden',
      id: 'selectedUser' + selectedUser.value,
      name: 'selectedUsersInput',
      value: selectedUser.value
  }).appendTo('form');

}

function searchPeople(areaId, url, areaName) {
  
  $.ajax({
      type: 'GET',
      url: url,
      data: {"filter_pk": areaId},
      success: function (response) {
        $('#user_selected')
            .find('option')
            .remove()
            .end();
        $("#user_selected").append('<option value=-1>Ninguno seleccionado</option>')
        response.forEach(function (value) {
          $("#user_selected")
            .append('<option value=' + value.pk + '>'+ value.username + ' ' + value.first_name + ' ' + value.last_name + '</option>')
        });
        $("#user_selected").selectpicker('refresh');
        $("#headerForm").text(areaName)
        $("#interest_area").val(areaId)
      },
      error: function (response) {
          console.log(response)
      }
  })
}
function cleanSearch() {
  $('#headerForm').html('')
}
$(document).ready(function () {

  $("#id_document_file").fileinput({
    theme: 'fas',
    allowedFileExtensions: ['pdf', 'docx', 'png', 'jpg', 'jpeg'],
    overwriteInitial: true,
    maxFileSize: 20000,
    maxFilesNum: 1,
    language: 'es',
    slugCallback: function (filename) {
      return filename.replace('(', '_').replace(']', '_');
    }
  });

  $('#id_office').on('change', function (evt) {
    $('#id_doctype').html('<option>Example 1</option><option>Example2</option>').selectpicker('refresh');

  });

});
