from django.contrib import admin
from django.urls import path
from django.views.generic import TemplateView

urlpatterns = [
    path("admin/", admin.site.urls),
    path(
        "dashboard/",
        TemplateView.as_view(template_name="invoice/dashboard.html"),
        name="dashboard",
    ),
]
