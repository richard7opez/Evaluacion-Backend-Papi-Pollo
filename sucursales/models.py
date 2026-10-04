from django.db import models


class Sucursal(models.Model):
    nombre = models.CharField(
        max_length=100,
        verbose_name="Nombre"
    )

    direccion = models.CharField(
        max_length=200,
        verbose_name="Dirección"
    )

    comuna = models.CharField(
        max_length=100,
        verbose_name="Comuna"
    )

    telefono = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="Teléfono"
    )

    horario = models.CharField(
        max_length=150,
        blank=True,
        verbose_name="Horario de atención"
    )

    activa = models.BooleanField(
        default=True,
        verbose_name="Sucursal activa"
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
        verbose_name = "Sucursal"
        verbose_name_plural = "Sucursales"
        ordering = ["nombre"]