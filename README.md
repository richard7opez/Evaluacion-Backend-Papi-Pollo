# Papi Pollo - Sistema Web Backend

## Evaluacion Sumativa 3: API RESTful

Antes de publicar o actualizar GitHub, revisar [seguridad de produccion](docs/SEGURIDAD_PRODUCCION.md).
La rotacion de secretos y la exclusion de bases locales no eliminan datos sensibles del historial Git anterior.

La web de Evaluacion 2 se conserva. La API reutiliza sus modelos, base y permisos.
Autor: **Richard Lopez Nuñez**, Programacion Back End, INACAP.

```powershell
.\venv\Scripts\python.exe -m pip install -r requirements.txt
.\venv\Scripts\python.exe -m api.configurar_clave_jwt
.\venv\Scripts\python.exe manage.py check
.\venv\Scripts\python.exe manage.py runserver
```

El generador solo configura JWT_SIGNING_KEY en el .env existente si falta o es
demasiado corta; no imprime secretos ni cambia usuarios, contrasenas o datos.
Un entorno nuevo debe configurar primero su .env segun .env.example.
No copiar .env.example encima de un .env existente.

- Swagger: http://127.0.0.1:8000/api/v1/docs/
- OpenAPI JSON: http://127.0.0.1:8000/api/v1/schema/
- Access/Refresh: POST /api/v1/token/; renovacion: POST /api/v1/token/refresh/.
- Productos, Sucursales y Pedidos: /api/v1/productos/, /api/v1/sucursales/, /api/v1/pedidos/.
- [Contrato, ejemplos y defensa](docs/API.md).
- [Documento tecnico](docs/documento_tecnico.md).
- [Evidencias del apoyo de IA](docs/evidencias_ia.md).
- [Lista de capturas y guion de defensa](docs/EVIDENCIAS_Y_DEFENSA.md).
- [Actualizar la instancia EC2 existente](docs/ACTUALIZACION_EC2_API.md).

La implementacion y validacion local no acreditan despliegue AWS. La actualizacion
remota y sus evidencias estan pendientes. No se necesitan migraciones nuevas
para la API ni cambios a los grupos existentes.

Proyecto desarrollado para la asignatura **Programación Back End - INACAP**, correspondiente a la **Evaluación Sumativa N.º 2**.

## Descripción

Papi Pollo es una aplicación web desarrollada con Django para gestionar los productos, sucursales y pedidos de un negocio de comida al paso.

El sistema permite consultar información pública del negocio y, mediante autenticación, acceder a funcionalidades de gestión de acuerdo con el perfil y los permisos asignados a cada usuario.

El proyecto implementa persistencia de datos mediante Django ORM, operaciones CRUD, gestión de archivos, autenticación, autorización por roles y una entidad transaccional para registrar pedidos.

## Tecnologías utilizadas

- Python
- Django
- SQLite para desarrollo local
- Django ORM
- HTML5
- CSS3
- Bootstrap
- JavaScript
- Pillow para gestión de imágenes
- python-dotenv para variables de entorno
- Git
- GitHub

## Funcionalidades principales

### Productos

El sistema permite administrar los productos de Papi Pollo mediante operaciones CRUD:

- Crear productos.
- Listar productos.
- Consultar el detalle de un producto.
- Modificar productos.
- Eliminar productos.
- Gestionar nombre, descripción, categoría y precio.
- Controlar disponibilidad.
- Gestionar imágenes y archivos asociados.

La información se almacena en la base de datos y se consulta mediante Django ORM.

### Sucursales

El sistema permite visualizar y gestionar información de las sucursales de Papi Pollo.

La información de las sucursales es obtenida dinámicamente desde el sistema y se presenta en la interfaz pública.

### Pedidos

El proyecto incorpora una entidad transaccional para representar las operaciones del negocio.

Los pedidos permiten relacionar información necesaria para registrar las transacciones realizadas dentro del sistema.

### Autenticación y autorización

La aplicación utiliza el sistema de autenticación y permisos de Django.

Se consideran tres perfiles:

#### Administrador

Tiene acceso completo a las funcionalidades administrativas del sistema.

Puede gestionar registros y acceder a las operaciones autorizadas para administración.

#### Operador

