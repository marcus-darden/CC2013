$(function() {
  // Draw Core Content Coverage Chart
  var ajax_url = '/program/' + $('#__program_id').val() + '/coverage';
  $.getJSON(ajax_url, null, function(response) {
    $('#coverage_chart').highcharts(response);
  });

  // Confirm program deletion
  $('#program_delete').submit(function(e) {
    if(!confirm("Do you want to delete this program?"))
      e.preventDefault();
  });
});
