from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("login/", views.UserLoginView.as_view(), name="login"),
    path("logout/", views.UserLogoutView.as_view(), name="logout"),
    path("register/", views.UserRegisterView.as_view(), name="register"),
    path("profile/", views.ProfileDetailView.as_view(), name="profile"),
    path("profile/edit/", views.ProfileUpdateView.as_view(), name="profile-edit"),
    path("overview/", views.account_overview, name="overview"),
    path("users/", views.UserListView.as_view(), name="user-list"),
    path("users/<int:user_id>/switch-role/<str:role>/", views.switch_user_role, name="switch-role"),
]
