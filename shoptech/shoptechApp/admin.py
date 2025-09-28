from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import *


class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ("email", "username", "first_name", "last_name", "role", "is_staff", "is_active")
    list_filter = ("role", "is_staff", "is_active")
    search_fields = ("email", "username", "first_name", "last_name")
    ordering = ("email",)

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal Info", {"fields": ("username", "first_name", "last_name", "phone_number", "date_of_birth", "county")}),
        ("Permissions", {"fields": ("role", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Important Dates", {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "password1", "password2", "role", "is_staff", "is_superuser"),
        }),
    )


admin.site.register(User, CustomUserAdmin)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
    "product_code",
        "name",
        "group",
        "price",
          "discount_price",
        "discount_percentage",
        "stock",
        "best_seller",
        "date_posted",
        "posted_by",
    )
    list_filter = ("group", "collection", "color", "size", "best_seller")
    search_fields = ("name", "description", "product_code")

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.posted_by = request.user
        super().save_model(request, obj, form, change)



# ✅ Cart Item Inline (shows items inside CartAdmin)
class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 1
    readonly_fields = ("total_price",)


# ✅ Cart Admin
class CartAdmin(admin.ModelAdmin):
    list_display = ("buyer", "created_at")
    search_fields = ("buyer__email", "buyer__username")
    inlines = [CartItemInline]


admin.site.register(Cart, CartAdmin)


# ✅ Cart Item Admin
class CartItemAdmin(admin.ModelAdmin):
    list_display = ("cart", "product", "quantity", "total_price")
    list_filter = ("cart__buyer", "product")
    search_fields = ("product__name", "cart__buyer__email")


admin.site.register(CartItem, CartItemAdmin)


@admin.register(ContactUs)
class ContactUsAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'phone_number', 'message', 'created_at')
    search_fields = ('full_name', 'phone_number', 'message')
    list_filter = ('created_at',)
    
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("total_price",)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "buyer", "status", "total_price", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("buyer__email",)
    inlines = [OrderItemInline]


admin.site.register(OrderItem)

    
    
@admin.register(CustomerAddress)
class CustomerAddressAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "buyer",
        "first_name",
        "last_name",
        "city",
        "county",
        "phone",
        "created_at",
    )
    list_filter = ("county", "city", "created_at")
    search_fields = (
        "first_name",
        "last_name",
        "contact",
        "city",
        "address",
        "postal_code",
        "phone",
        "buyer__username",
        "buyer__email",
    )
    ordering = ("-created_at",)
    readonly_fields = ("created_at",)

    fieldsets = (
        (None, {
            "fields": (
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
            )
        }),
    )


admin.site.register(Transaction)
