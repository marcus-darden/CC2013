$(function() {
  // Fill the Learning Outcomes table based on a selected Knowledge Unit
  function show_unit_outcomes(unit_id) {
    // Get Learning Outcomes, from a Unit and fill Learning Outcomes listbox
    var $table = $('#learning_outcomes');
    $table.empty();
    $('#outcome_breadcrumb').html('');

    if(unit_id != 0) {
      // Build table header
      var $row = $('<tr/>');
      $row.append($('<th/>').text('Tier'));
      $row.append($('<th/>').text('Mastery'));
      $row.append($('<th/>').text('Learning Outcome'));
      $table.append($row);

      // Insert Learning Outcome rows
      $.getJSON('/json/unit_outcomes', {'unit_id': unit_id}, function(response) {
        $.each(response.outcomes, function(i, outcome) {
          row = $('<tr/>');
          row.append($('<td/>').text(outcome.tier));
          row.append($('<td/>').text(outcome.mastery));
          row.append($('<td/>').text(outcome.text));
          $table.append(row);
        });
        var area_id = $('#knowledge_areas').val();
        var ka = $('#knowledge_areas option[value=\'' + area_id + '\']').text();
        $('#outcome_breadcrumb').html(' - ' + response.unit.text + ' <small>(' + ka + ')</small>');
      });
    }
  }

  function fill_unit_listbox(listbox_id, units) {
    var $listbox = $(listbox_id);
    $listbox.empty();
    $.each(units, function(i, unit) {
      var $option = $('<option/>');
      $option.text('(' + unit.tier1 + ', ' + unit.tier2 + ') ' + unit.text);
      $option.val(unit.id);
      $listbox.append($option);
    });
  }

  function show_area_units(area_id) {
    var $areas = $('#knowledge_areas');

    // Ignore a non-change
    if(area_id == $areas.val()) {
      return;
    }

    // Set dropdown
    if(area_id == '') {
      area_id = $areas.val();
    } else {
      $areas.val(area_id);
    }

    // Fill listbox
    var course_id = $('#__course_id').val();
    $.getJSON('/json/unassigned_units', {'area_id': area_id, 'course_id': course_id}, function(units) {
      fill_unit_listbox('#unassigned_units', units);
    });
  }

  function show_course_content() {
    // Fill listbox
    var course_id = $('#__course_id').val();
    $.getJSON('/json/course_content', {'course_id': course_id}, function(units) {
      fill_unit_listbox('#course_content', units);
    });
  }

  // Knowledge Area dropdown handler  
  // AJAX query for Knowledge Units not assigned in this program,
  // then display them in the unassigned units listbox.
  $('#knowledge_areas').change(function() {
    var area_id = $('#knowledge_areas').val();
    show_area_units(area_id);

    // Clear Learning Outcomes and deselect Course Content
    show_unit_outcomes(0);
    $('#course_content').find('option').attr('selected', false);
  });

  // Unassigned Units listbox handler
  $('#unassigned_units').change(function() {
    var unit_id = $('#unassigned_units').val();

    // Display Learning Outcomes
    show_unit_outcomes(unit_id);
    $('#course_content').find('option').attr('selected', false);
  });

  // Course Content listbox handler
  $('#course_content').change(function() {
    var unit_id = $('#course_content').val();

    $.getJSON('/json/unit_area_id', {'unit_id': unit_id}, function(response) {
      show_area_units(response.area.id);
      show_unit_outcomes(response.unit.id);

      // Display Learning Outcomes
      show_unit_outcomes(response.unit.id);
      $('#unassigned_units').find('option').attr('selected', false);
    });
  });

  // Add/Remove button handlers
    // Add Unit(s) button enable/disable
    //if(unit_ids.length > 0)
      //$('#add_units').removeAttr('disabled')
    //else
      //$('#add_units').attr('disabled', 'disabled')

  $('#remove_all').click(function() {
  });

  $('#remove_selected').click(function() {
    var unit_id = $('#course_content').val();
  });

  $('#add_selected').click(function() {
    var unit_id = $('#unassigned_units').val();
  });

  $('#add_all').click(function() {
  });

  // Ensure that selected Knowledge Area has units displayed
  show_area_units('');
  show_course_content();
});
