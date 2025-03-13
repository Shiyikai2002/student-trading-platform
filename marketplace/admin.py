from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from .models import CustomUser, Item, ItemImage, Transaction, Review, Report

# Custom User Admin
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ['username', 'email', 'is_verified', 'is_staff', 'is_active']
    list_filter = ['is_verified', 'is_staff', 'is_active']
    search_fields = ['username', 'email']
    fieldsets = UserAdmin.fieldsets + (
        ('Custom Fields', {'fields': ('is_verified',)}),
    )

# Inline display for multiple item images
class ItemImageInline(admin.TabularInline):
    model = ItemImage
    extra = 1  # Allows adding multiple images

# Item Admin with preview functionality
class ItemAdmin(admin.ModelAdmin):
    list_display = ['name', 'seller', 'price', 'category', 'status', 'created_at', 'image_preview']
    list_filter = ['category', 'status']
    search_fields = ['name', 'description', 'seller__username']
    inlines = [ItemImageInline]

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="50" height="50" style="border-radius:5px;"/>'.format(obj.image.url))
        return "No Image"
    image_preview.short_description = "Preview"

# Transaction Admin
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['buyer', 'item', 'total_price', 'status', 'date_initiated', 'date_completed']
    list_filter = ['status']
    search_fields = ['buyer__username', 'item__name']

# Review Admin
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['reviewer', 'item', 'rating', 'created_at']
    list_filter = ['rating']
    search_fields = ['reviewer__username', 'item__name']

class ReportAdmin(admin.ModelAdmin):
    list_display = ('reported_item', 'reported_by', 'status', 'reported_at')
    list_filter = ('status',)
    search_fields = ('reported_item__name', 'reported_by__username')

# Register models in Django admin
admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Item, ItemAdmin)
admin.site.register(Transaction, TransactionAdmin)
admin.site.register(Review, ReviewAdmin)
admin.site.register(Report, ReportAdmin)