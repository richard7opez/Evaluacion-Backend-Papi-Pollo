import io
import tempfile
from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import override_settings
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from menu.models import Pedido, Producto
from sucursales.models import Sucursal


class ApiBase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("configurar_roles", stdout=io.StringIO())
        cls.usuarios = {}
        for rol in ("Administrador", "Operador", "Consulta"):
            usuario = get_user_model().objects.create_user(
                username=rol.lower(), password="Clave-ficticia-de-test-2026!"
            )
            usuario.groups.add(Group.objects.get(name=rol))
            cls.usuarios[rol] = usuario
        cls.sin_rol = get_user_model().objects.create_user(username="sin_rol")
        cls.producto = Producto.objects.create(nombre="Pollo prueba", precio=12000, categoria="Asados")
        cls.sucursal = Sucursal.objects.create(nombre="Centro prueba", direccion="Calle 1", comuna="Coquimbo")
        cls.pedido = Pedido.objects.create(
            producto=cls.producto, sucursal=cls.sucursal, cantidad=2,
            cliente="Cliente privado", observaciones="Nota privada",
        )

    def setUp(self):
        cache.clear()

    def autorizar(self, rol="Administrador"):
        token = RefreshToken.for_user(self.usuarios[rol]).access_token
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")


class ApiConsultaTests(ApiBase):
    def test_listados_y_detalles_requieren_jwt(self):
        for recurso in ("productos", "sucursales", "pedidos"):
            for ruta in (f"/api/v1/{recurso}/", f"/api/v1/{recurso}/1/"):
                with self.subTest(ruta=ruta):
                    respuesta = self.client.get(ruta)
                    self.assertEqual(respuesta.status_code, 401)
                    self.assertEqual(respuesta.json()["error"]["status"], 401)
        self.client.force_login(self.usuarios["Administrador"])
        self.assertEqual(self.client.get("/api/v1/productos/").status_code, 401)

    def test_usuario_sin_permisos_recibe_403(self):
        token = RefreshToken.for_user(self.sin_rol).access_token
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        for recurso in ("productos", "sucursales", "pedidos"):
            self.assertEqual(self.client.get(f"/api/v1/{recurso}/").status_code, 403)

    def test_tres_roles_consultan_relaciones_y_paginacion(self):
        for rol in self.usuarios:
            self.autorizar(rol)
            for recurso in ("productos", "sucursales", "pedidos"):
                respuesta = self.client.get(f"/api/v1/{recurso}/")
                self.assertEqual(respuesta.status_code, 200)
                self.assertEqual(respuesta.json()["count"], 1)
                self.assertEqual(len(respuesta.json()["results"]), 1)
            detalle = self.client.get(f"/api/v1/pedidos/{self.pedido.pk}/").json()
            self.assertEqual(detalle["producto"], self.producto.pk)
            self.assertEqual(detalle["sucursal"], self.sucursal.pk)
            self.assertEqual(detalle["producto_nombre"], self.producto.nombre)

    def test_campos_privados_se_filtran_en_listado_y_detalle(self):
        privados = {"cliente", "observaciones", "precio_unitario", "total"}
        for rol in ("Operador", "Consulta"):
            self.autorizar(rol)
            listado = self.client.get("/api/v1/pedidos/").json()["results"][0]
            detalle = self.client.get(f"/api/v1/pedidos/{self.pedido.pk}/").json()
            self.assertFalse(privados.intersection(listado))
            self.assertFalse(privados.intersection(detalle))
            producto = self.client.get(f"/api/v1/productos/{self.producto.pk}/").json()
            self.assertNotIn("ficha_tecnica", producto)
            self.assertEqual(producto["precio"], 12000)
        self.autorizar()
        detalle = self.client.get(f"/api/v1/pedidos/{self.pedido.pk}/").json()
        self.assertTrue(privados.issubset(detalle))
        self.assertEqual(detalle["total"], 24000)

    def test_busqueda_operacional_sin_filtrar_datos_privados(self):
        self.autorizar("Consulta")
        for recurso in ("productos", "sucursales", "pedidos"):
            self.assertEqual(self.client.get(f"/api/v1/{recurso}/?search=prueba").json()["count"], 1)
            self.assertEqual(self.client.get(f"/api/v1/{recurso}/?search=inexistente").json()["count"], 0)
        self.assertEqual(self.client.get("/api/v1/pedidos/?search=privado").json()["count"], 0)

    def test_404_json(self):
        self.autorizar()
        respuesta = self.client.get("/api/v1/productos/999999/")
        self.assertEqual(respuesta.status_code, 404)
        self.assertEqual(respuesta.json()["error"]["status"], 404)

    def test_paginacion_real_sin_duplicados(self):
        for numero in range(21):
            Producto.objects.create(nombre=f"Producto {numero:02}", precio=1000, categoria="Prueba")
        self.autorizar("Consulta")
        primera = self.client.get("/api/v1/productos/").json()
        self.assertEqual(primera["count"], 22)
        self.assertEqual(len(primera["results"]), 20)
        self.assertIsNotNone(primera["next"])
        segunda = self.client.get(primera["next"]).json()
        self.assertEqual(len(segunda["results"]), 2)
        self.assertIsNone(segunda["next"])
        ids = [fila["id"] for fila in primera["results"] + segunda["results"]]
        self.assertEqual(len(set(ids)), 22)

    def test_detalles_sin_permisos_no_exponen_entidades(self):
        token = RefreshToken.for_user(self.sin_rol).access_token
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        for recurso, registro in (
            ("productos", self.producto), ("sucursales", self.sucursal), ("pedidos", self.pedido),
        ):
            with self.subTest(recurso=recurso):
                respuesta = self.client.get(f"/api/v1/{recurso}/{registro.pk}/")
                self.assertEqual(respuesta.status_code, 403)
                self.assertEqual(set(respuesta.json()), {"error"})

    def test_ficha_ausente_devuelve_404_json(self):
        self.autorizar()
        ruta = f"/api/v1/productos/{self.producto.pk}/ficha/"
        self.assertEqual(self.client.get(ruta).status_code, 404)
        with tempfile.TemporaryDirectory() as carpeta, override_settings(MEDIA_ROOT=carpeta):
            self.producto.ficha_tecnica = "documentos/productos/ausente.pdf"
            self.producto.save(update_fields=["ficha_tecnica"])
            respuesta = self.client.get(ruta)
            self.assertEqual(respuesta.status_code, 404)
            self.assertEqual(respuesta.json()["error"]["status"], 404)
            self.assertNotIn(carpeta, respuesta.content.decode())

    def test_consulta_no_puede_escribir(self):
        self.autorizar("Consulta")
        for recurso in ("productos", "sucursales", "pedidos"):
            for metodo, sufijo in (("post", ""), ("put", "1/"), ("patch", "1/"), ("delete", "1/")):
                respuesta = getattr(self.client, metodo)(f"/api/v1/{recurso}/{sufijo}", {}, format="json")
                self.assertEqual(respuesta.status_code, 403)
        self.assertEqual(Pedido.objects.count(), 1)

    def test_obtener_y_renovar_tokens_sin_actualizar_usuario(self):
        respuesta = self.client.post("/api/v1/token/", {
            "username": "operador", "password": "Clave-ficticia-de-test-2026!",
        }, format="json")
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(set(respuesta.json()), {"access", "refresh"})
        renovacion = self.client.post("/api/v1/token/refresh/", {
            "refresh": respuesta.json()["refresh"],
        }, format="json")
        self.assertEqual(renovacion.status_code, 200)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {renovacion.json()['access']}")
        self.assertEqual(self.client.get("/api/v1/productos/").status_code, 200)
        self.usuarios["Operador"].refresh_from_db()
        self.assertIsNone(self.usuarios["Operador"].last_login)

    def test_credenciales_y_payload_invalidos(self):
        self.assertEqual(self.client.post("/api/v1/token/", {}, format="json").status_code, 400)
        self.assertEqual(self.client.post("/api/v1/token/", {
            "username": "operador", "password": "incorrecta",
        }, format="json").status_code, 401)
        self.assertEqual(self.client.post("/api/v1/token/refresh/", {
            "refresh": "invalido",
        }, format="json").status_code, 401)

    def test_token_vencido_o_incorrecto_no_autoriza(self):
        token = RefreshToken.for_user(self.usuarios["Operador"]).access_token
        token.set_exp(lifetime=timedelta(seconds=-60))
        for valor in (str(token), "invalido", str(RefreshToken.for_user(self.usuarios["Operador"]))):
            self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {valor}")
            self.assertEqual(self.client.get("/api/v1/productos/").status_code, 401)

    def test_usuario_inactivo_no_accede_ni_renueva(self):
        usuario = self.usuarios["Operador"]
        token = RefreshToken.for_user(usuario)
        usuario.is_active = False
        usuario.save(update_fields=["is_active"])
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")
        self.assertEqual(self.client.get("/api/v1/productos/").status_code, 401)
        self.client.credentials()
        self.assertEqual(self.client.post("/api/v1/token/refresh/", {"refresh": str(token)}, format="json").status_code, 401)

    def test_usuario_eliminado_no_renueva(self):
        token = RefreshToken.for_user(self.usuarios["Operador"])
        self.usuarios["Operador"].delete()
        self.assertEqual(self.client.post("/api/v1/token/refresh/", {"refresh": str(token)}, format="json").status_code, 401)

    def test_cambio_de_contrasena_invalida_tokens(self):
        usuario = self.usuarios["Operador"]
        token = RefreshToken.for_user(usuario)
        usuario.set_password("Otra-clave-ficticia-2026!")
        usuario.save(update_fields=["password"])
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")
        self.assertEqual(self.client.get("/api/v1/productos/").status_code, 401)
        self.client.credentials()
        self.assertEqual(self.client.post("/api/v1/token/refresh/", {"refresh": str(token)}, format="json").status_code, 401)

    def test_permisos_se_revisan_aunque_token_siga_vigente(self):
        self.autorizar("Operador")
        self.usuarios["Operador"].groups.clear()
        self.assertEqual(self.client.get("/api/v1/productos/").status_code, 403)

    def test_documento_jwt_sin_exponer_ruta_de_almacenamiento(self):
        with tempfile.TemporaryDirectory() as carpeta, override_settings(MEDIA_ROOT=carpeta):
            self.producto.ficha_tecnica.save("prueba.pdf", SimpleUploadedFile("prueba.pdf", b"%PDF-1.4\nprueba"))
            self.autorizar()
            datos = self.client.get(f"/api/v1/productos/{self.producto.pk}/").json()
            self.assertIn(f"/api/v1/productos/{self.producto.pk}/ficha/", datos["ficha_tecnica"])
            ruta = f"/api/v1/productos/{self.producto.pk}/ficha/"
            respuesta = self.client.get(ruta)
            self.assertEqual(respuesta.status_code, 200)
            self.assertTrue(b"".join(respuesta.streaming_content).startswith(b"%PDF-"))
            respuesta.close()
            for rol in ("Operador", "Consulta"):
                self.autorizar(rol)
                self.assertEqual(self.client.get(ruta).status_code, 403)
            self.client.credentials()
            self.assertEqual(self.client.get(ruta).status_code, 401)

    def test_error_interno_no_expone_detalles(self):
        self.autorizar()
        with patch("api.views.ProductoViewSet.get_queryset", side_effect=RuntimeError("secreto-no-exponer")):
            with self.assertLogs("api.exceptions", level="ERROR"):
                respuesta = self.client.get("/api/v1/productos/")
        self.assertEqual(respuesta.status_code, 500)
        self.assertNotIn("secreto-no-exponer", respuesta.content.decode())

    def test_token_limita_intentos(self):
        for _ in range(10):
            self.assertEqual(self.client.post("/api/v1/token/", {}, format="json").status_code, 400)
        self.assertEqual(self.client.post("/api/v1/token/", {}, format="json").status_code, 429)
