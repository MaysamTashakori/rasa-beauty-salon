from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from datetime import datetime, timedelta
import jdatetime

def main_menu():
    keyboard = [
        [InlineKeyboardButton("🏠 سالن‌های ما", callback_data='salons')],
        [InlineKeyboardButton("📅 رزرو نوبت", callback_data='book_appointment')],
        [InlineKeyboardButton("👤 پروفایل من", callback_data='profile')],
        [InlineKeyboardButton("📋 نوبت‌های من", callback_data='appointments')],
        [InlineKeyboardButton("💬 پشتیبانی", callback_data='support')]
    ]
    return InlineKeyboardMarkup(keyboard)

def register_menu():
    keyboard = [
        [InlineKeyboardButton("👤 ثبت‌نام مشتری", callback_data='register_customer')],
        [InlineKeyboardButton("💇‍♀️ ثبت‌نام آرایشگر", callback_data='register_stylist')]
    ]
    return InlineKeyboardMarkup(keyboard)

def salon_services_menu(salon_id):
    keyboard = [
        [InlineKeyboardButton("💇‍♀️ خدمات مو", callback_data=f'services_hair_{salon_id}')],
        [InlineKeyboardButton("💅 خدمات ناخن", callback_data=f'services_nail_{salon_id}')],
        [InlineKeyboardButton("👗 خدمات پوست", callback_data=f'services_skin_{salon_id}')],
        [InlineKeyboardButton("💄 آرایش", callback_data=f'services_makeup_{salon_id}')],
        [InlineKeyboardButton("🔙 بازگشت", callback_data='main_menu')]
    ]
    return InlineKeyboardMarkup(keyboard)

def appointments_menu():
    keyboard = [
        [InlineKeyboardButton("📅 نوبت‌های فعال", callback_data='active_appointments')],
        [InlineKeyboardButton("📋 تاریخچه نوبت‌ها", callback_data='appointment_history')],
        [InlineKeyboardButton("❌ لغو نوبت", callback_data='cancel_appointment')],
        [InlineKeyboardButton("🏠 منوی اصلی", callback_data='main_menu')]
    ]
    return InlineKeyboardMarkup(keyboard)

def salon_details_menu(salon_id):
    keyboard = [
        [InlineKeyboardButton("📸 گالری تصاویر", callback_data=f'gallery_{salon_id}')],
        [InlineKeyboardButton("💰 لیست خدمات", callback_data=f'services_{salon_id}')],
        [InlineKeyboardButton("📍 موقعیت و آدرس", callback_data=f'location_{salon_id}')],
        [InlineKeyboardButton("⭐️ نظرات مشتریان", callback_data=f'reviews_{salon_id}')],
        [InlineKeyboardButton("📅 رزرو نوبت", callback_data=f'book_{salon_id}')],
        [InlineKeyboardButton("🏠 منوی اصلی", callback_data='main_menu')]
    ]
    return InlineKeyboardMarkup(keyboard)

def time_slots_menu(available_times, date):
    keyboard = []
    for time in available_times:
        keyboard.append([
            InlineKeyboardButton(
                f"⏰ {time}", 
                callback_data=f'time_{date}_{time}'
            )
        ])
    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data='select_date')])
    return InlineKeyboardMarkup(keyboard)

def profile_menu():
    keyboard = [
        [InlineKeyboardButton("✏️ ویرایش پروفایل", callback_data='edit_profile')],
        [InlineKeyboardButton("💰 کیف پول", callback_data='wallet')],
        [InlineKeyboardButton("🎁 امتیازات من", callback_data='my_points')],
        [InlineKeyboardButton("🏠 منوی اصلی", callback_data='main_menu')]
    ]
    return InlineKeyboardMarkup(keyboard)

def payment_menu(appointment_id, amount):
    keyboard = [
        [InlineKeyboardButton("💳 پرداخت آنلاین", callback_data=f'pay_online_{appointment_id}')],
        [InlineKeyboardButton("💰 پرداخت از کیف پول", callback_data=f'pay_wallet_{appointment_id}')],
        [InlineKeyboardButton("❌ انصراف", callback_data='cancel_payment')]
    ]
    return InlineKeyboardMarkup(keyboard)


def date_picker_menu():
    keyboard = []
    today = jdatetime.datetime.now()
    for i in range(7):
        date = today + timedelta(days=i)
        persain_date = jdatetime.date.fromgregorian(date=date.date())
        keyboard.append([
            InlineKeyboardButton(
                f"📅 {persain_date.strftime('%Y/%m/%d')}",
                callback_data=f'date_{persain_date.strftime("%Y-%m-%d")}'
            )
        ])
    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data='main_menu')])
    return InlineKeyboardMarkup(keyboard)
