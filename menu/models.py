from django.db import models


class Producto(models.Model):
    nombre = models.CharField(
        max_length=100,
        verbose_name="Nombre"
    )

    descripcion = models.TextField(
        blank=True,
        verbose_name="Descripción"
    )

    precio = models.PositiveIntegerField(
        verbose_name="Precio"
    )

    categoria = models.CharField(
        max_length=50,
        verbose_name="Categoría"
    )

    disponible = models.BooleanField(
        default=True,
        verbose_name="Disponible"
    )

    imagen = models.ImageField(
        upload_to="productos/",
        blank=True,
        null=True,
        verbose_name="Imagen del producto"
    )

    ficha_tecnica = models.FileField(
        upload_to="documentos/productos/",
        blank=True,
        null=True,
        verbose_name="Ficha técnica"
    )

    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de creación"
    )

    fecha_actualizacion = models.DateTimeField(
        auto_now=True,
        verbose_name="Última actualización"
    )

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"
        ordering = ["nombre"]