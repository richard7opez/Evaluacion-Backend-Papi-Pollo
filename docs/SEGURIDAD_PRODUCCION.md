# Revision de configuracion y secretos - 7 de octubre de 2026

Este informe actualiza el estado de seguridad posterior a INFORME_EVALUACION_3.md.
No se modificaron API, modelos, permisos, usuarios, contrasenas, datos ni AWS.

## Advertencias de Django

| Codigo | Advertencia original | Estado |
|---|---|---|
| security.W004 | HSTS no configurado | Pendiente del HTTPS real |
| security.W008 | SECURE_SSL_REDIRECT=False | Pendiente del HTTPS/proxy real |
| security.W009 | SECRET_KEY debil | CORREGIDA localmente |
| security.W012 | SESSION_COOKIE_SECURE=False | Activar en produccion HTTPS |
| security.W016 | CSRF_COOKIE_SECURE=False | Activar en produccion HTTPS |
| security.W018 | DEBUG=True | Desactivar en produccion, con hosts/estaticos configurados |

DJANGO_SECRET_KEY se sustituyo en .env por un valor aleatorio generado con
secrets.token_urlsafe(64). No se imprime ni se incorpora al codigo. Se comprobo
que JWT_SIGNING_KEY y todas las demas variables de .env quedaron iguales.
Las sesiones web anteriores requieren iniciar sesion otra vez; no se borraron
registros de sesion, usuarios ni contrasenas. JWT usa su clave independiente.

No se cambiaron opciones HTTPS del entorno local. settings.py ya permite
configurarlas mediante entorno; sus valores deben aplicarse en la instancia
existente una vez confirmado el dominio, certificado y proxy reales:

```dotenv
DJANGO_DEBUG=False
DJANGO_SECURE_SSL_REDIRECT=True
DJANGO_SESSION_COOKIE_SECURE=True
DJANGO_CSRF_COOKIE_SECURE=True
DJANGO_SECURE_HSTS_SECONDS=3600
```

No copiar este bloque al entorno local HTTP. HSTS solo despues de comprobar
HTTPS. ALLOWED_HOSTS, CSRF_TRUSTED_ORIGINS y TRUST_PROXY deben corresponder al
dominio y proxy reales; no se inventaron. Conservar las variables MySQL de EC2.
La rotacion local no cambia los secretos de la instancia: comprobarlos alli
sin compartirlos. Tras configurar: python manage.py check --deploy.

Actualizacion de cierre local: INCLUDE_SUBDOMAINS y PRELOAD tambien pueden
configurarse mediante DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS y
DJANGO_SECURE_HSTS_PRELOAD. Por defecto ambos son False. Una vez habilitado
HSTS, Django puede avisar W005/W021; su activacion depende del dominio completo
y de una decision de preload, no debe automatizarse para ocultar advertencias.

## Git: archivos actuales frente a historial

.env esta ignorado y no versionado. El analisis de los archivos candidatos al
proximo commit no encontro valores reales actuales de DJANGO_SECRET_KEY,
JWT_SIGNING_KEY ni DB_PASSWORD, ni patrones de tokens JWT o claves privadas.
Los ejemplos documentales y contrasenas ficticias de tests no son credenciales
de usuarios reales. Ningun analisis automatico garantiza detectar todo tipo de
secreto desconocido; revisar el diff antes de aprobar una publicacion.

Se detectaron tres archivos YA versionados con datos sensibles:
- db.sqlite3: contiene usuarios.
- datos_sqlite.json: exportacion con usuarios y sesiones.
- datos_sqlite_utf8.json: exportacion con usuarios y sesiones.

Se retiraron SOLO del indice con git rm --cached. Los tres archivos locales
siguen presentes, con el mismo contenido; no se borraron ni editaron. En
git status aparecen D staged: es la retirada del seguimiento, no un borrado
del disco. .gitignore impide agregarlos de nuevo con git add normal.
Tambien se excluyen dumps SQL comunes. No usar git add -f para estos archivos.
Antes de actualizar otros clones, respaldar sus copias de archivos de datos
versionados: aplicar una retirada de seguimiento por pull puede quitarlas alli.

IMPORTANTE: las versiones antiguas NO desaparecen del historial. Se detectaron
asignaciones literales de SECRET_KEY en los commits 78237b8b845a y 6bc987fd625b,
ademas de las bases/exportaciones previas. No se reescribio historial ni se hizo
commit/push. Una publicacion del historial actual puede volver a incluir estos
objetos sensibles aunque no aparezcan en el ultimo arbol.

Por ello NO se certifica el repositorio completo como listo para publicar sin
secretos. Antes de GitHub hace falta una decision explicita sobre saneamiento
del historial y coordinacion de clones; no ejecutar force-push ni herramientas
de reescritura sin autorizacion. Si ya estuvo publicado, considerar los secretos
historicos y sesiones expuestos y planificar su revocacion/rotacion donde sigan
en uso. No se cambiaron contrasenas ni se eliminaron sesiones en esta revision.

## Validacion

- Suite completa: 70 pruebas OK en SQLite temporal en memoria.
- manage.py check: System check identified no issues (0 silenced).
- manage.py check --deploy: 5 advertencias, 0 silenciadas (W009 resuelta).
- git diff --check y git diff --cached --check: sin errores de whitespace.
- Datos reales MySQL: no modificados; no se ejecutaron pruebas sobre esa base.
- Clave JWT: sin cambios; .env: ignorado.

Ningun commit, push o despliegue realizado. La configuracion local funciona;
el endurecimiento HTTPS se verifica al preparar el entorno real de produccion.
