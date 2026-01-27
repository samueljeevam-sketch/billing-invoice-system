from decimal import Decimal
from django.db import models
from django.core.exceptions import ValidationError


class Customer(models.Model):
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    address = models.TextField()
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


class Invoice(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    invoice_date = models.DateTimeField(auto_now_add=True)
    invoice_amount = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal("0.00")
    )

    def __str__(self):
        return f"Invoice #{self.id}"


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
