function requestSender() {
  $.ajax({
    url: "/pqrs/multi-request/",
    type: "POST",
    data: $("#sender_create_form").serializeArray(),
    dataType: "json",
    success: function (data) {
      if (data["success"]) {
        var datos = data["data"];
        $("#form_container").prop("hidden", false);
        var newrow =
          "<tr>" +
          "<td class='text-center'>" +
          datos["name"] +
          " " +
          datos["lasts_name"] +
          "</td>" +
          "<td class='text-center'>" +
          data["document_type_abbr"] +
          " " +
          datos["document_number"] +
          "</td>" +
          "<td class='d-flex'>" +
          '<input type="button" value="Modificar" class="btn btn-success mx-auto" ' +
          "onclick='modifyRequest(\"" +
          datos["document_number"] +
          "\")'/>" +
          '<input type="button" value="Eliminar" class="btn btn-danger mx-auto" ' +
          "onclick='deleteRequest(\"" +
          datos["document_number"] +
          "\",this)'/>" +
          "</td>" +
          "</tr>";
        localStorage.setItem(String(datos["document_number"]), JSON.stringify(datos));
        $("#tb_request_sender").append(newrow);
        $("#sender_create_form").trigger("reset");
      }
    },
    error: function () {
      console.log("fuck");
    },
  });
}
function modifyRequest(id) {
  var retrievedObject = JSON.parse(window.localStorage.getItem(id));
  $('input[name="name"]').val(retrievedObject["name"]);
  $('input[name="lasts_name"]').val(retrievedObject["lasts_name"]);
  $('input[name="document_number"]').val(retrievedObject["document_number"]);
  $('input[name="email"]').val(retrievedObject["email"]);
  $('input[name="email_confirmation"]').val(retrievedObject["email_confirmation"]);
  $('input[name="phone_number"]').val(retrievedObject["phone_number"]);
  $('input[name="address"]').val(retrievedObject["address"]);
  $('input[name="expedition_date"]').val(retrievedObject["expedition_date"]);
  console.log(retrievedObject);
}

function deleteRequest(id, objeto) {
  $(objeto).parent().parent().remove();
  localStorage.removeItem(id);
}
