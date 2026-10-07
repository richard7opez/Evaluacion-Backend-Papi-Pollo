import io
import tempfile
from pathlib import Path

from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import override_settings
from drf_spectacular.validation import validate_schema

from menu.models import Pedido, Producto
from sucursales.models import Sucursal
from .tests import ApiBase


class ApiEscrituraTests(ApiBase):
    def setUp(self):
        super().setUp()
        self.media = tempfile.TemporaryDirectory()
        self.addCleanup(self.media.cleanup)
        self.entorno = override_settings(MEDIA_ROOT=self.media.name)
        self.entorno.enable()
        self.addCleanup(self.entorno.disable)

    def datos(self, recurso):
        return {
            "productos": {"nombre": "Producto nuevo", "precio": 2000, "categoria": "Bebidas", "disponible": True},
            "sucursales": {"nombre": "Nueva", "direccion": "Calle 2", "comuna": "Coquimbo", "activa": True},
            "pedidos": {"cliente": "Prueba privada", "producto": self.producto.pk, "sucursal": self.sucursal.pk, "cantidad": 2, "estado": "pendiente"},
        }[recurso]

    def test_administrador_crud_completo_tres_entidades(self):
        self.autorizar()
        for recurso in ("productos", "sucursales", "pedidos"):
            with self.subTest(recurso=recurso):
                datos = self.datos(recurso)
                alta = self.client.post(f"/api/v1/{recurso}/", datos, format="json")
                self.assertEqual(alta.status_code, 201, alta.data)
                ruta = f"/api/v1/{recurso}/{alta.data['id']}/"
                self.assertEqual(self.client.get(ruta).status_code, 200)
                datos["estado" if recurso == "pedidos" else "nombre"] = "preparacion" if recurso == "pedidos" else "Editado"
                self.assertEqual(self.client.put(ruta, datos, format="json").status_code, 200)
                parcial = {"cantidad": 3} if recurso == "pedidos" else {"nombre": "Parcial"}
                self.assertEqual(self.client.patch(ruta, parcial, format="json").status_code, 200)
                baja = self.client.delete(ruta)
                self.assertEqual(baja.status_code, 200)
                self.assertEqual(baja.json(), {"detail": "Registro eliminado."})
                self.assertEqual(self.client.get(ruta).status_code, 404)

    def test_operador_crea_edita_no_elimina_ni_recibe_privados(self):
        self.autorizar("Operador")
        for recurso in ("productos", "sucursales", "pedidos"):
            datos = self.datos(recurso)
            alta = self.client.post(f"/api/v1/{recurso}/", datos, format="json")
            self.assertEqual(alta.status_code, 201, alta.data)
            ruta = f"/api/v1/{recurso}/{alta.data['id']}/"
            for respuesta in (alta, self.client.put(ruta, datos, format="json"), self.client.patch(ruta, {}, format="json")):
                self.assertIn(respuesta.status_code, (200, 201))
                self.assertFalse({"cliente", "observaciones", "precio_unitario", "total", "ficha_tecnica"}.intersection(respuesta.data))
            self.assertEqual(self.client.delete(ruta).status_code, 403)

    def test_sin_token_no_escribe(self):
        for recurso in ("productos", "sucursales", "pedidos"):
            self.assertEqual(self.client.post(f"/api/v1/{recurso}/", self.datos(recurso), format="json").status_code, 401)
            for metodo in ("put", "patch", "delete"):
                self.assertEqual(getattr(self.client, metodo)(f"/api/v1/{recurso}/1/", {}, format="json").status_code, 401)

    def test_validaciones_y_campos_desconocidos(self):
        self.autorizar()
        for recurso, cambio in (
            ("productos", {"precio": -1}), ("productos", {"nombre": ""}),
            ("sucursales", {"direccion": ""}), ("pedidos", {"cantidad": 0}),
            ("pedidos", {"cantidad": 10001}), ("pedidos", {"cantidad": 1.5}),
            ("pedidos", {"estado": "invalido"}), ("pedidos", {"producto": 999999}),
            ("pedidos", {"sucursal": 999999}), ("pedidos", {"precio_unitario": 1}),
            ("productos", {"is_staff": True}),
        ):
            with self.subTest(recurso=recurso, cambio=cambio):
                respuesta = self.client.post(f"/api/v1/{recurso}/", {**self.datos(recurso), **cambio}, format="json")
                self.assertEqual(respuesta.status_code, 400)
                self.assertEqual(respuesta.data["error"]["status"], 400)
        self.assertEqual(Pedido.objects.count(), 1)

    def test_put_requiere_campos_y_patch_preserva_otros(self):
        self.autorizar()
        ruta = f"/api/v1/productos/{self.producto.pk}/"
        self.assertEqual(self.client.put(ruta, {"nombre": "Falta"}, format="json").status_code, 400)
        self.assertEqual(self.client.patch(ruta, {"nombre": "Nuevo"}, format="json").status_code, 200)
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.precio, 12000)

    def test_editar_y_borrar_inexistentes(self):
        self.autorizar()
        for recurso in ("productos", "sucursales", "pedidos"):
            for metodo in ("put", "patch", "delete"):
                respuesta = getattr(self.client, metodo)(f"/api/v1/{recurso}/999999/", {}, format="json")
                self.assertEqual(respuesta.status_code, 404)

    def test_pedido_precio_historico_relaciones_y_total(self):
        self.autorizar()
        ruta = f"/api/v1/pedidos/{self.pedido.pk}/"
        self.producto.precio = 18000
        self.producto.save()
        respuesta = self.client.patch(ruta, {"cantidad": 3}, format="json")
        self.assertEqual(respuesta.data["precio_unitario"], 12000)
        self.assertEqual(respuesta.data["total"], 36000)
        otro = Producto.objects.create(nombre="Otro", precio=5000, categoria="Otro")
        respuesta = self.client.patch(ruta, {"producto": otro.pk}, format="json")
        self.assertEqual(respuesta.data["precio_unitario"], 5000)
        self.assertEqual(respuesta.data["total"], 15000)
        alta = self.client.post("/api/v1/pedidos/", self.datos("pedidos"), format="json")
        self.assertEqual(alta.data["precio_unitario"], 18000)

    def test_no_elimina_mantenedores_con_pedidos(self):
        self.autorizar()
        for recurso, objeto in (("productos", self.producto), ("sucursales", self.sucursal)):
            respuesta = self.client.delete(f"/api/v1/{recurso}/{objeto.pk}/")
            self.assertEqual(respuesta.status_code, 400)
            self.assertTrue(type(objeto).objects.filter(pk=objeto.pk).exists())
        self.assertEqual(Pedido.objects.count(), 1)

    def test_subida_imagen_y_pdf_y_descarga(self):
        self.autorizar()
        imagen = io.BytesIO()
        Image.new("RGB", (8, 8), "yellow").save(imagen, format="PNG")
        datos = self.datos("productos")
        datos["imagen"] = SimpleUploadedFile("imagen.png", imagen.getvalue(), content_type="image/png")
        datos["ficha_tecnica"] = SimpleUploadedFile("ficha.pdf", b"%PDF-1.4\n%%EOF", content_type="application/pdf")
        alta = self.client.post("/api/v1/productos/", datos, format="multipart")
        self.assertEqual(alta.status_code, 201, alta.data)
        registro = Producto.objects.get(pk=alta.data["id"])
        self.assertTrue(Path(registro.imagen.path).is_file())
        self.assertTrue(Path(registro.ficha_tecnica.path).is_file())
        respuesta = self.client.get(f"/api/v1/productos/{registro.pk}/ficha/")
        self.assertEqual(b"".join(respuesta.streaming_content), b"%PDF-1.4\n%%EOF")
        respuesta.close()

    def test_archivos_invalidos_y_limites(self):
        self.autorizar()
        ruta = f"/api/v1/productos/{self.producto.pk}/"
        for campo, nombre, contenido in (
            ("imagen", "falso.jpg", b"no es imagen"),
            ("ficha_tecnica", "archivo.txt", b"%PDF-1.4"),
            ("ficha_tecnica", "archivo.pdf", b"no es PDF"),
            ("ficha_tecnica", "grande.pdf", b"%PDF-" + b"x" * (10 * 1024 * 1024)),
        ):
            respuesta = self.client.patch(ruta, {campo: SimpleUploadedFile(nombre, contenido)}, format="multipart")
            self.assertEqual(respuesta.status_code, 400)
        imagen = io.BytesIO()
        Image.new("RGB", (8, 8)).save(imagen, format="PNG")
        respuesta = self.client.patch(ruta, {"imagen": SimpleUploadedFile("grande.png", imagen.getvalue() + b"x" * (5 * 1024 * 1024))}, format="multipart")
        self.assertEqual(respuesta.status_code, 400)

    def test_operador_no_cambia_ni_borra_documento(self):
        self.autorizar("Operador")
        ruta = f"/api/v1/productos/{self.producto.pk}/"
        self.assertEqual(self.client.patch(ruta, {"ficha_tecnica": None}, format="json").status_code, 403)
        self.assertEqual(self.client.patch(ruta, {"ficha_tecnica": SimpleUploadedFile("x.pdf", b"%PDF-1.4")}, format="multipart").status_code, 403)

    def test_error_json_malformado_y_ruta_desconocida(self):
        self.autorizar()
        respuesta = self.client.post("/api/v1/productos/", '{"nombre":', content_type="application/json")
        self.assertEqual(respuesta.status_code, 400)
        self.assertEqual(respuesta.json()["error"]["status"], 400)
        respuesta = self.client.get("/api/v1/no-existe/")
        self.assertEqual(respuesta.status_code, 404)
        self.assertEqual(respuesta.json()["error"]["status"], 404)

    def test_swagger_y_esquema_validos(self):
        respuesta = self.client.get("/api/v1/schema/")
        self.assertEqual(respuesta.status_code, 200)
        esquema = respuesta.json()
        validate_schema(esquema)
        for recurso in ("productos", "sucursales", "pedidos"):
            self.assertTrue({"get", "post"}.issubset(esquema["paths"][f"/api/v1/{recurso}/"]))
            self.assertTrue({"get", "put", "patch", "delete"}.issubset(esquema["paths"][f"/api/v1/{recurso}/{{id}}/"]))
            self.assertIn("jwtAuth", esquema["paths"][f"/api/v1/{recurso}/"]["get"]["security"][0])
        self.assertEqual(esquema["components"]["securitySchemes"]["jwtAuth"]["scheme"], "bearer")
        swagger = self.client.get("/api/v1/docs/")
        self.assertEqual(swagger.status_code, 200)
        self.assertContains(swagger, "SwaggerUIBundle")
        self.assertContains(swagger, "drf_spectacular_sidecar")

    def test_esquema_sin_advertencias(self):
        call_command("spectacular", validate=True, fail_on_warn=True, stdout=io.StringIO(), stderr=io.StringIO())
