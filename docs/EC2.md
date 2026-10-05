# Preparacion y despliegue en EC2

Esta guia prepara una instalacion nueva; no modifica el entorno local.
No se ha ejecutado contra una instancia AWS. Sustituir rutas y dominio
antes de usar los ejemplos. Nunca compartir el .env ni contrasenas.

## 1. Requisitos y clonacion

Referencia: EC2 Ubuntu 24.04 LTS, Python 3.12, MariaDB 10.11 o superior
(alternativa: MySQL 8.4 o superior), motor InnoDB. La base debe residir en
la instancia para cumplir la pauta. Abrir SSH solo a la IP del estudiante;
HTTP/HTTPS segun corresponda. No exponer 3306 ni Gunicorn a Internet.

```bash
sudo apt update
sudo apt install git python3-venv python3-dev build-essential pkg-config default-libmysqlclient-dev mariadb-server nginx
git clone https://github.com/richard7opez/Evaluacion-Backend-Papi-Pollo.git
cd Evaluacion-Backend-Papi-Pollo
python3 --version
python3 -m venv venv
. venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip check
git log -5 --oneline
git remote -v
```

Conservar las evidencias de git clone, remoto e historial. Las dependencias
existentes siguen fijadas; Gunicorn se instala solo en Linux. No ejecutar
estos pasos para recrear el venv de Windows que ya funciona.

## 2. Base y variables

Crear una base nueva vacia, utf8mb4, con un usuario exclusivo, sin usar root
para Django. En la consola local de MariaDB:

```sql
CREATE DATABASE papi_pollo CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'papi_pollo'@'127.0.0.1' IDENTIFIED BY 'REEMPLAZAR_POR_CLAVE_PRIVADA';
GRANT ALL PRIVILEGES ON papi_pollo.* TO 'papi_pollo'@'127.0.0.1';
```

Reemplazar la clave ilustrativa antes de ejecutar; no guardarla en Git.
No ejecutar CREATE DATABASE sobre una base ya existente ni importar datos
sin respaldo. Confirmar el motor InnoDB y la version del servidor.

```bash
test -e .env || cp .env.example .env
chmod 600 .env
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
nano .env
```

Configurar privadamente:

```dotenv
DJANGO_SECRET_KEY=
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=tu-dominio.example,127.0.0.1
DJANGO_CSRF_TRUSTED_ORIGINS=https://tu-dominio.example
DB_ENGINE=mariadb
DB_NAME=papi_pollo
DB_USER=papi_pollo
DB_PASSWORD=
DB_HOST=127.0.0.1
DB_PORT=3306
DJANGO_SECURE_SSL_REDIRECT=False
DJANGO_TRUST_PROXY=True
DJANGO_SESSION_COOKIE_SECURE=True
DJANGO_CSRF_COOKIE_SECURE=True
DJANGO_SECURE_HSTS_SECONDS=0
```

Rellenar SECRET_KEY y DB_PASSWORD; los valores vacios no permiten arrancar.
No copiar este bloque encima del .env local. SQLite sigue siendo el valor
predeterminado cuando DB_ENGINE no esta definido. La seleccion de MySQL
con credenciales incompletas falla explicitamente, no cae a SQLite.

```bash
python manage.py check --database default
python manage.py migrate
python manage.py showmigrations
python manage.py configurar_roles
python manage.py createsuperuser
python manage.py collectstatic --noinput
```

Crear usuarios Operador y Consulta con el comando documentado en README.
Estos pasos escriben solo en la base seleccionada en EC2: revisar .env antes.
La suite de tests crea una base separada. Para probar con MariaDB usar una
cuenta de pruebas con permisos sobre test_papi_pollo, no ampliar permisos
globales de la cuenta de produccion. Ejecutar check/test tambien en EC2.

## 3. Archivos, Gunicorn y Nginx

STATIC_ROOT es staticfiles/; collectstatic no sustituye los archivos de media/.
Transferir las imagenes y documentos de demostracion mediante un canal privado,
conservando rutas y permisos. Gunicorn debe poder escribir en media/ y Nginx
solo necesita lectura de imagenes/estaticos. Nunca servir .env, SQLite ni
el directorio completo del repositorio desde Nginx.

Prueba inicial en la instancia:

```bash
venv/bin/gunicorn config.wsgi:application --bind 127.0.0.1:8000 --workers 2
```

