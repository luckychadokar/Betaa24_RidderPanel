from django.contrib import admin
from .models import Rider, RiderTraining, RiderDocument, WalletTransaction
from .models import BankDetail

@admin.register(Rider)
class RiderAdmin(admin.ModelAdmin):
    list_display = ['name','mobile','city','status','rating','total_tasks']
    list_filter = ['status','city']
    search_fields = ['name','mobile']

@admin.register(RiderTraining)
class TrainingAdmin(admin.ModelAdmin):
    list_display = ['rider','status','training_date']
    list_filter = ['status']

@admin.register(RiderDocument)
class DocAdmin(admin.ModelAdmin):
    list_display = ['rider','overall_status']

@admin.register(WalletTransaction)
class WalletAdmin(admin.ModelAdmin):
    list_display = ['rider','txn_type','amount','created_at']
    list_filter = ['txn_type']

@admin.register(BankDetail)
class BankAdmin(admin.ModelAdmin):
    list_display = ['rider', 'account_holder_name', 'bank_name', 'verify_status']