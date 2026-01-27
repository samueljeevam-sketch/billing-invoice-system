from django.contrib import admin
from django.forms import BaseInlineFormSet
from django.core.exceptions import ValidationError

from .models import Customer, Product, Invoice, InvoiceItem

 
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



class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 1
    readonly_fields = ('price', 'gst_amount')
    formset = InvoiceItemInlineFormSet


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    inlines = [InvoiceItemInline]
    list_display = ('id', 'customer', 'invoice_date', 'invoice_amount')
    readonly_fields = ('invoice_amount',)



@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'created_at')


# -------- PRODUCT ADMIN --------
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'gst_percent', 'stock')
