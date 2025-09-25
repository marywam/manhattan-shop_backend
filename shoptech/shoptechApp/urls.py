from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import *
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Buyer registration
    path("register/", BuyerRegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),

    # JWT Authentication
    path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),   # login
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"), # refresh token
    
    
  # Admin
    path("product/create/", ProductCreateView.as_view(), name="product-create"),
    path("products/admin/<str:product_code>/", ProductDetailAdminView.as_view(), name="product-detail-admin"),

    # Public
    path("products/", ProductListView.as_view(), name="product-list"),
    path("products/<str:product_code>/", ProductDetailView.as_view(), name="product-detail"),
    path("products/filters/", ProductFiltersView.as_view(), name="product-filters"),
    
    
    # Cart (Buyer only)
    path("cart/", CartViewSet.as_view({"get": "list", "post": "create"}), name="cart"),
    path("cart/<int:pk>/", CartViewSet.as_view({"put": "update", "delete": "destroy"}), name="cart-item"),
    
    
    path('contact/', ContactUsCreateView.as_view(), name='contact-create'),
    path('contact/list/', ContactUsListView.as_view(), name='contact-list'),
    
    path("profile/", ProfileView.as_view(), name="profile"),
    
    path("payment/", views.payment_view, name="payment"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


