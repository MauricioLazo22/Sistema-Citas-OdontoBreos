"""
Casos de prueba automatizados - Sistema de Citas Odontologicas (Grupo D).

Cubre los Criterios de Aceptacion de los 5 RFs.

Tecnologias usadas:
  - Django TestCase (framework de testing automatizado, basado en unittest)
  - Faker (generacion automatica de datos de prueba aleatorios)
  - Django Test Client (cliente HTTP virtual para probar las vistas)

Como ejecutar:
  python manage.py test casosdeprueba
  python manage.py test casosdeprueba -v 2
  python manage.py test casosdeprueba.RF01TestCase
"""
from datetime import date, timedelta
import re

from django.core.exceptions import ValidationError
from django.test import Client, TestCase
from django.urls import reverse
from faker import Faker

from citas.forms import (
    ListarAgendaForm,
    ReasignarCitaForm,
    RegistrarCitaForm,
)
from citas.models import Cita, Dentista
from citas.validators import (
    parsear_fecha_ddmmaaaa,
    validar_dni,
    validar_hora,
    validar_id_cita,
    validar_motivo,
    validar_nombre,
    validar_telefono,
)

fake = Faker("es_ES")
Faker.seed(2026)

HORAS = ["08:00", "09:00", "10:00", "11:00", "14:00", "15:00", "16:00", "17:00"]
MOTIVOS = ["Limpieza", "Extraccion", "Endodoncia", "Ortodoncia", "Revision general"]
