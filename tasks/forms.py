from django import forms
from .models import Task, CustomerWallet, CustomerRecharge


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['rider', 'task_date', 'task_type', 'num_tasks', 'time_taken',
                  'distance_km', 'customer_name', 'customer_number', 'customer_wallet',
                  'pickup_address', 'drop_address', 'remarks', 'status',
                  'cancelled_by', 'cancellation_reason']
        widgets = {
            'task_date': forms.DateInput(attrs={'type': 'date'}),
            'pickup_address': forms.Textarea(attrs={'rows': 2}),
            'drop_address': forms.Textarea(attrs={'rows': 2}),
            'cancellation_reason': forms.Textarea(attrs={'rows': 2}),
        }


class CustomerWalletForm(forms.ModelForm):
    class Meta:
        model = CustomerWallet
        fields = ['customer_name', 'customer_mobile']


class CustomerRechargeForm(forms.ModelForm):
    class Meta:
        model = CustomerRecharge
        fields = ['recharge_type', 'amount_paid', 'tasks_added',
                  'minutes_added', 'km_added', 'note']
        widgets = {
            'note': forms.Textarea(attrs={'rows': 2}),
        }
fields = ['rider', 'task_date', 'task_type', 'num_tasks', 'time_taken',
          'distance_km', 'customer_name', 'customer_number',
          'customer_beta_id', 'task_work_id', 'customer_wallet',
          'pickup_address', 'drop_address', 'remarks', 'status',
          'cancelled_by', 'cancellation_reason']