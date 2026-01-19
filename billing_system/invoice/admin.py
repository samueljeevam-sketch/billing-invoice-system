from django.contrib import admin
from .models import Customer,product,invoice,invoiceItem

class Invoiceiteminline(admin.TabularInline):
    model=invoiceItem
    extra=1

@admin.register(invoice)

class invoiceadmin(admin.ModelAdmin):
    inlines=[Invoiceiteminline]
    list_display=('id','customer','invoice_date','invoice_amount')
    readonly_fields=('invoice_amount',)

admin.site.register(Customer)
admin.site.register(product)


# Register your models here.
