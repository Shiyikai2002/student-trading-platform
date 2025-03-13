from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
import re

from django.utils import timezone


# Custom User Model to enforce email validation
class CustomUser(AbstractUser):
    profile_image = models.ImageField(upload_to='profile_pics/', null=True, blank=True)
    bio = models.TextField(blank=True, null=True)
    email = models.EmailField(unique=True)  # Ensure email is unique
    is_verified = models.BooleanField(default=False)  # Future email verification flag
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)  
    address = models.CharField(max_length=255, blank=True, null=True)  # 新增地址字段


    def save(self, *args, **kwargs):
        if not re.match(r"^\d{7}[A-Z]@student\.gla\.ac\.uk$", self.email):
            raise ValidationError("Please use a valid university email address.")
        super().save(*args, **kwargs)

    def deposit(self, amount):
        if amount > 0:
            self.balance += amount
            self.save()

# Item model for listing products
class Item(models.Model):
    CATEGORY_CHOICES = [
        ('Books', 'Books'),
        ('Electronics', 'Electronics'),
        ('Clothing', 'Clothing'),
        ('Furniture', 'Furniture'),
        ('Others', 'Others'),
    ]
    STATUS_CHOICES = [
        ('Available', 'Available'),
        ('Pending', 'Pending'),
        ('Sold', 'Sold'),
    ]

    name = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='items/', null=True, blank=True)
    seller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Available')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.get_status_display()}"

# Item Images (For multi-image support)
class ItemImage(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='items/')

# Transaction model for purchases
class Transaction(models.Model):
    buyer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='purchases')
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=[('Pending', 'Pending'), ('Sold', 'Sold')])
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    date_initiated = models.DateTimeField(auto_now_add=True)
    date_completed = models.DateTimeField(null=True, blank=True)
    buyer_confirmation = models.BooleanField(default=False)
    seller_confirmation = models.BooleanField(default=False)

    def confirm_transaction(self, user):
        """Allows buyer and seller to confirm the transaction"""
        if user == self.buyer:
            self.buyer_confirmation = True
        if user == self.item.seller:
            self.seller_confirmation = True

        if self.buyer_confirmation and self.seller_confirmation:
            self.status = "Sold"
            self.date_completed = timezone.now()
            self.item.status = "Sold"
            self.item.save()

        self.save()

    def __str__(self):
        return f"Transaction: {self.item.name} - {self.status}"

# Review model for user feedback
class Review(models.Model):
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    rating = models.IntegerField(choices=[(i, str(i)) for i in range(1, 6)])
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review by {self.reviewer.username} on {self.item.name}"

# Report model for inappropriate listings
class Report(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Reviewed', 'Reviewed'),
        ('Resolved', 'Resolved'),
    ]

    reported_item = models.ForeignKey('Item', on_delete=models.CASCADE, related_name='reports')
    reported_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    reason = models.TextField()  # Reason for reporting
    description = models.TextField(blank=True, null=True)  # Description field
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    reported_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Report on {self.reported_item.name} by {self.reported_by.username}"

class Offer(models.Model):
    buyer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(
        max_length=10, choices=[('Pending', 'Pending'), ('Accepted', 'Accepted'), ('Rejected', 'Rejected')],
        default='Pending'
    )
    created_at = models.DateTimeField(auto_now_add=True)

class UserRating(models.Model):
    rated_user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='received_ratings', on_delete=models.CASCADE)
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='given_ratings', on_delete=models.CASCADE)
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

class Cart(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

class Wishlist(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

class Message(models.Model):
    sender = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="sent_messages")
    receiver = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="received_messages")
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"From {self.sender} to {self.receiver}: {self.content[:30]}"
