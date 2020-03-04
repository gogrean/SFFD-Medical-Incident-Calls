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

  console.log('Made it here!')

  $.get('/tract-stats', formInputs, (res) => {
    $('.bokeh-scripts').html(res.js_tract);
    $('.display-stats').html(res.div_tract);
  });

});
