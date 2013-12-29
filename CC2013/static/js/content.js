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
    update_buttons();
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

  function show_area_units(area_id, selected_unit_id) {
    var $areas = $('#knowledge_areas');

    // Don't update KA/UU if no change
    if(area_id == $areas.val()) {
      show_unit_outcomes(selected_unit_id);
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
      show_unit_outcomes(selected_unit_id);
    });
  }

  function show_course_content() {
    // Fill listbox
    var course_id = $('#__course_id').val();
    $.getJSON('/json/course_content', {'course_id': course_id}, function(units) {
      fill_unit_listbox('#course_content', units);
      update_buttons();
    });
  }

  function update_buttons() {
    var $content = $('#course_content');
    var $unassigned = $('#unassigned_units');

    // Selectively enable buttons
    // remove_all
    if($content.find('option').length)
      $('#remove_all').removeAttr('disabled');
    else
      $('#remove_all').attr('disabled', 'disabled');

    // remove_selected
    if($content.val() !== null)
      $('#remove_selected').removeAttr('disabled');
    else
      $('#remove_selected').attr('disabled', 'disabled');

    // add_selected
    if($unassigned.val() !== null)
      $('#add_selected').removeAttr('disabled');
    else
      $('#add_selected').attr('disabled', 'disabled');

    // add_all
    if($unassigned.find('option').length)
      $('#add_all').removeAttr('disabled');
    else
      $('#add_all').attr('disabled', 'disabled');
  }

  // Knowledge Area dropdown handler  
  // AJAX query for Knowledge Units not assigned in this program,
  // then display them in the unassigned units listbox.
  $('#knowledge_areas').change(function() {
    // Deselect
    $('#course_content').find('option').attr('selected', false);

    show_area_units('', 0);
  });

  // Unassigned Units listbox handler
  $('#unassigned_units').change(function() {
    // Deselect
    $('#course_content').find('option').attr('selected', false);

    var unit_id = $('#unassigned_units').val();
    show_unit_outcomes(unit_id);
  });

  // Course Content listbox handler
  $('#course_content').change(function() {
    // Deselect
    $('#unassigned_units').find('option').attr('selected', false);

    var unit_id = $('#course_content').val();
    $.getJSON('/json/unit_area_id', {'unit_id': unit_id}, function(response) {
      show_area_units(response.area.id, response.unit.id);
    });
  });

  // course_content -> NULL
  function remove_content(units) {
    var course_id = $('#__course_id').val();
    var program_id = $('#__program_id').val();
    var json_url = '/program/' + program_id + '/course/' + course_id + '/remove';

    var units_obj = JSON.stringify({'units': units});
    $.getJSON(json_url, {'units': units_obj}, function(response) {
      if(response)
        update_page();
    });
  }
  
  $('#remove_all').click(function() {
    remove_content($.map($('#course_content option'), function(opt) { return opt.value; }));
  });

  $('#remove_selected').click(function() {
    remove_content([$('#course_content').val()]);
  });

  // unassigned_units -> course_content
  function add_content(units) {
    var course_id = $('#__course_id').val();
    var program_id = $('#__program_id').val();
    var json_url = '/program/' + program_id + '/course/' + course_id + '/add';

    var units_obj = JSON.stringify({'units': units});
    $.getJSON(json_url, {'units': units_obj}, function(response) {
      if(response)
        update_page();
    });
  }

  $('#add_selected').click(function() {
    add_content([$('#unassigned_units').val()]);
  });

  $('#add_all').click(function() {
    add_content($.map($('#unassigned_units option'), function(opt) { return opt.value; }));
  });

  function update_page() {
    // Ensure that selected Knowledge Area has units displayed
    show_area_units('', 0);
    show_course_content();
  }
  update_page();
});
