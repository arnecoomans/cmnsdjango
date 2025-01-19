from django.contrib import admin

class BaseModelAdmin(admin.ModelAdmin):
  list_display = ('__str__', 'status', 'user')
  list_filter = ('status', 'user')
  search_fields = ('name',)
  date_hierarchy = 'date_created'
  ordering = ('-date_created',)
  
  def get_changeform_initial_data(self, request):
    get_data = super(BaseModelAdmin, self).get_changeform_initial_data(request)
    get_data['user'] = request.user.pk
    return get_data 
  
  def get_list_display(self, request):
    # Start with the base list_display
    list_display = list(self.list_display)
    # Add additional fields to the list_display
    if hasattr(self.model, 'sites'):
      list_display.append('count_sites')
    if hasattr(self.model, 'get_current'):
      list_display.append('get_current_version')
    return list_display