from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import *

urlpatterns = [
    # Buyer registration
    path("register/", BuyerRegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),

    # JWT Authentication
    path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),   # login
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"), # refresh token
]
