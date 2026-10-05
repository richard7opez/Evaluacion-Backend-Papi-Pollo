import io
import tempfile
from pathlib import Path
from unittest.mock import patch

from PIL import Image
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import IntegrityError, transaction
from django.test import Client, TestCase, override_settings

from sucursales.models import Sucursal
from .models import Pedido, Producto


class GestionTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("configurar_roles", stdout=io.StringIO())
        cls.usuarios = {}
        for rol in ("Administrador", "Operador", "Consulta"):
            user = get_user_model().objects.create_user(username=rol.lower(), password="Prueba-local-2026!", is_staff=rol == "Administrador")
            user.groups.add(Group.objects.get(name=rol))
            cls.usuarios[rol] = user
        cls.producto = Producto.objects.create(nombre="Pollo", precio=12000, categoria="Asados")
        cls.sucursal = Sucursal.objects.create(nombre="Centro", direccion="Calle 1", comuna="Coquimbo")
        cls.pedido = Pedido.objects.create(producto=cls.producto, sucursal=cls.sucursal, cliente="Cliente inicial", cantidad=2)

    def setUp(self):
        self.media = tempfile.TemporaryDirectory()
        self.addCleanup(self.media.cleanup)
        self.override = override_settings(MEDIA_ROOT=self.media.name)
        self.override.enable()
        self.addCleanup(self.override.disable)

    def login(self, rol):
        self.client.force_login(self.usuarios[rol])

    def payload(self, entidad):
        return {
            "productos": {"nombre": "Nuevo producto", "precio": 1500, "categoria": "Bebidas", "disponible": "on"},
            "sucursales": {"nombre": "Nueva sucursal", "direccion": "Calle 2", "comuna": "La Serena", "activa": "on"},
            "pedidos": {"cliente": "Nuevo cliente", "producto": self.producto.pk, "sucursal": self.sucursal.pk, "cantidad": 3, "estado": "pendiente"},
        }[entidad]

    def test_publico_y_orm_sin_json(self):
        from django.test import RequestFactory
        from .views import productos
        with patch("builtins.open", side_effect=AssertionError("No debe leer JSON")), patch("menu.views.render") as render:
            productos(RequestFactory().get("/productos/"))
            self.assertEqual(list(render.call_args.args[2]["productos"]), [self.producto])
        for url in ("/", "/productos/", "/sucursales/", "/sucursales/listado/"):
            self.assertEqual(self.client.get(url).status_code, 200)

    def test_inicio_muestra_datos_reales_y_actualizados(self):
        self.producto.nombre = "Producto de prueba local"
        self.producto.precio = 9876
        self.producto.save()
        response = self.client.get("/")
        self.assertContains(response, self.producto.nombre)
        self.assertContains(response, "$9876")
        self.assertContains(response, self.sucursal.direccion)
        self.assertContains(response, self.sucursal.comuna)
        self.assertEqual(list(response.context["productos_destacados"]), [self.producto])
        self.producto.disponible = False
        self.producto.save()
        self.sucursal.activa = False
        self.sucursal.save()
        response = self.client.get("/")
        self.assertNotContains(response, self.producto.nombre)
        self.assertNotContains(response, self.sucursal.direccion)
        self.assertContains(response, "No hay sucursales disponibles.")

    def test_inicio_limita_destacados_y_menu_conserva_catalogo(self):
        for n in range(5):
            Producto.objects.create(nombre=f"Destacado {n}", precio=2000, categoria="Otros")
        self.assertEqual(len(self.client.get("/").context["productos_destacados"]), 4)
        self.assertEqual(len(self.client.get("/productos/").context["productos"]), 6)

    def test_anonimo_y_usuario_sin_perfil(self):
        for entidad in ("productos", "sucursales", "pedidos"):
            for suffix in ("", "agregar/", "1/editar/", "1/eliminar/"):
                response = self.client.get(f"/gestion/{entidad}/{suffix}")
                self.assertEqual(response.status_code, 302)
                self.assertIn("/cuentas/login/", response.url)
        self.client.force_login(get_user_model().objects.create_user(username="sinperfil"))
        for entidad in ("productos", "sucursales", "pedidos"):
            self.assertEqual(self.client.get(f"/gestion/{entidad}/").status_code, 403)
            self.assertEqual(self.client.post(f"/gestion/{entidad}/agregar/", self.payload(entidad)).status_code, 403)

    def test_consulta_no_puede_mutar_por_url(self):
        self.login("Consulta")
        for entidad, registro in (("productos", self.producto), ("sucursales", self.sucursal), ("pedidos", self.pedido)):
            self.assertEqual(self.client.get(f"/gestion/{entidad}/").status_code, 200)
            for suffix in ("agregar/", f"{registro.pk}/editar/", f"{registro.pk}/eliminar/"):
                with self.subTest(entidad=entidad, suffix=suffix):
                    self.assertEqual(self.client.get(f"/gestion/{entidad}/{suffix}").status_code, 403)
                    self.assertEqual(self.client.post(f"/gestion/{entidad}/{suffix}", self.payload(entidad)).status_code, 403)

    def test_operador_crud_sin_eliminar(self):
        self.login("Operador")
        for entidad, model in (("productos", Producto), ("sucursales", Sucursal), ("pedidos", Pedido)):
            data = self.payload(entidad)
            self.assertEqual(self.client.post(f"/gestion/{entidad}/agregar/", data).status_code, 302)
            item = model.objects.order_by("-pk").first()
            self.assertEqual(self.client.get(f"/gestion/{entidad}/{item.pk}/editar/").status_code, 200)
            campo = "cliente" if entidad == "pedidos" else "nombre"
            data[campo] = "Modificado"
            self.assertEqual(self.client.post(f"/gestion/{entidad}/{item.pk}/editar/", data).status_code, 302)
            item.refresh_from_db()
            self.assertEqual(getattr(item, campo), "Modificado")
            self.assertEqual(self.client.post(f"/gestion/{entidad}/{item.pk}/eliminar/").status_code, 403)
            self.assertTrue(model.objects.filter(pk=item.pk).exists())
        self.assertEqual(self.client.get("/admin/auth/user/").status_code, 302)

    def test_administrador_crud_confirmacion_y_usuarios(self):
        self.login("Administrador")
        for entidad, model in (("productos", Producto), ("sucursales", Sucursal), ("pedidos", Pedido)):
            data = self.payload(entidad)
            self.assertEqual(self.client.post(f"/gestion/{entidad}/agregar/", data).status_code, 302)
            item = model.objects.order_by("-pk").first()
            self.assertEqual(self.client.post(f"/gestion/{entidad}/{item.pk}/editar/", data).status_code, 302)
            url = f"/gestion/{entidad}/{item.pk}/eliminar/"
            self.assertEqual(self.client.get(url).status_code, 200)
            self.assertTrue(model.objects.filter(pk=item.pk).exists())
            self.assertEqual(self.client.post(url).status_code, 302)
            self.assertFalse(model.objects.filter(pk=item.pk).exists())
        self.assertEqual(self.client.get("/admin/auth/user/").status_code, 200)

    def test_proteccion_de_relaciones(self):
        self.login("Administrador")
        for entidad, item in (("productos", self.producto), ("sucursales", self.sucursal)):
            response = self.client.post(f"/gestion/{entidad}/{item.pk}/eliminar/", follow=True)
            self.assertContains(response, "hay pedidos asociados")
            self.assertTrue(type(item).objects.filter(pk=item.pk).exists())

    def test_precio_historico(self):
        self.producto.precio = 14000
        self.producto.save()
        self.pedido.cantidad = 3
        self.pedido.save()
        self.assertEqual(self.pedido.precio_unitario, 12000)
        self.assertEqual(self.pedido.total, 36000)
        self.pedido.producto = Producto.objects.create(nombre="Agua", precio=1000, categoria="Bebidas")
        self.pedido.save()
        self.assertEqual(self.pedido.precio_unitario, 1000)

    def test_guardado_parcial_no_cambia_precio_de_otro_producto(self):
        self.pedido.producto = Producto.objects.create(nombre="Otro", precio=1000, categoria="Otros")
        self.pedido.estado = Pedido.Estado.ENTREGADO
        self.pedido.save(update_fields=["estado"])
        self.pedido.refresh_from_db()
        self.assertEqual(self.pedido.producto_id, self.producto.pk)
        self.assertEqual(self.pedido.precio_unitario, 12000)
        self.assertEqual(self.pedido.estado, Pedido.Estado.ENTREGADO)

    def test_detalle_consulta_y_acceso_protegido(self):
        self.pedido.observaciones = "Entregar en recepción"
        self.pedido.save(update_fields=["observaciones"])
        for entidad, item in (("productos", self.producto), ("sucursales", self.sucursal), ("pedidos", self.pedido)):
            self.client.logout()
            url = f"/gestion/{entidad}/{item.pk}/"
            self.assertEqual(self.client.get(url).status_code, 302)
            self.login("Consulta")
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            self.assertNotContains(response, "/editar/")
            self.assertNotContains(response, "/eliminar/")
            if entidad == "pedidos":
                self.assertContains(response, "Entregar en recepción")
                self.assertContains(response, self.producto.nombre)
                self.assertContains(response, self.sucursal.nombre)

    def test_validaciones(self):
        self.login("Operador")
        for cambios in ({"cantidad": 0}, {"cantidad": -1}, {"cantidad": 10001}, {"producto": 999999}, {"sucursal": 999999}, {"cliente": ""}, {"estado": "inventado"}):
            response = self.client.post("/gestion/pedidos/agregar/", self.payload("pedidos") | cambios)
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.context["form"].errors)
        self.assertEqual(Pedido.objects.count(), 1)
        for entidad in ("productos", "sucursales"):
            self.assertTrue(self.client.post(f"/gestion/{entidad}/agregar/", {}).context["form"].errors)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Pedido.objects.filter(pk=self.pedido.pk).update(cantidad=0)

    def test_busqueda_y_filtros(self):
        self.login("Consulta")
        Producto.objects.create(nombre="Oculto", precio=1000, categoria="Otros", disponible=False)
        self.assertEqual(self.client.get("/gestion/productos/").context["pagina"].paginator.count, 2)
        self.assertEqual(self.client.get("/gestion/productos/", {"estado": "0"}).context["pagina"].paginator.count, 1)
        for entidad, query in (("productos", "Asados"), ("sucursales", "Coquimbo"), ("pedidos", "Centro"), ("pedidos", str(self.pedido.pk))):
            self.assertEqual(self.client.get(f"/gestion/{entidad}/", {"q": query}).context["pagina"].paginator.count, 1)
        self.assertEqual(self.client.get("/gestion/pedidos/", {"estado": "entregado"}).context["pagina"].paginator.count, 0)

    def test_archivos_y_descarga_protegida(self):
        self.login("Operador")
        buffer = io.BytesIO()
        Image.new("RGB", (8, 8), "red").save(buffer, format="PNG")
        data = self.payload("productos") | {
            "imagen": SimpleUploadedFile("imagen.png", buffer.getvalue(), content_type="image/png"),
            "ficha_tecnica": SimpleUploadedFile("ficha.pdf", b"%PDF-1.4\n%%EOF", content_type="application/pdf"),
        }
        self.assertEqual(self.client.post("/gestion/productos/agregar/", data).status_code, 302)
        producto = Producto.objects.order_by("-pk").first()
        self.assertTrue(Path(producto.imagen.path).exists())
        self.assertTrue(Path(producto.ficha_tecnica.path).exists())
        self.assertContains(self.client.get("/productos/"), producto.imagen.url)
        self.login("Consulta")
        for url in (f"/gestion/productos/{producto.pk}/ficha/", producto.ficha_tecnica.url):
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            self.assertTrue(b"".join(response.streaming_content).startswith(b"%PDF"))
            response.close()
        self.client.logout()
        self.assertEqual(self.client.get(producto.ficha_tecnica.url).status_code, 302)

    def test_archivos_invalidos(self):
        self.login("Operador")
        for field, upload in (
            ("imagen", SimpleUploadedFile("falsa.png", b"no es imagen", content_type="image/png")),
            ("ficha_tecnica", SimpleUploadedFile("falso.pdf", b"no es PDF", content_type="application/pdf")),
        ):
            response = self.client.post("/gestion/productos/agregar/", self.payload("productos") | {field: upload})
            self.assertEqual(response.status_code, 200)
            self.assertIn(field, response.context["form"].errors)
        self.assertEqual(Producto.objects.count(), 1)

    def test_login_logout_y_csrf(self):
        client = Client(enforce_csrf_checks=True)
        client.get("/cuentas/login/")
        response = client.post("/cuentas/login/", {
            "username": "consulta", "password": "Prueba-local-2026!",
            "csrfmiddlewaretoken": client.cookies["csrftoken"].value, "next": "https://example.org/",
        })
        self.assertRedirects(response, "/")
        self.assertEqual(client.get("/cuentas/logout/").status_code, 405)
        self.assertEqual(client.post("/cuentas/logout/").status_code, 403)
        self.assertEqual(client.post("/cuentas/logout/", {"csrfmiddlewaretoken": client.cookies["csrftoken"].value}).status_code, 302)
        self.assertNotIn("_auth_user_id", client.session)
        client.force_login(self.usuarios["Administrador"])
        for entidad in ("productos", "sucursales", "pedidos"):
            self.assertEqual(client.post(f"/gestion/{entidad}/agregar/", self.payload(entidad)).status_code, 403)

    def test_menu_y_acciones(self):
        self.assertNotContains(self.client.get("/"), "/gestion/pedidos/")
        for rol in ("Administrador", "Operador", "Consulta"):
            self.login(rol)
            self.assertContains(self.client.get("/"), "/gestion/pedidos/")
            response = self.client.get("/gestion/productos/")
            if rol == "Consulta":
                self.assertNotContains(response, "/agregar/")
                self.assertNotContains(response, "/editar/")
            else:
                self.assertContains(response, "/agregar/")
                self.assertContains(response, "/editar/")
            if rol != "Administrador":
                self.assertNotContains(response, "/eliminar/")

    def test_roles_idempotentes(self):
        call_command("configurar_roles", stdout=io.StringIO())
        self.assertEqual(Group.objects.filter(name__in=("Administrador", "Operador", "Consulta")).count(), 3)
        call_command("configurar_roles", usuario="consulta", rol="Operador", stdout=io.StringIO())
        user = get_user_model().objects.get(username="consulta")
        self.assertTrue(user.has_perm("menu.add_pedido"))
        self.assertFalse(user.has_perm("menu.delete_pedido"))
        self.assertFalse(user.has_perm("auth.change_user"))
        self.assertFalse(user.is_staff)

    def test_crear_usuarios_por_perfil_y_login(self):
        for rol in ("Administrador", "Operador", "Consulta"):
            nombre = "nuevo_" + rol.lower()
            password = "Prueba-local-segura-2026!"
            with patch("menu.management.commands.configurar_roles.getpass", side_effect=[password, password]):
                call_command("configurar_roles", usuario=nombre, rol=rol, crear=True, stdout=io.StringIO())
            user = get_user_model().objects.get(username=nombre)
            self.assertFalse(user.is_superuser)
            self.assertEqual(user.is_staff, rol == "Administrador")
            self.assertEqual(list(user.groups.values_list("name", flat=True)), [rol])
            self.assertTrue(self.client.login(username=nombre, password=password))
            self.assertEqual(self.client.get("/gestion/pedidos/").status_code, 200)
            self.assertEqual(self.client.get("/gestion/pedidos/agregar/").status_code, 403 if rol == "Consulta" else 200)
            self.assertEqual(self.client.post(f"/gestion/productos/{self.producto.pk}/eliminar/").status_code, 302 if rol == "Administrador" else 403)
            self.client.logout()

    def test_crear_usuario_rechaza_password_debil_o_distinto(self):
        for contrasenas in (("123", "123"), ("Prueba-local-segura-2026!", "Distinta")):
            with patch("menu.management.commands.configurar_roles.getpass", side_effect=contrasenas):
                with self.assertRaises(CommandError):
                    call_command("configurar_roles", usuario="nuevo", rol="Operador", crear=True, stdout=io.StringIO())
            self.assertFalse(get_user_model().objects.filter(username="nuevo").exists())

    def test_crear_usuario_no_sobrescribe_cuentas(self):
        original = get_user_model().objects.get(username="operador").password
        with self.assertRaises(CommandError):
            call_command("configurar_roles", usuario="operador", rol="Consulta", crear=True, stdout=io.StringIO())
        user = get_user_model().objects.get(username="operador")
        self.assertEqual(user.password, original)
        self.assertEqual(list(user.groups.values_list("name", flat=True)), ["Operador"])

    def test_admin_crud_de_las_tres_entidades(self):
        self.login("Administrador")
        for entidad, model in (("productos", Producto), ("sucursales", Sucursal), ("pedidos", Pedido)):
            base = f"/admin/{model._meta.app_label}/{model._meta.model_name}/"
            self.assertEqual(self.client.get(base + "add/").status_code, 200)
            data = self.payload(entidad)
            self.assertEqual(self.client.post(base + "add/", data | {"_save": "Guardar"}).status_code, 302)
            item = model.objects.order_by("-pk").first()
            self.assertContains(self.client.get(base, {"q": "Nuevo"}), str(item))
            self.assertEqual(self.client.get(base + f"{item.pk}/change/").status_code, 200)
            self.assertEqual(self.client.post(base + f"{item.pk}/change/", data | {"_save": "Guardar"}).status_code, 302)
            self.assertEqual(self.client.get(base + f"{item.pk}/delete/").status_code, 200)
            self.assertEqual(self.client.post(base + f"{item.pk}/delete/", {"post": "yes"}).status_code, 302)
            self.assertFalse(model.objects.filter(pk=item.pk).exists())

    def test_foreign_keys_rechazan_referencias_inexistentes(self):
        for field in ("producto_id", "sucursal_id"):
            with self.assertRaises(IntegrityError), transaction.atomic():
                Pedido.objects.filter(pk=self.pedido.pk).update(**{field: 999999})
                from django.db import connection
                connection.check_constraints(table_names=[Pedido._meta.db_table])
        self.pedido.refresh_from_db()
        self.assertEqual(self.pedido.producto, self.producto)
        self.assertEqual(self.pedido.sucursal, self.sucursal)

    def test_precarga_y_paginacion(self):
        self.login("Operador")
        for entidad, item in (("productos", self.producto), ("sucursales", self.sucursal), ("pedidos", self.pedido)):
            form = self.client.get(f"/gestion/{entidad}/{item.pk}/editar/").context["form"]
            self.assertEqual(form.instance.pk, item.pk)
            campo = "cliente" if entidad == "pedidos" else "nombre"
            self.assertEqual(form[campo].value(), getattr(item, campo))
        for n in range(12):
            Producto.objects.create(nombre=f"Adicional {n:02d}", precio=500, categoria="Prueba")
        pagina = self.client.get("/gestion/productos/", {"page": "2"}).context["pagina"]
        self.assertEqual(pagina.number, 2)
        self.assertEqual(pagina.paginator.count, 13)
        self.assertEqual(len(pagina), 3)

    def test_editar_conserva_imagen_documento_y_bytes(self):
        self.login("Operador")
        buffer = io.BytesIO()
        Image.new("RGB", (10, 10), "white").save(buffer, format="PNG")
        imagen = buffer.getvalue()
        documento = b"%PDF-1.4\n%%EOF"
        self.client.post("/gestion/productos/agregar/", self.payload("productos") | {
            "imagen": SimpleUploadedFile("imagen.png", imagen, content_type="image/png"),
            "ficha_tecnica": SimpleUploadedFile("ficha.pdf", documento, content_type="application/pdf"),
        })
        item = Producto.objects.order_by("-pk").first()
        nombres = (item.imagen.name, item.ficha_tecnica.name)
        self.assertEqual(self.client.post(f"/gestion/productos/{item.pk}/editar/", self.payload("productos") | {"nombre": "Editado"}).status_code, 302)
        item.refresh_from_db()
        self.assertEqual((item.imagen.name, item.ficha_tecnica.name), nombres)
        with item.imagen.open("rb") as stream:
            self.assertEqual(stream.read(), imagen)
        with item.ficha_tecnica.open("rb") as stream:
            self.assertEqual(stream.read(), documento)
