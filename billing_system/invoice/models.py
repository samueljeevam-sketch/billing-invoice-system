from decimal import Decimal
from django.conf import settings
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db.models import Sum, F, ExpressionWrapper, DecimalField


class Customer(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(blank=True, null=True)   # ✅ Added
    phone = models.CharField(max_length=15)
    address = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name



class Product(models.Model):
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    gst_percent = models.DecimalField(max_digits=5, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.name
    @property
    def price_with_gst(self):
        return self.price + (self.price * self.gst_percent / 100)


class Invoice(models.Model):

    STATUS_CHOICES = (
        ('ACTIVE', 'Active'),
        ('PENDING_CANCEL', 'Pending Cancel Approval'),
        ('CANCELLED', 'Cancelled'),
    )

    invoice_number = models.CharField(
        max_length=20,
        unique=True,
        null=True,
        blank=True
    )
    approved_by = models.ForeignKey(
    settings.AUTH_USER_MODEL,
    null=True,
    blank=True,
    on_delete=models.SET_NULL,
    related_name="approved_invoices"
    )

    approved_at = models.DateTimeField(null=True, blank=True)


    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    invoice_date = models.DateTimeField(auto_now_add=True)

    invoice_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00")
    )

    gst_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=12.00
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='ACTIVE'
    )

    created_at = models.DateTimeField(default=timezone.now)

    def save(self, *args, **kwargs):
        if not self.invoice_number:
            last_invoice = Invoice.objects.order_by('-id').first()

            if last_invoice and last_invoice.invoice_number:
                last_number = int(last_invoice.invoice_number.split('-')[-1])
                new_number = last_number + 1
            else:
                new_number = 1

            self.invoice_number = f"INV-{new_number:04d}"

        super().save(*args, **kwargs)

    def __str__(self):
        return self.invoice_number

    class Meta:
        permissions = [
            ("can_approve_cancel", "Can approve invoice cancellation"),
        ]



class InvoiceItem(models.Model):
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name="items"
    )
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(
        max_digits=12, decimal_places=2, editable=False
    )
    gst_amount = models.DecimalField(
        max_digits=12, decimal_places=2, editable=False
    )

    def clean(self):
        """Validate stock before saving"""
        if self.pk is None and self.quantity > self.product.stock:
            raise ValidationError(
                f"Only {self.product.stock} items left in stock"
            )

    def save(self, *args, **kwargs):
        self.clean()

        base_price = self.product.price * self.quantity
        gst = (base_price * self.product.gst_percent) / Decimal("100")

        self.price = base_price
        self.gst_amount = gst

        if self.pk is None:
            self.product.stock -= self.quantity
            self.product.save()

        super().save(*args, **kwargs)

        total = sum(
            item.price + item.gst_amount
            for item in self.invoice.items.all()
        )

        self.invoice.invoice_amount = total
        self.invoice.save()

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"
    
    @property
    def total_price(self):
        return self.quantity * self.price
    

