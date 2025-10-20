from django.urls import path

from . import views

app_name = "reports"

urlpatterns = [
    path("dashboard/", views.DashboardView.as_view(), name="dashboard"),
    path("loans/export/", views.LoanCSVExportView.as_view(), name="loan-export"),
]
