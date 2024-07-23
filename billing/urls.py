# billing/urls.py
from django.urls import path
from . import views

app_name = 'billing'

urlpatterns = [
    path('time-entries/', views.time_entry_list, name='time_entry_list'),
    path('time-entries/create/', views.time_entry_create, name='time_entry_create'),
    path('invoices/', views.invoice_list, name='invoice_list'),
    path('invoices/<int:invoice_id>/', views.invoice_detail, name='invoice_detail'),
    path('invoices/create/', views.invoice_create, name='invoice_create'),
    path('invoices/<int:invoice_id>/items/create/', views.invoice_item_create, name='invoice_item_create'),
    path('invoices/<int:invoice_id>/payments/create/', views.payment_create, name='payment_create'),
]