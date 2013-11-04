$(function() {
    // Knowledge Area listbox handler
    $('#knowledge_areas').change(function() {
        var area_id = $('#knowledge_areas').val();

        // Get Knowledge Units, based on val and fill Knowledge Units listbox
        $('#knowledge_units').empty();
        $.getJSON('/json', {'area_id': area_id}, function(units) {
            $.each(units, function(i, unit) {
                $('#knowledge_units').append($('<option/>').text(unit.text).val(unit.id));
            });
        });
    });

    // Knowledge Unit listbox handler
    $('#knowledge_units').change(function() {
        var unit_ids = $('#knowledge_units').val();

        // Add Unit(s) button enable/disable
        //if(unit_ids.length > 0)
            //$('#add_units').enable()
        //else
            //$('#add_units').disable()

        // Get Learning Outcomes, based on vals and fill Learning Outcomes listbox
        $('#learning_outcomes').empty();
        $.each(unit_ids, function(i, unit_id) {
            $.getJSON('/json', {'unit_id': unit_id}, function(outcomes) {
                $.each(outcomes, function(j, outcome) {
                    $('#learning_outcomes').append($('<option/>').text(outcome.text).val(outcome.id));
                });
            });
        });
    });

    // Knowledge Unit button handler
    $('#add_units').click(function() {
        var unit_ids = $('#knowledge_units').val();
        var action = {'action': 'add', 'unit_ids': unit_ids.join(',')};
        // Send 'em!!
        console.log(action);
    });

    // Learning Outcome listbox handler
    $('#learning_outcomes').change(function() {
        var outcome_ids = $('#learning_outcomes').val();

        // Add Outcome(s) button enable/disable
        //if(outcome_ids.length > 0)
            //$('#add_outcomes').enable();
        //else
            //$('#add_outcomes').disable();
    });

    // Learning Outcome button handler
    $('#add_outcomes').click(function() {
        var outcome_ids = $('#learning_outcomes').val();
        var action = {'action': 'add', 'outcome_ids': outcome_ids.join(',')};
        // Send 'em!!
        console.log(action);
    });

});
