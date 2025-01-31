document.addEventListener("DOMContentLoaded", function() {
  /**
   * Event delegation for dynamically injected elements.
   * Listens for clicks on elements with the 'delete-attribute' class.
   */
  document.body.addEventListener("click", async function(event) {
    const target = event.target.closest(".delete-attribute");
    if (!target) return; // Ignore clicks outside target elements

    // Retrieve the URL from the data attribute
    const url = target.getAttribute("data-url");

    if (!url) {
      console.error("No data-url found.");
      return;
    }

    // Retrieve the CSRF token (Django-specific)
    const csrf_token = getCookie("csrftoken");

    try {
      // Send the AJAX POST request
      const response = await fetch(url, {
        method: "POST",
        headers: {
          "X-CSRFToken": csrf_token,
          "Content-Type": "application/json",
        },
        // body: JSON.stringify({ action: "toggle" }), // Optional payload
      });

      const data = await response.json();
      if (data.error) {
        console.error(`Error: ${data.message}`);
        showMessage('danger', data.message);
        return;
      }
      // Toon een succesbericht als dat aanwezig is
      if (data.messages && data.messages.length > 0) {
        data.messages.forEach(message => {
          showMessage(message.level, message.message);
        });
      }
      // Execute callback function if it exists
      getAttributes(target.getAttribute("data-success-url"), target.getAttribute('data-attribute'), before = '', after = '')
    } catch (error) {
      console.error("AJAX request failed:", error);
      alert("An error occurred while toggling the attribute.");
    }
  });
});
