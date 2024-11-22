from django.db import models
from django.utils import timezone
import jdatetime
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    telegram_id = models.CharField(max_length=50, unique=True, null=True)
    phone = models.CharField(max_length=11, null=True)
    points = models.IntegerField(default=0)
    wallet_balance = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.get_full_name()} - {self.phone}"

class Salon(models.Model):
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=11)
    address = models.TextField()
    description = models.TextField()
    rating = models.FloatField(default=0)
    is_active = models.BooleanField(default=True)
    latitude = models.FloatField()
    longitude = models.FloatField()
    instagram = models.CharField(max_length=100, blank=True, null=True)
    manager_phone = models.CharField(max_length=11, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Service(models.Model):
    CATEGORIES = [
        ('hair', 'مو'),
        ('nail', 'ناخن'),
        ('skin', 'پوست'),
        ('makeup', 'آرایش')
    ]
    
    salon = models.ForeignKey(Salon, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.IntegerField()
    duration = models.IntegerField(help_text='مدت زمان به دقیقه')
    category = models.CharField(max_length=10, choices=CATEGORIES)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} - {self.salon.name}"

class Appointment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'در انتظار پرداخت'),
        ('confirmed', 'تایید شده'),
        ('cancelled', 'لغو شده'),
        ('completed', 'انجام شده')
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    date = models.DateField()
    time = models.TimeField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    payment_id = models.CharField(max_length=100, null=True, blank=True)
    is_paid = models.BooleanField(default=False)

    def get_persian_date(self):
        return jdatetime.date.fromgregorian(date=self.date)

    def __str__(self):
        return f"{self.user.full_name} - {self.service.name} - {self.date}"

class Portfolio(models.Model):
    salon = models.ForeignKey(Salon, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='portfolio/')
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.salon.name} - {self.created_at}"

class Review(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    salon = models.ForeignKey(Salon, on_delete=models.CASCADE)
    rating = models.IntegerField()
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.full_name} - {self.salon.name} - {self.rating}"

class WorkingHours(models.Model):
    DAYS = [
        (0, 'شنبه'),
        (1, 'یکشنبه'),
        (2, 'دوشنبه'),
        (3, 'سه‌شنبه'),
        (4, 'چهارشنبه'),
        (5, 'پنج‌شنبه'),
        (6, 'جمعه')
    ]
    
    salon = models.ForeignKey(Salon, on_delete=models.CASCADE)
    day = models.IntegerField(choices=DAYS)
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_closed = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.salon.name} - {self.get_day_display()}"

class Payment(models.Model):
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE)
    amount = models.IntegerField()
    transaction_id = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)

    def verify(self):
        # اینجا کد تایید پرداخت از درگاه بانکی قرار می‌گیرد
        return True