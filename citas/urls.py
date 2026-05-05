"""URLs de la app citas."""
from django.urls import path

from . import views

app_name = "citas"

urlpatterns = [
    path("", views.menu, name="menu"),
    path("registrar/", views.registrar, name="registrar"),
    path("consultar/", views.consultar, name="consultar"),
    path("cancelar/", views.cancelar, name="cancelar"),
    path("reasignar/", views.reasignar, name="reasignar"),
    path("agenda/", views.agenda, name="agenda"),
]
