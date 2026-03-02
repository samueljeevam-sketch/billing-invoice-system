from decimal import Decimal
from django.conf import settings
from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.utils import timezone


# -----------------------
# GST VALIDATOR
# -----------------------

gst_validator = RegexValidator(
    regex=r'^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$',
    message="Enter valid GSTIN (15 characters, uppercase)"
)


# -----------------------
# Customer Model
# -----------------------

class Customer(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=15)
    address = models.TextField(blank=True, null=True)

    gst_number = models.CharField(
        max_length=15,
        blank=True,
        null=True,
        validators=[gst_validator]
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


# -----------------------
# Product Model
# -----------------------

class Product(models.Model):
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    gst_percent = models.DecimalField(max_digits=5, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.name


# -----------------------
# Invoice Model
# -----------------------

class Invoice(models.Model):

    STATUS_CHOICES = (
        ('ACTIVE', 'Active'),
        ('PENDING_CANCEL', 'Pending Cancel Approval'),
        ('CANCELLED', 'Cancelled'),
    )

    PAYMENT_STATUS_CHOICES = (
    ('UNPAID', 'Unpaid'),
    ('PAID', 'Paid'),
    )

    status = models.CharField(
    max_length=20,
    choices=STATUS_CHOICES,
    default='ACTIVE'
    )

    payment_status = models.CharField(
    max_length=10,
    choices=PAYMENT_STATUS_CHOICES,
    default='UNPAID'
)

    invoice_number = models.CharField(
        max_length=20,
        unique=True,
        null=True,
        blank=True
    )

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    invoice_date = models.DateTimeField(auto_now_add=True)

    discount_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("0.00")
    )

    invoice_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00")
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='ACTIVE'
    )

    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="approved_invoices"
    )

    approved_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        permissions = [
            ("can_approve_cancel", "Can approve invoice cancellation"),
        ]

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

    # -----------------------
    # Calculation Properties
    # -----------------------

    @property
    def subtotal(self):
        return sum(item.price for item in self.items.all())

    @property
    def discount_amount(self):
        return (self.subtotal * self.discount_percentage) / Decimal("100")

    @property
    def taxable_amount(self):
        return self.subtotal - self.discount_amount

    @property
    def total_cgst(self):
        return (self.taxable_amount * Decimal("9")) / Decimal("100")

    @property
    def total_sgst(self):
        return (self.taxable_amount * Decimal("9")) / Decimal("100")

    @property
    def total_gst(self):
        return self.total_cgst + self.total_sgst

    @property
    def grand_total(self):
        return self.taxable_amount + self.total_gst


# -----------------------
# Invoice Item Model
# -----------------------

class InvoiceItem(models.Model):

    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name="items"
    )

    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()

    price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        editable=False
    )

    cgst_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        editable=False
    )

    sgst_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        editable=False
    )

    def clean(self):
        if self.pk is None and self.quantity > self.product.stock:
            raise ValidationError(
                f"Only {self.product.stock} items left in stock"
            )

    def save(self, *args, **kwargs):
        self.clean()

        base_price = self.product.price * self.quantity

        # GST split 50/50
        total_gst = (base_price * self.product.gst_percent) / Decimal("100")
        cgst = total_gst / Decimal("2")
        sgst = total_gst / Decimal("2")

        self.price = base_price
        self.cgst_amount = cgst
        self.sgst_amount = sgst

        # Reduce stock when creating new item
        if self.pk is None:
            self.product.stock -= self.quantity
            self.product.save()

        super().save(*args, **kwargs)

        # Update invoice total using centralized calculation
        self.invoice.invoice_amount = self.invoice.grand_total
        self.invoice.save()

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"

    @property
    def total_price(self):
        return self.price + self.cgst_amount + self.sgst_amount