from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from datetime import date
from django.utils import timezone
from django.conf import settings


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


class Product(models.Model):
    name = models.CharField(max_length=255)
    image1 = models.ImageField(upload_to='products/')
    image2 = models.ImageField(upload_to='products/', blank=True, null=True)
    image3 = models.ImageField(upload_to='products/', blank=True, null=True)
    image4 = models.ImageField(upload_to='products/', blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True, help_text="Discount in %")
    description = models.TextField()
    date_posted = models.DateTimeField(default=timezone.now, editable=False)
    posted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="products")

    def __str__(self):
        return self.name

    @property
    def discounted_price(self):
      if self.discount is not None and self.discount > 0:
        return self.price - (self.price * self.discount / 100)
      return None
  
  
  
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
    amount=models.DecimalField(max_digits=10,decimal_places=2)
    checkout_id=models.CharField(max_length=100, unique=True)
    mpesa_code=models.CharField(max_length=100, unique=True)
    phone_number=models.CharField(max_length=15)
    status=models.CharField(max_length=20)
    timestamp=models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.mpesa_code} - {self.amount} KES" 
    
    
    

