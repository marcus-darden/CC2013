$(function() {
    // Knowledge Area listbox handler
    $('#knowledge_areas').change(function() {
        var area_id = $('#knowledge_areas').val();
        var course_id = $('#__course_id').val();

        // Get Knowledge Units, based on val and fill Knowledge Units listbox
        $('#knowledge_units').empty();
        $.getJSON('/json', {'area_id': area_id, 'course_id': course_id}, function(units) {
            $.each(units, function(i, unit) {
                $('#knowledge_units').append($('<option/>').text('(' + unit.tier1 + ', ' + unit.tier2 + ') ' + unit.text).val(unit.id));
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
        var row = $('<tr/>').append($('<td/>').text('Tier')).append($('<td/>').text('Mastery')).append($('<td/>').text('Learning Outcome'));
        $('#learning_outcomes').append(row);
        //$.each(unit_ids, function(i, unit_id) {
            //$.getJSON('/json', {'unit_id': unit_id}, function(outcomes) {
                //$.each(outcomes, function(j, outcome) {
                    //$('#learning_outcomes').append($('<option/>').text(outcome.tier + ' (' + outcome.mastery + '): ' + outcome.text).val(outcome.id));
                //});
            //});
        //});
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
});
