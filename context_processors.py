from django.conf import settings

''' Context Processors for CMNS Django Project 

    Add this to your settings.py:
    TEMPLATES = [
      {
        [...]
        'OPTIONS': {
          'context_processors': [
            [...]
            'cmnsdjango.context_processors.setting_data',
          ],
        },
      },
    ]
'''

def setting_data(request):
  ''' Re-useable defaults'''
  default_ajax_load = True
  ''' Return Context Variables 
      with default fallback values if not set in project/settings.py 
  '''
  
  return {
    'project_name': getattr(settings, 'SITE_NAME', 'A CMNS Django Project'),
    'meta_description': getattr(settings, 'META_DESCRIPTION', 'A CMNS Django Project'),#
    'language_code': getattr(settings, 'LANGUAGE_CODE', 'en'),

    'ajax_load_default': getattr(settings, 'AJAX_LOAD_DEFAULT', default_ajax_load),
    'ajax_load_attributes': getattr(settings, 'AJAX_LOAD_ATTRIBUTES', default_ajax_load),
    'disallow_delete_attribute': getattr(settings, 'DISALLOW_DELETE_ATTRIBUTE', False),
  }