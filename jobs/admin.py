from django.contrib import admin
from .models import Job, Application

# Register your models here.

class JobAdmin(admin.ModelAdmin):
    list_display = ('title', 'company_name', 'location', 'salary', 'posted_by', 'date_posted')
    search_fields = ('title', 'company_name')
    list_filter = ('location', 'date_posted')


class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('applicant', 'job', 'date_applied')

admin.site.register(Job, JobAdmin)
admin.site.register(Application, ApplicationAdmin)

