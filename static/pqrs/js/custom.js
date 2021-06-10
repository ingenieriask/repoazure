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

$("#id_files_uploaded").fileinput({
  theme: 'fas',
  allowedFileExtensions: ['pdf','docx','png','jpg','jpeg'],
  overwriteInitial: true,
  maxFileSize:2000,
  language: 'es',
  slugCallback: function (filename) {
      return filename.replace('(', '_').replace(']', '_');
  }
});