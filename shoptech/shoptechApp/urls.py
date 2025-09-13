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
    
    
    # Admin
    path("product/create/", ProductCreateView.as_view(), name="product-create"),
    path("products/admin/<int:pk>/", ProductDetailAdminView.as_view(), name="product-detail-admin"),

    # Buyer / Public
    path("products/", ProductListView.as_view(), name="product-list"),
    path("products/<int:pk>/", ProductDetailView.as_view(), name="product-detail"),
    
    
    # Cart (Buyer only)
    path("cart/", CartViewSet.as_view({"get": "list", "post": "create"}), name="cart"),
    path("cart/<int:pk>/", CartViewSet.as_view({"put": "update", "delete": "destroy"}), name="cart-item"),
]
