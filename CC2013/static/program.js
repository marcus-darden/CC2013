$(function() {
  /*
  $("#dialog-confirm").dialog({
    resizable: false,
    height: 140,
    modal: true,
    buttons: {
      "Delete program": function() {
        $( this ).dialog( "close" );
      },
      Cancel: function() {
        $( this ).dialog( "close" );
      }
    }
  });
  */
  
  $('#program_delete').submit(function(e) {
    if(!confirm("Do you want to delete this program?"))
      e.preventDefault();
  });
});
