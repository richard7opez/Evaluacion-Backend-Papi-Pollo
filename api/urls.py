from django.urls import include, path
from rest_framework.routers import SimpleRouter
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from drf_spectacular.renderers import OpenApiJsonRenderer

from .views import (
    ObtenerTokenView, RenovarTokenView,
    PedidoViewSet, ProductoViewSet, SucursalViewSet,
    RutaNoEncontradaView,
)


app_name = "api"
router = SimpleRouter()
router.register("productos", ProductoViewSet, basename="producto")
router.register("sucursales", SucursalViewSet, basename="sucursal")
router.register("pedidos", PedidoViewSet, basename="pedido")

urlpatterns = [
    path("schema/", SpectacularAPIView.as_view(renderer_classes=[OpenApiJsonRenderer]), name="schema"),
    path("docs/", SpectacularSwaggerView.as_view(url_name="api:schema"), name="swagger"),
    path("token/", ObtenerTokenView.as_view(), name="token"),
    path("token/refresh/", RenovarTokenView.as_view(), name="token-refresh"),
    path("", include(router.urls)),
    path("<path:ruta>", RutaNoEncontradaView.as_view()),
]
