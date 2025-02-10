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
  if (level == 'danger') {
    console.error(message);
  } else {
    console.log(message);
  }
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
    throw error;  // Let specific functions handle the error display if needed
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
