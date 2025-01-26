from django.http import JsonResponse
from django.core.exceptions import PermissionDenied
from django.utils.translation import gettext_lazy as _
import traceback
from django.conf import settings

from cmnsdjango.views.json_utils import JsonUtils

class JsonGetSuggestions(JsonUtils):
  def get(self, request, *args, **kwargs):
    try:
      # Check CSRF token
      self.check_csrf_token()
      # Get Field to fetch suggestions for
      current_values = self.get_field_value()
      # Get Model of Field to query for all objects
      model = self.get_model('suggest')
      suggestion_model = self.get_field_model()
      suggestions = self.get_unused_related_objects(model=suggestion_model, exclude_queryset=self.get_field_value(), extra_filters=None)
      # Process search query
      suggestions = self.search_queryset(suggestions)
      # Add the suggestions to the payload
      for suggestion in suggestions:
        self.payload.append(self.render_attribute(suggestion, format='json'))
      return self.return_response()
    except PermissionDenied as e:
        return JsonResponse({"error": str(e)}, status=403)
    except ValueError as e:
      # Handle specific errors and return as JSON
      return JsonResponse({"error": str(e)}, status=400)
    except Exception as e:
      response = {"error": _("an unexpected error occurred: {}").format(str(e))}
      if settings.DEBUG and self.request.user.is_staff:
        response['traceback'] = traceback.format_exc()
      return JsonResponse(response, status=500)
