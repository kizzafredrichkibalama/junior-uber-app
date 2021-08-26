var originA;
var destinationA;
var counter = 1;
var interval;
var d_lat;
var d_lng;
var travelTime;
var timeToDest;
var rideFare;
var rideAccepted;
var rideAcceptedTimeout;
var pickedUp;
var pickedUpTimeout;
var rideCompleted;
var rideCompletedTimeout;
var driverMarkersTimeout;
var cnt = 0;


function startIntervalCalls() {
    interval = setTimeout(function() {getLocation();}, 7000);
    cnt +=1;
}

function showAvailableDrivers(lat, lng) {
    if (cnt === 0) {
        startIntervalCalls();
    }
    console.log("showAvailableDrivers rightnow");
    $.ajax({
        url: '/api/getDrivers',
        type: 'POST',
        data: {
          'lat': lat,
          'lng': lng,
        },
        success: function(data, status) {
          console.log(status + " : " + data);
        }
    });
}

function updateDriverMarkers() {
    // remove the current marker
    // check database(rides table) here by ajax
    $.ajax({
        url: '/api/checkDriverLocation',
        type: 'GET',
        success: function(data) {
            if (data == 'none') {
                console.log('Driver coords not found... check the RIDERS table connection');
            } else {
                d_lat = data.dest_lat;
                d_lng = data.dest_long;
            }
        }
    });
    if (typeof(d_lat) == "undefined") {
        console.log("UNDEFINED DRIVER's LOCATION");
    } else {
        console.log("updating location " + counter + " - driver lat: ", d_lat + ", driver lng: " + d_lng);
    }
    for (var i = 0; i < curMarkers.length; i++) {
        console.log(curMarkers[i]);
        driverslocations[i][1] = d_lat;
        driverslocations[i][2] = d_lng;
        curMarkers[i].setPosition(new google.maps.LatLng(driverslocations[i][1], driverslocations[i][2]));
    }
    counter = counter + 1;
}

function getCurrentAddress(lat, lng) {
    $.ajax({
        url: 'https://maps.googleapis.com/maps/api/geocode/json?latlng='+ lat + ',' + lng + '&key=AIzaSyBnXUp2Txy1C2OyYp0crd8iyaIDSb-N8oU',
        method: 'POST',
        success: function(data,status) {
          console.log(status + " : " + data);
          //get the address from the response object
          //address = data.results[0].formatted_address;
          //insert the addres
          //$('#originRider').val(address);
        }
    });
}

function requestRide() {
    console.log("requesting ride");
    originA = document.getElementById('originRider').value;
    destinationA = document.getElementById('destinationRider').value;
    var formData = {
        'origin': originA,
        'destination': destinationA
    }
    $.ajax({
        url: '/api/rider',
        type: 'POST',
        data: formData,
        success: function(data, status) {
            console.log(data);
            requestDriver(originA, destinationA);
            calculateAndDisplayRoute(directionsService, directionsDisplay, originA, destinationA);
            directionsDisplay.setMap(map);
            $(".overlay.destination").hide();
            $('#rider-logout-tooltip').html("You cannot log out while searching for a ride!");
            $('.log-out-box').addClass('disabled');
            $('#waitting-state').addClass('active');
            setTimeout(function() {
                $("body.rider").addClass('side-bar-active');
            }, 200);
        }
    });
}

function requestDriver(origin, destination) {
    console.log("called requestDriver")
    $.ajax({
        url: '/api/requestdriver',
        type: 'POST',
        data: {
          'origin': origin,
          'destination': destination
        },
        success: function(data, status) {
            console.log("requestdriver data = " + data);
            if (data == "No drivers available. Check back later!") {
                toggleNoDrivers();
            } else if (data == "destination is out of range/too far") {
                toggleTooFar();
            } else {
                travelTime = data.travelTime;
                rideFare = data.fare;
                // estimated time to destination (minutes) assuming departure time = pickup time
                timeToDest = data.timeToDest;
                rideAccepted = false;
                checkRideAccepted();
                console.log(data);
            }
        }
    });
}

