$(function() {
  // Knowledge Area listbox handler
  $('#knowledge_areas').change(function() {
    var area_id = $('#knowledge_areas').val();
    var course_id = $('#__course_id').val();

    // Add Unit(s) button disable
    $('#add_units').attr('disabled', 'disabled')
    $('#learning_outcomes').empty();

    // Get Knowledge Units, based on val and fill Knowledge Units listbox
    lb = $('#knowledge_units');
    lb.empty();
    $.getJSON('/json', {'area_id': area_id, 'course_id': course_id}, function(units) {
      $.each(units, function(i, unit) {
        var item = $('<option/>');
        item.text('(' + unit.tier1 + ', ' + unit.tier2 + ') ' + unit.text);
        item.val(unit.id);
        lb.append(item);
      });
    });
  });

    // Knowledge Unit listbox handler
  $('#knowledge_units').change(function() {
    var unit_ids = $('#knowledge_units').val();

    // Add Unit(s) button enable/disable
    if(unit_ids.length > 0)
      $('#add_units').removeAttr('disabled')
    else
      $('#add_units').attr('disabled', 'disabled')

    // Get Learning Outcomes, based on KUs and fill Learning Outcomes listbox
    var table = $('#learning_outcomes');
    table.empty();

    var row = $('<tr/>');
    row.append($('<th/>').text('Tier'));
    row.append($('<th/>').text('Mastery'));
    row.append($('<th/>').text('Learning Outcome'));
    table.append(row);

    $.each(unit_ids, function(i, unit_id) {
      $.getJSON('/json', {'unit_id': unit_id}, function(outcomes) {
        $.each(outcomes, function(j, outcome) {
          row = $('<tr/>');
          row.append($('<td/>').text(outcome.tier));
          row.append($('<td/>').text(outcome.mastery));
          row.append($('<td/>').text(outcome.text));
          table.append(row);
        });
      });
    });
  });

  $('#course_delete').submit(function(e) {
    if(!confirm("Do you want to delete this course?"))
      e.preventDefault();
  });
});
