from django.views import View
from django.conf import settings
from django.middleware.csrf import CsrfViewMiddleware
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.apps import apps
from django.template.loader import render_to_string
from django.template.exceptions import TemplateDoesNotExist
from django.utils.translation import gettext_lazy as _
from django.db.models import Q
from django.db.models.fields.related import ForeignKey, ManyToManyField, OneToOneField
import json

from .messages import Messages
class JsonUtils(View):
  """
  Json Utility Class
  Extend this class to include basic and reusable utilities for
  handling JSON responses in Django views.
  """

  def __init__(self, *args, **kwargs):
    super().__init__(**kwargs)
    self.model = None
    self.object = None
    self.attributes = None
    self.value = None
    self.parent = None
    self.status = 200
    self.csrf_token = None
    self.payload = []
    self.messages = Messages()

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
    if key in self.kwargs:
      return self.kwargs[key]
    value = self.request.GET.get(key, None)
    if value:
      return value
    value = self.request.POST.get(key, None)
    if value:
      return value
    header_key = f"HTTP_{key.replace('-', '_').upper()}"
    value = self.request.META.get(header_key, None)
    if value:
      return value
    return default

  def check_csrf_token(self):
    """
    Check the CSRF token in the current request if DEBUG mode not is enabled.

    This function validates the CSRF token using Django's CsrfViewMiddleware.

    Raises:
      PermissionDenied: If the CSRF token is missing or invalid.
    """
    if settings.DEBUG:
      self.messages.add("CSRF token check skipped in DEBUG mode.", "debug")
      return
    self.csrf_token = self.get_value_from_request("csrfmiddlewaretoken", default=None)
    if not self.csrf_token:
      raise PermissionDenied(_('csrf token is missing or invalid.').capitalize())
    try:
      CsrfViewMiddleware().process_view(self.request, None, (), {})
    except PermissionDenied:
      raise PermissionDenied(_('invalid csrf token.').capitalize())

  def get_model(self, model_name=None):
    """
    Retrieve a model class based on the 'model' parameter from the request.
    """
    if self.model:
      return self.model
    model_name = model_name if model_name else self.get_value_from_request('model')
    if not model_name:
      raise ValueError(_('the model parameter is required but was not provided.').capitalize())
    self.model = self.get_specific_model(model_name)
    return self.model
  
  def get_specific_model(self, model_name, action='read'):
    try:
      matching_models = []
      for app_config in apps.get_app_configs():
        try:
          model = app_config.get_model(model_name)
          if model:
            matching_models.append(model)
        except LookupError:
          continue
      if len(matching_models) == 0:
        raise ValueError(_("no model with the name '{}' could be found.".format(model_name)).capitalize())
      elif len(matching_models) > 1:
        raise ValueError(_("multiple models with the name '{}' were found. specify 'app_label.modelname' instead.".format({model_name})).capitalize())
      model = matching_models[0]
      """ Authentication check
          Raise ValueError if the model does not allow access via the 'allow_read_attributes' attribute """
      if getattr(model, f'allow_{action}_attributes', getattr(settings, 'ALLOW{action.upper()}_ATTRIBUTES', False)) is False:
        raise ValueError(_("{} access to the model '{}' is not allowed".format(action, model_name)).capitalize())
      elif str(getattr(model, 'allow_{action}_attributes', getattr(settings, 'ALLOW_{action.upper()}_ATTRIBUTES', False))).lower()[:4] == 'auth' and not self.request.user.is_authenticated:
        raise ValueError(_("{} access to the model '{}' is not allowed for unauthenticated users".format(action, model_name)).capitalize())
      elif str(getattr(model, 'allow_{action}_attributes', getattr(settings, 'ALLOW_{action.upper()}_ATTRIBUTES', False))).lower()[:5] == 'staff' and not self.request.user.is_staff:
        raise ValueError(_("{} access to the model '{}' is not allowed for non-staff users".format(action, model_name)).capitalize())
      """ Authentication check passed: set model """
      self.model = model
      return model
    except ValueError as e:
      raise ValueError(_('error when accessing model: {}.').format(e).capitalize())

  def get_model_of_field(self, field_name):
    if hasattr(field_name, '_meta'):
      # 1-to-1 Relation
      model = field_name._meta.model_name
    elif isinstance(field_name, type):
      model = field_name.__name__
    elif hasattr(field_name, 'field'):
      # Foreign Key Relation
      model = field_name.field.related_model.__name__
    elif hasattr(field_name, 'model'):
      # Many-to-Many Relation
      model = field_name.model.__name__
    elif isinstance(field_name, bool):
      model = 'Boolean'
    else:
      raise ValueError(_("invalid field to get model of: {}").format(self.get_value_from_request('attribute')))
    model = self.get_specific_model(model)
    return model
  
  def get_object(self):
    """
    Retrieve an object instance based on the model and identifiers (pk, slug) from the request.
    """
    if self.object:
      return self.object
    model = self.get_model()
    pk = self.get_value_from_request('pk')
    slug = self.get_value_from_request('slug')
    if not pk and not slug:
      raise ValueError(_('either pk or slug parameter must be provided to retrieve an object.').capitalize())
    try:
      if pk and slug:
        obj = model.objects.filter(pk=pk, slug=slug)
      elif pk:
        obj = model.objects.filter(pk=pk)
      elif slug:
        obj = model.objects.filter(slug=slug)
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

  def get_attributes(self):
    """
    Retrieve a specific attribute from an object.
    """
    if self.attributes:
      return self.attributes
    attribute = self.get_value_from_request('attribute')
    if not attribute:
      raise ValueError(_('the attribute parameter is required but was not provided.').capitalize())
    obj = self.get_object()
    if not hasattr(obj, attribute):
      raise ValueError(_("the attribute {} does not exist on the object.".format({attribute})).capitalize())
    value = getattr(obj, attribute)
    return value
  
  def search_attributes(self, attributes, q=False):
    if not q:
      q = self.get_value_from_request('q', False)
    if q:
      searchable_fields = ['name', 'title', 'description']
      if hasattr(attributes, 'searchable_fields'):
        searchable_fields += attributes.searchable_fields
      attributes = self.filter_queryset_by_fields(attributes, searchable_fields, q)
    return attributes
  
  def render_attribute(self, attribute, format='html'):
    """ Returns the attribute as string.
        If a template exists in templates/objects, the string will be 
        formatted by the template.
    """
    model_name = attribute.__class__.__name__.lower()
    rendered_attribute = None
    try:
      # Try to find the attribute template to render in templates/objects/
      rendered_attribute = render_to_string(f'objects/{ model_name }.{ format }', {model_name: attribute})
      if format == 'json':
        rendered_attribute = json.loads(rendered_attribute)
    except TemplateDoesNotExist:
      # If the template does not exist, return the string representation of the attribute
      self.messages.add(_("{} template for {} not found in objects/").format(format, model_name).capitalize(), "debug")
      rendered_attribute = str(attribute)
    except Exception as e:
      self.messages.add(_("error rendering attribute: {}").format(e).capitalize(), "debug")
      rendered_attribute = str(attribute)
    return rendered_attribute

  def return_response(self):
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
        },
      }
      for kwarg in self.kwargs:
        response_data['__meta']['request']['url_' + kwarg] = self.get_value_from_request(kwarg)
      if self.get_value_from_request('q', False):
        response_data['__meta']['request']['q'] = self.get_value_from_request('q')
    return JsonResponse(response_data)
  
  def get_unused_related_objects(self, model, instance, related_field_name, extra_filters=None):
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
    # Validate the related_field_name
    if not hasattr(instance, related_field_name):
      raise ValueError(f"'{related_field_name}' is not a valid field for '{model.__name__}'.")

    # Get the related manager for the field
    related_manager = getattr(instance, related_field_name)

    # Get the primary key of related objects that are already associated
    used_related_ids = related_manager.values_list('pk', flat=True)

    # Query the related model for objects not in the used IDs
    related_model = related_manager.model
    unused_related_objects = related_model.objects.exclude(pk__in=used_related_ids)

    # Apply additional filters if provided
    if extra_filters:
      unused_related_objects = unused_related_objects.filter(**extra_filters)

    return unused_related_objects

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

    for field_name in searchable_fields:
      # Skip non-existent fields
      if field_name not in valid_field_names:
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

