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


# RF-01 -----------------------------------------------------------------

class RF01TestCase(BaseCT):
    """Registrar Cita."""

    def test_CA1_registro_valido(self):
        form = RegistrarCitaForm(datos_validos(self.d1))
        self.assertTrue(form.is_valid(), form.errors)

    def test_CA1_HTTP_redirect(self):
        resp = self.client.post(reverse("citas:registrar"), datos_validos(self.d1))
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(Cita.objects.count(), 1)

    def test_CA1_id_formato(self):
        self.client.post(reverse("citas:registrar"), datos_validos(self.d1))
        cita = Cita.objects.first()
        self.assertRegex(cita.id_cita, r"^CIT-\d{8}-\d{3}$")
        self.assertEqual(cita.estado, "Activa")

    def test_CA2_nombre_vacio(self):
        form = RegistrarCitaForm(datos_validos(self.d1, nombre_paciente=""))
        self.assertFalse(form.is_valid())

    def test_CA2_dni_vacio(self):
        form = RegistrarCitaForm(datos_validos(self.d1, dni_paciente=""))
        self.assertFalse(form.is_valid())

    def test_CA2_telefono_vacio(self):
        form = RegistrarCitaForm(datos_validos(self.d1, telefono=""))
        self.assertFalse(form.is_valid())

    def test_CA3_dni_7_digitos(self):
        form = RegistrarCitaForm(datos_validos(self.d1, dni_paciente="1234567"))
        self.assertFalse(form.is_valid())
        self.assertIn("DNI invalido. Ingrese exactamente 8 digitos.", str(form.errors))

    def test_CA3_dni_con_letras(self):
        form = RegistrarCitaForm(datos_validos(self.d1, dni_paciente="1234ABCD"))
        self.assertFalse(form.is_valid())

    def test_CA3_telefono_8_digitos(self):
        form = RegistrarCitaForm(datos_validos(self.d1, telefono="98765432"))
        self.assertFalse(form.is_valid())
        self.assertIn("Telefono invalido. Ingrese exactamente 9 digitos.", str(form.errors))

    def test_CA4_fecha_pasada(self):
        ayer = (date.today() - timedelta(days=1)).strftime("%d/%m/%Y")
        form = RegistrarCitaForm(datos_validos(self.d1, fecha=ayer))
        self.assertFalse(form.is_valid())
        self.assertIn("No se pueden registrar citas en fechas pasadas.", str(form.errors))

    def test_fecha_domingo(self):
        dom = proximo_domingo().strftime("%d/%m/%Y")
        form = RegistrarCitaForm(datos_validos(self.d1, fecha=dom))
        self.assertFalse(form.is_valid())
        self.assertIn("No se atiende los domingos.", str(form.errors))

    def test_fecha_formato_malo(self):
        form = RegistrarCitaForm(datos_validos(self.d1, fecha="2026-06-15"))
        self.assertFalse(form.is_valid())
        self.assertIn("Formato de fecha invalido. Use DD/MM/AAAA.", str(form.errors))

    def test_CA5_turno_ocupado(self):
        d = datos_validos(self.d1, hora="10:00")
        f = parsear_fecha_ddmmaaaa(d["fecha"])
        Cita.objects.create(
            id_cita=Cita.generar_id(f), nombre_paciente=d["nombre_paciente"],
            dni_paciente=d["dni_paciente"], telefono=d["telefono"], fecha=f,
            hora=d["hora"], motivo=d["motivo"], dentista=self.d1,
        )
        d2 = datos_validos(self.d1, fecha=d["fecha"], hora=d["hora"], dni_paciente="99999999")
        form = RegistrarCitaForm(d2)
        self.assertFalse(form.is_valid())
        self.assertIn("El turno seleccionado no esta disponible para ese dentista.", str(form.errors))

    def test_turno_libre_otro_dentista(self):
        f = fecha_futura()
        Cita.objects.create(
            id_cita=Cita.generar_id(f), nombre_paciente="Uno",
            dni_paciente="11111111", telefono="987111222", fecha=f, hora="09:00",
            motivo="Limpieza", dentista=self.d1,
        )
        d = datos_validos(self.d2, fecha=f.strftime("%d/%m/%Y"), hora="09:00", dni_paciente="22222222")
        self.assertTrue(RegistrarCitaForm(d).is_valid())

    def test_CA6_mismo_dni_misma_fecha(self):
        f = fecha_futura()
        Cita.objects.create(
            id_cita=Cita.generar_id(f), nombre_paciente="Original",
            dni_paciente="55555555", telefono="987000000", fecha=f, hora="09:00",
            motivo="Limpieza", dentista=self.d1,
        )
        d = datos_validos(self.d2, fecha=f.strftime("%d/%m/%Y"), hora="14:00", dni_paciente="55555555")
        form = RegistrarCitaForm(d)
        self.assertFalse(form.is_valid())
        self.assertIn("El paciente ya tiene una cita registrada para esa fecha.", str(form.errors))


# RF-02 -----------------------------------------------------------------