function checkRideAccepted() {
    var formData = {
        'timeToRider': travelTime
    };
    $.ajax({
      url: '/api/checkRideAccepted',
      type: 'POST',
      data: formData,
      success: function(data, status) {
          // if ride request is pending acceptance
          if (data == "ride request not accepted yet") {
              console.log("ride request is pending acceptance");
          } else if (data == "ride request hasn't been paired yet or has been declined") {
            // else if ride request is declined
              rideAccepted = true;
              clearTimeout(rideAcceptedTimeout);
              // request ride/find another driver (check if paired in requestDriver?)
              console.log("driver declined ride request. searching for another driver");
              requestDriver(originA, destinationA);
          } else {
            // else if ride request is accepted
              rideAccepted = true;
              clearTimeout(rideAcceptedTimeout);
              pickedUp = false;
              checkPickedUp();
              toggleFoundDriver(data.name, data.make, data.color, data.license_plate, data.pickup_eta);
          }
      }
    });
    if (!rideAccepted) {
        clearTimeout(rideAcceptedTimeout);
        rideAcceptedTimeout = setTimeout(checkRideAccepted, 5000);
    }
}

function toggleFoundDriver(driverName, carModel, carColor, plates, pickupTime) {
    $('.sidebar-state').removeClass('active'); //disables any active
    $('#driver-found').addClass('active');
    $('#rider-buttons').addClass('active');
    $('#driver-found-title').html('A driver is on the way!');
    $('.driver-name').html(driverName);
    $('.car-model').html(carModel);
    $('.car-color').html(carColor);
    $('.car-plates').html(plates);
    $('.time-title').html('Estimated Time of Pickup:');
    $('.time').html(pickupTime);
    $('.cost').html("$" + rideFare);
    $('#rider-logout-tooltip').html("You must complete the ride first!");
}

function toggleNoDrivers() {
    $('.sidebar-state').removeClass('active'); //disables any active
    $('#no-drivers').addClass('active');
    $('.log-out-box').removeClass('disabled');
    directionsDisplay.setMap(null);
}

function toggleTooFar() {
    $('.sidebar-state').removeClass('active'); //disables any active
    $('#too-far').addClass('active');
    $('.log-out-box').removeClass('disabled');
    directionsDisplay.setMap(null);
}

function cancelRide() {
    $.ajax({
        url: '/api/cancelRide',
        type: 'POST',
        success: function(data) {
            console.log(data);
            pickedUp = true;
            clearTimeout(pickedUpTimeout);
            toggleRideCanceled();
        }
    });
}

function toggleRideCanceled() {
    console.log("canceled ride; view updated");
    $('.sidebar-state').removeClass('active');
    $('#ride-canceled').addClass('active');
    $('.fare').html("$5.00");
    $('#payment-form').addClass('active');
    directionsDisplay.setMap(null);
}

function checkPickedUp() {
    var formData = {
        'timeToRider': travelTime,
        'timeToDest': timeToDest
    };
    $.ajax({
        url: '/api/checkPickedUp',
        type: 'POST',
        data: formData,
        success: function(data, status) {
            if (data != 'false') {
                pickedUp = true;
                clearTimeout(pickedUpTimeout);
                rideCompleted = false;
                checkRideCompleted();
                togglePickedUp(data.arrival_time);
            } else {
                updateDriverMarkers();
                console.log("rider is still waiting to be picked up");
            }
        }
    });
    if (!pickedUp) {
        clearTimeout(pickedUpTimeout);
        pickedUpTimeout = setTimeout(checkPickedUp, 3000);
    }
}

function togglePickedUp(arrivaltime) {
    console.log("picked up and updating view");
    $('#driver-found-title').html('Enroute to Destination');
    $('#rider-buttons').removeClass('active');
    $('.time-title').html('Estimated Time of Arrival:');
    $('.time').html(arrivaltime);
    $('#directions-ride').addClass('active');
    directionsDisplay.setPanel(document.getElementById("directions-ride"));
}

