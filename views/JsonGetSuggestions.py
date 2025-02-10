from django.http import JsonResponse
from django.core.exceptions import PermissionDenied
from django.utils.translation import gettext_lazy as _
import traceback
from django.conf import settings
from django.template.loader import render_to_string

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
        self.payload.append(self.render_attribute(suggestion, format='json', context={'query': self.get_value_from_request('q')}))
      return self.return_response()
    except PermissionDenied as e:
        return JsonResponse({"[PermissionDenied error]": str(e)}, status=403)
    except ValueError as e:
      # Handle specific errors and return as JSON
      return JsonResponse({"[ValueError": str(e)}, status=400)
    except Exception as e:
      response = {"error": _("an unexpected error occurred: {}").format(str(e))}
      if settings.DEBUG and self.request.user.is_staff:
        response['traceback'] = traceback.format_exc()
      return JsonResponse(response, status=500)

from archive.models import Tag

class GetJsonAddObjectForm(JsonUtils):
  def get(self, request, *args, **kwargs):
    try:
      field = self.get_field_model().__name__.lower()
    except AttributeError:
      #field = self.get_model()._meta.get_field(self.get_field_name().name)
      #Image._meta.get_field('description')
      field_name = self.get_field_name().name
      field = self.get_model()._meta.get_field(field_name).__class__.__name__.lower()
      
    # Fetch specific model configuration
    allow_create_attribute = getattr(self.get_field_model(field), 'allow_create_attribute', True)

    # Set context for AddObjectForm
    template_context = {
      'model': self.kwargs['model'], # Model name, required for URL building
      'field': type(field), # Field name, required for URL building
      'related_field': self.get_field_name().name, # Related field name, required for URL building
      'object': self.get_object(), # Object to add a new related object to
      'title': _('add new {}').format(field).capitalize(), # Title of the overlay
      'attribute': self.get_field_name().verbose_name, 
      'allow_create_attribute': allow_create_attribute,
    }
    ''' Try to render the specific form for the field, if that fails, render the generic form '''
    try:
      self.payload.append(render_to_string(f'sections/add_{ field}_overlay.html', template_context))
    except:
      try:
        self.payload.append(render_to_string('sections/add_object_overlay.html', template_context))
      except Exception as e:
        raise ValueError(_('could not render form: {}').format(str(e)).capitalize())
    return self.return_response()