from django.views import View
from django.conf import settings
from django.middleware.csrf import get_token
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.apps import apps
from django.template.loader import render_to_string
from django.template.exceptions import TemplateDoesNotExist
from django.utils.translation import gettext_lazy as _
from django.db.models import Q
from django.db import models
from django.contrib.auth.context_processors import PermWrapper


# from django.db.models.fields.related import ForeignKey, ManyToManyField, OneToOneField
from django.db.models import (
    ForeignKey,
    ManyToManyField,
    OneToOneField,
    TextField,
    CharField,
    IntegerField,
    BooleanField,
    DateField,
    DateTimeField,
    FloatField,
)
from markdown import markdown
import json
from django.db.models import TextField

from .messages import Messages
class JsonUtils(View):
  """
  Json Utility Class
  Extend this class to include basic and reusable utilities for
  handling JSON responses in Django views.
  """

  def __init__(self, *args, **kwargs):
    super().__init__(**kwargs)
    self.model = None         # Model of the object
    self.object = None        # The object
    self.field = None         # The field of the object
    self.field_name = None    # The name of the field of the object
    self.field_model = None   # The model of the field of the object
    self.field_value = None   # The value of the field of the object
    self.new_value = None     # The new value of the field of the object
    self.attribute = None
    self.status = 200   # Default status code
    self.csrf_token = None
    self.payload = []
    self.messages = Messages()

  ''' Value Retrieve Functions '''
  def get_value_from_request(self, key, default=None):
    """
    Retrieve a value from the request in the following order of priority:
    1. URL kwargs
    2. GET parameters
    3. POST parameters
    4. Headers (case-insensitive)

    Args:
        key (str): The key to be fetched from the request.
        default: The default value to return if the key is not found.

    Returns:
        str or None: The value associated with the key, or the default value if not found.
    """
    value = None
    header_key = f"HTTP_{key.replace('-', '_').upper()}"
    jsondata = {}
    try:
      jsondata = json.loads(self.request.body)
    except:
      pass
    try:
      if key in self.kwargs:
        value = self.kwargs[key]
      elif key in self.request.GET:
        value = self.request.GET.get(key, None)
      elif key in self.request.POST:
        value = self.request.POST.get(key, None)
      elif key in jsondata:
        value = jsondata.get(key)
      elif header_key in self.request.META:
        value = self.request.META.get(header_key, None)
    except Exception as e:
      self.messages.add(_("error when fetching value: {}").format(str(e)).capitalize(), "debug")
    return value if value else default

  def get_new_value(self, field=None):
    # Get the value for the request parameters. 
    # The value can be stored in get, post or
    # query parameters, and can be id, slug or value.
    if self.new_value:
      if field in self.new_value.keys():
        return self.new_value[field]
      return self.new_value
    # Loop through the possible keys to get the value
    for key in ['set_id', 'get_id', 'obj_id',
                'set_slug', 'get_slug', 'obj_slug',
                'value', 'set_value', 'get_value', 'obj_value']:
      value = self.get_value_from_request(key, False)
      if value:
        for word in ['set', 'get', 'obj']:
          key = key.replace(f"{ word }_" , '')  
        self.new_value = {'key': key, 'value': value,}
        return self.get_new_value(field) # Recursively call the function to get the value if field is specified
  
  
  ''' Security Functions ''' 
  def check_csrf_token(self):
    """
    Check the CSRF token in the current request if DEBUG mode not is enabled.

    This function validates the CSRF token using Django's CsrfViewMiddleware.

    Raises:
      PermissionDenied: If the CSRF token is missing or invalid.
    """
    client_token = (
      self.request.META.get("HTTP_X_CSRFTOKEN")
      or self.request.POST.get("csrfmiddlewaretoken")
      or self.request.GET.get("csrfmiddlewaretoken")
      or None
    )
    server_token = self.request.COOKIES.get(getattr(settings, 'CSRF_COOKIE_NAME', 'csrftoken'), None)
    if client_token != server_token:
      if settings.DEBUG:
        self.messages.add(_("CSRF token validation failed, but failure is ignored due to DEBUG status"), "debug")
      else:
        raise PermissionDenied("Invalid CSRF token." + str(client_token) + ' - ' + str(server_token))
    

  ''' Model Functions '''
  def get_model(self, model_name=None, action='read'):
    """
    Retrieve a model class based on the 'model' parameter from the request.
    """
    if self.model:
      return self.model
    self.action = action
    # Get the model name from the request
    model_name = model_name if model_name else self.get_value_from_request('model')
    if not model_name:
      raise ValueError(_('the model parameter is required but was not provided.').capitalize())
    # Get the specific model supplied by the model name
    try:
      # Loop through all installed apps to find the first
      # model with the specified name
      matching_models = []
      for app_config in apps.get_app_configs():
        try:
          model = app_config.get_model(str(model_name))
          if model:
            matching_models.append(model)
        except LookupError:
          continue
      if len(matching_models) == 0:
        raise ValueError(_("no model with the name '{}' could be found".format(model_name)).capitalize())
      elif len(matching_models) > 1:
        raise ValueError(_("multiple models with the name '{}' were found. specify 'app_label.modelname' instead.".format({model_name})).capitalize())
      model = matching_models[0]
      self.model = model
      """ Authentication check
          Raise ValueError if the model does not allow access via the 'allow_read_attribute' attribute """
      if getattr(model, f'allow_{action}_attribute', getattr(settings, 'ALLOW{action.upper()}_attribute', False)) is False:
        raise ValueError(_("{} access to the model '{}' is not allowed".format(action, model_name)).capitalize())
      elif str(getattr(model, f'allow_{action}_attribute', getattr(settings, 'ALLOW_{action.upper()}_attribute', False))).lower()[:4] == 'auth' and not self.request.user.is_authenticated:
        raise ValueError(_("{} access to the model '{}' is not allowed for unauthenticated users".format(action, model_name)).capitalize())
      elif str(getattr(model, f'allow_{action}_attribute', getattr(settings, 'ALLOW_{action.upper()}_attribute', False))).lower() == 'staff' and not self.request.user.is_staff:
        raise ValueError(_("{} access to the model '{}' is not allowed for non-staff users".format(action, model_name)).capitalize())
      elif str(getattr(model, f'allow_{action}_attribute', getattr(settings, 'ALLOW_{action.upper()}_attribute', False))).lower() == 'self' and not self.get_object().user == self.request.user:
        self.model = None
        raise ValueError(_("{} access to the model '{}' is is only allowed for object user".format(action, model_name)).capitalize())
      """ Authentication check passed: set model """
      return model
    except ValueError as e:
      raise ValueError(_('error when accessing model: {}.').format(e).capitalize())

  ''' Object functions '''
  def get_object(self):
    """
    Retrieve an object instance based on the model and identifiers (pk, slug) from the request.
    """
    if self.object:
      return self.object
    model = self.get_model()
    pk = self.get_value_from_request('pk')
    slug = self.get_value_from_request('slug')
    user = self.request.user if 'for-self' in self.request.resolver_match.url_name else None
    if 'for-self' in self.request.resolver_match.url_name:
     if not user.is_authenticated:
       raise ValueError(_('unauthenticated users are not allowed to access this object.').capitalize())
    elif not pk and not slug:
      raise ValueError(_('either pk or slug parameter must be provided to retrieve an object.').capitalize())
    try:
      if pk and slug:
        obj = model.objects.filter(pk=pk, slug=slug)
      elif pk:
        obj = model.objects.filter(pk=pk)
      elif slug:
        obj = model.objects.filter(slug=slug)
      elif 'for-self' in self.request.resolver_match.url_name:
        if not user.is_authenticated:
          raise ValueError(_('unauthenticated users are not allowed to access this object.').capitalize())
        elif str(getattr(model, f'allow_{self.action}_attribute', getattr(settings, 'ALLOW_{action.upper()}_attribute', False))).lower() == 'self':
          obj = model.objects.filter(user=user)
        else:
          raise ValueError(_('unable to retrieve object without key or slug.').capitalize())
      else:
        raise ValueError(_('unable to determine the object retrieval criteria.').capitalize())
      if hasattr(self, 'filter_status'):
        obj = self.filter_status(obj)
      if hasattr(self, 'filter_visibility'):
        obj = self.filter_visibility(obj)
      if obj.count() == 0:
        raise ValueError(_('the requested object does no longer exist.').capitalize())
      elif obj.count() > 1:
        raise ValueError(_('multiple objects were found.').capitalize())
      else:
        obj = obj.first()
      self.object = obj
      return obj
    except model.DoesNotExist:
      raise ValueError(_('the requested object does not exist.').capitalize())
    except Exception as e:
      raise ValueError(_("an error occurred while retrieving the object: {}".format({str(e)})).capitalize())

  ''' Field Functions '''
  def get_field(self, field_name=None):
    """
    Retrieve a specific attribute from an object.
    """
    if self.field:
      return self.field
    # Fetch the field name from the request
    field = field_name if field_name else self.get_value_from_request('field')
    if not field:
      raise ValueError(_('the field parameter is required but was not provided.').capitalize())
    obj = self.get_object()
    if not hasattr(obj, field):
      raise ValueError(_("the attribute {} does not exist on the object.".format({field})).capitalize())
    value = getattr(obj, field)
    return value
  
  def get_field_name(self, field=None):
    if self.field_name:
      return self.field_name
    if not field:
      field = self.get_value_from_request('field')
    self.field_name = self.get_model()._meta.get_field(field)
    return self.get_field_name(field) # Recursively call the function to get the value if field is specified
  
  def get_field_model(self, field=None):
    if self.field_model:
      return self.field_model
    if not field:
      field = self.get_value_from_request('field')
    self.field_model = self.get_object()._meta.get_field(field).related_model
    return self.get_field_model(field) # Recursively call the function to get the value if field is specified
  
  def get_field_value(self, field=None):
    if self.field_value != None:
      return self.field_value
    if not field:
      field = self.get_value_from_request('field')
    field = self.get_field(field)
    # Based on the field model and type, retrieve the value
    if hasattr(field, 'all') and callable(field.all):
      # If attributes is a queryset, display each attribute
      result = field.all()  
    elif callable(field):
      # If attributes is a callable function, add its result to payload
      try:
        result = field()
      except Exception as e:
        # If the function raises an exception, return it as JSON
        raise ValueError(_('error when fetching field: {}').format(str(e)).capitalize())
    elif (
      # Handle textfield values and apply markdown filter if "markdown" is mentioned in the 
      # field's help_text (example: "This field supports markdown")
      isinstance(field, str) and 
      isinstance(self.get_model()._meta.get_field(self.get_value_from_request('field')), TextField) and
      "markdown" in (self.get_model()._meta.get_field(self.get_value_from_request('field')).help_text or "").lower()
    ):
      result = markdown(field)
    # Handle non-iterable values directly
    else:
      result = field
    self.field_value = result
    return self.get_field_value(field) # Recursively call the function to get the value if field is specified

  def is_related_field(self, field_name=None):
    """
    Check if a field is a related field.
    """
    field = field_name if field_name else self.get_value_from_request('field')
    if not field:
      raise ValueError(_('the field parameter is required but was not provided.').capitalize())
    return isinstance(self.get_field_name(field), (ForeignKey, ManyToManyField, OneToOneField))

  def is_value_field(self, field_name=None):
    """
    Check if a field is a value field.
    """
    field = field_name if field_name else self.get_value_from_request('field')
    if not field:
      raise ValueError(_('the field parameter is required but was not provided.').capitalize())
    return isinstance(self.get_field_name(field), (TextField, CharField, IntegerField, BooleanField, DateField, DateTimeField, FloatField))


  def search_queryset(self, queryset, q=False):
    if not q:
      q = self.get_value_from_request('q', False)
    if q:
      ### Add searchable fields from searched model to searchable_fields
      searchable_fields = ['name', 'title', 'description']
      if hasattr(queryset.model, 'searchable_fields'):
        searchable_fields += queryset.model.searchable_fields
      return self.filter_queryset_by_fields(queryset, searchable_fields, q)
    return queryset
    
  
  def render_attribute(self, attribute, format='html', context={}):
    """ Returns the attribute as string.
        If a template exists in templates/objects, the string will be 
        formatted by the template.
    """
    # If model is related, set model name
    if isinstance(attribute, models.Model):
      field_name = attribute.__class__.__name__.lower()
    else:
      field_name = self.get_field_name().name.lower()
    rendered_attribute = None
    object_name = self.get_object().__class__.__name__.lower()
    context = context | {
      'field_name': field_name,
      field_name: attribute,
      # 'perms': PermWrapper(self.request.user),
      'request': self.request,
      self.get_object().__class__.__name__.lower(): self.get_object(),
      'object_name': object_name,
      'debug': {
        'A': self.get_object().__class__.__name__.lower(),
        'B': self.get_object(),
        'C': object_name,
        'D': field_name,
      }
    }
    try:
      # Try to find the attribute template to render in templates/objects/
      rendered_attribute = render_to_string(f'objects/{ field_name }.{ format }', context) 
    except TemplateDoesNotExist:
      # Try again with extended file name
      try:
        rendered_attribute = render_to_string(f'objects/{ object_name }_{ field_name }.{ format }', context)
      except TemplateDoesNotExist:
        # If the template does not exist, return the string representation of the attribute
        self.messages.add(_("{} template for {} not found in objects/ when rendering {}").format(format, field_name, self.get_field_name().name).capitalize(), "debug")
        rendered_attribute = str(attribute)
    except Exception as e:
      self.messages.add(_("error rendering attribute: {}").format(e).capitalize(), "debug")
      rendered_attribute = str(attribute)
    if format == 'json':
      rendered_attribute = json.loads(rendered_attribute)
    return rendered_attribute

  def return_response(self, **kwargs):
    """
    Prepare and return a structured JSON response.
    """
    if self.request.user.is_staff:
      self.messages.user_is_staff = True
    response_data = {
      "status": self.status,
      "messages": self.messages.get(),
      "payload": self.payload,
    }
    for key, value in kwargs.items():
      response_data[key] = value
    if self.request.user.is_staff:
      response_data["__meta"] = {
        "model": str(self.model) if self.model else self.model,
        "object": str(self.object) if self.object else self.object,
        "attribute": self.get_value_from_request('attribute'),
        "debug": settings.DEBUG,
                "request_user": {
          "id": self.request.user.id,
          "username": self.request.user.username,
          "is_staff": self.request.user.is_staff,
          "is_superuser": self.request.user.is_superuser,
        },
        "request": {
          "path": self.request.path,
          "method": self.request.method,
          "handler": self.__class__.__name__,
          "resolver": self.request.resolver_match.url_name,
          "csrf": "present" if self.csrf_token else "missing",
        },
      }
      for kwarg in self.kwargs:
        response_data['__meta']['request']['url_' + kwarg] = self.get_value_from_request(kwarg)
      if self.get_value_from_request('q', False):
        response_data['__meta']['request']['q'] = self.get_value_from_request('q')
    return JsonResponse(response_data)
  
  def get_unused_related_objects(self, model, exclude_queryset=None, extra_filters=None):
    """
    Retrieve all related objects for a model's field that are not associated with the given instance.

    Args:
        model (models.Model): The model to query the related objects.
        instance (models.Model): The specific instance of the model.
        related_field_name (str): The name of the related field on the model.
        extra_filters (dict, optional): Additional filters to apply to the unused related objects.

    Returns:
        QuerySet: A queryset of unused related objects.

    Raises:
        ValueError: If the related_field_name is invalid for the given model.
    """
    # Query the related model for objects not in the used IDs
    queryset = model.objects.all()
    if exclude_queryset:
      # Fetch the primary keys of the related objects that are already used 
      # and exclude them from the queryset
      used_related_ids = exclude_queryset.values_list('pk', flat=True)
      queryset = queryset.exclude(pk__in=used_related_ids)
    # Apply default filters
    for filter in ['filter_status', 'filter_visibility']:
      if hasattr(self, filter):
        queryset = getattr(self, filter)(queryset)
    # Apply additional filters if provided
    if extra_filters:
      queryset = queryset.filter(**extra_filters)
    return queryset

  def filter_queryset_by_fields(self, queryset, searchable_fields, q):
    """
    Filters a queryset based on a search term in the specified fields.

    Supports many-to-many, one-to-one, and direct fields. Provides a clear
    error message for unsupported field types.

    Args:
        queryset (QuerySet): The queryset to filter.
        searchable_fields (list): A list of fields to search.
        q (str): The search term.

    Returns:
        QuerySet: The filtered queryset.

    Raises:
        ValueError: If a field is unsupported for filtering.
    """
    if not q:
      return queryset  # Return unfiltered queryset if no search term is provided
    model = queryset.model
    query = Q()
    # Get all valid field names for the model
    valid_field_names = [f.name for f in model._meta.get_fields()]
    tried_fields = 0
    for field_name in searchable_fields:
      # Skip non-existent fields
      if field_name not in valid_field_names:
        tried_fields += 1
        if tried_fields == len(searchable_fields):
          # All fields have been tried, but no matching field has been found. 
          self.messages.add(_("no valid field found for search query: {} after {} tries").format(searchable_fields, str(tried_fields)), "debug")
          # Return an empty queryset
          return model.objects.none()
        continue
      # Get the field definition
      field = next((f for f in model._meta.get_fields() if f.name == field_name), None)
      # Handle different field types
      if isinstance(field, (ForeignKey, OneToOneField)):
        # Search related models
        related_model = field.related_model
        related_query = Q(**{f"{field_name}__{f.name}__icontains": q for f in related_model._meta.get_fields() if hasattr(f, 'name')})
        query |= related_query
      elif isinstance(field, ManyToManyField):
        # Search related many-to-many fields
        query |= Q(**{f"{field_name}__name__icontains": q})
      elif hasattr(field, "attname"):  # Direct fields
        query |= Q(**{f"{field_name}__icontains": q})
      else:
        # Unsupported field types are skipped
        continue

    return queryset.filter(query)

  def get_defaults(self, model=None, fields={}):
    """
    Get default values for a model.
    """
    if not model:
      model = self.get_model()
    defaults = {}
    for field in model._meta.get_fields():
      if field.is_relation:
        continue
      if hasattr(field, 'default') and field.default != models.NOT_PROVIDED:
        defaults[field.name] = field.default
    if 'user' in [f.name for f in model._meta.get_fields()]:
      defaults['user'] = self.request.user
    for field in fields:
      defaults[field] = fields[field]
    return defaults

class DebugView(View):
  def get(self, request, *args, **kwargs):
    server_token = get_token(request)
    cookie_token = request.COOKIES.get('csrftoken', None)
    return JsonResponse({
      'server_token': server_token,
      'cookie_token': cookie_token,
      'message': 'Tokens logged',
    })