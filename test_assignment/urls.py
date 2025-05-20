from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from core.views import BulkUploadView, IndexView, UploadPhotoView

urlpatterns = [
        path('admin/', admin.site.urls),
        path('', IndexView.as_view(), name='index'),
        path('api/upload/', UploadPhotoView.as_view(), name='upload'),
        path('api/bulk-upload/', BulkUploadView.as_view(), name='bulk-upload'),
    ] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
