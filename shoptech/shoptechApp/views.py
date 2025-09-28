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
from rest_framework.decorators import action
from rest_framework.decorators import permission_classes
from rest_framework.permissions import AllowAny
from django.http import JsonResponse
from requests.auth import HTTPBasicAuth

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
@permission_classes([IsAuthenticated])
def mpesa_payment_view(request):
    phone_number = request.data.get("phone_number")
    order_id = request.data.get("order_id")

    if not phone_number or not order_id:
        return Response({"error": "Phone number and order_id are required"}, status=400)

    # Validate phone number format
    if not phone_number.startswith("254") or len(phone_number) != 12:
        return Response({"error": "Phone number must be in format 254XXXXXXXXX"}, status=400)
    
    # ✅ Get the order & validate it belongs to user
    try:
        order = Order.objects.get(id=order_id, buyer=request.user)
    except Order.DoesNotExist:
        return Response({"error": "Order not found or doesn't belong to you"}, status=404)
    
    # ✅ Check if order is already paid
    if order.status == "paid":
        return Response({"error": "Order is already paid"}, status=400)
    
    # ✅ Check if there's already a pending transaction for this order
    existing_pending = Transaction.objects.filter(
        order=order, 
        status="pending"
    ).first()
    
    if existing_pending:
        return Response({
            "error": "There's already a pending payment for this order",
            "checkout_request_id": existing_pending.checkout_id
        }, status=400)

    amount = order.total_price
    
    # ✅ Validate amount is greater than 0
    if amount <= 0:
        return Response({"error": "Order amount must be greater than 0"}, status=400)

    try:
        # Use settings instead of hardcoded values
        consumer_key = settings.MPESA_CONSUMER_KEY
        consumer_secret = settings.MPESA_CONSUMER_SECRET
        shortcode = settings.MPESA_SHORTCODE
        passkey = settings.MPESA_PASSKEY
        callback_url = settings.MPESA_CALLBACK_URL

        print(f"🔑 Processing payment for Order #{order.id}, Amount: {amount}")

        # 1. Get Access Token
        token_url = f"{settings.MPESA_BASE_URL}/oauth/v1/generate?grant_type=client_credentials"
        token_response = requests.get(token_url, auth=HTTPBasicAuth(consumer_key, consumer_secret))
        
        if token_response.status_code != 200:
            return Response({
                "error": f"Failed to get access token: {token_response.text}",
                "status_code": token_response.status_code
            }, status=400)

        if not token_response.text.strip():
            return Response({
                "error": "Empty response from M-Pesa OAuth endpoint"
            }, status=400)

        try:
            token_data = token_response.json()
        except ValueError as e:
            return Response({
                "error": f"Invalid JSON response from M-Pesa: {token_response.text}"
            }, status=400)
            
        access_token = token_data.get("access_token")
        if not access_token:
            return Response({"error": "No access token received"}, status=400)

        # 2. Generate Password
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        data_to_encode = shortcode + passkey + timestamp
        password = base64.b64encode(data_to_encode.encode()).decode("utf-8")

        # 3. Make STK Push Request
        stk_url = f"{settings.MPESA_BASE_URL}/mpesa/stkpush/v1/processrequest"
        stk_headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "BusinessShortCode": shortcode,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": int(amount),
            "PartyA": phone_number,
            "PartyB": shortcode,
            "PhoneNumber": phone_number,
            "CallBackURL": callback_url,
            "AccountReference": f"Order_{order.id}",
            "TransactionDesc": f"Payment for Order #{order.id}"
        }

        stk_response = requests.post(stk_url, json=payload, headers=stk_headers)
        
        if stk_response.status_code != 200:
            return Response({
                "error": f"STK Push failed: {stk_response.text}",
                "status_code": stk_response.status_code
            }, status=stk_response.status_code)

        res_data = stk_response.json()

        # 4. Save Transaction if STK push is accepted
        if res_data.get("ResponseCode") == "0":
            transaction = Transaction.objects.create(
                buyer=request.user,
                order=order, 
                amount=amount,
                checkout_id=res_data.get("CheckoutRequestID"),
                phone_number=phone_number,
                status="pending"
            )
            
            # ✅ Update order status to show payment is being processed
            order.status = "pending"
            order.save()
            
            print(f"💾 Transaction created for Order #{order.id}")
            
            # ✅ Return comprehensive response
            return Response({
                "success": True,
                "message": "STK push sent successfully. Check your phone to complete payment.",
                "checkout_request_id": res_data.get("CheckoutRequestID"),
                "order_id": order.id,
                "amount": float(amount),
                "phone_number": phone_number,
                "transaction_id": transaction.id,
                "customer_message": res_data.get("CustomerMessage", ""),
                "response_code": res_data.get("ResponseCode")
            }, status=200)
        else:
            return Response({
                "error": "STK Push was rejected",
                "response_code": res_data.get("ResponseCode"),
                "response_description": res_data.get("ResponseDescription"),
                "error_code": res_data.get("errorCode"),
                "error_message": res_data.get("errorMessage")
            }, status=400)

    except requests.exceptions.RequestException as e:
        print(f"🔥 Network Error: {str(e)}")
        return Response({"error": f"Network error: {str(e)}"}, status=500)
    except Exception as e:
        print(f"🔥 General Error: {str(e)}")
        return Response({"error": f"Server error: {str(e)}"}, status=500)


