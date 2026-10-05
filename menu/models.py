from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


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


class Pedido(models.Model):
    class Estado(models.TextChoices):
        PENDIENTE = "pendiente", "Pendiente"
        PREPARACION = "preparacion", "En preparación"
        ENTREGADO = "entregado", "Entregado"
        CANCELADO = "cancelado", "Cancelado"

    producto = models.ForeignKey(Producto, on_delete=models.PROTECT, related_name="pedidos")
    sucursal = models.ForeignKey("sucursales.Sucursal", on_delete=models.PROTECT, related_name="pedidos")
    cliente = models.CharField(max_length=100)
    cantidad = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1), MaxValueValidator(10000)])
    precio_unitario = models.PositiveIntegerField(editable=False)
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.PENDIENTE)
    observaciones = models.TextField(blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-fecha_creacion", "-pk"]
        constraints = [models.CheckConstraint(condition=models.Q(cantidad__gte=1, cantidad__lte=10000), name="pedido_cantidad_valida")]

    @property
    def total(self):
        if self.cantidad is None or self.precio_unitario is None:
            return None
        return self.cantidad * self.precio_unitario

    def save(self, *args, **kwargs):
        campos = kwargs.get("update_fields")
        if campos is not None and not {"producto", "producto_id"}.intersection(campos):
            return super().save(*args, **kwargs)
        anterior = type(self).objects.filter(pk=self.pk).values("producto_id").first() if self.pk else None
        # Conserva el precio histórico, salvo cuando se cambia el producto del pedido.
        if anterior is None or anterior["producto_id"] != self.producto_id:
            self.precio_unitario = Producto.objects.get(pk=self.producto_id).precio
            if kwargs.get("update_fields") is not None:
                kwargs["update_fields"] = set(kwargs["update_fields"]) | {"precio_unitario"}
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Pedido #{self.pk} - {self.cliente}"
