
/**
 * Fetch attributes from a URL and add the payload to a target element.
 * 
 * @param {string} url - The URL to fetch data from.
 * @param {string} attribute - The attribute name to process.
 * @param {string} before - Optional HTML to prepend to each payload item.
 * @param {string} after - Optional HTML to append to each payload item.
 * @param {string} [csrf_token] - Optional CSRF token for the request.
 */
async function getAttributes(url, attribute, before = '', after = '', func_csrf_token = csrf_token) {
  console.log(`Fetching data from ${url} for ${attribute}`);
  try {
    // Stel de headers in, inclusief de CSRF-token als deze bestaat
    const headers = {
      'Content-Type': 'application/json',
    };
    if (csrf_token) {
      headers['x-csrftoken'] = getCookie("csrftoken");
      // headers['X-csrftoken'] = func_csrf_token;
    }

    // Fetch de data van de opgegeven URL
    const response = await fetch(url, {
      method: 'GET', // Of 'POST', afhankelijk van de situatie
      headers: headers,
    });

    // Controleer of de response OK is
    if (!response.ok) {
      throw new Error(`HTTP error! Status: ${response.status}`);
    }

    // Parse de JSON-response
    const data = await response.json();

    // Verwerk foutmeldingen uit de JSON-response
    if (data.error) {
      console.error(`Error: ${data.message}`);
      showMessage('danger', data.message);
      return;
    }

    // Verwerk de payload
    if (data.payload && data.payload.length > 0) {
      const targetId = `target-${attribute}`;
      const targetElement = document.getElementById(targetId);

      if (targetElement) {
        console.log(`${attribute}-data: ${data.payload.length} item(s) fetched successfully. Writing to ${targetId}.`);

        // Leeg het target-element en vul deze met nieuwe data
        targetElement.innerHTML = '';
        data.payload.forEach(payload => {
          targetElement.innerHTML += `${before}${payload}${after}`;
        });
      } else {
        console.warn(`Target element with ID "${targetId}" not found.`);
      }
    }

    // Toon een succesbericht als dat aanwezig is
    if (data.messages && data.messages.length > 0) {
      data.messages.forEach(message => {
        showMessage(message.level, message.message);
      });
    }
  } catch (error) {
    // Verwerk netwerkfouten en andere onverwachte problemen
    console.error(`Error: ${error.message}`);
    showMessage('danger', `An error occurred: ${error.message}`);
  }
}
