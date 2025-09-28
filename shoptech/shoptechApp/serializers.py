from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from .models import *


User = get_user_model()


class BuyerRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = [
            "username",
            "first_name",
            "last_name",
            "phone_number",
            "email",
            "date_of_birth",
            "county",
            "password",
            "password2",
        ]

    def validate(self, attrs):
        if attrs["password"] != attrs["password2"]:
            raise serializers.ValidationError({"password": "Passwords must match."})
        return attrs

    def create(self, validated_data):
        validated_data.pop("password2")
        # 🔒 Ensure no buyer can set themselves as admin
        validated_data.pop("role", None)
        user = User.objects.create_user(**validated_data)
        return user
    
    


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "first_name", "last_name", "email", "role"]


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")

        if email and password:
            user = authenticate(username=email, password=password)
            if not user:
                raise serializers.ValidationError(_("Invalid email or password"))
        else:
            raise serializers.ValidationError(_("Both email and password are required"))

        attrs["user"] = user
        return attrs

    def create(self, validated_data):
        """Return tokens for the logged-in user"""
        user = validated_data["user"]
        refresh = RefreshToken.for_user(user)

        return {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role,
            },
        }
        

class ProductSerializer(serializers.ModelSerializer):
    discount_percentage = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            "product_code",
            "name",
            "group",
            "collection",
            "color",
            "size",
            "price",
            "discount_price",
            "discount_percentage",
            "stock",
            "best_seller",
            "description",
            "image1",
            "image2",
            "image3",
            "image4",
            "date_posted",
        ]

    def get_discount_percentage(self, obj):
        return obj.discount_percentage
    
class ProductMiniSerializer(serializers.ModelSerializer):
    image1 = serializers.SerializerMethodField()
    class Meta:
        model = Product
        fields = ["id", "name", "price", "discount_price", "stock", "image1"]
        
    def get_image1(self, obj):
        request = self.context.get("request")
        if obj.image1 and request:
            return request.build_absolute_uri(obj.image1.url)
        return None

    
    
class CartItemSerializer(serializers.ModelSerializer):
    product = ProductMiniSerializer(read_only=True)
    product_code = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(), source="product", write_only=True
    )

    class Meta:
        model = CartItem
        fields = ["id", "product", "product_code", "quantity", "total_price"]


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)

    class Meta:
        model = Cart
        fields = ["id", "buyer", "items", "created_at"]
        read_only_fields = ["buyer", "created_at"]
        
class ContactUsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactUs
        fields = '__all__'
        
class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "role",
            "phone_number",
            "date_of_birth",
            "county",
        ]

class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductMiniSerializer(read_only=True)

    class Meta:
        model = OrderItem
        fields = ["id", "product", "quantity", "price", "total_price"]


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    buyer = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Order
        fields = ["id", "buyer", "status", "total_price", "created_at", "items"]
        
class CustomerAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerAddress
        fields = [
            "id",
            "buyer",
            "first_name",
            "last_name",
            "contact",
            "county",
            "city",
            "address",
            "apartment",
            "postal_code",
            "phone",
            "created_at",
        ]
        read_only_fields = ["buyer", "created_at"]

