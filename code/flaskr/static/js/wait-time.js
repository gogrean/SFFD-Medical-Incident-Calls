"use strict";

// Display the estimated arrival time for an ambulance,
// based on the fitted random forest regression model.
// This is an AJAX request that allows displaying the
// estimated arrival time on the homepage each time a
// new request is made.

$(".form-inline").on('click', '#get-estimate', (evt) => {
  evt.preventDefault();

  const formInputs = {
    'incident-address': $('#incident-address').val(),
    'priority': $('#incident-priority').val(),
    'unit-type': $('#unit-type').val(),
  };

  $.get('/make-prediction', formInputs, (res) => {
    $('.display-prediction').html(res);
  });
});
