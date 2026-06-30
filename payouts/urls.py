from django.urls import path
from . import views

urlpatterns = [
    path("", views.payout_list, name="payout_list"),
    path("add/", views.payout_add, name="payout_add"),
    path("<int:pk>/mark-paid/", views.payout_mark_paid, name="payout_mark_paid"),
    path("rider/<int:pk>/", views.rider_payout_summary, name="rider_payout_summary"),
    path("export/", views.payout_export, name="payout_export"),
    path('auto-calculate/<int:rider_pk>/', views.auto_calculate_payout, name='auto_calculate_payout'),
]

