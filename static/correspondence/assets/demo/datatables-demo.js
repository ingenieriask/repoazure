// Call the dataTables jQuery plugin
$(document).ready(function() {
    $('#radicateListTable').DataTable({
      "order": [[ 0, 'desc' ]],
       "scrollX": true,
       language: {
        url: "https://cdn.datatables.net/plug-ins/1.10.22/i18n/Spanish.json"
      }
    });
    console.log("Table List Radicate ready !!!");

    $('#resultsSearchTable').DataTable({
      "order": [[ 0, 'asc' ]],
       "scrollX": true,
       language: {
        url: "https://cdn.datatables.net/plug-ins/1.10.22/i18n/Spanish.json"
      }
    });
    console.log("Table List ready !!!");
});

$(document).ready(function() {
    $('#dataTableActivity').DataTable({
        "order": [[ 0, 'desc' ]]
    });
});
