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

var permissions = []

function searchPeople(areaId, url, areaName, kindTask) {
  
  $.ajax({
      type: 'GET',
      url: url,
      data: {"filter_pk": areaId, "kind_task": kindTask, "permissions": permissions},
      success: function (response) {
        console.info('response', response)
        $('#user_selected')
            .find('option')
            .remove()
            .end();
        $("#user_selected").append('<option value=-1>Ninguno seleccionado</option>')
        response.forEach(function (value) {
          $("#user_selected")
            .append('<option value=' + value.pk + '>['+ value.username + '] ' + value.first_name + ' ' + value.last_name + '</option>')
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
function descriptionPersonRequest(
  name,personType,dateDoc,docType,docNumber,
  address,email,city,phoneNumber){
  $('#containerpersonRequest').removeClass('d-none')
  $('#contTypePerson').html(personType)
  $('#contNameLastName').html(name)
  $('#contDocNum').html(docNumber)
  $('#contDocType').html(docType)
  $('#contAddress').html(address)
  $('#contDate').html(dateDoc)
  $('#contPhoneNumber').html(phoneNumber)
  $('#contDepMuni').html(city)
  $('#contMail').html(email)
}
function historyObservation(observation){
  $('#containerObservation').removeClass('d-none')
  $('#contObservation').html(observation)
}
$("#id_pqrs_type").on("change", function () {
  if (this.value) {
    token = $("input[name=csrfmiddlewaretoken]").val();
    console.log(this.value);
    $.ajax({
      type: "POST",
      url: "../bring-subtype/",
      data: {
        csrfmiddlewaretoken: token,
        pqrs_type: this.value,
      },
      success: function (response) {
        array = response.response;
        $("#id_pqrs_subtype").html("");
        $("#id_pqrs_subtype").append('<option value="" selected="">---------</option>');
        for (let index = 0; index < array.length; index++) {
          $("#id_pqrs_subtype").append(
            '<option value="' + array[index]["id"] + '" >' + array[index]["name"] + "</option>"
          );
        }
      },
    });
  }
});
$(document).ready(function () {
  if ($("#id_pqrs_subtype")) {
    $("#id_pqrs_subtype").html("");
  }
  $("#id_document_file").fileinput({
    theme: "fas",
    allowedFileExtensions: ["pdf", "docx", "png", "jpg", "jpeg"],
    overwriteInitial: true,
    maxFileSize: 20000,
    maxFilesNum: 1,
    language: "es",
    slugCallback: function (filename) {
      return filename.replace("(", "_").replace("]", "_");
    },
  });

  $("#id_office").on("change", function (evt) {
    $("#id_doctype").html("<option>Example 1</option><option>Example2</option>").selectpicker("refresh");
  });
  if ($("#tb_request_sender")) {
    $("#tb_request_sender").DataTable({
      scrollX: true,
      language: {
        sProcessing: "Procesando...",
        sLengthMenu: "Mostrar _MENU_ registros",
        sZeroRecords: "No se encontraron resultados",
        sEmptyTable: "Ningún dato disponible en esta tabla",
        sInfo: "Mostrando registros del _START_ al _END_ de un total de _TOTAL_ registros",
        sInfoEmpty: "Mostrando registros del 0 al 0 de un total de 0 registros",
        sInfoFiltered: "(filtrado de un total de _MAX_ registros)",
        sSearch: "",
        sSearchPlaceholder: "Escriba una palabra clave para realizar la búsqueda...",
        sInfoThousands: ",",
        sLoadingRecords: "Cargando...",
        oPaginate: {
          sFirst: "Primero",
          sLast: "Último",
          sNext: "Siguiente",
          sPrevious: "Anterior",
        },
        oAria: {
          sSortAscending: ": Activar para ordenar la columna de manera ascendente",
          sSortDescending: ": Activar para ordenar la columna de manera descendente",
        },
        buttons: {
          copy: "Copiar",
          colvis: "Visibilidad",
        },
      },
    });
  }
});
