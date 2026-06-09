from django.urls import path

from . import views

app_name = "dashboard"

urlpatterns = [
    path("", views.home, name="home"),
    path("painel/", views.strategic_panel, name="strategic_panel"),
    path("relatorios/", views.reports, name="reports"),
    path("relatorios/exportar-csv/", views.export_reports_csv, name="reports_export_csv"),
]
