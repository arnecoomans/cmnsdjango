$(document).ready(function () {
  const $overlay = $("#attributeOverlay");

  // Open de overlay en haal inhoud op via JSON
  $(".addOverlayButton").on("click", function () {
    obj = $(this);
    overlayUrl = obj.data('url');
    $.ajax({
      url: overlayUrl,
      method: "GET",
      success: function (data) {
        console.log(data);
        $overlay.html(data.payload);
        $overlay.show();
        // Re-bind event listeners aan nieuwe elementen
        setupOverlayEvents();
        $("#attributeInput").focus();
      },
      error: function () {
        showMessage('danger', 'Failed to load overlay content.');
      },
    });
  });

  // Sluit de overlay
  $(document).on("click", "#closeOverlay", function () {
    $overlay.hide();
  });

  // Functie om alle functionaliteit in de overlay opnieuw te binden
  function setupOverlayEvents() {
    const $input = $("#attributeInput");
    const $suggestions = $("#suggestions");

    // Haal suggesties op terwijl de gebruiker typt
    $input.on("input", function () {
      const query = $input.val();

      if (query.length < 2) {
        $suggestions.empty();
        return;
      }

      $.ajax({
        url: $input.data("suggestion-url"),
        method: "GET",
        data: { q: query },
        success: function (data) {
          $suggestions.empty();
          data.payload.forEach((item) => {
            const listItem = $(`<li data-slug="${item.slug}">${item.display_text}</li>`);
            $suggestions.append(listItem);
          });
        },
        error: function () {
          showMessage('danger', 'Error fetching suggestions.');
        },
      });
    });

    // Selecteer een suggestie en verstuur deze
    $suggestions.on("click", "li", function () {
      const slug = $(this).data("slug");

      $.ajax({
        url: $input.data("submit-url"),
        method: "POST",
        headers: {
          "X-CSRFToken": getCSRFToken(),
        },
        data: JSON.stringify({ obj_slug: slug }),
        contentType: "application/json",
        success: function (response) {
          if (response.messages && response.messages.length > 0) {
            response.messages.forEach(message => {
              showMessage(message.level, message.message);
            });
          }
          $overlay.hide();
        },
        error: function () {
          showMessage('danger', 'Failed to add person.');
          if (response.messages && response.messages.length > 0) {
            response.messages.forEach(message => {
              showMessage(message.level, message.message);
            });
          }
        },
      });
    });
  }

  // Helperfunctie om de CSRF-token te krijgen
  function getCSRFToken() {
    return document.cookie
      .split("; ")
      .find((row) => row.startsWith("csrftoken="))
      ?.split("=")[1];
  }
});
