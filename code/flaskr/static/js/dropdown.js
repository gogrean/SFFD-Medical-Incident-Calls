$(document).ready(function() {
  $(".dropdown-menu li a").click(function(){
    $(this).parents(".dropdown").find('.btn').html($(this).text() + ' <span class="caret"></span>');
    $(this).parents(".dropdown").find('.btn').val($(this).data('value'));
  });
});

function getVals(formControl, controlType) {
            switch (controlType) {
                case 'select':
                    // Get the value for a select
                    var value = $(formControl).val();
                    $("#pSelect").text(value);
                    break;
            }
        }
