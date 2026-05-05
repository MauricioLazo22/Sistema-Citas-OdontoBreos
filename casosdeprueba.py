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

# Helpers ---------------------------------------------------------------

def fecha_futura(dias=7):
    f = date.today() + timedelta(days=dias)
    while f.weekday() == 6:
        f += timedelta(days=1)
    return f


def proximo_domingo():
    f = date.today()
    while f.weekday() != 6:
        f += timedelta(days=1)
    return f


def _limpiar(s):
    s = re.sub(r"[^A-Za-z ]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def datos_validos(dentista, **overrides):
    nombre = _limpiar(fake.first_name() + " " + fake.last_name()) or "Paciente Demo"
    base = {
        "nombre_paciente": nombre,
        "dni_paciente": fake.numerify("########"),
        "telefono": fake.numerify("9########"),
        "fecha": fecha_futura().strftime("%d/%m/%Y"),
        "hora": fake.random_element(HORAS),
        "motivo": fake.random_element(MOTIVOS),
        "dentista": dentista.pk,
    }
    base.update(overrides)
    return base


# Base TestCase ---------------------------------------------------------

class BaseCT(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.d1 = Dentista.objects.create(nombre="Dr. Juan Perez", activo=True)
        cls.d2 = Dentista.objects.create(nombre="Dra. Maria Gomez", activo=True)
        cls.d3 = Dentista.objects.create(nombre="Dr. Carlos Ramirez", activo=True)

    def setUp(self):
        self.client = Client()
