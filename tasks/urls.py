from django.urls import path
from . import views

urlpatterns = [
    path("", views.task_list, name="task_list"),
    path("add/", views.task_add, name="task_add"),
    path("<int:pk>/", views.task_detail, name="task_detail"),
    path("<int:pk>/edit/", views.task_edit, name="task_edit"),
    path("<int:pk>/delete/", views.task_delete, name="task_delete"),
    path("cancelled/", views.cancelled_tasks, name="cancelled_tasks"),
    path("export/", views.task_export, name="task_export"),
    path("earnings-preview/", views.earnings_preview, name="earnings_preview"),
    path('customers/', views.customer_wallet_list, name='customer_wallet_list'),
    path('customers/add/', views.customer_wallet_add, name='customer_wallet_add'),
    path('customers/<int:pk>/', views.customer_wallet_detail, name='customer_wallet_detail'),
    path('customers/<int:pk>/recharge/', views.customer_recharge, name='customer_recharge'),
    path('customers/api/', views.customer_wallet_api, name='customer_wallet_api'),
]

