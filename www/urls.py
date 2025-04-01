"""
URL configuration for www project.
"""
from django.contrib import admin
from django.conf import settings
from django.urls import path, include
from django.contrib.auth import views
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    #path('login/', views.LoginView.as_view(), name='login'),
    path("accounts/", include("django.contrib.auth.urls")),
    path('', include('index.urls')),
]

# static urls
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
