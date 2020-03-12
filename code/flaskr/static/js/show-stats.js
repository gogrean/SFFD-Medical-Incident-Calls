"use strict";

// Display the ambulance statistics for the tract corresponding
// to the address entered by the user.
// This is an AJAX request that allows displaying the
// stats on the stats page each time a new request is made,
// without redirecting the user to a new page.

$(".form-inline").on('click', '#show-stats', (evt) => {
  evt.preventDefault();

  const formInputs = {
    'location': $('#location').val()
  };

  $.get('/tract-stats', formInputs, (res) => {
    $('.bokeh-scripts').html(res.js_func);
    $('.display-stats').html(res.div_tag);
    $('.flash-warning').html(res.error_msg);
  });

});
