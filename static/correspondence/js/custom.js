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

function addPerson(area) {
  var selectedUser = getSelectedOption(document.getElementById('user_selected'))
  let item = { user: {pk: selectedUser.value, username: selectedUser.text}, area: area}
  var tableUsers = document.getElementById('people_list')
  let row = tableUsers.insertRow(1)
  let cellUser = row.insertCell(0)
  let cellArea = row.insertCell(1)

  cellUser.innerHTML = item.user.username
                
  cellArea.innerHTML = item.area

  $('<input>', {
      type: 'hidden',
      id: 'selectedUser' + selectedUser.value,
      name: 'selectedUsersInput',
      value: selectedUser.value
  }).appendTo('form');

}

function setSearch(numId, url) {
  
  $.ajax({
      type: 'GET',
      url: url,
      data: {"filter_pk": numId},
      success: function (response) {
        $('#user_selected')
            .find('option')
            .remove()
            .end();
          response.forEach(function (value) {
            let op = $('<option>', {
                value: value.pk
            })
            op.text(value.username)
            op.appendTo("#user_selected");
          });
      },
      error: function (response) {
          console.log(response)
      }
  })
}
//   function setSearch(numId, name, parent_name, radicate, destination) {
//   console.log(numId, name, parent_name)
//   $('#headerForm').html(parent_name + '/' + name)
//   $('#searchpk').val(numId)
//   location.href = "/correspondence/" + destination + "/" + radicate + "/" + numId 
// }
function cleanSearch() {
  $('#headerForm').html('')
}
$(document).ready(function () {

  // $("#id_item" ).autocomplete({
  //   source: "/correspondence/autocomplete",
  // });

  //$('#id_current_user').selectpicker();
  //$('#id_person').selectpicker();

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
