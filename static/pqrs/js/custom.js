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

var filesUploadedCount = 0;

$('input[type="file"]').change(function(){

    if ($('#id_file_uploaded')[0].value != ''){

        var div = document.createElement('div');

        var clonedInputHtml = '<div class="form-control custom-file" style="border:0">' +
                                '<input type="file" name="file_uploaded" class="custom-file-input"'+
                                'id="id_file_uploaded'+filesUploadedCount+'" onchange="updateLabel(this), newInputFileField(this)">' + 
                                '<label class="custom-file-label text-truncate" for="id_file_uploaded'+filesUploadedCount+'">---</label>' + 
                              '</div>';

        div.innerHTML = clonedInputHtml;            

        ($("#id_file_uploaded").parents()[2]).appendChild(div);
        filesUploadedCount++;
    }
})

function updateLabel(element){
  if (typeof(document.getElementById(element.id).files[0]) != 'undefined'){
    var labelName = document.getElementById(element.id).files[0].name
  }
  else{
    labelName = "---"
  }
  $('label[for="'+element.id+'"]')[0].textContent = labelName
}

function newInputFileField(element){
  elementIdNumber = element.id.split('')[element.id.split('').length-1];
  nextElementIdNumber = parseInt(elementIdNumber) + 1;
  if (document.getElementById('id_file_uploaded'+nextElementIdNumber) == null){
    filesUploadedCount++;
    var div = document.createElement('div');
    div.setAttribute("class", "mt-2");

    var clonedInputHtml = '<div class="form-control custom-file" style="border:0">' +
                            '<input type="file" name="file_uploaded" class="custom-file-input"'+
                            'id="id_file_uploaded'+filesUploadedCount+'" onchange="updateLabel(this), newInputFileField(this)">' + 
                            '<label class="custom-file-label text-truncate" for="id_file_uploaded'+filesUploadedCount+'">---</label>' + 
                          '</div>';

    div.innerHTML = clonedInputHtml;            

    ($("#"+element.id).parents()[2]).appendChild(div);
    
  }
}