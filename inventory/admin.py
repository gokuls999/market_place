from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Users, Sellers

class CustomUserAdmin(UserAdmin):
    model = Users
    list_display = ['username', 'email', 'phone', 'role', 'is_verified', 'date_joined']
    list_filter = ['role', 'is_verified', 'date_joined']
    search_fields = ['username', 'email', 'phone']
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('phone', 'role', 'address', 'is_verified')}),
    )

class SellersAdmin(admin.ModelAdmin):
    model = Sellers
    list_display = ['user', 'business_name', 'gst_number', 'approved', 'onboarding_date']
    list_filter = ['approved', 'onboarding_date']
    search_fields = ['user__username', 'business_name', 'gst_number']
    readonly_fields = ('onboarding_date',)  # Make onboarding_date readonly
    fieldsets = (
        ('User Info', {'fields': ('user',)}),
        ('Business Details', {'fields': ('business_name', 'gst_number', 'bank_details')}),
        ('Approval', {'fields': ('approved',)}),
        ('Documents', {'fields': ('documents',)}),
        ('Date', {'fields': ('onboarding_date',)}),  # No 'readonly' here
    )

admin.site.register(Users, CustomUserAdmin)
admin.site.register(Sellers, SellersAdmin)