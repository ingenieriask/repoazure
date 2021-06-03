function requestSender() {
  var sender_data = $("#sender_create_form").serializeObject();
  if (sender_data["person_type"] != "1") {
    $("#alertMessageContainer").show();
    $("#alertMessageContent").html("Como persona Juridica solo se puede agregar una sola peticion");
  } else {
    $.ajax({
      url: "/pqrs/multi-request/",
      type: "POST",
      data: $("#sender_create_form").serializeArray(),
      dataType: "json",
      success: function (data) {
        createCellsTable(data, sender_data);
        localStorage.setItem(String(sender_data["document_number"]), JSON.stringify(sender_data));
        $("#sender_create_form").trigger("reset");
      },
    });
  }
}
function createCellsTable(data, sender_data) {
  if (data["success"]) {
    $("#form_container").prop("hidden", false);
    var trContainer = document.createElement("tr");
    var tdName = document.createElement("td");
    tdName.innerHTML = sender_data["name"] + " " + sender_data["lasts_name"];
    var tdDcoument = document.createElement("td");
    tdDcoument.innerHTML = data["document_type_abbr"] + " " + sender_data["document_number"];
    var tdAccion = document.createElement("td");
    var modButton = document.createElement("button");
    modButton.innerHTML = "Modificar";
    modButton.setAttribute("class", "btn btn-success mx-auto");
    modButton.setAttribute("onclick", "modifyRequest('" + sender_data["document_number"] + "')");
    var delButton = document.createElement("button");
    delButton.innerHTML = "Eliminar";
    delButton.setAttribute("class", "btn btn-danger mx-auto");
    delButton.setAttribute("onclick", "deleteRequest('" + sender_data["document_number"] + "',this)");
    tdAccion.appendChild(modButton);
    tdAccion.appendChild(delButton);
    trContainer.appendChild(tdName);
    trContainer.appendChild(tdDcoument);
    trContainer.appendChild(tdAccion);
    document.getElementById("tb_request_sender").appendChild(trContainer);
  } else {
    $("#alertMessageContainer").show();
    $("#alertMessageContent").html(data["data"]);
  }
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
