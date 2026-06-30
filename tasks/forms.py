from django import forms
from .models import Task


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = [
            "rider",
            "task_date",
            "task_type",
            "num_tasks",
            "time_taken",
            "distance_km",
            "customer_name",
            "customer_number",
            "pickup_address",
            "drop_address",
            "remarks",
            "status",
            "cancelled_by",
            "cancellation_reason",
        ]
        widgets = {
            "task_date": forms.DateInput(attrs={"type": "date"}),
            "pickup_address": forms.Textarea(attrs={"rows": 2}),
            "drop_address": forms.Textarea(attrs={"rows": 2}),
            "cancellation_reason": forms.Textarea(attrs={"rows": 2}),
        }

