from django.db import models

class Customer(models.Model):
    name=models.CharField(max_length=100)
    phone=models.CharField(max_length=15)
    address=models.TextField()
    created_at=models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class product(models.Model):
    name=models.CharField(max_length=100)
    price=models.DecimalField(max_digits=10,decimal_places=2)
    gst_percent=models.DecimalField(max_digits=12,decimal_places=2)
    stock=models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.name

class invoice(models.Model):
    customer=models.ForeignKey(Customer,on_delete=models.CASCADE)
    invoice_date=models.DateTimeField(auto_now_add=True)
    invoice_amount=models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return str(self.id)

    
class invoiceItem(models.Model):
    invoice=models.ForeignKey(invoice,on_delete=models.CASCADE)
    product=models.ForeignKey(product,on_delete=models.CASCADE)
    quantity=models.PositiveIntegerField()
    price=models.DecimalField(max_digits=12,decimal_places=2)
    gst_amount=models.DecimalField(max_digits=12,decimal_places=2)

    def save(self,*args,**kwargs):
        base_price=self.product.price*self.quantity
        gst=(base_price*self.product.gst_percent)/100

        self.price=base_price
        self.gst_amount=gst

        super().save(*args,**kwargs)

        total=sum(item.price+item.gst_amount
                  for item in self.invoice.all()
                )
        self.invoice.invoice_amount=total
        self.invoice.save()
        


    def __str__(self):
        return f"{self.product.name} - {self.quantity}"