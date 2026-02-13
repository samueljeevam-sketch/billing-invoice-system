from django.shortcuts import redirect
from django.urls import path, include
from django.contrib import admin
from django.contrib.auth import views as auth_views

def root_redirect(request):
    return redirect('/login/')

urlpatterns = [
    path('admin/', admin.site.urls),

    path('', root_redirect),  # 👈 THIS LINE

    path('login/', auth_views.LoginView.as_view(
        template_name='registration/login.html'
    ), name='login'),

    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    path('', include('invoice.urls')),
]
