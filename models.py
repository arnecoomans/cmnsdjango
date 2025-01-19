from django.db import models
from django.contrib.sites.models import Site
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.contrib.sites.managers import CurrentSiteManager

''' BaseModel
    Abstract base model with common fields and methods
    for all models in the project.
'''
class BaseModel(models.Model):
  status_choices      = (
    ('c', _('concept').capitalize()),
    ('p', _('published').capitalize()),
    ('r', _('revoked').capitalize()),
    ('x', _('deleted').capitalize()),
  )
  status              = models.CharField(max_length=1, choices=status_choices, default='p')
  
  date_created = models.DateTimeField(auto_now_add=True)
  date_modified = models.DateTimeField(auto_now=True)
  user = models.ForeignKey(
      get_user_model(),
      on_delete=models.SET_NULL,
      null=True,
      blank=True,
      related_name="%(class)s_created_by"
  )
  class Meta:
    abstract = True

  def __str__(self):
    if hasattr(self, "name"):
        return self.name
    ''' Fallback to Django Default Displaying '''
    return f"{self.__class__.__name__} object ({self.pk})"
  
  def get_model_fields(self):
    return [field.name for field in self._meta.get_fields()]


''' MultiSiteBaseModel 
    Extends BaseModel with multi-site support.
'''
class MultiSiteBaseModel(BaseModel):
  """Abstract base model with common fields and methods."""
  sites = models.ManyToManyField(Site, related_name="%(class)s_sites")
  # Add site-aware manager
  objects = models.Manager()  # Default manager
  on_site = CurrentSiteManager()  # Site-specific manager

  class Meta:
    abstract = True

  def count_sites(self):
    return self.sites.count()
  count_sites.short_description = _('sites')