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