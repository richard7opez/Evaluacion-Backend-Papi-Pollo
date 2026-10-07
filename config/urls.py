from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from menu.gestion import documento_media


urlpatterns = [
    path('api/v1/', include('api.urls')),
    path('admin/', admin.site.urls),
    path('cuentas/login/', auth_views.LoginView.as_view(), name='login'),
    path('cuentas/logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('gestion/', include('menu.gestion_urls')),
    path('media/documentos/productos/<path:nombre>', documento_media, name='documento_media'),
    path('', include('menu.urls')),
    path('sucursales/', include('sucursales.urls')),
]


# Permite mostrar las imágenes subidas desde Django Admin
if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )
