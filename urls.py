from django.urls import path

from cmnsdjango import views as cmnsviews
#from core.views import SignUpView

urlpatterns = [
  # JSON GET Attributes
  path('json/<str:model>/<int:pk>:<str:slug>/attribute/<str:field>/', cmnsviews.JsonGetAttributes.as_view(), name='json-get-attributes-by-pk-slug'),
  path('json/<str:model>/<str:slug>/attribute/<str:field>/', cmnsviews.JsonGetAttributes.as_view(), name='json-get-attributes'),
  path('json/<str:model>/attribute/<str:field>/', cmnsviews.JsonGetAttributes.as_view(), name='json-get-attributes-for-self'),
  # JSON GET Suggestions
  path('json/<str:model>/<int:pk>:<str:slug>/suggest/<str:field>/', cmnsviews.JsonGetSuggestions.as_view(), name='json-get-suggestions-by-pk-slug'),
  path('json/<str:model>/<str:slug>/suggest/<str:field>/', cmnsviews.JsonGetSuggestions.as_view(), name='json-get-suggestions'),
  path('json/<str:model>/suggest/<str:field>/', cmnsviews.JsonGetSuggestions.as_view(), name='json-get-suggestions-for-self'),
  # JSON SET Attributes
  path('json/<str:model>/<int:pk>:<str:slug>/set/<str:field>/', cmnsviews.JsonSetAttribute.as_view(), name='json-set-attribute-by-pk-slug'),
  path('json/<str:model>/<str:slug>/set/<str:field>/', cmnsviews.JsonSetAttribute.as_view(), name='json-set-attribute'),
  path('json/<str:model>/set/<str:field>/', cmnsviews.JsonSetAttribute.as_view(), name='json-set-attribute-for-self'),
  # JSON getAttribute Form
  path('json/<str:model>/<str:slug>/add/<str:field>/', cmnsviews.GetJsonAddObjectForm.as_view(), name='json-suggestion-form'),  
]