Perfil orientado a la operación diaria del sistema.

Puede realizar las operaciones habilitadas según los permisos configurados para su grupo.

#### Consulta

Perfil destinado principalmente a visualizar información.

Tiene acceso restringido a operaciones que modifican o eliminan información.

Los permisos se controlan desde el backend y no solamente ocultando opciones en la interfaz.

## Estructura general del proyecto

```text
Evaluacion Backend/
│
├── config/
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
│
├── menu/
│   ├── management/
│   ├── migrations/
│   ├── templates/
│   ├── admin.py
│   ├── forms.py
│   ├── gestion.py
│   ├── gestion_urls.py
│   ├── models.py
│   ├── tests.py
│   └── views.py
│
├── pedidos/
│   ├── migrations/
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── tests.py
│   └── views.py
│
├── sucursales/
│   ├── templates/
│   ├── forms.py
│   └── views.py
│
├── static/
│   ├── css/
│   ├── img/
│   └── bootstrap/
│
├── templates/
│   ├── gestion/
│   ├── includes/
│   └── registration/
│
├── .env.example
├── .gitignore
├── manage.py
├── requirements.txt
└── README.md
```

## Instalación local

Requiere Python **3.12 o superior** compatible con Django 6.1. Estas instrucciones
son para una clonacion nueva; no recrear el entorno virtual del proyecto existente.
SQLite es la opcion local predeterminada. Para EC2 y MariaDB/MySQL, seguir
[la guia de despliegue](docs/EC2.md).

### 1. Clonar el repositorio

```bash
git clone https://github.com/richard7opez/Evaluacion-Backend-Papi-Pollo.git
```

Ingresar al directorio del proyecto:

```bash
cd Evaluacion-Backend-Papi-Pollo
```

### 2. Crear el entorno virtual

En Windows:

```bash
python -m venv venv
```

### 3. Activar el entorno virtual

PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

CMD:

```cmd
venv\Scripts\activate
```

### 4. Instalar las dependencias

```bash
python -m pip install -r requirements.txt
```

## Variables de entorno

El proyecto utiliza variables de entorno para evitar almacenar información sensible directamente en el código fuente.

Existe un archivo:

```text
.env.example
```

Se debe crear un archivo `.env` local tomando ese archivo como referencia.

En PowerShell, solamente si aun no existe:

