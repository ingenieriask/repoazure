$(function () {
    var start = moment();
    var end = moment();

    function cb(start,end) {
        $("#reportrange span").html(
            start.format("MM/DD/YYYY")
        );
    }

    cb(start,end);
    
    // $("#reportrange").daterangepicker(
    //     {
    //         startDate: start,
    //         endDate: end,
    //         ranges: {
    //             Today: [moment(), moment()],
    //             Yesterday: [
    //                 moment().subtract(1, "days"),
    //                 moment().subtract(1, "days"),
    //             ],
    //             "Last 7 Days": [moment().subtract(6, "days"), moment()],
    //             "Last 30 Days": [moment().subtract(29, "days"), moment()],
    //             "This Month": [
    //                 moment().startOf("month"),
    //                 moment().endOf("month"),
    //             ],
    //             "Last Month": [
    //                 moment().subtract(1, "month").startOf("month"),
    //                 moment().subtract(1, "month").endOf("month"),
    //             ],
    //         },
    //     },
    //     cb
    // );



    // $('#reportrange').daterangepicker({
    //   singleDatePicker: true,
    //   showDropdowns: true,
    //   minYear: 1901,
    //   maxYear: parseInt(moment().format('YYYY'),10),
    //   startDate: moment()
    // }, function(start, end, label) {
    //   var years = moment().diff(start, 'years');
    //   alert("You are " + years + " years old!");
    // });


    $('#reportrange').daterangepicker({
    "singleDatePicker": true,
    "locale": {
        "format": "MM/DD/YYYY",
        "separator": " - ",
        "applyLabel": "Aplicar",
        "cancelLabel": "Cancelar",
        "fromLabel": "Desde",
        "toLabel": "Hasta",
        "customRangeLabel": "Custom",
        "weekLabel": "W",
        "daysOfWeek": [
            "Dom",
            "Lun",
            "Mar",
            "Mie",
            "Jue",
            "Vie",
            "Sab"
        ],
        "monthNames": [
            "Enero",
            "Febrero",
            "Marzo",
            "Abril",
            "Mayo",
            "Junio",
            "Julio",
            "Agosto",
            "Septiembre",
            "Octubre",
            "Noviembre",
            "Diciembre"
        ],
        "firstDay": 1
    },
    "startDate": moment(),
    "endDate": moment()
}, function(start, end, label) {
  cb(start, end);
  console.log('New date range selected: ' + start.format('MM/DD/YYY') + ' to ' + end.format('MM/DD/YYY') + ' (predefined range: ' + label + ')');
});

});
