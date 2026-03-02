from decimal import Decimal
import os

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.db.models import Sum, F, ExpressionWrapper, DecimalField
from django.db.models.functions import TruncMonth
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.template.loader import render_to_string
from django.utils import timezone
from django.views.decorators.cache import never_cache

from weasyprint import HTML

from .models import Customer, Invoice, InvoiceItem, Product

os.environ["GDK_SCALE"] = "1"



@login_required
@never_cache
def dashboard(request):
    customer_count = Customer.objects.count()
    invoice_count = Invoice.objects.count()

    recent_invoices = (
        Invoice.objects
        .select_related("customer")
        .order_by("-invoice_date")[:5]
    )

    # 🔹 Total Revenue (All invoices)
    total_revenue = Invoice.objects.aggregate(
        total=Sum("invoice_amount")
    )["total"] or 0

    # 🔹 Inventory Value (price × stock)
    inventory_value_expression = ExpressionWrapper(
        F("price") * F("stock"),
        output_field=DecimalField()
    )

    inventory_value = Product.objects.aggregate(
        total=Sum(inventory_value_expression)
    )["total"] or 0

    # 🔹 Inventory Stats
    product_count = Product.objects.count()
    low_stock_threshold = 5
    low_stock_products = Product.objects.filter(stock__lte=low_stock_threshold)
    low_stock_count = low_stock_products.count()

    lowest_item = low_stock_products.order_by('stock').first()
    lowest_stock_product_name = lowest_item.name if lowest_item else "All Clear"

    context = {
        "customer_count": customer_count,
        "invoice_count": invoice_count,
        "recent_invoices": recent_invoices,
        "total_revenue": total_revenue,
        "inventory_value": inventory_value,
        "product_count": product_count,
        "low_stock_count": low_stock_count,
        "lowest_stock_product_name": lowest_stock_product_name,
    }

    return render(request, "invoice/dashboard.html", context)

 

@login_required
@never_cache
def invoice_list(request):
    invoices = Invoice.objects.all().order_by('-id')
    return render(request, 'invoice/invoice/invoice_list.html', {'invoices': invoices})




@login_required
@never_cache
def invoice_create(request):
    customers = Customer.objects.all()
    products = Product.objects.all()

    if request.method == "POST":
        customer_id = request.POST.get("customer")
        product_ids = request.POST.getlist("product[]")
        quantities = request.POST.getlist("quantity[]")

        try:
            with transaction.atomic():

                invoice = Invoice.objects.create(
                    customer_id=customer_id
                )

                for product_id, qty in zip(product_ids, quantities):
                    if not product_id or not qty:
                        continue

                    product = Product.objects.get(id=product_id)
                    quantity = int(qty)

                    item = InvoiceItem(
                        invoice=invoice,
                        product=product,
                        quantity=quantity
                    )

                    item.save()  # triggers stock validation

            # 🔥 No success message
            return redirect("invoice_success", pk=invoice.id)

        except ValidationError as e:
            messages.error(request, e.message)

    return render(request, "invoice/invoice/new_invoice.html", {
        "customers": customers,
        "products": products
    })





