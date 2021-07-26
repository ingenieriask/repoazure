function requestSender() {
  $.ajax({
    url: "/pqrs/multi-request/",
    type: "POST",
    data: $("#sender_create_form").serializeArray(),
    dataType: "json",
  });
}

$("#id_uploaded_files").fileinput({
  theme: "fas",
  allowedFileExtensions: ["pdf", "docx", "png", "jpg", "jpeg"],
  overwriteInitial: true,
  maxFileSize: 10000,
  language: "es",
  slugCallback: function (filename) {
    return filename.replace("(", "_").replace("]", "_");
  },
});
$("#create_room_button").on("click", function (event) {
  name_room = $("#room_name").val();
  reference_name_creator = $("#name_reference").val();
  email_room = $("#email_room").val();

  $.ajax({
    url: "/pqrs/create-room/",
    data: {
      csrfmiddlewaretoken: $("input[name=csrfmiddlewaretoken]").val(),
      name_room: name_room,
      reference_name_creator: reference_name_creator,
      email_room: email_room,
    },
    type: "POST",

    success: function (data) {
      if (data != "False") {
        $("#crate-room-form").remove();
        $("#chat-submit").prop("disabled", false);
        localStorage.setItem("user_id_room", reference_name_creator);
        localStorage.setItem("char-room-id", data);
        $("#room_id").val(data);
        $("#name_create_user").val(reference_name_creator);
        socketClient = new WebSocket(
          "ws://" + window.location.host + "/ws/some_url/" + localStorage.getItem("char-room-id") + "/"
        );
        socketClient.onmessage = function (event) {
          var arrive = JSON.parse(event.data);
          arrive = arrive["payload"];
          generate_message(arrive["message"], arrive["user"]);
        };
      }
    },
  });
  console.log(name_room, reference_name_creator, email_room);
});
$(document).ready(function () {
  if (document.getElementById("tb_request_creator")) {
    $("#tb_request_creator").dataTable({
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
  if (localStorage.getItem("char-room-id")) {
    $("#crate-room-form").remove();
    $("#chat-submit").prop("disabled", false);
    $("#room_id").val(localStorage.getItem("char-room-id"));
    $("#name_create_user").val(localStorage.getItem("user_id_room"));
    socketClient = new WebSocket(
      "ws://" + window.location.host + "/ws/some_url/" + localStorage.getItem("char-room-id") + "/"
    );
    socketClient.onmessage = function (event) {
      var arrive = JSON.parse(event.data);
      arrive = arrive["payload"];
      generate_message(arrive["message"], arrive["user"]);
    };
  }
});
