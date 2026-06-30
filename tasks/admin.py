from django.contrib import admin
from .models import Task


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ["task_id", "rider", "task_date", "earnings", "status"]
    list_filter = ["status"]
    search_fields = ["task_id", "customer_name"]

