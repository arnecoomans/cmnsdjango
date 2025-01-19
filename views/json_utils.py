from django.views import View
from django.conf import settings
from django.middleware.csrf import CsrfViewMiddleware
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.core.serializers import serialize
from django.apps import apps

class JsonUtils(View):
  """
  Json Utility Class
  Extend this class to include basic and reusable utilities for
  handling JSON responses in Django views.
  """

  def __init__(self, request, *args, **kwargs):
    self.request = request
    self.args = args
    self.kwargs = kwargs
    self.model = None
    self.object = None
    self.attribute = None
    self.value = None
    self.parent = None
    self.status = 200
    self.messages = []

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
    # Check URL parameters
    if key in self.kwargs:
      return self.kwargs[key]
    # Check GET parameters
    value = self.request.GET.get(key, None)
    if value:
      return value
    # Check POST parameters
    value = self.request.POST.get(key, None)
    if value:
      return value
    # Check headers (case-insensitive)
    header_key = f"HTTP_{key.replace('-', '_').upper()}"
    value = self.request.META.get(header_key, None)
    if value:
      return value
    # Key not found
    return default

  def check_csrf_token(self):
    """
    Check the CSRF token in the current request if DEBUG mode is enabled.

    This function validates the CSRF token using Django's CsrfViewMiddleware. It is intended for development
    environments where DEBUG=True, allowing for additional debugging of CSRF-related issues.

    The CSRF token is searched for in the following sources:
    - Headers (e.g., X-CSRFToken)
    - GET parameters
    - POST data

    If the token is missing or invalid, a PermissionDenied exception is raised.

    Raises:
      PermissionDenied: If the CSRF token is missing or invalid.

    Example Usage:
      try:
        self.check_csrf_token()
      except PermissionDenied as e:
        return JsonResponse({"error": str(e)}, status=403)
    """
    if not settings.DEBUG:
      return  # Skip CSRF checks in non-debug environments
    # Attempt to extract CSRF token from the request
    csrf_token = self.get_value_from_request("csrfmiddlewaretoken", default=None)
    if not csrf_token:
      raise PermissionDenied("CSRF token is missing or invalid.")
    # Validate the CSRF token
    try:
      CsrfViewMiddleware().process_view(self.request, None, (), {})
    except PermissionDenied:
      raise PermissionDenied("Invalid CSRF token.")


  def get_model(self):
    """
    Retrieve a model class based on the 'model' parameter from the request.

    This function uses the 'model' parameter retrieved via get_value_from_request() to dynamically
    fetch the corresponding model class from the Django apps registry.

    Returns:
        Model class if found, otherwise raises an Exception.

    Raises:
        ValueError: If the model parameter is missing or invalid.
    """
    model_name = self.get_value_from_request('model')
    if not model_name:
      raise ValueError("The 'model' parameter is required but was not provided.")
    try:
      app_label, model_class_name = model_name.split('.')
      model = apps.get_model(app_label=app_label, model_name=model_class_name)
      if model is None:
        raise ValueError(f"The model '{model_name}' could not be found.")
      # Check if the model allows read access
      elif hasattr(model, 'allow_read_attributes'):
        if not model.allow_read_attributes():
          raise ValueError(f"Read access to the model '{model_name}' is not allowed.")
      return model
    except ValueError as e:
      raise ValueError(f"Invalid model parameter format. Expected 'app_label.ModelName'. Error: {str(e)}")

  def get_object(self):
    """
    Retrieve an object instance based on the model and identifiers (pk, slug) from the request.

    This function uses the `get_model` method to fetch the model and then attempts to retrieve
    an object instance using the provided primary key (pk), slug, or both.

    Returns:
        Object instance if found, otherwise raises an Exception.

    Raises:
        ValueError: If neither pk nor slug is provided, or the object cannot be found.
    """
    model = self.get_model()
    # Retrieve pk and slug from the request
    pk = self.get_value_from_request('pk')
    slug = self.get_value_from_request('slug')
    if not pk and not slug:
      raise ValueError("Either 'pk' or 'slug' parameter must be provided to retrieve an object.")
    try:
      # Attempt to retrieve the object based on the provided identifiers
      if pk and slug:
        obj = model.objects.get(pk=pk, slug=slug)
      elif pk:
        obj = model.objects.get(pk=pk)
      elif slug:
        obj = model.objects.get(slug=slug)
      else:
        raise ValueError("Unable to determine the object retrieval criteria.")
      # Apply status and visibility if they exist
      if hasattr(self, 'filter_status'):
        obj = self.filter_status(obj)
      if hasattr(self, 'filter_visibility'):
        obj = self.filter_visibility(obj)
      return obj
    except model.DoesNotExist:
      raise ValueError("The requested object does not exist.")
    except Exception as e:
      raise ValueError(f"An error occurred while retrieving the object: {str(e)}")


  def get_attribute(self):
    """
    Retrieve a specific attribute from an object.

    This function uses `get_object()` to fetch the object and retrieves
    the value of a specific attribute defined in the request.

    Returns:
        The value of the attribute if found, otherwise raises an Exception.

    Raises:
        ValueError: If the attribute is missing, invalid, or cannot be accessed.
    """
    # Get the attribute name from the request
    attribute = self.get_value_from_request('attribute')
    if not attribute:
      raise ValueError("The 'attribute' parameter is required but was not provided.")
    # Retrieve the object
    obj = self.get_object()
    # Check if the attribute exists in the object
    if not hasattr(obj, attribute):
      raise ValueError(f"The attribute '{attribute}' does not exist on the object.")
    # Retrieve the attribute value
    value = getattr(obj, attribute)
    # If the attribute is callable (e.g., a method), call it
    if callable(value):
      try:
        value = value()
      except Exception as e:
        raise ValueError(f"Error calling the attribute '{attribute}': {str(e)}")
    return value

  def return_response(self):
    """
    Prepare and return a structured JSON response.

    This function structures the stored data and includes a '_meta' 
    field if the request.user is a staff member.

    Returns:
        JsonResponse: A JSON response containing the structured data.
    """
    response_data = {
      "status": self.status,
      "messages": self.messages,
      "payload": None,  # Placeholder for rendered content
    }

    # Add _meta information if the user is staff
    if self.request.user.is_staff:
      response_data["_meta"] = {
        "user_id": self.request.user.id,
        "username": self.request.user.username,
        "object": serialize(self.object),
      }
    return JsonResponse(response_data)
