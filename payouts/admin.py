from django.contrib import admin
from .models import Payout


@admin.register(Payout)
class PayoutAdmin(admin.ModelAdmin):
    list_display = ["rider", "amount", "status", "payout_date"]
    list_filter = ["status"]

