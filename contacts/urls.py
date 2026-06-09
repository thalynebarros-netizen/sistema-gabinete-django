from django.urls import path

from . import views

app_name = "contacts"

urlpatterns = [
    path("", views.list_contacts, name="list"),
    path("crm/", views.crm_contacts, name="crm"),
    path("crm/<int:pk>/", views.crm_contact_detail, name="crm_detail"),
]
