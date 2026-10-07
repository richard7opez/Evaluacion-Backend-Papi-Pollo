# Actualizar API en la instancia EC2 existente

No se ejecuto este despliegue. No crear otra instancia, base, usuario o proyecto.
Conservar el venv, media, .env, servicio Gunicorn y configuracion Nginx actuales.
Revisar los valores reales; no se conocen desde esta sesion ni se inventan.

## 1. Antes de actualizar

Antes de publicar, resolver el riesgo del historial descrito en
SEGURIDAD_PRODUCCION.md. Despues de aprobar el contenido y la estrategia Git,
el propietario realiza la publicacion. Nada se publica automaticamente.
Si se sanea el historial, coordinar la actualizacion del clon remoto: no forzar
pull ni hacer reset destructivo. La secuencia pull --ff-only siguiente solo
aplica si el historial sigue siendo compatible. En la instancia existente por SSH:

```bash
read -r -p "Ruta absoluta del proyecto existente: " PROYECTO
cd "$PROYECTO" || exit 1
pwd
git status --short
git branch --show-current
git remote -v
python3 --version
```

Si hay cambios remotos locales sin guardar, detenerse; no usar reset/clean/force.
Respaldar la base MySQL con el procedimiento existente (dump/snapshot privado)
y media antes de actualizar. No incluir backups ni contrasenas en Git. No
ejecutar pruebas con la base de produccion. No importar datos_sqlite*.json.

Antes de pull, copiar tambien .env y cualquier db.sqlite3/exportacion local
necesaria a un respaldo PRIVADO fuera del repositorio: las retiradas del
seguimiento pueden borrar esos archivos versionados en otros clones. Confirmar
el respaldo antes de continuar. No reemplazar media ni la base MySQL al actualizar.

## 2. Codigo, dependencias y configuracion

Dentro de la carpeta confirmada, usando el venv existente:

```bash
git pull --ff-only
. venv/bin/activate
python --version
python -m pip install -r requirements.txt
python -m pip check
python -m api.configurar_clave_jwt
chmod 600 .env
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py showmigrations
python manage.py migrate --plan
```

No hay nuevas migraciones por esta API. Si migrate --plan muestra operaciones
pendientes previas, revisarlas contra el respaldo antes de ejecutar migrate.
No regenerar migraciones. No ejecutar configurar_roles ni crear usuarios si
los tres perfiles existentes ya funcionan.

JWT_SIGNING_KEY debe existir tambien en el entorno efectivo del servicio. Si
systemd define una variable antigua, tiene prioridad sobre .env: corregirla
sin imprimir su valor. El generador no rota claves ya fuertes. Los tokens
firmados con la clave anterior dejan de servir, no las contrasenas de usuarios.

Revisar DJANGO_SECRET_KEY por separado: debe ser aleatoria y suficientemente
larga. La clave local anterior ya fue fortalecida; esto no modifica el secreto
de EC2. Para rotar explicitamente el secreto del .env de EC2, en ventana de
mantenimiento (invalida sesiones/tokens firmados de Django, no cambia usuarios):

```bash
python -c "import secrets; from dotenv import set_key; set_key('.env', 'DJANGO_SECRET_KEY', secrets.token_urlsafe(64)); print('Secreto actualizado sin mostrarlo; sera necesario iniciar sesion otra vez.')"
```

Mantener DB_ENGINE/DB_NAME/DB_USER/DB_PASSWORD/DB_HOST/DB_PORT reales. No copiar
un .env de Windows ni reemplazar la configuracion de produccion con ejemplos.
Configurar DEBUG=False, ALLOWED_HOSTS real y HTTPS antes de usar JWT remotamente.

### Variables exactas a revisar en el entorno efectivo del servicio

| Variable | Valor/criterio en EC2 |
|---|---|
| DJANGO_SECRET_KEY | Secreto aleatorio fuerte propio del servidor; nunca publicar |
| JWT_SIGNING_KEY | Secreto independiente, minimo 32 bytes aleatorios |
| DJANGO_DEBUG | False |
| DJANGO_ALLOWED_HOSTS | DNS/IP reales, separados por comas, sin esquema ni comodin |
| DB_ENGINE | mysql o mariadb, conservar el motor existente |
| DB_NAME / DB_USER / DB_PASSWORD | Valores privados de la base existente |
| DB_HOST / DB_PORT | Host/puerto existentes; no abrirlos a Internet |
| DJANGO_CSRF_TRUSTED_ORIGINS | Origenes HTTPS reales, con https:// |
| DJANGO_TRUST_PROXY | True solo si Nginx es confiable y sobrescribe cabecera de esquema |
| DJANGO_SECURE_SSL_REDIRECT | True tras comprobar HTTPS/proxy sin bucles |
| DJANGO_SESSION_COOKIE_SECURE | True con HTTPS |
| DJANGO_CSRF_COOKIE_SECURE | True con HTTPS |
| DJANGO_SECURE_HSTS_SECONDS | 3600 inicialmente, solo tras comprobar HTTPS |
| DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS | False por defecto; True solo si TODOS los subdominios admiten HTTPS |
| DJANGO_SECURE_HSTS_PRELOAD | False por defecto; decision explicita sobre la politica preload |

