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
});