function checkRideCompleted() {
    $.ajax({
        url: '/api/checkRideCompleted',
        type: 'GET',
        success: function(data, status) {
          if (data == 'true') {
              rideCompleted = true;
              clearTimeout(rideCompletedTimeout);
              clearTimeout(interval);
              console.log("ride completed");
              toggleRideCompleted();
          } else {
              updateDriverMarkers();
              console.log("ride is still in progress");
          }
        }
    });
    if (!rideCompleted) {
        clearTimeout(rideCompletedTimeout);
        rideCompletedTimeout = setTimeout(checkRideCompleted, 10000);
    }
}

function toggleRideCompleted() {
    $('.sidebar-state').removeClass('active');
    $('.fare').html("$" + rideFare);
    $('#payment-title').addClass('active');
    $('#payment-form').addClass('active');
    $('#rider-logout-tooltip').html("You must pay for your ride first!");
    directionsDisplay.setMap(null);
}

$(document).ready(function() {
    setTimeout(function(){
      $('.circle-main').remove();
    }, 8000);
    $('#ccNumField').payment('formatCardNumber');
    $('#ccCVCField').payment('formatCardCVC');
    $('#ccNumField').on('keyup paste input', function(e) {
        var ccNum = $(this).val();
        var cardIconDIv = $('#card-icon');
        cardIconDIv.removeClass();
        // american express
        if (ccNum.length == 15) {
            if (ccNum.substring(0, 1) == "3" && ccNum.substring(1, 2) == "4") {
                console.log("amex 34 card entered");
                cardIconDIv.addClass('amex');
            } else if (ccNum.substring(0, 1) == "3" && ccNum.substring(1, 2) == "7") {
                console.log("amex 37 card entered");
                cardIconDIv.addClass('amex');
            }
        }
        // visa 13/19 digits
        else if (ccNum.length == 13 || ccNum.length == 19) {
            if (ccNum.substring(0, 1) == "4") {
                console.log("13/19 digit visa card entered");
                cardIconDIv.addClass('visa');
            }
        }
        else if (ccNum.length == 16) {
            // mastercard
            if (ccNum.substring(0, 1) == "5" && parseInt(ccNum.substring(1, 2)) >= 1 && parseInt(ccNum.substring(1, 2)) <= 5) {
                console.log("mastercard 5[1-5] card entered");
                cardIconDIv.addClass('mastercard');
            } else if (ccNum.substring(0, 1) == "2" && parseInt(ccNum.substring(1, 2)) >= 2 && parseInt(ccNum.substring(1, 2)) <= 7) {
                console.log("mastercard 2[2-7] card entered");
                cardIconDIv.addClass('mastercard');
            } else if (ccNum.substring(0, 1) == "4") {
                // visa 16 digits
                console.log("19 digit visa card entered");
                cardIconDIv.addClass('visa');
            }
        }
    });
    $('#payFare').submit(function(e) {
        e.preventDefault();
        var numValid = $.payment.validateCardNumber($('#ccNumField').val());
        var cardType = $.payment.cardType($('#ccNumField').val());
        var cvcValid = $.payment.validateCardCVC($('#ccCVCField').val(), cardType);
        var expValid = $.payment.validateCardExpiry($('#ccMonthField').val(), $('#ccYearField').val());
        if (!numValid) {
            $('#payFare').effect('shake');
            $('#card-error').html("Card number invalid. Try again.");
            $('#card-error').css('color', '#d50000');
        } else {
              if (!cvcValid) {
                  $('#payFare').effect('shake');
                  $('#card-error').html("Card CVC code invalid. Try again.");
                  $('#card-error').css('color', '#d50000');
              } else {
                  if (!expValid) {
                      $('#payFare').effect('shake');
                      $('#card-error').html("Card expiration date invalid. Try again.");
                      $('#card-error').css('color', '#d50000');
                  } else {
                      $('form').trigger('reset');
                      $('#card-error').html("");
                      $('#card-icon').removeClass();
                      $('.sidebar-state').removeClass('active');
                      $('#thank-rider').addClass('active');
                      setTimeout(function() {
                          $('#thank-rider').removeClass('active');
                          $("body.rider").removeClass('side-bar-active');
                          $('.log-out-box').removeClass('disabled');
                          $(".overlay.destination").show();
                      }, 5000);
                  }
              }
        }
    });
});