No se proporcionan dominios ni secretos ficticios como valores para copiar.
Si HTTPS no esta disponible, dejar esa activacion pendiente y no transmitir
credenciales reales por HTTP remoto. El HTTP local sigue siendo util para
desarrollo y no se cambia para eliminar artificialmente advertencias.
Al activar HSTS pueden aparecer W005/W021 por las dos opciones anteriores.
No activarlas a ciegas para silenciar checks. La prueba automatizada de perfil
estricto solo simula esas decisiones con un dominio reservado para tests;
no acredita aptitud para la lista preload ni sustituye comprobar sus requisitos.

## 3. Swagger, archivos y proxy

```bash
python manage.py collectstatic --noinput
python manage.py check --deploy
sudo nginx -t
```

Swagger sidecar necesita /static/ servido por Nginx. No usa una CDN externa.
Revisar el bloque ACTUAL, no reemplazar todo el archivo. Su location / debe
enviar /api/v1/ al mismo Gunicorn que la web. Ejemplo de directivas necesarias:

```nginx
client_max_body_size 20m;
location / {
    proxy_pass http://127.0.0.1:8000; # conservar el upstream/socket real
    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header Authorization $http_authorization;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
}
```

Conservar /static/ y /media/productos/. NO agregar alias general /media/ ni
alias /media/documentos/: el PDF debe pasar por las vistas protegidas. Nginx
debe aceptar Authorization; no registrar esa cabecera ni cuerpos de token.
No abrir MySQL ni Gunicorn a Internet. HTTPS con certificado valido es requerido.
Si solo hay HTTP, no probar credenciales reales aun. Activar proxy/SSL en
settings mediante las variables existentes solo cuando TLS funcione.

El limite de intentos DRF usa cache por proceso; para produccion complementar
con limite de peticiones en el proxy o cache compartida. No se cambia la
infraestructura automaticamente. El limite de subida del proxy puede devolver
413 antes de Django: configurar una respuesta JSON si el consumidor la requiere.

## 4. Reinicio controlado y comprobaciones

Usar el nombre del servicio existente, no crear otro:

```bash
systemctl list-units --type=service --all | grep -Ei 'gunicorn|papi'
read -r -p "Nombre exacto de la unidad existente: " SERVICIO
sudo systemctl restart "$SERVICIO"
sudo systemctl status "$SERVICIO" --no-pager
sudo nginx -t && sudo systemctl reload nginx
read -r -p "Origen HTTPS real, sin barra final: " ORIGEN
curl -I "$ORIGEN/"
curl -I "$ORIGEN/api/v1/docs/"
curl -i "$ORIGEN/api/v1/productos/"
curl -I "$ORIGEN/api/v1/schema/"
```

Esperado: web/Swagger/esquema disponibles; productos anonimo responde 401 JSON.
En navegador, usar Swagger para token/Authorize/CRUD/refresh con datos nuevos
de demostracion, nunca borrar los originales. Comprobar los tres perfiles y
403; PDF protegido; imagenes; precio historico; web/CSRF/login/Admin anteriores.
No copiar tokens en comandos de shell, historial ni capturas.

Para la suite en EC2 sin tocar MySQL real:
```bash
DB_ENGINE=sqlite python manage.py test --noinput
```
Para validar especificamente MySQL, usar credenciales de testing y una base
test separada; no ampliar privilegios de la cuenta de produccion a ciegas.

## 5. Evidencia y disponibilidad

Guardar capturas de instancia activa, IP/DNS, SSH, venv, servicios, base,
web, Swagger y resultados de endpoints desplegados. Ocultar claves, tokens,
correos/personas y contrasenas. Mantener la instancia disponible durante la
evaluacion. No afirmar CUMPLE en despliegue hasta realizar estas verificaciones.

Si falla el reinicio, revisar logs privados localmente; no compartir .env ni
trazas con credenciales. No hacer reset destructivo ni restaurar una base sin
respaldo y aprobacion. Las instrucciones de EC2.md son de instalacion nueva de
Evaluacion 2; esta guia es la apropiada para actualizar el despliegue existente.
