// cmnsdjango-ajax-actions.js

/** SUGGESTIONS */
/**
 * Sets up a listener for the attribute input to fetch suggestions via AJAX.
 * 
 * @param {HTMLElement} inputElement - The input element to monitor.
 */
function setupSuggestionListener(inputElement) {
  const suggestionUrl = inputElement.getAttribute('data-suggestion-url');
  const suggestionList = document.getElementById('suggestions');  // Ensure you have a container for suggestions

  if (!suggestionUrl || !suggestionList) {
    console.warn("Suggestion URL or container for suggestions not found.");
    return;
  }

  inputElement.addEventListener('input', async function () {
    const query = inputElement.value.trim();

    if (query.length < 2) {
      suggestionList.innerHTML = '';  // Clear suggestions if input is too short
      return;
    }

    try {
      const data = await sendAjaxRequest(suggestionUrl, "GET", { q: query });

      // Clear existing suggestions
      suggestionList.innerHTML = '';

      // Populate new suggestions from payload
      data.payload.forEach(item => {
        const suggestionItem = document.createElement('li');
        suggestionItem.className = 'clickable';  // Optional: make suggestions clickable
        suggestionItem.setAttribute('data-slug', item.slug);
        suggestionItem.setAttribute('data-action', 'setAttribute');
        suggestionItem.setAttribute('data-url', inputElement.getAttribute('data-url'));  // Submit URL
        suggestionItem.setAttribute('data-attribute', inputElement.getAttribute('data-attribute'));  // Attribute
        suggestionItem.setAttribute('data-success-url', inputElement.getAttribute('data-success-url'));  // Success URL
        suggestionItem.innerHTML = item.display_text;
        suggestionList.appendChild(suggestionItem);
      });

    } catch (error) {
      showMessage("danger", "Failed to fetch suggestions.");
    }
  });
}


/** OVERLAY */
/**
 * Function to close the overlay.
 */
function closeOverlay() {
  const overlay = document.getElementById("attributeOverlay");
  if (overlay) {
    overlay.style.display = "none";
  }
}

/**
 * Sets up close actions for the overlay:
 * - Close when clicking on the #closeOverlay button.
 * - Close when clicking outside the overlay content.
 */
function setupOverlayCloseActions() {
  const overlay = document.getElementById("attributeOverlay");
  const overlayContent = document.getElementById("overlayContent");
  const closeOverlayButton = document.getElementById("closeOverlay");

  // Close the overlay when clicking the close button
  if (closeOverlayButton) {
    closeOverlayButton.addEventListener("click", function () {
      closeOverlay();
    });
  }

  // Close the overlay when clicking outside the content area
  if (overlay) {
    overlay.addEventListener("click", function (event) {
      // Check if the click target is exactly the overlay itself (the background)
      if (event.target === overlay) {
        closeOverlay();
      }
    });
  }

}

/**
 * Fetches overlay content via AJAX and displays it in the overlay container.
 * 
 * @param {string} url - The URL to fetch overlay content from.
 */
async function getOverlay(url) {
  try {
    const data = await sendAjaxRequest(url, "GET");
    const overlay = document.getElementById("attributeOverlay");
    overlay.innerHTML = data.payload;
    overlay.style.display = "flex";

    // Setup close actions once the overlay is displayed
    setupOverlayCloseActions();

    // Wait for the DOM to update before focusing the input
    setTimeout(() => {
      const inputElement = document.getElementById('attributeInput');
      if (inputElement) {
        inputElement.focus();
        setupSuggestionListener(inputElement);  
      }
    }, 0);
  } catch (error) {
    showMessage("danger", "Failed to load overlay.");
  }
}

/** Attributes */
/**
 * Submits an attribute via AJAX based on the provided identifier (ID, slug, or value).
 *
 * @param {string} url - The URL to submit the attribute to.
 * @param {string} attribute - The name of the attribute being modified.
 * @param {Object} data - The data object containing obj_id, obj_slug, or obj_value.
 * @param {string} successurl - The URL to fetch updated attributes after success.
 */