@api_view(["POST"])
@permission_classes([AllowAny])
def mpesa_callback(request):
    """Enhanced callback to handle M-Pesa payment confirmations"""
    print(f"📞 M-Pesa Callback received: {request.data}")
    
    data = request.data
    stk_callback = data.get("Body", {}).get("stkCallback", {})
    checkout_id = stk_callback.get("CheckoutRequestID")
    result_code = stk_callback.get("ResultCode")
    result_desc = stk_callback.get("ResultDesc")
    
    if not checkout_id:
        print("❌ No CheckoutRequestID in callback")
        return Response({"ResultCode": 0, "ResultDesc": "No CheckoutRequestID found"})

    try:
        transaction = Transaction.objects.get(checkout_id=checkout_id)
        print(f"🔍 Found transaction: {transaction.id} for order: {transaction.order.id}")

        if result_code == 0:  # ✅ Payment successful
            # Extract payment details from callback metadata
            callback_metadata = stk_callback.get("CallbackMetadata", {})
            items = callback_metadata.get("Item", [])
            
            mpesa_receipt = None
            transaction_date = None
            amount_paid = None
            
            for item in items:
                if item.get("Name") == "MpesaReceiptNumber":
                    mpesa_receipt = item.get("Value")
                elif item.get("Name") == "TransactionDate":
                    transaction_date = item.get("Value")
                elif item.get("Name") == "Amount":
                    amount_paid = item.get("Value")
            
            # ✅ Update transaction
            transaction.status = "success"
            transaction.result_desc = result_desc
            transaction.mpesa_receipt = mpesa_receipt
            transaction.save()
            
            # ✅ Update order status
            if transaction.order:
                transaction.order.status = "paid"
                transaction.order.save()
                print(f"✅ Order {transaction.order.id} marked as PAID with receipt: {mpesa_receipt}")
                
                # ✅ Optionally reduce product stock here
                for item in transaction.order.items.all():
                    product = item.product
                    if product.stock >= item.quantity:
                        product.stock -= item.quantity
                        product.save()
                        print(f"📦 Reduced stock for {product.name}: {item.quantity} units")

        else:  # ❌ Payment failed
            transaction.status = "failed"
            transaction.result_desc = result_desc
            transaction.save()
            
            # ✅ Reset order status back to pending
            if transaction.order:
                transaction.order.status = "pending"
                transaction.order.save()
                print(f"❌ Payment failed for Order {transaction.order.id}: {result_desc}")

    except Transaction.DoesNotExist:
        print(f"❌ Transaction with CheckoutID {checkout_id} not found")

    return Response({"ResultCode": 0, "ResultDesc": "Callback processed successfully"})