```powershell
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Colocar la clave generada en `DJANGO_SECRET_KEY` dentro de `.env`, sin compartirla.
No reemplazar un `.env` existente. En desarrollo mantener `DB_ENGINE=sqlite`,
`DJANGO_DEBUG=True` y los hosts locales. `DB_ENGINE=mysql` o `mariadb` requiere
`DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST` y `DB_PORT`.
Las variables del proceso tienen prioridad sobre `.env`.

El archivo `.env` real está excluido del repositorio mediante `.gitignore`.

## Base de datos y migraciones

Aplicar las migraciones con:

```bash
python manage.py migrate
```

## Configuración de roles

El proyecto incorpora un comando de administración para configurar los grupos y permisos utilizados por la aplicación:

```bash
python manage.py configurar_roles
```

Esto permite preparar los perfiles definidos para el sistema según la configuración implementada en el proyecto.

## Crear un superusuario

Para acceder al panel administrativo de Django:

```bash
python manage.py createsuperuser
```

Completar los datos solicitados por la terminal.

## Verificación del proyecto

Antes de ejecutar la aplicación se puede comprobar la configuración con:

```bash
python manage.py check
```

Para ejecutar las pruebas:

```bash
python manage.py test
```

## Ejecutar el servidor

```bash
python manage.py runserver
```

Luego acceder desde el navegador a:

```text
http://127.0.0.1:8000/
```

## Seguridad

El proyecto aplica distintas medidas de seguridad y buenas prácticas:

- Uso del sistema de autenticación de Django.
- Autorización mediante grupos y permisos.
- Protección CSRF proporcionada por Django.
- Validación de formularios en el backend.
- Variables sensibles separadas del código mediante `.env`.
- `.env` excluido del control de versiones.
- Control de acceso a funcionalidades de gestión.
- Separación entre interfaz pública y operaciones administrativas.

## Gestión de archivos

El sistema permite trabajar con imágenes y archivos asociados a los registros que lo requieren.

Django administra estos recursos mediante la configuración de archivos `media`, mientras que los recursos propios de la interfaz se mantienen en `static`.

## Control de versiones

El proyecto utiliza Git como sistema de control de versiones y GitHub como repositorio remoto.

Repositorio:

https://github.com/richard7opez/Evaluacion-Backend-Papi-Pollo

El archivo `.gitignore` evita versionar elementos que no deben almacenarse en el repositorio, incluyendo:

```text
.env
venv/
__pycache__/
*.pyc
```

## Autor

**Richard Lopez Nuñez**

Estudiante de Ingeniería Informática - INACAP.

## Estado del proyecto

### Verificacion frente a la pauta

Producto y Sucursal son los mantenedores. La transaccion es **menu.Pedido**,
con ForeignKey a ambos, cantidad, precio historico, total, estado y fechas.
La app `pedidos` no define otro modelo; no crear un Pedido duplicado.

| Perfil | Consultar / buscar | Crear / modificar | Eliminar | Gestionar usuarios |
| --- | --- | --- | --- | --- |
| Administrador | Si | Si | Si, con confirmacion | Si, Django Admin |
| Operador | Si | Si | No | No |
| Consulta | Si | No | No | No |

Rutas del CRUD: `/gestion/productos/`, `/gestion/sucursales/` y
`/gestion/pedidos/`. Las tres tienen tablas, filtros, busqueda, detalle,
formularios precargados y confirmacion de eliminacion. Producto/Sucursal
referenciados por pedidos estan protegidos contra borrado, incluso para el
administrador, para conservar la integridad. Django Admin registra las tres
entidades y permite buscar y consultar las relaciones del pedido.

`Producto.imagen` almacena imagenes (hasta 5 MB en el formulario web);
`Producto.ficha_tecnica` almacena PDF (hasta 10 MB en el formulario web).
Los nombres/rutas se guardan en la base; los bytes, en `media/`.
Las fichas se descargan con permiso `menu.view_producto`, incluso con
`DEBUG=False`. En EC2 no publicar documentos directamente mediante Nginx.

Para cuentas nuevas, el comando solicita la contrasena en la terminal:

```bash
python manage.py configurar_roles --usuario operador --rol Operador --crear
python manage.py configurar_roles --usuario consulta --rol Consulta --crear
```

No repetir `--crear` para cuentas existentes. No ejecutar comandos de roles
sobre la base real solo para verificarla; las pruebas usan una base aislada.

### Pendientes de entrega

- Ejecutar y verificar MySQL/MariaDB y phpMyAdmin dentro de EC2.
- Clonar en EC2 la version que se decida publicar y configurar HTTPS,
  Gunicorn, Nginx y el servicio persistente.
- Demostrar CRUD, roles, subida/descarga de archivos y registros reales en EC2.
- Preparar documento tecnico y capturas de la pauta, incluidos prompts,
  respuestas de IA y explicacion de su aplicacion.

La preparacion del repositorio no equivale a un despliegue verificado.
No se migro la base local ni se publicaron cambios automaticamente.

### Precauciones antes de publicar

`.env` esta ignorado y `.env.example` no contiene credenciales. Sin embargo,
`db.sqlite3` ya estaba versionado: agregarlo a `.gitignore` no lo retira
del historial ni del indice. Puede contener usuarios, hashes y sesiones.
Revisar su publicacion y renovar claves/cuentas de demostracion antes de
exponer el sitio. Se detectaron claves literales antiguas en los commits
`78237b8` y `6bc987f`; no reutilizarlas. La configuracion actual ya toma
SECRET_KEY del entorno y no se muestran aqui los valores historicos.
Los respaldos y documentos privados no deben subirse a GitHub.
No borrar la base ni reescribir el historial para resolver esto sin un plan
de respaldo y autorizacion.

Versión funcional correspondiente a la **Evaluación Sumativa N.º 2 de Programación Back End**.

El proyecto incorpora gestión de datos mediante ORM, operaciones CRUD, entidad transaccional, autenticación, autorización mediante perfiles, gestión de archivos, pruebas y control de versiones con Git/GitHub.
