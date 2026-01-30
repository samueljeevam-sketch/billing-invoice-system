from django.shortcuts import render
from django.db.models import Sum
from .models import Customer, Invoice

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
    invoice=Invoice.objects.select_related('customer').order_by("-invoice_date")
    return render(request, "invoice/invoice_list.html", {
        "invoices": invoice})