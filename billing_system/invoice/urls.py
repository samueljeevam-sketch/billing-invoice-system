from django.urls import path
from .views import dashboard, invoice_list

urlpatterns = [
    path('', dashboard, name='dashboard'),
    path("invoices/", invoice_list, name="invoice_list"),
]
