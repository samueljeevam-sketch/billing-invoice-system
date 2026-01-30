from django.shortcuts import render, get_object_or_404
from django.db.models import Sum
from .models import Customer, Invoice, InvoiceItem, Product


def dashboard(request):
    context = {
        "customer_count": Customer.objects.count(),
        "invoice_count": Invoice.objects.count(),
        "total_amount": Invoice.objects.aggregate(
            total=Sum("invoice_amount")
        )["total"] or 0,
    }
    return render(request, "invoice/dashboard.html", context)


def invoice_list(request):
    invoices = Invoice.objects.select_related("customer").order_by("-id")
    return render(request, "invoice/invoice_list.html", {
        "invoices": invoices
    })


def invoice_create(request):
    customers = Customer.objects.all()
    products = Product.objects.all()   

    if request.method == "POST":
        customer_id = request.POST.get("customer")
        invoice_date = request.POST.get("invoice_date")
        

        items_data = request.POST.getlist("product[]")
        quantities = request.POST.getlist("qty[]")
        prices = request.POST.getlist("price[]")
        customer = Customer.objects.get(id=customer_id)

        # ✅ STORE the created invoice
        invoice = Invoice.objects.create(
            customer=customer,
            invoice_date=invoice_date,
            invoice_amount=0  # Temporary, will update later
        )

        total_amount = 0

        for item, quantity, price in zip(items_data, quantities, prices):
            quantity = int(quantity)
            price = float(price)
            amount = quantity * price

            InvoiceItem.objects.create(
                invoice=invoice,
                description=item,
                quantity=quantity,
                unit_price=price,
                amount=amount,
            )

            total_amount += amount

        # ✅ update invoice total
        invoice.invoice_amount = total_amount
        invoice.save()

        return render(request, "invoice/invoice_success.html", {
            "invoice": invoice
        })

    # ✅ send customers to template
    return render(request, "invoice/new_invoice.html", {
        "customers": customers,
        "products": products
    })


def invoice_detail(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    items = InvoiceItem.objects.filter(invoice=invoice)
    return render(request, "invoice/invoice_detail.html", {
        "invoice": invoice,
        "items": items
    })
