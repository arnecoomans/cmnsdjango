// cmnsdjango-ajax-utils.js

/**
 * Displays a message in a standardized format.
 * 
 * @param {string} level - The message level ('success', 'danger', 'info').
 * @param {string} message - The message content.
 */
function showMessage(level, message) {
  const messageContainer = document.getElementById("messages-placeholder");
  const alertHtml = `
    <div class="alert alert-${level} alert-dismissible fade show" role="alert">
      ${message}
      <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    </div>
  `;
  messageContainer.insertAdjacentHTML('beforeend', alertHtml);
  if (level === 'danger') {
    console.error(message);
  } else {
    console.log(message);
  }
  applyFadeOut();  // Automatically apply fade-out to newly added messages
}

/**
 * Handles general AJAX responses, displaying messages if present.
 * 
 * @param {Object} response - The response from the server.
 */
function processResponse(response) {
  if (response.messages) {
    response.messages.forEach(msg => showMessage(msg.level, msg.message));
  }
}

/**
 * Applies fade-out effect to alert messages after a certain duration.
 */
function applyFadeOut() {
  const duration = 10 * 1000;  // 10 seconds before fade-out

  document.querySelectorAll('.alert').forEach(alertElement => {
    // Check if fade-out has already been set to prevent duplication
    if (!alertElement.dataset.fadeOutSet) {
      alertElement.dataset.fadeOutSet = true;

      setTimeout(() => {
        alertElement.style.transition = "opacity 1s";
        alertElement.style.opacity = "0";

        // Remove the element after the fade-out completes
        setTimeout(() => {
          const message = alertElement.textContent.replace('(Undo)', '').trim();
          console.log(`Removing alert "${message}"`);
          alertElement.remove();
        }, 1000);  // 1 second for the fade-out effect
      }, duration);
    }
  });
}

/**
 * Automatically capitalize the first letter of each word in inputs with class 'autocapitalize'.
 */
function setupAutoCapitalize() {
  document.querySelectorAll('input.autocapitalize').forEach(input => {
    input.addEventListener('input', function () {
      const capitalizedVal = this.value.replace(/\b\w/g, char => char.toUpperCase());
      this.value = capitalizedVal;
    });
  });
}

/**
 * Returns the default HTTP method for a given action.
 */
function getDefaultMethod(action) {
  return action === "setAttribute" ? "POST" : "GET";
}

/**
 * Parses data-fields from a JSON-like string in data attributes.
 */
function parseDataFields(fields) {
  if (!fields) return {};
  try {
    return JSON.parse(fields);
  } catch (error) {
    console.error("Failed to parse data-fields:", error);
    return {};
  }
}

/**
 * Core AJAX function to handle requests with CSRF protection and standardized error handling.
 *
 * @param {string} url - The URL to make the request to.
 * @param {string} method - HTTP method ('GET' or 'POST').
 * @param {Object} data - Data to send with the request (optional).
 * @returns {Promise<Object>} - Returns a promise that resolves with the JSON response.
 */
async function sendAjaxRequest(url, method = "GET", data = {}) {
  const csrfToken = getCSRFToken();
  
  const fetchOptions = {
    method: method.toUpperCase(),
    headers: {
      "X-CSRFToken": csrfToken,
      "Content-Type": "application/json",
    },
  };

  if (method === "POST") {
    fetchOptions.body = JSON.stringify(data);
  } else if (method === "GET" && Object.keys(data).length > 0) {
    url += "?" + new URLSearchParams(data).toString();
  }

  try {
    const response = await fetch(url, fetchOptions);
    if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
    return await response.json();
  } catch (error) {
    console.error(`Error during AJAX call to ${url}:`, error);
    throw error;
  }
}

/**
 * Retrieves CSRF token from cookies.
 */
function getCSRFToken() {
  return document.cookie
    .split("; ")
    .find(row => row.startsWith("csrftoken="))
    ?.split("=")[1];
}

/**
 * Setup event listeners after DOM content is loaded.
 */
document.addEventListener("DOMContentLoaded", function () {
  // Apply fade-out effect to alerts already on the page
  applyFadeOut();

  // Auto-capitalize input fields
  setupAutoCapitalize();
  
  // Reapply fade-out logic after AJAX content is loaded using MutationObserver
  const observer = new MutationObserver(applyFadeOut);
  observer.observe(document.getElementById("messages-placeholder"), { childList: true });
});

