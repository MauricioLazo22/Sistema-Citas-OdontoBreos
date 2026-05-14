"""
Modelos del Sistema de Citas Odontologicas - Grupo D
RF-01 Registrar, RF-02 Consultar, RF-03 Cancelar.
"""
from datetime import date, datetime
from django.db import models
from django.db.models import Q


HORAS_DISPONIBLES = [
    ("08:00", "08:00"),
    ("09:00", "09:00"),
    ("10:00", "10:00"),
    ("11:00", "11:00"),
    ("14:00", "14:00"),
    ("15:00", "15:00"),
    ("16:00", "16:00"),
    ("17:00", "17:00"),
]

MOTIVOS = [
    ("Limpieza", "Limpieza"),
    ("Extraccion", "Extraccion"),
    ("Endodoncia", "Endodoncia"),
    ("Ortodoncia", "Ortodoncia"),
    ("Revision general", "Revision general"),
]

ESTADOS = [
    ("Activa", "Activa"),
    ("Cancelada", "Cancelada"),
]

class Dentista(models.Model):
    """Dentista al que se le pueden asignar citas."""

    nombre = models.CharField(max_length=120, unique=True)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Dentista"
        verbose_name_plural = "Dentistas"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre

class Cita(models.Model):
    """
    Cita odontologica.
    El ID interno (PK) lo maneja Django; ademas se genera un id_cita publico
    con formato CIT-YYYYMMDD-NNN segun lo pide RF-01.
    """

    id_cita = models.CharField(
        max_length=20,
        unique=True,
        editable=False,
        help_text="Formato CIT-YYYYMMDD-NNN",
    )
    nombre_paciente = models.CharField(max_length=80)
    dni_paciente = models.CharField(max_length=8)
    telefono = models.CharField(max_length=9)
    fecha = models.DateField()
    hora = models.CharField(max_length=5, choices=HORAS_DISPONIBLES)
    motivo = models.CharField(max_length=20, choices=MOTIVOS)
    dentista = models.ForeignKey(
        Dentista, on_delete=models.PROTECT, related_name="citas"
    )
    estado = models.CharField(max_length=10, choices=ESTADOS, default="Activa")
    creada_en = models.DateTimeField(auto_now_add=True)
    actualizada_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Cita"
        verbose_name_plural = "Citas"
        ordering = ["fecha", "hora"]
        constraints = [
            models.UniqueConstraint(
                fields=["fecha", "hora", "dentista"],
                condition=Q(estado="Activa"),        # ← solo aplica a citas Activas
                name="unique_turno_activo_por_dentista",
            )
        ]

    def __str__(self):
        return f"{self.id_cita} - {self.nombre_paciente} ({self.fecha} {self.hora})"

    @staticmethod
    def generar_id(fecha_cita):
        """
        Genera el id_cita con formato CIT-YYYYMMDD-NNN.
        NNN es un correlativo por dia (001, 002, ...).
        """
        prefijo_fecha = fecha_cita.strftime("%Y%m%d")
        prefijo = f"CIT-{prefijo_fecha}-"
        ultimos = (
            Cita.objects.filter(id_cita__startswith=prefijo)
            .order_by("-id_cita")
            .values_list("id_cita", flat=True)
        )
        if ultimos:
            try:
                ultimo_num = int(ultimos[0].split("-")[-1])
            except (ValueError, IndexError):
                ultimo_num = 0
        else:
            ultimo_num = 0
        nuevo = ultimo_num + 1
        return f"{prefijo}{nuevo:03d}"

    @property
    def es_cancelable(self):
        """Solo se pueden cancelar citas Activas con fecha futura o de hoy."""
        return self.estado == "Activa" and self.fecha >= date.today()
