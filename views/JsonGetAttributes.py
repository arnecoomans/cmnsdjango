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
      # Fetch the attributes and
      # add the attributes to the payload
      attributes = self.get_attributes()
      # Process search query
      attributes = self.search_attributes(attributes)
      if hasattr(attributes, 'all') and callable(attributes.all):
        # If attributes is a queryset, display each attribute
        for attribute in attributes.all():
          self.payload.append(self.render_attribute(attribute))
      elif isinstance(attributes, (list, tuple)):
        # If attributes is a list or tuple, display each attribute
        for attribute in attributes:
          self.payload.append(self.render_attribute(attribute))
      elif callable(attributes):
        # If attributes is a callable function, add its result to payload
        try:
          self.payload.append(attributes())  # Add the result to payload
        except Exception as e:
          # If the function raises an exception, return it as JSON
          raise ValueError(_('error when fetching attribute: {}').format(str(e)).capitalize())
      # Handle textfield values and apply markdown filter if "markdown" is mentioned in the 
      # field's help_text (example: "This field supports markdown")
      elif (
        isinstance(attributes, str) and 
        isinstance(self.model._meta.get_field(self.get_value_from_request('attribute')), TextField) and
        "markdown" in (self.model._meta.get_field(self.get_value_from_request('attribute')).help_text or "").lower()
      ):
        self.payload.append(markdown(attributes))
      # Handle non-iterable values directly
      else:
        self.payload.append(self.render_attribute(attributes))
      # Return the response
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