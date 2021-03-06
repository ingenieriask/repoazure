var socketClient;
var INDEX = 0;
function generate_message(msg, type) {
  new_type = "user";
  if (localStorage.getItem("user_id_room")) {
    if (type == localStorage.getItem("user_id_room")) {
      new_type = "self";
      $("#chat-input").val("");
    }
  } else {
    if (type == $("#name_create_user").val()) {
      new_type = "self";
      $("#chat-input").val("");
    }
  }

  INDEX++;
  var str = "";
  str += "<div id='cm-msg-" + INDEX + "' class=\"chat-msg " + new_type + '">';
  str += '          <span class="msg-avatar">';
  str += '            <img src="https://uctlanguagecentre.com/wp-content/uploads/2020/05/avatar.png">';
  str += "          </span>";
  str += '          <div class="cm-msg-text">';
  str += msg;
  str += "          </div>";
  str += "        </div>";
  $(".chat-logs").append(str);
  $("#cm-msg-" + INDEX)
    .hide()
    .fadeIn(300);

  $(".chat-logs")
    .stop()
    .animate({ scrollTop: $(".chat-logs")[0].scrollHeight }, 1000);
}

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
  var exists = false;
  $("input[name='selectedUsersInput']").each(function (idx, elem) {
    if ($(elem).val() == pk) exists = true;
  });
  return exists;
}

function deleteRow(btn, pk) {
  var row = btn.parentNode.parentNode;
  row.parentNode.removeChild(row);

  $("input[name='selectedUsersInput']").each(function (idx, elem) {
    if ($(elem).val() == pk) $(elem).remove();
  });
}

function addPerson() {
  var selectedUser = getSelectedOption(document.getElementById("user_selected"));
  if (selectedUser === undefined || selectedUser.value == -1) {
    window.alert("Por favor seleccione el usuario a agregar");
    return;
  }
  if (validatePersonExists(selectedUser.value)) {
    window.alert("la persona ya existe");
    return;
  }
  let item = { user: { pk: selectedUser.value, username: selectedUser.text }, area: $("#interest_area").val() };
  var tableUsers = document.getElementById("people_list");
  if (tableUsers) {
    let row = tableUsers.insertRow(1);
    let cellUser = row.insertCell(0);
    let cellArea = row.insertCell(1);
    let cellActions = row.insertCell(2);

    cellUser.innerHTML = item.user.username;

    cellArea.innerHTML = item.area;

    cellActions.innerHTML =
      '<div onclick="deleteRow(this, ' + selectedUser.value + ')"><i class="fas fa-minus-circle fa-2x"></i></div>';
  }

  $("<input>", {
    type: "hidden",
    id: "selectedUser" + selectedUser.value,
    name: "selectedUsersInput",
    value: selectedUser.value,
  }).appendTo("form");
}

var permissions = [];

