function ready(fn) {
	if (document.attachEvent ? document.readyState === "complete" : document.readyState !== "loading"){
		fn();
	} else {
		document.addEventListener('DOMContentLoaded', fn);
	}
}

ready(startPollLoop);

var checkIntervalId;

function startPollLoop() {
	checkIntervalId = setInterval(checkInvoicePaid, 5000);
}

function checkInvoicePaid() {
	console.debug("Checking if invoice has been paid", "");

  var request = new XMLHttpRequest();
  request.open('GET', "{{ url_for('check_invoice_paid', payment_request=payment_request) }}", true);

  request.onload = function() {

    if (request.status >= 200 && request.status < 400) {
      // Success!
      var data = JSON.parse(request.responseText);
			console.debug(data);

      if(data.paid) {
        console.log("Invoice has been paid!");
        handleInvoicePaid();
      } else {
        console.debug("Invoice not yet paid");
			}

    } else if (request.status == 404) {
      handleInvoiceExpired();

    } else {
      // We reached our target server, but it returned an HTTP error code
      console.error("Error :( request.status: ", request.status);
    }
  };

  request.onerror = function() {
    // There was a connection error of some sort
      console.error("Mystery error :)");
  };

  request.send();
}

function handleInvoiceExpired() {
  console.error('Invoice expired, generating new payment request.');
  clearInterval(checkIntervalId);
  window.location.href = "{{ url_for('redirect_to_payment_request', product_slug=product_slug) }}";
}

function handleInvoicePaid() {
  window.location.href = "{{ url_for('deliver_product', product_slug=product_slug, payment_request=payment_request) }}";
}
