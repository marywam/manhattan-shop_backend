from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model
from .serializers import *
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
import requests
import base64
from datetime import datetime
from django.conf import settings
from rest_framework.decorators import api_view
from rest_framework.views import APIView


User = get_user_model()


class BuyerRegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = [permissions.AllowAny]
    serializer_class = BuyerRegisterSerializer
    
class LoginView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = LoginSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.create(serializer.validated_data)
        return Response(data, status=status.HTTP_200_OK)



# Admin: create product
class ProductCreateView(generics.CreateAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAdminUser]

    def perform_create(self, serializer):
        serializer.save(posted_by=self.request.user)

# Admin: retrieve/update/delete by product_code
class ProductDetailAdminView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAdminUser]
    lookup_field = "product_code"

# Public: list products with optional group filter
class ProductListView(generics.ListAPIView):
    serializer_class = ProductSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        queryset = Product.objects.all().order_by("-date_posted")
        group = self.request.query_params.get("group")
        if group:
            queryset = queryset.filter(group=group)
        return queryset

# Public: single product (using product_code instead of id)
class ProductDetailView(generics.RetrieveAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = "product_code"

# Distinct filter options API
class ProductFiltersView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        collections = Product.objects.values_list("collection", flat=True).distinct()
        colors = Product.objects.values_list("color", flat=True).distinct()
        sizes = Product.objects.values_list("size", flat=True).distinct()
        prices = Product.objects.values_list("price", flat=True).distinct()
        return Response({
            "collections": [c for c in collections if c],
            "colors": [c for c in colors if c],
            "sizes": [s for s in sizes if s],
            "prices": prices,
        })

    
    
class CartViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request):
        cart, _ = Cart.objects.get_or_create(buyer=request.user)
        serializer = CartSerializer(cart, context={"request": request})
        return Response(serializer.data)

    def create(self, request):
        product_code = request.data.get("product_code")
        quantity = int(request.data.get("quantity", 1))

        product = get_object_or_404(Product, product_code=product_code)
        cart, _ = Cart.objects.get_or_create(buyer=request.user)

        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={"quantity": quantity}
        )

        if not created:
            cart_item.quantity += quantity
            cart_item.save()

        serializer = CartSerializer(cart, context={"request": request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, pk=None):
        cart, _ = Cart.objects.get_or_create(buyer=request.user)
        cart_item = get_object_or_404(CartItem, cart=cart, id=pk)

        quantity = int(request.data.get("quantity", cart_item.quantity))
        cart_item.quantity = quantity
        cart_item.save()

        serializer = CartSerializer(cart, context={"request": request})
        return Response(serializer.data)

    def destroy(self, request, pk=None):
        cart, _ = Cart.objects.get_or_create(buyer=request.user)
        cart_item = get_object_or_404(CartItem, cart=cart, id=pk)
        cart_item.delete()

        serializer = CartSerializer(cart, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)



@api_view(["POST"])
def payment_view(request):
    phone_number = request.data.get("phone_number")
    amount = request.data.get("amount")

    if not phone_number or not amount:
        return Response({"error": "Phone number and amount are required"}, status=400)

    # Safaricom credentials
    consumer_key = settings.MPESA_CONSUMER_KEY
    consumer_secret = settings.MPESA_CONSUMER_SECRET
    shortcode = settings.MPESA_SHORTCODE
    passkey = settings.MPESA_PASSKEY

    # 1. Get access token
    token_url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
    r = requests.get(token_url, auth=(consumer_key, consumer_secret))
    if r.status_code != 200:
        return Response({"error": "Failed to get access token", "details": r.json()}, status=500)

    access_token = r.json().get("access_token")

    # 2. Generate password
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    data_to_encode = shortcode + passkey + timestamp
    password = base64.b64encode(data_to_encode.encode()).decode("utf-8")

    # 3. STK Push request
    stk_url = "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
    headers = {"Authorization": f"Bearer {access_token}"}
    payload = {
        "BusinessShortCode": shortcode,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": amount,
        "PartyA": phone_number,
        "PartyB": shortcode,
        "PhoneNumber": phone_number,
        "CallBackURL": "https://7adcf57cb017.ngrok-free.app/api/mpesa/callback/",
        "AccountReference": "Test123",
        "TransactionDesc": "Payment"
    }

    response = requests.post(stk_url, json=payload, headers=headers)
    res_data = response.json()

    # 4. Save transaction (only if request accepted)
    if res_data.get("ResponseCode") == "0":
        Transaction.objects.create(
            amount=amount,
            checkout_id=res_data.get("CheckoutRequestID"),
            phone_number=phone_number,
            status="pending"
        )

    return Response(res_data, status=response.status_code)




# Buyer posts a contact message
class ContactUsCreateView(generics.CreateAPIView):
    queryset = ContactUs.objects.all()
    serializer_class = ContactUsSerializer
    permission_classes = [permissions.AllowAny]  # anyone can submit

# Admin views all contact messages
class ContactUsListView(generics.ListAPIView):
    queryset = ContactUs.objects.all()
    serializer_class = ContactUsSerializer
    permission_classes = [permissions.IsAdminUser]  # only admin can view
    
    
class ProfileView(generics.RetrieveAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


