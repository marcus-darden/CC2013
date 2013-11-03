$(function() {
    $('#knowledge_areas').change(function() {
        var val = $('#knowledge_areas').val();

        // Get Knowledge Units, based on val

        // Fill Knowledge Units listbox
        $('#knowledge_units').empty();
        $('#knowledge_units').append($('<option></option>').text(val));
    });
    $('#knowledge_units').change(function() {
        var vals = $('#knowledge_units').val();

        // Get Learning Outcomes, based on vals

        // Fill Learning Outcomes listbox
        $('#learning_outcomes').empty();
        $.each(vals, function(i, val) {
            $('#learning_outcomes').append($('<option></option>').text(val));
        });
    });
});
