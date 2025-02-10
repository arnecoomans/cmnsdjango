// /**
//  * Display a message in the messages-placeholder element.
//  * 
//  * @param {string} type - The type of alert (e.g., 'success', 'danger').
//  * @param {string} message - The message to display.
//  */
// function showMessage(type, message) {
//   const messagesPlaceholder = document.getElementById('messages-placeholder');
//   if (messagesPlaceholder) {
//     messagesPlaceholder.innerHTML += `
//       <div class="alert alert-${type} alert-dismissible fade show" role="alert">
//         ${message}
//         <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
//       </div>
//     `;
//   }
//   if (type == 'danger') {
//     console.error(message);
//   } else {
//     console.log(message);
//   }
// }


// Function to apply fade-out to alerts
function applyFadeOut() {
  var duration = 10 * 1000; // X times 1000 ms = X seconds

  $('.alert').each(function() {
    var $this = $(this);

    // Check if the alert already has a fade-out timer to prevent duplication
    if (!$this.data('fade-out-set')) {
      $this.data('fade-out-set', true); // Mark this alert as having a fade-out timer

      // Set the timer for fade-out
      setTimeout(function() {
        $this.fadeOut(1000, function() { // 1000 ms = 1 second fade-out
          message = $this.text();
          message = message.replace('(Undo)', '').trim();
          console.log('Removing alert "' + message + '"');
          $this.remove();
        });
      }, duration);
    }
  });
}

$(document).ready(function() {
  // Select all alert messages and set a timer to fade them out
  applyFadeOut();
  // Reapply fade-out logic after AJAX content is loaded
  $(document).ajaxComplete(function() {
    applyFadeOut();
  });

  /**  Auto-Capitalize
   * Auto-capitalize the first letter of each word in an input field
   * with the class 'autocapitalize'
   */
  $('input.autocapitalize').on('input', function() {
    var inputVal = $(this).val();
    var capitalizedVal = inputVal.replace(/\b\w/g, function(char) {
        return char.toUpperCase();
    });
    $(this).val(capitalizedVal);
  });

  
  // Reapply fade-out logic after AJAX content is loaded
  $(document).ajaxComplete(function() {
    applyFadeOut();
  });
});