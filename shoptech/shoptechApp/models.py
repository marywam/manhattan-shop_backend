from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from datetime import date
from django.utils import timezone
from django.conf import settings
import uuid



class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        extra_fields.setdefault("role", "buyer")  # default role is buyer

        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db) 
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields["role"] = "admin"  # enforce admin role

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    ROLE_CHOICES = (
        ("admin", "Admin"),   # you (the sole proprietor)
        ("buyer", "Buyer"),   # customers
    )
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="buyer")

    # 🔹 Extra Buyer Fields
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    county = models.CharField(max_length=100, blank=True, null=True)

    # 🔹 We don’t want username as login — use email instead
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "first_name", "last_name"]

    objects = UserManager()

    def save(self, *args, **kwargs):
        # force all superusers to have admin role
        if self.is_superuser:
            self.role = "admin"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.email} ({self.role})"


PRODUCT_GROUPS = [
    ("rings", "Rings"),
    ("necklaces", "Necklaces"),
    ("bangles", "Bangles"),
    ("earrings", "Earrings"),
]

def generate_product_code():
    return "PRD-" + uuid.uuid4().hex[:8].upper()

class Product(models.Model):
    product_code = models.CharField(
        max_length=50, unique=True, default=generate_product_code, editable=False
    )
    name = models.CharField(max_length=255)
    group = models.CharField(max_length=50, choices=PRODUCT_GROUPS, default="rings")
    collection = models.CharField(max_length=100, blank=True, null=True)
    color = models.CharField(max_length=50, blank=True, null=True)
    size = models.CharField(max_length=50, blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    # store the discounted price directly
    discount_price = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True, help_text="Discounted price"
    )

    stock = models.PositiveIntegerField(default=0)
    best_seller = models.BooleanField(default=False)

    description = models.TextField(blank=True, null=True)
    image1 = models.ImageField(upload_to="products/")
    image2 = models.ImageField(upload_to="products/", blank=True, null=True)
    image3 = models.ImageField(upload_to="products/", blank=True, null=True)
    image4 = models.ImageField(upload_to="products/", blank=True, null=True)
    date_posted = models.DateTimeField(default=timezone.now, editable=False)
    posted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="products"
    )

    def __str__(self):
        return f"{self.name} ({self.product_code})"

    @property
    def discount_percentage(self):
        """Return percentage discount based on price and discount_price."""
        if self.price and self.discount_price and self.discount_price < self.price:
            return float(((self.price - self.discount_price) / self.price) * 100)
        return 0.0

  
class Cart(models.Model):
    buyer = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="cart"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Cart of {self.buyer.email}"


class CartItem(models.Model):
    cart = models.ForeignKey(
        Cart, on_delete=models.CASCADE, related_name="items"
    )
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ("cart", "product")  # prevent duplicates

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"

    @property
    def total_price(self):
        """Return discounted price * quantity if discount exists, else normal price."""
        price = self.product.discounted_price or self.product.price
        return price * self.quantity


#MPESA MODEL
class Transaction(models.Model):
    buyer = models.ForeignKey(User, on_delete=models.CASCADE, default="")
    order = models.ForeignKey('Order', on_delete=models.CASCADE, null=True, blank=True, related_name="transactions")
    phone_number = models.CharField(max_length=15)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    checkout_id = models.CharField(max_length=100, unique=True)
    status = models.CharField(max_length=20, default="pending")  # pending, success, failed
    result_desc = models.TextField(blank=True, null=True)
    mpesa_receipt = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.phone_number} - {self.amount} ({self.status})"
    
    
class ContactUs(models.Model):
    full_name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=20)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.full_name} - {self.phone_number}"
    

ORDER_STATUS = [
    ("pending", "Pending"),
    ("paid", "Paid"),
    ("shipped", "Shipped"),
    ("delivered", "Delivered"),
    ("cancelled", "Cancelled"),
]

class Order(models.Model):
    buyer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="orders"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=ORDER_STATUS, default="pending")
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"Order {self.id} - {self.buyer.email} - {self.status}"

    def calculate_total(self):
        total = sum(item.total_price for item in self.items.all())
        self.total_price = total
        self.save()
        return total


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="items"
    )
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    @property
    def total_price(self):
        if self.price is None or self.quantity is None:
            return 0
        return self.price * self.quantity

    def __str__(self):
        return f"{self.quantity} x {self.product.name} (Order {self.order.id})"

    

class CustomerAddress(models.Model):
    COUNTY_CHOICES = [
        ("Kenya", "Kenya"),  # only Kenya allowed
    ]

    buyer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="addresses"
    )
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    contact = models.CharField(
        max_length=100,
        help_text="Email or Phone number"
    )
    county = models.CharField(max_length=50, choices=COUNTY_CHOICES, default="Kenya")
    city = models.CharField(max_length=100)
    address = models.CharField(max_length=255)
    apartment = models.CharField(max_length=100, blank=True, null=True)
    postal_code = models.CharField(max_length=20)
    phone = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Customer Address"
        verbose_name_plural = "Customer Addresses"

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.city}, {self.county}"
