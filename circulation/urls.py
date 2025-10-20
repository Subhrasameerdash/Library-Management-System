from django.urls import path

from . import views

app_name = "circulation"

urlpatterns = [
    path("loans/", views.LoanListView.as_view(), name="loan-list"),
    path("loans/create/", views.LoanCreateView.as_view(), name="loan-create"),
    path("loans/<int:pk>/", views.LoanDetailView.as_view(), name="loan-detail"),
    path("loans/<int:pk>/return/", views.LoanReturnView.as_view(), name="loan-return"),
    path("reservations/", views.ReservationListView.as_view(), name="reservation-list"),
    path("reservations/create/", views.ReservationCreateView.as_view(), name="reservation-create"),
    path("reservations/<int:pk>/edit/", views.ReservationUpdateView.as_view(), name="reservation-edit"),
    path(
        "reservations/<int:pk>/<str:action>/",
        views.ReservationStatusView.as_view(),
        name="reservation-action",
    ),
    path("reservations/mine/", views.my_reservations, name="my-reservations"),
    path("fines/", views.FineListView.as_view(), name="fine-list"),
    path("fines/create/", views.FineCreateView.as_view(), name="fine-create"),
    path("fines/<int:pk>/edit/", views.FineUpdateView.as_view(), name="fine-edit"),
    path("fines/mine/", views.my_fines, name="my-fines"),
    path("fines/<int:pk>/pay/", views.pay_fine, name="fine-pay"),
]
