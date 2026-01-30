from django.urls import path
from .views import dashboard, invoice_list, invoice_create, invoice_detail

urlpatterns = [
    path('', dashboard, name='dashboard'),
    path("invoices/", invoice_list, name="invoice_list"),
    path("invoices/new/", invoice_create, name="invoice_create"),
    path("invoices/<int:pk>/", invoice_detail, name="invoice_detail"),
]
