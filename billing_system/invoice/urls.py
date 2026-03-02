from django.urls import path
from .views import *

urlpatterns = [
    path('dashboard/', dashboard, name='dashboard'),

    path("invoices/", invoice_list, name="invoice_list"),
path("invoices/new/", invoice_create, name="invoice_create"),   
path("invoices/<int:pk>/", invoice_detail, name="invoice_detail"),
path("invoices/success/<int:pk>/", invoice_success, name="invoice_success"),

path('invoice/<int:pk>/request-cancel/', request_cancel, name='request_cancel'),
path('invoice/<int:pk>/cancel/', cancel_invoice, name='cancel_invoice'),



    path("products/", product_list, name="product_list"),
    path("products/edit/<int:pk>/", product_edit, name="product_edit"),
    path("products/delete/<int:pk>/", product_delete, name="product_delete"),
    path("products/create/", product_create, name="product_create"),

    path('customers/', customer_list, name='customer_list'),
    path('customers/create/', customer_create, name='customer_create'),
    path('customers/delete/<int:pk>/', customer_delete, name='customer_delete'),
     path("customers/<int:pk>/edit/", edit_customer, name="edit_customer"),
    path("customers/delete/<int:pk>/",delete_customer, name="delete_customer"),


    path('invoice/<int:pk>/pdf/', invoice_pdf, name='invoice_pdf'),

    path('invoice/<int:pk>/mark-paid/', mark_as_paid, name='mark_as_paid'),
    path("reports/",report_dashboard, name="report_dashboard"),

    


]
