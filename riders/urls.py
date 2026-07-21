from django.urls import path
from . import views
urlpatterns = [
    path('', views.rider_list, name='rider_list'),
    path('add/', views.rider_add, name='rider_add'),
    path('<int:pk>/', views.rider_detail, name='rider_detail'),
    path('<int:pk>/edit/', views.rider_edit, name='rider_edit'),
    path('<int:pk>/delete/', views.rider_delete, name='rider_delete'),
    path('<int:pk>/training/', views.training_update, name='training_update'),
    path('<int:pk>/documents/', views.document_update, name='document_update'),
    path('import/', views.excel_import, name='excel_import'),
    path('export/', views.excel_export, name='excel_export'),
    path('<int:pk>/bank-details/', views.bank_detail_update, name='bank_detail_update'),
    path('ifsc-lookup/', views.ifsc_lookup, name='ifsc_lookup'),
    path('training-records/', views.training_records, name='training_records'),
    path('training-import/', views.training_import, name='training_import'),
    path('beta24-app-import/', views.beta24_app_import, name='beta24_app_import'),
]
