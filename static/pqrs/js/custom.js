function requestSender() {
  $.ajax({
    url: "/pqrs/multi-request/",
    type: "POST",
    data: $("#sender_create_form").serializeArray(),
    dataType: "json",
  });
}

$("#id_uploaded_files").fileinput({
  theme: 'fas',
  allowedFileExtensions: ['pdf','docx','png','jpg','jpeg'],
  overwriteInitial: true,
  maxFileSize:10000,
  language: 'es',
  slugCallback: function (filename) {
      return filename.replace('(', '_').replace(']', '_');
  }
});

$('#close-dialog').click(function (e) {
  e.preventDefault();
  $('#agreement-modal').modal('hide')
})

$('#link_agreement').click(function (e) {
  $('#agreement-modal').modal('show')
})

$(document).ready(function () {
  if ($("#tb_request_sender")) {
    $("#tb_request_sender").DataTable(
      {
        "scrollX": true,
        language: {
          "sProcessing": "Procesando...",
          "sLengthMenu": "Mostrar _MENU_ registros",
          "sZeroRecords": "No se encontraron resultados",
          "sEmptyTable": "Ningún dato disponible en esta tabla",
          "sInfo": "Mostrando registros del _START_ al _END_ de un total de _TOTAL_ registros",
          "sInfoEmpty": "Mostrando registros del 0 al 0 de un total de 0 registros",
          "sInfoFiltered": "(filtrado de un total de _MAX_ registros)",
          "sSearch": "",
          "sSearchPlaceholder": "Escriba una palabra clave para realizar la búsqueda...",
          "sInfoThousands": ",",
          "sLoadingRecords": "Cargando...",
          "oPaginate": {
            "sFirst": "Primero",
            "sLast": "Último",
            "sNext": "Siguiente",
            "sPrevious": "Anterior"
          },
          "oAria": {
            "sSortAscending": ": Activar para ordenar la columna de manera ascendente",
            "sSortDescending": ": Activar para ordenar la columna de manera descendente"
          },
          "buttons": {
            "copy": "Copiar",
            "colvis": "Visibilidad"
          }
        }
      }
    );
  }
});

