from django.http import JsonResponse
from django.core.exceptions import PermissionDenied
from django.utils.translation import gettext_lazy as _
import traceback
from django.conf import settings
from markdown import markdown
from django.db.models import TextField

from cmnsdjango.views.json_utils import JsonUtils

class JsonGetAttributes(JsonUtils):
  def get(self, request, *args, **kwargs):
    try:
      # Check CSRF token
      self.check_csrf_token()
      # Fetch current valies of field in model
      # field and model are implied in get_field_values()
      values = self.get_field_value()
      # Process search query
      values = self.search_queryset(values)
      # Return the value as rendered response
      if callable(values):
        # Return the function outcome
        self.messages.add(_("The attribute is a callable function."), 'debug')
        self.payload.append(self.render_attribute(values()))
      elif isinstance(values, (list, tuple)):
        # For each value in the list, render the value
        self.messages.add(_("The attribute is a list or tuple."), 'debug')
        for value in values:
          self.payload.append(self.render_attribute(value))
      else:
        # Try to render each value in the queryset
        try:
          for value in values.all():
            self.payload.append(self.render_attribute(value))
        except:
          try:
            # If the queryset is not iterable, render the value
            self.payload.append(self.render_attribute(values))
          except:
            # If the queryset is not renderable, add a string representation
            # of the value to the payload
            self.payload.append(self.render_attributes(str(values)))
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