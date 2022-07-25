from django.conf.urls import url
from django.views.decorators.csrf import csrf_exempt

from . import views
from .views import MyChunkedUploadCompleteView, MyChunkedUploadView

urlpatterns = [
    url('api/chunked_upload/', csrf_exempt(MyChunkedUploadView.as_view()), name='api_chunked_upload'),
    url(r'^api/chunked_upload_complete/', csrf_exempt(MyChunkedUploadCompleteView.as_view()), name='api_chunked_upload_async'),
]