function requestSender() {
  $.ajax({
    url: "/pqrs/multi-request/",
    type: "POST",
    data: $("#sender_create_form").serializeArray(),
    dataType: "json",
  });
}
$(document).ready(function () {
  if ($("#tb_request_sender")) {
    $("#tb_request_sender").DataTable();
  }
});
