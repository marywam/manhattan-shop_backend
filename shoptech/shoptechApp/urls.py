from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import *
from . import views
from django.conf import settings
from django.conf.urls.static import static


order_list = OrderViewSet.as_view({
    "get": "list",
})

order_detail = OrderViewSet.as_view({
    "get": "retrieve",
})

order_create_from_cart = OrderViewSet.as_view({
    "post": "create_from_cart",
})

address_list = CustomerAddressViewSet.as_view({
    "get": "list",
    "post": "create",
})
address_detail = CustomerAddressViewSet.as_view({
    "get": "retrieve",
    "put": "update",
    "patch": "partial_update",
    "delete": "destroy",
})
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
    
    # Orders (Buyer only)
     # Orders (Buyer only)
    path("orders/", order_list, name="order-list"),  
    path("orders/<int:pk>/", order_detail, name="order-detail"),  
    path("orders/create_from_cart/", order_create_from_cart, name="order-create-from-cart"),
    
    
    # Order payment status endpoints
    path('orders/<int:order_id>/payment-status/', views.check_payment_status, name='check_payment_status'),
    path('orders/<int:order_id>/success/', views.order_success, name='order_success'),
    
    
    path("addresses/", address_list, name="address-list"),
    path("addresses/<int:pk>/", address_detail, name="address-detail"),
    
    path("mpesa/pay/", mpesa_payment_view, name="mpesa-pay"),
    path("mpesa/callback/", mpesa_callback, name="mpesa-callback"),
    path("mpesa/testcredentials/", test_mpesa_credentials, name = "test_mpesa_credentials"),
    # In your urls.py
    path("mpesa/simulate-success/", simulate_successful_payment, name="mpesa-simulate-success"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


