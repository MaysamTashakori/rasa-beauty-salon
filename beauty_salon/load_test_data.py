from django.core.management.base import BaseCommand
from salon.models import User, Salon, Service, WorkingHours
from django.utils import timezone
from datetime import time

class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        # ایجاد سالن‌ها
        salon1 = Salon.objects.create(
            name="سالن زیبایی ونوس",
            phone="02133445566",
            address="تهران، خیابان ولیعصر",
            description="بهترین سالن زیبایی با 10 سال سابقه",
            rating=4.5,
            is_active=True
        )

        salon2 = Salon.objects.create(
            name="آرایشگاه گلبرگ",
            phone="02177889900",
            address="تهران، سعادت آباد",
            description="ارائه خدمات تخصصی عروس",
            rating=4.8,
            is_active=True
        )

        # ایجاد خدمات
        services_data = [
            {
                'salon': salon1,
                'name': 'کوتاهی مو',
                'price': 150000,
                'duration': 45,
                'category': 'مو',
                'description': 'کوتاهی مو با جدیدترین متدها'
            },
            {
                'salon': salon1,
                'name': 'رنگ مو',
                'price': 500000,
                'duration': 120,
                'category': 'مو',
                'description': 'رنگ مو با برندهای معتبر'
            },
            {
                'salon': salon2,
                'name': 'میکاپ عروس',
                'price': 2500000,
                'duration': 180,
                'category': 'آرایش',
                'description': 'میکاپ حرفه‌ای عروس'
            },
            {
                'salon': salon2,
                'name': 'پاکسازی پوست',
                'price': 350000,
                'duration': 60,
                'category': 'پوست',
                'description': 'پاکسازی تخصصی پوست'
            }
        ]

        for service_data in services_data:
            Service.objects.create(**service_data)

        # ایجاد ساعات کاری
        days = range(7)  # 0=شنبه تا 6=جمعه
        for salon in [salon1, salon2]:
            for day in days:
                WorkingHours.objects.create(
                    salon=salon,
                    day=day,
                    start_time=time(9, 0),  # 9:00
                    end_time=time(21, 0),   # 21:00
                    is_closed=day == 5  # جمعه‌ها تعطیل
                )

        self.stdout.write("اطلاعات تستی با موفقیت اضافه شدند!")
