from django.contrib import admin
from django.forms import BaseInlineFormSet
from django.core.exceptions import ValidationError

from .models import Customer, Product, Invoice, InvoiceItem


# -----------------------
# Inline Formset Validation
# -----------------------

class InvoiceItemInlineFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()

        for form in self.forms:
            if not form.cleaned_data or form.cleaned_data.get('DELETE'):
                continue

            product = form.cleaned_data.get('product')
            quantity = form.cleaned_data.get('quantity')

            if product and quantity:
                if product.stock < quantity:
                    raise ValidationError(
                        f"Not enough stock for {product.name}"
                    )


# -----------------------
# Invoice Item Inline
# -----------------------

class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 1
    readonly_fields = ('price', 'cgst_amount', 'sgst_amount')
    formset = InvoiceItemInlineFormSet


# -----------------------
# Invoice Admin
# -----------------------
@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    inlines = [InvoiceItemInline]
    list_display = (
        'id',
        'customer',
        'invoice_date',
        'invoice_amount',
        'payment_status'
    )
    readonly_fields = ('invoice_amount',)
    list_filter = ('payment_status',)
# -----------------------
# Customer Admin
# -----------------------

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'created_at')


# -----------------------
# Product Admin
# -----------------------

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'gst_percent', 'stock')