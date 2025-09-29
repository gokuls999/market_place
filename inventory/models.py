from django.db import models
from django.contrib.auth.models import AbstractUser
import uuid

class Users(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    role = models.CharField(
        max_length=20,
        choices=[('customer', 'Customer'), ('seller', 'Seller'), ('admin', 'Admin'), ('inspector', 'Inspector')],
        default='customer'
    )
    phone = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    is_verified = models.BooleanField(default=False)

class Sellers(models.Model):
    user = models.OneToOneField(Users, on_delete=models.CASCADE, primary_key=True)
    business_name = models.CharField(max_length=100)
    gst_number = models.CharField(max_length=15, unique=True)
    bank_details = models.TextField()
    rating = models.FloatField(default=0.0)
    approved = models.BooleanField(default=False)

class Categories(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE)
    description = models.TextField(blank=True)

class Products(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    seller = models.ForeignKey(Sellers, on_delete=models.CASCADE)
    category = models.ForeignKey(Categories, on_delete=models.CASCADE)
    attributes = models.JSONField(default=dict)
    image_urls = models.JSONField(default=list)
    approved = models.BooleanField(default=False)

class Hubs(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    address = models.TextField()
    latitude = models.FloatField()
    longitude = models.FloatField()
    region = models.CharField(max_length=50)
    capacity = models.IntegerField()

class Cart(models.Model):
    user = models.ForeignKey(Users, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Products, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['cart', 'product']  # Prevent duplicate products in cart    