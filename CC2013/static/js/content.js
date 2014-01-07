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
      $.getJSON('/unit/' + unit_id + '/outcomes', null, function(response) {
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

  // Build and insert a list of options from a list of units
  function fill_unit_listbox(listbox_id, units) {
    // Find and empty the listbox
    var $listbox = $(listbox_id);
    $listbox.empty();

    // Add all the units
    $.each(units, function(i, unit) {
      // Make an option from the unit
      var $option = $('<option/>');
      $option.text('(' + unit.tier1 + ', ' + unit.tier2 + ') ' + unit.text);
      $option.val(unit.id);
      $option.attr('data-area_id', unit.area_id)

      // Insert the option into the target listbox
      $listbox.append($option);
    });
  }

  // Update the Knowledge Area dropdown and show related unassigned units
  function show_area_units(area_id, selected_unit_id) {
    var $areas = $('#knowledge_areas');

    // Don't update KA/UU if no change
    if(area_id === $areas.val()) {
      return;
    }

    // Set dropdown
    if(area_id == '')  // A no-op for change event handler
      area_id = $areas.val();
    else
      $areas.val(area_id);

    // Build AJAX url
    var course_id = $('#__course_id').val();
    var program_id = $('#__program_id').val();
    var ajax_url = '/program/' + program_id + '/unassigned';

    // Fill listbox
    $.getJSON(ajax_url, {'area_id': area_id}, function(units) {
      fill_unit_listbox('#unassigned_units', units);
    });
  }

  // AJAX Fill Course Content listbox from course info provided to template
  function show_course_content() {
    // Build AJAX url
    var course_id = $('#__course_id').val();
    var program_id = $('#__program_id').val();
    var ajax_url = '/program/' + program_id + '/course/' + course_id + '/units';

    // Fill listbox
    $.getJSON(ajax_url, null, function(units) {
      fill_unit_listbox('#course_content', units);
      update_buttons();
    });
  }

  // Enable Add/Remove buttons based on listbox contents and selection
  function update_buttons() {
    // Simple enable function
    function button_enable(button_id, enable) {
      if(enable)
        $(button_id).removeAttr('disabled');
      else
        $(button_id).attr('disabled', 'disabled');
    }

    var $content = $('#course_content');
    var $unassigned = $('#unassigned_units');

    button_enable('#remove_all', $content.find('option').length);
    button_enable('#remove_selected', $content.val());
    button_enable('#add_selected', $unassigned.val());
    button_enable('#add_all', $unassigned.find('option').length);
  }

  // Knowledge Area dropdown handler  
  $('#knowledge_areas').change(function() {
    // Deselect
    $('#course_content').find('option').attr('selected', false);

    show_area_units('', 0);
    show_unit_outcomes(0);
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

    var $unit = $('#course_content option:selected');
    var unit_id = parseInt($unit.val());
    show_unit_outcomes(unit_id);
    show_area_units($unit.data('area_id'), unit_id);
  });

  // Add a unit to the given listbox, sorted by unit id (ASC)
  function insert_unit($unit, $listbox) {
    var unit_id = parseInt($unit.val());
    var $dest_units = $listbox.find('option');

    for(var i = 0; i < $dest_units.length; i++) {
      if(parseInt($dest_units[i].value) > unit_id) {
        $unit.insertBefore($dest_units.slice(i, i + 1));
        return;
      }
    }

    // Add to empty list or end of non-empty list
    $unit.appendTo($listbox);
  }

  // Remove the given list of Knowledge Units from the current course
  function unit_remove($units) {
    // Build AJAX url
    var course_id = parseInt($('#__course_id').val());
    var program_id = parseInt($('#__program_id').val());
    //var ajax_url = "{{ url_for('unit_remove', program_id=program_id, course_id=course_id) }}";
    var ajax_url = '/program/' + program_id + '/course/' + course_id + '/content';

    // Build units list and send to server
    var units = $.map($units, function(option, i) {
      return parseInt(option.value);
    });
    var units_json = JSON.stringify(units);
    $.post(ajax_url, {'units': units_json, 'add': false},
      function(response) {
        // Upon successful db activity, move course_content -> {unassigned_units | null}
        if(response) {
          var area_id = $('#knowledge_areas').val();
          var $unassigned_units = $('#unassigned_units');

          $.each($units, function(i, option) {
            if(option.getAttribute('data-area_id') === area_id)
              insert_unit($(option), $unassigned_units);
            else
              $(option).remove();
          });
        }
        update_buttons();
      },
      'json'
    );
  }

  $('#remove_all').click(function() {
    unit_remove($('#course_content option'));
  });

  $('#remove_selected').click(function() {
    unit_remove($('#course_content option:selected'));
  });

  // unassigned_units -> course_content
  function unit_add($units) {
    // Build AJAX url
    var course_id = $('#__course_id').val();
    var program_id = $('#__program_id').val();
    var ajax_url = '/program/' + program_id + '/course/' + course_id + '/content';

    // Build units list and send to server
    var units = $.map($units, function(option, i) {
      return parseInt(option.value);
    });
    var units_json = JSON.stringify(units);
    $.post(ajax_url, {'units': units_json, 'add': true},
      function(response) {
        // Upon successful db activity, move unassigned_units -> course_content
        if(response) {
          var $course_content = $('#course_content');

          $.each($units, function(i, option) {
            insert_unit($(option), $course_content);
          });
        }
        update_buttons();
      },
      'json'
    );
  }

  $('#add_selected').click(function() {
    unit_add($('#unassigned_units option:selected'));
  });

  $('#add_all').click(function() {
    unit_add($('#unassigned_units option'));
  });

  function update_page() {
    // Ensure that selected Knowledge Area has units displayed
    show_area_units('', 0);
    show_course_content();
  }
  update_page();
});
