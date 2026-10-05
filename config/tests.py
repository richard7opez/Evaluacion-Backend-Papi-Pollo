import os
import runpy
from pathlib import Path
from unittest.mock import patch

from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase


class EnvironmentSettingsTests(SimpleTestCase):
    def load_settings(self, **environment):
        # No lee .env real ni abre conexiones a bases de datos.
        values = {"DJANGO_SECRET_KEY": "clave-ficticia-solo-para-pruebas", **environment}
        with patch.dict(os.environ, values, clear=True), patch("dotenv.load_dotenv"):
            return runpy.run_path(str(Path(__file__).with_name("settings.py")))

    def test_sqlite_por_defecto_conserva_ruta(self):
        config = self.load_settings(DJANGO_DEBUG="True")
        self.assertEqual(config["DATABASES"]["default"]["ENGINE"], "django.db.backends.sqlite3")
        self.assertEqual(config["DATABASES"]["default"]["NAME"], config["BASE_DIR"] / "db.sqlite3")
        self.assertFalse(config["SESSION_COOKIE_SECURE"])

    def test_mysql_y_mariadb_configurados_sin_conectar(self):
        for engine in ("mysql", "mariadb"):
            with self.subTest(engine=engine):
                config = self.load_settings(
                    DB_ENGINE=engine, DB_NAME="prueba", DB_USER="usuario_prueba",
                    DB_PASSWORD="valor-ficticio", DB_HOST="127.0.0.1", DB_PORT="3307",
                )
                database = config["DATABASES"]["default"]
                self.assertEqual(database["ENGINE"], "django.db.backends.mysql")
                self.assertEqual(database["NAME"], "prueba")
                self.assertEqual(database["USER"], "usuario_prueba")
                self.assertEqual(database["PASSWORD"], "valor-ficticio")
                self.assertEqual(database["PORT"], "3307")
                self.assertEqual(database["OPTIONS"]["charset"], "utf8mb4")
                self.assertIn("STRICT_TRANS_TABLES", database["OPTIONS"]["init_command"])

    def test_mysql_no_retrocede_a_sqlite_si_faltan_credenciales(self):
        with self.assertRaisesMessage(ImproperlyConfigured, "DB_PASSWORD"):
            self.load_settings(DB_ENGINE="mysql", DB_NAME="prueba", DB_USER="prueba")

    def test_motor_invalido_se_rechaza(self):
        with self.assertRaisesMessage(ImproperlyConfigured, "DB_ENGINE"):
            self.load_settings(DB_ENGINE="invalido")

    def test_secret_key_obligatoria(self):
        with self.assertRaisesMessage(ImproperlyConfigured, "DJANGO_SECRET_KEY"):
            self.load_settings(DJANGO_SECRET_KEY="")

    def test_https_y_hosts_por_entorno(self):
        config = self.load_settings(
            DJANGO_DEBUG="False", DJANGO_ALLOWED_HOSTS=" ejemplo.test, localhost ",
            DJANGO_CSRF_TRUSTED_ORIGINS="https://ejemplo.test",
            DJANGO_SECURE_SSL_REDIRECT="True", DJANGO_TRUST_PROXY="True",
            DJANGO_SECURE_HSTS_SECONDS="3600",
        )
        self.assertFalse(config["DEBUG"])
        self.assertEqual(config["ALLOWED_HOSTS"], ["ejemplo.test", "localhost"])
        self.assertEqual(config["CSRF_TRUSTED_ORIGINS"], ["https://ejemplo.test"])
        self.assertTrue(config["SESSION_COOKIE_SECURE"])
        self.assertTrue(config["CSRF_COOKIE_SECURE"])
        self.assertTrue(config["SECURE_SSL_REDIRECT"])
        self.assertEqual(config["SECURE_PROXY_SSL_HEADER"], ("HTTP_X_FORWARDED_PROTO", "https"))
        self.assertEqual(config["SECURE_HSTS_SECONDS"], 3600)

    def test_static_root_separado_y_proxy_no_confiado_por_defecto(self):
        config = self.load_settings()
        self.assertNotIn(config["STATIC_ROOT"], config["STATICFILES_DIRS"])
        self.assertNotIn("SECURE_PROXY_SSL_HEADER", config)
