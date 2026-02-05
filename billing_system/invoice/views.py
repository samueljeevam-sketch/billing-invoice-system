from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Sum
from .models import Customer, Invoice, InvoiceItem, Product
from django.db import transaction
from decimal import Decimal




def dashboard(request):
    customer_count = Customer.objects.count()
    invoice_count = Invoice.objects.count()

    recent_invoices = (
        Invoice.objects
        .select_related("customer")
        .order_by("-invoice_date")[:5]
    )

    context = {
        "customer_count": customer_count,
        "invoice_count": invoice_count,
        "recent_invoices": recent_invoices,
    }

    return render(request, "invoice/dashboard.html", context)
 


def invoice_list(request):
    invoices = Invoice.objects.select_related("customer").order_by("-id")
    return render(request, "invoice/invoice_list.html", {
        "invoices": invoices
    })





def invoice_create(request):
    if request.method == "POST":
        customer_id = request.POST.get("customer")

        invoice = Invoice.objects.create(
            customer_id=customer_id
        )

        products = request.POST.getlist("product[]")
        quantities = request.POST.getlist("quantity[]")

        for product_id, qty in zip(products, quantities):
            if not product_id or not qty:
                continue

            InvoiceItem.objects.create(
                invoice=invoice,
                product_id=product_id,
                quantity=int(qty)
            )

        # ✅ DO NOT SET invoice_amount HERE
        # Model handles it automatically

        return redirect("invoice_success", pk=invoice.id)

    return render(request, "invoice/new_invoice.html", {
        "products": Product.objects.all(),
        "customers": Customer.objects.all(),
    })




def invoice_detail(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    items = invoice.items.all()

    subtotal = items.aggregate(
        total=Sum("price")
    )["total"] or 0

    gst = items.aggregate(
        total=Sum("gst_amount")
    )["total"] or 0

    total = subtotal + gst 

    return render(request, "invoice/invoicedetails.html", {
        "invoice": invoice,
        "items": items,
        "subtotal": subtotal,
        "gst": gst,
    })

def invoice_success(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    return render(request, "invoice/invoice_success.html", {
        "invoice": invoice
    })