function searchPeople(areaId, url, areaName, kindTask, target="#user_selected") {
  $.ajax({
    type: "GET",
    url: url,
    data: { filter_pk: areaId, kind_task: kindTask, permissions: permissions },
    success: function (response) {
      $(target).find("option").remove().end();
      $(target).append("<option value=-1>Ninguno seleccionado</option>");
      response.forEach(function (value) {
        $(target).append(
          "<option value=" +
            value.pk +
            ">[" +
            value.username +
            "] " +
            value.first_name +
            " " +
            value.last_name +
            "</option>"
        );
      });
      $(target).selectpicker("refresh");
      $("#headerForm").text(areaName);
      $("#interest_area").val(areaId);
      $(target + "_area").val(areaId);
    },
    error: function (response) {
      console.error(response);
    },
  });
}
function cleanSearch() {
  $("#headerForm").html("");
}
function descriptionPersonRequest(name, personType, dateDoc, docType, docNumber, address, email, city, phoneNumber) {
  $("#containerpersonRequest").removeClass("d-none");
  $("#contTypePerson").html(personType);
  $("#contNameLastName").html(name);
  $("#contDocNum").html(docNumber);
  $("#contDocType").html(docType);
  $("#contAddress").html(address);
  $("#contDate").html(dateDoc);
  $("#contPhoneNumber").html(phoneNumber);
  $("#contDepMuni").html(city);
  $("#contMail").html(email);
}
function loaderBTN() {
  $("#loading").show();
}
function defTablePaginator(tableName, formName, id_limit_form, id_magic_word) {
  $("#" + tableName).DataTable({
    scrollX: true,
    language: {
      sProcessing: "Procesando...",
      sLengthMenu: "Mostrar _MENU_ registros",
      sZeroRecords: "No se encontraron resultados",
      sEmptyTable: "Ning??n dato disponible en esta tabla",
      sInfo: "Mostrando registros del _START_ al _END_ de un total de _TOTAL_ registros",
      sInfoEmpty: "Mostrando registros del 0 al 0 de un total de 0 registros",
      sInfoFiltered: "(filtrado de un total de _MAX_ registros)",
      sSearch: "",
      sSearchPlaceholder: "Escriba una palabra clave para realizar la b??squeda...",
      sInfoThousands: ",",
      sLoadingRecords: "Cargando...",
      oPaginate: {
        sFirst: "Primero",
        sLast: "??ltimo",
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
  $('select[name="' + tableName + '_length"] option[value="' + $("#" + id_limit_form).attr("value") + '"]').prop(
    "selected",
    true
  );
  $('select[name="' + tableName + '_length"]').on("change", function () {
    value = this.value;
    $("#" + id_limit_form).attr("value", value);
    document.getElementById(formName).submit.click();
  });
  $("input[aria-controls='" + tableName + "']")
    .unbind()
    .attr("type", "text")
    .attr("value", "");
  let button_search = document.createElement("BUTTON");
  button_search.innerHTML = "Buscar";
  button_search.onclick = function () {
    const text_value = $("input[aria-controls='" + tableName + "']").val();
    $("#" + id_magic_word).attr("value", text_value);
    document.getElementById(formName).submit.click();
  };
  button_search.setAttribute("class", "btn btn-primary mx-2");
  document.getElementById(tableName + "_filter").appendChild(button_search);
}
$("#id_pqrs_type").on("change", function () {
  if (this.value) {
    token = $("input[name=csrfmiddlewaretoken]").val();
    $.ajax({
      type: "POST",
      url:  "../../../pqrs/bring-subtype/",
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
$("#bologna-list a").on("click", function (e) {
  e.preventDefault();
  $(this).tab("show");
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
  if (document.getElementById("tb_request_sender")) {
    defTablePaginator("tb_request_sender", "search-form", "id_limit_finder", "id_search_magic_word");
  }
  $("form").submit(function (e) {
    loaderBTN();
  });
});
$;

var el = document.querySelector(".notification");

function addNotification(activity, disable_url) {
  var count = Number(el.getAttribute("data-count")) || 0;
  el.setAttribute("data-count", count + 1);
  el.classList.remove("notify");
  el.offsetWidth = el.offsetWidth;
  el.classList.add("notify");
  if (count === 0) {
    el.classList.add("show-count");
  }

  $("#notification-list").append(
    `<a class="dropdown-item dropdown-notifications-item" href="` +
      activity.href +
      `" onclick="disableNotification('` +
      disable_url +
      `', ` +
      activity.pk +
      `)">
        <div class="dropdown-notifications-item-icon bg-warning"><i data-feather="` +
      'Nuevo evento' +
      `"></i></div>
        <div class="dropdown-notifications-item-content">
            <div class="dropdown-notifications-item-content-details">` +
      activity.icon +
      `</div>
            <div>` +
      activity.info +
      `</div>
        </div>
    </a>`
  );
}

function updateNotifications(url, disable_url) {
  var exec = function () {
    $.ajax({
      type: "GET",
      url: url,
      data: {},
      success: function (response) {
        $("#notification-list").html("");
        el.setAttribute("data-count", 0);
        el.classList.add("show-count");
        for (const act of response) addNotification(act, disable_url);
      },
      error: function (response) {
        console.error(response);
      },
    });
  }
  exec()
  setInterval(exec, 5000);
}

function disableNotification(url, pk) {
  $.ajax({
    type: "POST",
    url: url,
    data: { pk: pk },
    success: function (response) {
      //do nothing
    },
    error: function (response) {
      console.error(response);
    },
  });
}
$(window).on("load", function () {
  $("#loading").hide();
});
$(function () {
  $("#chat-submit").click(function (e) {
    e.preventDefault();
    var msg = $("#chat-input").val();
    var msg = $("#chat-input").val();
    if (msg.trim() == "") {
      return false;
    }
    var data = {
      user: $("#name_create_user").val(),
      message: msg,
    };
    socketClient.send(JSON.stringify(data));
    socketClient.onmessage = function (event) {
      var arrive = JSON.parse(event.data);
      arrive = arrive["payload"];
      generate_message(arrive["message"], arrive["user"]);
    };
  });
});
$("#close-dialog").click(function (e) {
  e.preventDefault();
  $("#agreement-modal").modal("hide");
});

$("#link_agreement").click(function (e) {
  $("#agreement-modal").modal("show");
});

$("#chat-circle").click(function () {
  $("#chat-circle").toggle("scale");
  $(".chat-box").toggle("scale");
});

$(".chat-box-toggle").click(function () {
  $("#chat-circle").toggle("scale");
  $(".chat-box").toggle("scale");
});

$("#response_click_button").on("click", function (event) {
  $("#crate-room-form").hide();
  $("#chat-submit").prop("disabled", false);
  $("#room_id").val($("#chat_respondle").val());
  socketClient = new WebSocket("ws://" + window.location.host + "/ws/some_url/" + $("#chat_respondle").val() + "/");
  socketClient.onmessage = function (event) {
    var arrive = JSON.parse(event.data);
    arrive = arrive["payload"];
    generate_message(arrive["message"], arrive["user"]);
  };
});
