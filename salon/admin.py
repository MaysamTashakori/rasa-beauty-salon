from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Salon, Service, Appointment, Portfolio, Payment, WorkingHours


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'first_name', 'last_name', 'phone', 'points', 'wallet_balance']
    search_fields = ['username', 'first_name', 'last_name', 'phone']
    fieldsets = BaseUserAdmin.fieldsets + (
        ('اطلاعات اضافی', {'fields': ('telegram_id', 'phone', 'points', 'wallet_balance')}),
    )

@admin.register(Salon)
class SalonAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone', 'rating', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'phone']

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ['name', 'salon', 'price', 'duration', 'category', 'is_active']
    list_filter = ['category', 'salon', 'is_active']
    search_fields = ['name', 'description']

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ['user', 'service', 'date', 'time', 'status', 'is_paid']
    list_filter = ['status', 'is_paid', 'date']
    search_fields = ['user__username', 'service__name']
    date_hierarchy = 'date'

@admin.register(Portfolio)
class PortfolioAdmin(admin.ModelAdmin):
    list_display = ['salon', 'created_at']
    list_filter = ['salon', 'created_at']
    search_fields = ['description']

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['appointment', 'amount', 'is_verified', 'created_at']
    list_filter = ['is_verified', 'created_at']
    search_fields = ['transaction_id']
    date_hierarchy = 'created_at'

@admin.register(WorkingHours)
class WorkingHoursAdmin(admin.ModelAdmin):
    list_display = ['salon', 'get_day_display', 'start_time', 'end_time', 'is_closed']
    list_filter = ['day', 'is_closed', 'salon']
