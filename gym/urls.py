
from django.views.static import serve
from django.conf.urls.static import static
from django.urls.conf import include, re_path
from django.urls import path
from django.contrib import admin

from gym import settings
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('memberships.urls')),
    re_path(r'admin/?', admin.site.urls),
    re_path(r'^media/(?P<path>.*)$', serve,{'document_root': settings.MEDIA_ROOT}),
    re_path(r'^static/(?P<path>.*)$', serve,{'document_root': settings.STATIC_ROOT}),
]

admin.site.site_header = 'Back Office'
admin.site.site_title = 'Admin Panel'
admin.site.index_title = 'Admin Panel'

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