Ejemplo de /etc/systemd/system/papi-pollo.service. Reemplazar USUARIO y
RUTA_ABSOLUTA_PROYECTO por el usuario no root y la ruta real de la clonacion:

```ini
[Unit]
Description=Papi Pollo Django
After=network.target mariadb.service

[Service]
User=USUARIO
Group=www-data
WorkingDirectory=RUTA_ABSOLUTA_PROYECTO
ExecStart=RUTA_ABSOLUTA_PROYECTO/venv/bin/gunicorn config.wsgi:application --bind 127.0.0.1:8000 --workers 2 --access-logfile - --error-logfile -
Restart=on-failure
UMask=0027

[Install]
WantedBy=multi-user.target
```

Python carga .env desde el proyecto. No colocar secretos en la unidad.
Nginx debe poder atravesar los directorios padres y leer staticfiles/ y
media/productos/, sin concederle acceso a .env ni documentos privados.

Ejemplo del bloque server para Nginx (sustituir dominio y ruta):

```nginx
server {
    listen 80;
    server_name tu-dominio.example;
    client_max_body_size 20m;

    location /static/ {
        alias RUTA_ABSOLUTA_PROYECTO/staticfiles/;
        autoindex off;
    }
    location /media/productos/ {
        alias RUTA_ABSOLUTA_PROYECTO/media/productos/;
        autoindex off;
        add_header X-Content-Type-Options nosniff always;
    }
    # Los PDF, incluida /media/documentos/productos/, pasan por Django.
    # No agregar un alias general para /media/: anularia sus permisos.
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

Habilitar el sitio Nginx y configurar un certificado TLS valido para el dominio.
El bloque HTTP es solo base de configuracion; no enviar contrasenas por HTTP.
Con HTTPS operativo, activar DJANGO_SECURE_SSL_REDIRECT=True y
DJANGO_SECURE_HSTS_SECONDS=3600. Aumentar HSTS solo tras verificar HTTPS.
Mantener cookies seguras en produccion. DJANGO_TRUST_PROXY=True requiere que
solo el proxy confiable alcance Gunicorn y sobrescriba X-Forwarded-Proto.

```bash
sudo nginx -t
sudo systemctl daemon-reload
sudo systemctl enable --now papi-pollo
sudo systemctl reload nginx
python manage.py check --deploy
```

Resolver las advertencias segun el dominio y HTTPS reales. Verificar que un
anonimo no pueda descargar un PDF, y que Consulta si pueda. No basta comprobar
la pagina inicial: probar formularios, CSRF, Admin, uploads y reinicio del servicio.

## 4. phpMyAdmin y preservacion de datos

Configurar phpMyAdmin compatible con MariaDB/MySQL, accesible solo por tunel
SSH o acceso restringido; no publicarlo sin proteccion. No cambiar el root de
MariaDB a una cuenta web. Mostrar tablas menu_producto, sucursales_sucursal,
menu_pedido, sus claves foraneas y registros coherentes con la interfaz.

La preparacion de settings no transfiere registros de SQLite a MySQL.
Conservar db.sqlite3 y media/ originales. Si se necesita transferir datos,
respaldar ambos y ensayar exportacion/importacion en una base vacia aislada;
comprobar cantidades, FK, precios historicos, cuentas y rutas de archivos antes
de aprobar el cambio. No ejecutar flush ni importar sobre una base en uso.

db.sqlite3 ya esta versionado en el historial existente. .gitignore no lo
desversiona ni elimina. Revisar con el propietario la publicacion de datos
y hashes de usuarios; no copiar cuentas/sesiones locales a produccion sin
revision. Generar una SECRET_KEY nueva y credenciales exclusivas para EC2.

## 5. Cierre de la evaluacion

Faltan evidencias reales de clonacion en EC2, entorno virtual, servicio activo,
base y phpMyAdmin, CRUD de las tres entidades, roles, archivos y uso de IA.
El documento tecnico debe explicar arquitectura, modelo de datos y cada prueba.
Estas instrucciones no constituyen evidencia de un despliegue realizado.

Referencias: [Django: bases de datos](https://docs.djangoproject.com/en/6.1/ref/databases/),
[Django: despliegue](https://docs.djangoproject.com/en/6.1/howto/deployment/checklist/),
[mysqlclient: instalacion](https://pypi.org/project/mysqlclient/),
[Gunicorn](https://pypi.org/project/gunicorn/).
