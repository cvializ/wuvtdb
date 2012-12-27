from django.contrib import admin

from tbdblog.models import Error, ErrorBatch

class ErrorBatchAdmin(admin.ModelAdmin):
    list_display    = ('class_name', 'is_resolved', 'last_seen', 'times_seen', 'url', 'server_name')
    list_filter     = ('class_name', 'times_seen', 'server_name', 'is_resolved')
    ordering        = ('-last_seen', )

class ErrorAdmin(admin.ModelAdmin):
    list_display    = ('class_name', 'links', 'datetime', 'url', 'server_name')
    list_filter     = ('class_name', 'datetime', 'server_name')
    ordering        = ('-datetime', )

admin.site.register(ErrorBatch, ErrorBatchAdmin)
admin.site.register(Error, ErrorAdmin)