# Test endpoint to verify credentials
@api_view(["GET"])
@permission_classes([AllowAny])
def test_mpesa_credentials(request):
    """Test endpoint to verify M-Pesa credentials"""
    try:
        consumer_key = settings.MPESA_CONSUMER_KEY
        consumer_secret = settings.MPESA_CONSUMER_SECRET
        
        # Test token generation
        token_url = f"{settings.MPESA_BASE_URL}/oauth/v1/generate?grant_type=client_credentials"
        
        # Use GET with HTTPBasicAuth for M-Pesa OAuth
        response = requests.get(token_url, auth=HTTPBasicAuth(consumer_key, consumer_secret))
        
        return Response({
            "status": "success" if response.status_code == 200 else "failed",
            "status_code": response.status_code,
            "response": response.text if response.text else "Empty response",
            "response_length": len(response.text) if response.text else 0,
            "consumer_key": consumer_key[:10] + "...",
            "base_url": settings.MPESA_BASE_URL,
            "headers": dict(response.headers) if hasattr(response, 'headers') else {}
        })
        
    except Exception as e:
        return Response({
            "status": "error",
            "error": str(e)
        })
 
 

@api_view(["POST"])
@permission_classes([AllowAny])
def simulate_successful_payment(request):
    """
    Test endpoint to simulate a successful M-Pesa payment
    POST /mpesa/simulate-success/
    {
        "checkout_request_id": "ws_CO_27092025202037491798592832"
    }
    """
    checkout_request_id = request.data.get("checkout_request_id")
    
    if not checkout_request_id:
        return Response({"error": "checkout_request_id is required"}, status=400)
    
    # Simulated callback data
    success_callback_data = {
        "Body": {
            "stkCallback": {
                "MerchantRequestID": "2efe-4d43-847f-eb9dc8222de09952",
                "CheckoutRequestID": checkout_request_id,
                "ResultCode": 0,  # Success
                "ResultDesc": "The service request is processed successfully.",
                "CallbackMetadata": {
                    "Item": [
                        {"Name": "Amount", "Value": 1.00},
                        {"Name": "MpesaReceiptNumber", "Value": "SIM123456789"},
                        {"Name": "TransactionDate", "Value": 20250927172100},
                        {"Name": "PhoneNumber", "Value": 254798592832}
                    ]
                }
            }
        }
    }
    
    try:
        stk_callback = success_callback_data.get("Body", {}).get("stkCallback", {})
        checkout_id = stk_callback.get("CheckoutRequestID")
        result_code = stk_callback.get("ResultCode")
        result_desc = stk_callback.get("ResultDesc")

        if not checkout_id:
            return Response({"error": "Invalid callback data"}, status=400)

        try:
            transaction = Transaction.objects.get(checkout_id=checkout_id)
        except Transaction.DoesNotExist:
            return Response({"error": f"Transaction with CheckoutID {checkout_id} not found"}, status=404)

        # ✅ Mark transaction
        if result_code == 0:
            transaction.status = "success"
            transaction.mpesa_receipt = "SIM123456789"
            transaction.result_desc = result_desc
            transaction.save()

            # ✅ If transaction is linked to order, mark order as paid
            if transaction.order:
                transaction.order.status = "paid"
                transaction.order.save()
                print(f"✅ SIMULATION - Order {transaction.order.id} marked as PAID")

        else:
            transaction.status = "failed"
            transaction.result_desc = result_desc
            transaction.save()

        return Response({
            "success": True,
            "message": "Payment simulation successful",
            "transaction_status": transaction.status,
            "mpesa_receipt": getattr(transaction, 'mpesa_receipt', None),
            "order_status": getattr(transaction.order, 'status', None) if transaction.order else None
        })
        
    except Exception as e:
        print(f"🔥 Simulation Error: {str(e)}")
        return Response({"error": f"Simulation failed: {str(e)}"}, status=500)



