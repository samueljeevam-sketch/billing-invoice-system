from django.urls import path
from .views import *

urlpatterns = [
    path('dashboard/', dashboard, name='dashboard'),

    path("invoices/", invoice_list, name="invoice_list"),
    path("invoices/new/", invoice_create, name="invoice_create"),
    path("invoices/delete/<int:pk>/", invoice_delete, name="invoice_delete"),   
    path("invoices/<int:pk>/", invoice_detail, name="invoice_detail"),
    path("invoices/success/<int:pk>/", invoice_success, name="invoice_success"),

    path("products/", product_list, name="product_list"),
    path("products/edit/<int:pk>/", product_edit, name="product_edit"),
    path("products/delete/<int:pk>/", product_delete, name="product_delete"),
    path("products/create/", product_create, name="product_create"),

    path('customers/', customer_list, name='customer_list'),
    path('customers/create/', customer_create, name='customer_create'),
    path('customers/delete/<int:pk>/', customer_delete, name='customer_delete'),
]
