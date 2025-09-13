from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model
from .serializers import *
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

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


# Admin-only product creation
class ProductCreateView(generics.CreateAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAdminUser]  # Admin must be logged in

    def perform_create(self, serializer):
        serializer.save(posted_by=self.request.user)


# Admin-only: retrieve, update, delete a product
class ProductDetailAdminView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAdminUser]  # Admin must be logged in


# Public: List all products for buyers (no login required)
class ProductListView(generics.ListAPIView):
    queryset = Product.objects.all().order_by('-date_posted')
    serializer_class = ProductSerializer
    permission_classes = [permissions.AllowAny]  # No login required


# Public: Retrieve single product for buyers
class ProductDetailView(generics.RetrieveAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.AllowAny]  # No login required
    
    
class CartViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request):
        cart, _ = Cart.objects.get_or_create(buyer=request.user)
        serializer = CartSerializer(cart)
        return Response(serializer.data)

    def create(self, request):
        product_id = request.data.get("product_id")
        quantity = int(request.data.get("quantity", 1))

        product = get_object_or_404(Product, id=product_id)
        cart, _ = Cart.objects.get_or_create(buyer=request.user)

        # either get existing cart item or create new
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={"quantity": quantity}
        )

        if not created:
            cart_item.quantity += quantity
            cart_item.save()

        serializer = CartSerializer(cart)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, pk=None):
        cart, _ = Cart.objects.get_or_create(buyer=request.user)
        cart_item = get_object_or_404(CartItem, cart=cart, id=pk)

        quantity = int(request.data.get("quantity", cart_item.quantity))
        cart_item.quantity = quantity
        cart_item.save()

        serializer = CartSerializer(cart)
        return Response(serializer.data)

    def destroy(self, request, pk=None):
        cart, _ = Cart.objects.get_or_create(buyer=request.user)
        cart_item = get_object_or_404(CartItem, cart=cart, id=pk)
        cart_item.delete()

        serializer = CartSerializer(cart)
        return Response(serializer.data, status=status.HTTP_200_OK)