@api_view(["GET"])
@permission_classes([IsAuthenticated])
def check_payment_status(request, order_id):
    """Check the payment status of an order"""
    try:
        order = Order.objects.get(id=order_id, buyer=request.user)
        
        # Get the latest transaction for this order
        latest_transaction = Transaction.objects.filter(order=order).order_by('-created_at').first()
        
        response_data = {
            "order_id": order.id,
            "order_status": order.status,
            "order_total": float(order.total_price),
            "order_created": order.created_at,
        }
        
        if latest_transaction:
            response_data.update({
                "transaction_status": latest_transaction.status,
                "mpesa_receipt": latest_transaction.mpesa_receipt,
                "transaction_created": latest_transaction.created_at,
                "checkout_request_id": latest_transaction.checkout_id,
                "result_description": latest_transaction.result_desc,
            })
        else:
            response_data["transaction_status"] = "no_transaction"
            
        return Response(response_data)
        
    except Order.DoesNotExist:
        return Response({"error": "Order not found"}, status=404)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def order_success(request, order_id):
    """Get order success details after payment"""
    try:
        order = Order.objects.get(id=order_id, buyer=request.user)
        
        if order.status != "paid":
            return Response({"error": "Order is not yet paid"}, status=400)
        
        # Get successful transaction
        successful_transaction = Transaction.objects.filter(
            order=order, 
            status="success"
        ).first()
        
        order_items = []
        for item in order.items.all():
            order_items.append({
                "product_name": item.product.name,
                "product_code": item.product.product_code,
                "quantity": item.quantity,
                "price": float(item.price),
                "total": float(item.total_price)
            })
        
        response_data = {
            "success": True,
            "message": "Order payment successful!",
            "order": {
                "id": order.id,
                "status": order.status,
                "total_amount": float(order.total_price),
                "created_at": order.created_at,
                "items": order_items
            }
        }
        
        if successful_transaction:
            response_data["payment"] = {
                "mpesa_receipt": successful_transaction.mpesa_receipt,
                "transaction_date": successful_transaction.created_at,
                "phone_number": successful_transaction.phone_number
            }
            
        return Response(response_data)
        
    except Order.DoesNotExist:
        return Response({"error": "Order not found"}, status=404)
        
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
    



class OrderViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request):
        orders = Order.objects.filter(buyer=request.user).order_by("-created_at")
        serializer = OrderSerializer(orders, many=True, context={"request": request})
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        order = get_object_or_404(Order, id=pk, buyer=request.user)
        serializer = OrderSerializer(order, context={"request": request})
        return Response(serializer.data)

    @action(detail=False, methods=["post"])
    def create_from_cart(self, request):
        cart, _ = Cart.objects.get_or_create(buyer=request.user)
        if not cart.items.exists():
            return Response({"error": "Cart is empty"}, status=400)

        # Create Order
        order = Order.objects.create(buyer=request.user)

        for item in cart.items.all():
            price = item.product.discount_price or item.product.price
            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                price=price,
            )

        order.calculate_total()

        # Clear cart
        cart.items.all().delete()

        serializer = OrderSerializer(order, context={"request": request})
        return Response(serializer.data, status=201)

class CustomerAddressViewSet(viewsets.ModelViewSet):
    serializer_class = CustomerAddressSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Only return addresses of logged-in buyer
        return CustomerAddress.objects.filter(buyer=self.request.user)

    def perform_create(self, serializer):
        serializer.save(buyer=self.request.user)
        

def test_env(request):
    return JsonResponse({
        "CONSUMER_KEY": settings.MPESA_CONSUMER_KEY,
        "CONSUMER_SECRET": settings.MPESA_CONSUMER_SECRET
    })

