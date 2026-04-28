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

