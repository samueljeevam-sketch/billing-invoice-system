from .models import Invoice

def pending_approval_count(request):
    if request.user.is_authenticated:
        count = Invoice.objects.filter(status="PENDING_CANCEL").count()
    else:
        count = 0

    return {
        "pending_approval_count": count
    }