@login_required
@never_cache
def invoice_detail(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    items = invoice.items.all()

    totals = items.aggregate(
    subtotal=Sum("price"),
    total_cgst=Sum("cgst_amount"),
    total_sgst=Sum("sgst_amount"),
)

    subtotal = totals["subtotal"] or 0
    total_cgst = totals["total_cgst"] or 0
    total_sgst = totals["total_sgst"] or 0
    total_gst = total_cgst + total_sgst
    total = subtotal + total_gst

    return render(request, "invoice/invoice/invoicedetails.html", {
    "invoice": invoice,
    "items": items,
    "subtotal": subtotal,
    "total_cgst": total_cgst,
    "total_sgst": total_sgst,
    "total_gst": total_gst,
    "total": total,
    })



@login_required
@never_cache

def invoice_success(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    return render(request, "invoice/invoice/invoice_success.html", {
        "invoice": invoice
    })

@login_required
@transaction.atomic
@permission_required('invoice.can_approve_cancel', raise_exception=True)
def cancel_invoice(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)

    if invoice.status != 'PENDING_CANCEL':
        messages.warning(request, "Invoice must be pending approval.")
        return redirect('invoice_detail', pk=pk)

    # Restore stock
    for item in invoice.items.all():
        product = item.product
        product.stock += item.quantity
        product.save()

    invoice.status = 'CANCELLED'
    invoice.approved_by = request.user
    invoice.approved_at = timezone.now()
    invoice.save()

    messages.success(request, "Invoice cancellation approved.")
    return redirect('invoice_detail', pk=pk)



@login_required
@permission_required('invoice.change_invoice', raise_exception=True)
def request_cancel(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)

    if invoice.status != 'ACTIVE':
        messages.warning(request, "Only active invoices can be requested for cancellation.")
        return redirect('invoice_detail', pk=pk)

    invoice.status = 'PENDING_CANCEL'
    invoice.save()

    messages.success(request, "Cancellation request submitted.")
    return redirect('invoice_detail', pk=pk)


@login_required
@never_cache
def product_list(request):
    products = Product.objects.all()
    return render(request, "invoice/product/product_list.html", {"products": products})




@login_required
@never_cache
def product_edit(request, pk):
    product = get_object_or_404(Product, pk=pk)

    if request.method == "POST":
        product.name = request.POST.get("name")

        product.price = Decimal(request.POST.get("price") or 0)
        product.gst_percent = Decimal(request.POST.get("gst_percent") or 0)
        product.stock = int(request.POST.get("stock") or 0)

        product.save()
        return redirect("product_list")

    return redirect("product_list")



@login_required
@never_cache

def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)

    if request.method == "POST":
        product.delete()
        return redirect("product_list")

    return redirect("product_list")


@login_required
@never_cache
def product_create(request):
    if request.method == "POST":
        name = request.POST.get("name")
        price = request.POST.get("price")
        gst_percent = request.POST.get("gst_percent")
        stock = request.POST.get("stock")

        Product.objects.create(
            name=name,
            price=price,
            gst_percent=gst_percent,
            stock=stock
        )

        return redirect("product_list")

    return redirect("product_list")





@login_required
@never_cache
def customer_list(request):
    customers = Customer.objects.all().order_by('-id')
    return render(request, 'invoice/customer/customer_list.html', {
        'customers': customers
    })



@login_required
@never_cache
def customer_create(request):
    if request.method == "POST":
        name = request.POST.get("name")
        email = request.POST.get("email")
        phone = request.POST.get("phone")
        address = request.POST.get("address")

        Customer.objects.create(
            name=name,
            email=email,
            phone=phone,
            address=address
        )

    return redirect('customer_list')



@login_required
@never_cache
def customer_delete(request, pk):
    customer = get_object_or_404(Customer, pk=pk)

    if request.method == "POST":
        customer.delete()

    return redirect('customer_list')




@login_required
@never_cache
def invoice_pdf(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    items = invoice.items.all()

    totals = items.aggregate(
        subtotal=Sum("price"),
        total_cgst=Sum("cgst_amount"),
        total_sgst=Sum("sgst_amount"),
    )

    subtotal = totals["subtotal"] or 0
    total_cgst = totals["total_cgst"] or 0
    total_sgst = totals["total_sgst"] or 0
    total_gst = total_cgst + total_sgst
    total = subtotal + total_gst

    html_string = render_to_string(
        "invoice/invoice/invoice_page.html",
        {
            "invoice": invoice,
            "items": items,
            "subtotal": subtotal,
            "total_cgst": total_cgst,
            "total_sgst": total_sgst,
            "total_gst": total_gst,
            "total": total,
        }
    )

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="Invoice_{invoice.id}.pdf"'

    HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf(response)

    return response


@permission_required('invoice.change_invoice')
def mark_as_paid(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)

    if invoice.status == "ACTIVE":
        invoice.payment_status = "PAID"
        invoice.save()

    return redirect('invoice_detail', pk=pk)



@login_required
def report_dashboard(request):

    invoices = Invoice.objects.filter(status="ACTIVE")

    from_date = request.GET.get("from_date")
    to_date = request.GET.get("to_date")

    if from_date and to_date:
        invoices = invoices.filter(
            invoice_date__date__range=[from_date, to_date]
        )

    total_invoices = invoices.count()
    paid_invoices = invoices.filter(payment_status="PAID").count()
    unpaid_invoices = invoices.filter(payment_status="UNPAID").count()

    total_revenue = invoices.filter(payment_status="PAID") \
        .aggregate(Sum("invoice_amount"))["invoice_amount__sum"] or 0

    # GST aggregation from InvoiceItem
    gst_data = InvoiceItem.objects.filter(
        invoice__in=invoices,
        invoice__payment_status="PAID"
    ).aggregate(
        total_cgst=Sum("cgst_amount"),
        total_sgst=Sum("sgst_amount")
    )

    total_gst = (gst_data["total_cgst"] or 0) + (gst_data["total_sgst"] or 0)

    # Monthly Revenue
    monthly_data = invoices.filter(payment_status="PAID") \
        .annotate(month=TruncMonth("invoice_date")) \
        .values("month") \
        .annotate(total=Sum("invoice_amount")) \
        .order_by("month")

    labels = [entry["month"].strftime("%b %Y") for entry in monthly_data]
    values = [float(entry["total"]) for entry in monthly_data]

    context = {
        "total_invoices": total_invoices,
        "paid_invoices": paid_invoices,
        "unpaid_invoices": unpaid_invoices,
        "total_revenue": total_revenue,
        "total_gst": total_gst,
        "labels": labels,
        "values": values,
        "from_date": from_date,
        "to_date": to_date,
    }

    return render(request, "reports/dashboard.html", context)

# ----------------------------
# EDIT CUSTOMER
# ----------------------------
@login_required
def edit_customer(request, pk):

    customer = get_object_or_404(Customer, pk=pk)

    if request.method == "POST":
        customer.name = request.POST.get("name")
        customer.email = request.POST.get("email")
        customer.phone = request.POST.get("phone")
        customer.address = request.POST.get("address")
        customer.save()

        messages.success(request, "Client updated successfully.")
        return redirect("customer_list")

    return redirect("customer_list")


# ----------------------------
# DELETE CUSTOMER
# ----------------------------
@login_required
def delete_customer(request, pk):

    customer = get_object_or_404(Customer, pk=pk)

    if request.method == "POST":
        customer.delete()
        messages.success(request, "Client deleted successfully.")

    return redirect("customer_list")