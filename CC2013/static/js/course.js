$(function() {
  $('#course_delete').submit(function(e) {
    if(!confirm("Do you want to delete this course?"))
      e.preventDefault();
  });
});