async function setAttributeValue(url, attribute, data, successurl) {
  console.log(`Setting attribute '${attribute}' with data:`, data);
  try {
    // Send AJAX request with the appropriate data
    const response = await sendAjaxRequest(url, "POST", data);
    processResponse(response);

    // If successful, refresh the attributes and close the overlay
    if (response.status === 200) {
      getAttributes(successurl, attribute);
      closeOverlay();
    }
  } catch (error) {
    showMessage("danger", "Failed to set attribute.");
  }
}




/** GET ATTRIBUTE */
/**
 * Fetches attributes from the server and injects them into the target container.
 * 
 * @param {string} url - The URL to fetch attributes from.
 * @param {string} targetId - The ID of the target element to inject attributes into.
 */
async function getAttributes(url, attribute, before='', after='') {
  // Inform fetching data
  console.log(`Fetching data from ${url} for ${attribute}`);
  try {
    // Fetch data from the server based on the URL
    const data = await sendAjaxRequest(url, "GET");
    // Fetch the target element, stop with error message if not found
    const targetElement = document.getElementById('target-' + attribute);
    if (!targetElement) {
      console.warn(`Target element with ID "${targetId}" not found.`);
      return;
    }
    // Clear the target element
    targetElement.innerHTML = '';
    // Insert the response into the target element
    data.payload.forEach(payload => {
      targetElement.innerHTML += `${before}${payload}${after}`;
    });
  } catch (error) {
    showMessage("danger", "Failed to fetch attributes for " + attribute);
  }
}

/** LISTNERS */
document.addEventListener("DOMContentLoaded", function () {
  
  /**
   * Catch click events for all elements with the 'clickable' class,
   * even if they are inserted dynamically later.
   */
  document.body.addEventListener("click", function (event) {
    const target = event.target.closest(".clickable");
    if (!target) return;  // Ignore clicks outside 'clickable' elements
    event.preventDefault();  // Prevent the default action to avoid scrolling

    // Extract data attributes from the clicked element
    const url = target.getAttribute("data-url");
    const action = target.getAttribute("data-action") || "default";
    const method = target.getAttribute("data-method") || getDefaultMethod(action);

    if (!url) {
      console.error("No data-url attribute found on the clicked element.");
      return;
    }

    // Call the corresponding action based on the data-action attribute
    handleAction(action, url, method, target);
    return false;
  });

  /**
   * Determines which function to call based on the 'data-action' attribute.
   */
  function handleAction(action, url, method, element) {
    switch (action) {
      case "getOverlay":
        getOverlay(url);
        break;

      case "getSuggestions":
        const query = element.getAttribute("data-query") || "";
        getSuggestions(url, query);
        break;

        case "setAttribute":
          const attribute = element.getAttribute("data-attribute");
          const successurl = element.getAttribute("data-success-url");
          // Initialize an empty object to hold the data
          let data = {};
          // Check if element has data-id
          if (element.hasAttribute("data-id")) {
            data.obj_id = element.getAttribute("data-id");
          }
          // Check if element has data-slug
          if (element.hasAttribute("data-slug")) {
            data.obj_slug = element.getAttribute("data-slug");
          }
          // Check for neighboring input field with a value
          const inputSelector = element.getAttribute("data-input-selector") || "input";
          const inputElement = element.closest("form")?.querySelector(inputSelector) || 
                              element.parentElement.querySelector(inputSelector);
          if (inputElement && inputElement.value.trim().length > 2) {
            data.obj_value = inputElement.value.trim();
          }
          if (data == {}) {
            console.warn("No data found to set attribute.");
          }
          // Call setAttributeValue with the detected data
          setAttributeValue(url, attribute, data, successurl);
          break;

      case "getAttributes":
        const targetId = element.getAttribute("data-target");
        getAttributes(url, targetId);
        break;

      default:
        console.warn(`No handler defined for action: ${action} when clicking element:`, element);
        showMessage("info", `No specific handler defined for action: ${action}`);
    }
  }
});
