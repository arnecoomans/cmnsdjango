from django.http import JsonResponse
from django.core.exceptions import PermissionDenied
from django.utils.translation import gettext_lazy as _
import traceback
from django.conf import settings
from markdown import markdown
from django.db import models
from django.utils.text import slugify
from django.utils.html import escape
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from cmnsdjango.views.json_utils import JsonUtils

@method_decorator(csrf_exempt, name='dispatch')
class JsonSetAttribute(JsonUtils):
  def get(self, request, *args, **kwargs):
    return self.set_attribute(request, *args, **kwargs)
  
  def post(self, request, *args, **kwargs):
    return self.set_attribute(request, *args, **kwargs)


  def set_attribute(self, request, *args, **kwargs):
    try:
      # Check CSRF token
      self.check_csrf_token()
      # Get Attribute Field to change
      new_value = self.get_new_value() # Get the identifier of the content to be changed, can be id, slug or textual value.
      # If no new-value is set, should the content be set to ""?
      # Should new value be set to field, or should an object be toggled?
      obj = self.get_object()
      field = self.get_field_name().name
      if field: 
        field_type = self.get_model('set')._meta.get_field(self.get_field_name().name).__class__.__name__
        ''' Based on Field Type, toggle the value '''
        if field_type == 'BooleanField':
          self.__toggle_boolean_field(obj, field)
        elif field_type == 'ForeignKey':
          self.__toggle_foreign_key_field(onj, field)
        elif field_type == 'ManyToManyField':
          self.__toggle_many_to_many_field(obj, field)
        elif field_type == 'TextField':
          self.__update_text_field(obj, field, new_value)
        else:
          raise ValueError(_('field type "{}" not supported').format(field_type).capitalize())
      return self.return_response()
    except models.ObjectDoesNotExist as e:
      return self.return_response({'message': _('object not found: {}').format(str(e)).capitalize(), 'status': 404})
    except PermissionDenied as e:
        return self.return_response({'message': _('permission to object is denied: {}').format(str(e)).capitalize(), 'status': 403})
    except ValueError as e:
      # Handle specific errors and return as JSON
      return JsonResponse({"error": str(e)}, status=400)
    except Exception as e:
      response = {"error": _("an unexpected error occurred: {}").format(str(e))}
      if settings.DEBUG and self.request.user.is_staff:
        response['traceback'] = traceback.format_exc()
      return JsonResponse(response, status=500)
    
  def __update_text_field(self, obj, field, new_value):
    try:
      value = new_value['value']
      if not self.get_field_name().editable:
        raise ValueError(f"Field '{field}' is not editable.")
      setattr(obj, field, value)
      obj.save()
      self.messages.add(_('updated field "{}" on "{}"').format(self.get_field_name().name, self.get_object()), 'success')
      return True
    except Exception as e:
      self.messages.add(_('error when setting {} {} to {}: {}').format(obj, field, value, e).capitalize(), 'error')
      return False
      
  def __toggle_boolean_field(self, obj, field):
    try:
      setattr(obj, field, not getattr(obj, field))
      obj.save()
      self.messages.add(f"{ _('toggled {} on {} to {}').format(field, obj, getattr(obj, field)).capitalize() }", 'success',)
      return True
    except Exception as e:
      raise ValueError(_("Error when toggling {} of {}: {}").format(field, obj, e).capitalize())

  def __toggle_many_to_many_field(self, obj, field):
    related_obj = self.__get_related_object()
    if related_obj in getattr(obj, field).all():
      # Object is already in the ManyToManyField: Remove it
      getattr(self.get_object(), field).remove(related_obj)
      self.messages.add(f"{ _('removed "{}" from {} {}').format(related_obj, field, self.get_object()).capitalize() }", 'success')
    else:
      # Object should be added
      getattr(self.get_object(), field).add(related_obj)
      self.messages.add(f"{ _('added "{}" to {} {}').format(related_obj, field, self.get_object()).capitalize() }", 'success')
    obj.save()

  def __toggle_foreign_key_field(self, obj, field):
    related_obj = self.__get_related_object()
    if getattr(self.get_object(), field) == related_obj:
      # Value is already set: Remove it
      setattr(self.get_object(), field, None)
      self.messages.add(f"{ _('removed {} from {}').format(related_obj, field).capitalize() }", 'success')
    else:
      # Value should be set
      setattr(self.get_object(), field, related_obj)
      self.messages.add(f"{ _('set {} to {}').format(field, related_obj).capitalize() }", 'success')
    obj.save()


  def __get_related_object(self):
    search_model = self.get_model(action='set')._meta.get_field(self.get_field_name().name).related_model
    # if id or slug is set, look for the object or create an error
    #@TODO: Add Parent Check if field has attribute parent
    #@BUG This doesnt work for creating values...
    new_value = self.get_new_value()
    # If key or slug is mentioned in new_value.keys(), assume it is safe
    # to search the object by key or slug
    if new_value['key'] in ['id', 'slug']:
      try:
        return search_model.objects.get(**{new_value['key']: new_value['value']})
      except search_model.DoesNotExist:
        raise ValueError(_("related {} object not found with {}: {}").format(search_model.__name__, new_value['key'], new_value['value']).capitalize())
    elif new_value['key'] in ['value', 'name' 'title']:
      # Find the field to search for
      target_field = None
      target_fields = ['name', 'title']
      for field in target_fields:
        if field in [field.name for field in search_model._meta.get_fields()]:
          target_field = field
          break
      if not target_field:
        raise ValueError(_("No valid field found to search for related object").capitalize())
      try:
        print(target_field + '__iexact' + ' = ' + new_value['value'])
        print(new_value['value'])
        defaults = self.get_defaults(search_model, {
          'slug': slugify(new_value['value']),
          target_field: new_value['value']  
          })
        related_obj = search_model.objects.get_or_create(
          **{target_field + '__iexact': new_value['value']},
          defaults=defaults)
        print(str(related_obj))
        if related_obj[1]:
          self.messages.add(_("Created new {} with {}").format(search_model, related_obj[0]), 'success')
        return related_obj[0]
      except search_model.DoesNotExist:
        raise ValueError(_("related object not found with {} = {}").format(new_value['key'], new_value['value']))
      except Exception as e: 
        raise ValueError(_("Error when creating object: {}").format(e))      
    else:
      raise ValueError(_("No valid identifier found in new value ").capitalize())
    # if self.get_new_value():
    #   try:
    #     if self.get_new_value('key') == 'id':
    #       return search_model.objects.get(id=self.get_new_value('value'))
    #     elif self.get_new_value('key') == 'slug':
    #       return search_model.objects.get(slug=self.get_new_value('value'))
    #   except search_model.DoesNotExist:
    #     raise ValueError(_("related {} object not found with {}: {}").format(search_model.__name__, self.get_new_value('key'), self.get_new_value('value')).capitalize())
    # Search or create a new object based on name, title or value parameter
    # if self.get_value_from_request('name', False):
    #   search_key = 'name'
    #   search_value = self.get_value_from_request('name')
    # elif self.get_value_from_request('title', False):
    #   search_key = 'title'
    #   search_value = self.get_value_from_request('title')
    # else:
    #   raise ValueError("[3x312] " + _("No valid identifier found in new value ") + str(self.get_new_value()))
    # try:
    #   related_obj = search_model.objects.get_or_create(**{search_key + '__iexact': search_value}, defaults=self.get_defaults(search_model, {'slug': slugify(search_value)}))
    #   if related_obj[1]:
    #     self.messages.add(_("Created new {} with {}").format(search_model, related_obj[0]), 'success')
    #   return related_obj[0]
    # except search_model.DoesNotExist:
    #   raise ValueError(_("related object not found with {} = {}").format(search_key, search_value))
    # except Exception as e:
    #   raise ValueError(_("Error when creating object: {}").format(e))