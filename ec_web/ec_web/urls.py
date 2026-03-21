# ec_web/urls.py
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView   # ✅ use this instead of Index
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin_admin/', admin.site.urls),
    path('store/',include('store.urls')),
    path('',RedirectView.as_view(url='/store/', permanent=False)),  # ✅ simple GET redirect
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)