class RF02TestCase(BaseCT):
    """Consultar Cita."""

    def setUp(self):
        super().setUp()
        self.f1 = fecha_futura(7)
        self.f2 = fecha_futura(14)
        self.cA = Cita.objects.create(
            id_cita=Cita.generar_id(self.f1), nombre_paciente="Ana Lopez",
            dni_paciente="11223344", telefono="987111222", fecha=self.f1,
            hora="09:00", motivo="Limpieza", dentista=self.d1,
        )
        self.cB = Cita.objects.create(
            id_cita=Cita.generar_id(self.f2), nombre_paciente="Bruno Diaz",
            dni_paciente="11223344", telefono="987111222", fecha=self.f2,
            hora="10:00", motivo="Endodoncia", dentista=self.d2,
        )

    def test_CA1_buscar_por_dni(self):
        r = self.client.get(reverse("citas:consultar"), {"criterio": "1", "dni": "11223344"})
        self.assertContains(r, self.cA.id_cita)
        self.assertContains(r, self.cB.id_cita)

    def test_CA2_buscar_por_fecha(self):
        r = self.client.get(reverse("citas:consultar"), {"criterio": "2", "fecha": self.f1.strftime("%d/%m/%Y")})
        self.assertContains(r, self.cA.id_cita)
        self.assertNotContains(r, self.cB.id_cita)

    def test_CA3_dni_sin_citas(self):
        r = self.client.get(reverse("citas:consultar"), {"criterio": "1", "dni": "00000000"})
        self.assertContains(r, "No se encontraron citas")

    def test_CA4_fecha_sin_citas(self):
        r = self.client.get(reverse("citas:consultar"), {"criterio": "2", "fecha": fecha_futura(60).strftime("%d/%m/%Y")})
        self.assertContains(r, "No se encontraron citas")

    def test_CA5_dni_letras(self):
        r = self.client.get(reverse("citas:consultar"), {"criterio": "1", "dni": "ABCD1234"})
        self.assertContains(r, "DNI invalido. Ingrese exactamente 8 digitos.")

    def test_CA6_fecha_formato(self):
        r = self.client.get(reverse("citas:consultar"), {"criterio": "2", "fecha": "30-12-2026"})
        self.assertContains(r, "Formato de fecha invalido")

    def test_orden_cronologico(self):
        r = self.client.get(reverse("citas:consultar"), {"criterio": "1", "dni": "11223344"})
        c = r.content.decode()
        self.assertTrue(0 < c.find(self.cA.id_cita) < c.find(self.cB.id_cita))


# RF-03 -----------------------------------------------------------------

class RF03TestCase(BaseCT):
    """Cancelar Cita."""

    def setUp(self):
        super().setUp()
        self.f = fecha_futura(10)
        self.cita = Cita.objects.create(
            id_cita=Cita.generar_id(self.f), nombre_paciente="Test Cancelar",
            dni_paciente="44556677", telefono="987444555", fecha=self.f,
            hora="11:00", motivo="Revision general", dentista=self.d1,
        )

    def test_CA1_confirmacion_S(self):
        r = self.client.post(reverse("citas:cancelar"), {"id_cita": self.cita.id_cita, "confirmacion": "S"})
        self.assertEqual(r.status_code, 302)
        self.cita.refresh_from_db()
        self.assertEqual(self.cita.estado, "Cancelada")

    def test_CA2_confirmacion_N(self):
        self.client.post(reverse("citas:cancelar"), {"id_cita": self.cita.id_cita, "confirmacion": "N"})
        self.cita.refresh_from_db()
        self.assertEqual(self.cita.estado, "Activa")

    def test_CA3_id_formato_invalido(self):
        r = self.client.get(reverse("citas:cancelar"), {"id_cita": "ABC-XXX"})
        self.assertContains(r, "Formato de ID invalido. Use CIT-YYYYMMDD-NNN.")

    def test_CA4_id_no_existe(self):
        r = self.client.get(reverse("citas:cancelar"), {"id_cita": "CIT-20990101-999"})
        self.assertContains(r, "No existe ninguna cita con el ID ingresado.")

    def test_CA5_doble_cancelacion(self):
        self.cita.estado = "Cancelada"
        self.cita.save()
        r = self.client.get(reverse("citas:cancelar"), {"id_cita": self.cita.id_cita})
        self.assertContains(r, "La cita ya fue cancelada previamente.")

    def test_CA6_fecha_pasada(self):
        Cita.objects.filter(pk=self.cita.pk).update(fecha=date.today() - timedelta(days=2))
        r = self.client.get(reverse("citas:cancelar"), {"id_cita": self.cita.id_cita})
        self.assertContains(r, "No se pueden cancelar citas de fechas pasadas.")

    def test_CA7_turno_libre_tras_cancelar(self):
        self.client.post(reverse("citas:cancelar"), {"id_cita": self.cita.id_cita, "confirmacion": "S"})
        d = datos_validos(self.d1, fecha=self.f.strftime("%d/%m/%Y"), hora=self.cita.hora, dni_paciente="99887766")
        self.assertTrue(RegistrarCitaForm(d).is_valid())
