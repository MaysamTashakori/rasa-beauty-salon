import os
import django
from bot.ai_chat import BeautySalonAI
import logging
import jdatetime
import requests
from django.conf import settings
from django.utils import timezone
from datetime import datetime, timedelta
from salon.models import User, Salon, Service, Appointment, Portfolio, WorkingHours, Payment
from bot.payment_handler import PaymentHandler
from bot.point_system import PointSystem

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'beauty_salon.settings')
django.setup()
from telegram import (
    Update, 
    InlineKeyboardButton, 
    InlineKeyboardMarkup,
    InputMediaPhoto
)
from telegram.ext import (
    ApplicationBuilder, 
    CommandHandler, 
    CallbackQueryHandler, 
    MessageHandler, 
    filters, 
    ContextTypes
)
from bot.keyboards import (
    main_menu, 
    register_menu, 
    salon_services_menu, 
    appointments_menu, 
    salon_details_menu,
    profile_menu,
    payment_menu
)
from salon.models import User, Salon, Service, Appointment, Portfolio

class PaymentSystem:
    def __init__(self):
        self.api_key = settings.IDPAY_API_KEY
        self.sandbox = settings.IDPAY_SANDBOX
        
    async def create_payment(self, amount, appointment_id):
        headers = {
            'X-API-KEY': self.api_key,
            'Content-Type': 'application/json'
        }
        data = {
            'order_id': str(appointment_id),
            'amount': amount,
            'callback': f"{settings.SITE_URL}/verify/{appointment_id}/",
            'name': 'پرداخت نوبت آرایشگاه',
        }
        response = requests.post(
            'https://api.idpay.ir/v1.1/payment',
            json=data,
            headers=headers
        )
        if response.status_code == 201:
            return response.json()['link']
        return None
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'beauty_salon.settings')
django.setup()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    telegram_id = str(user.id)
    
    try:
        db_user = User.objects.get(telegram_id=telegram_id)
        await update.message.reply_text(
            f"خوش آمدید {db_user.get_full_name()}!",
            reply_markup=main_menu()
        )
    except User.DoesNotExist:
        await update.message.reply_text(
            "به سیستم نوبت‌دهی سالن زیبایی خوش آمدید!\n"
            "لطفاً نوع کاربری خود را انتخاب کنید:",
            reply_markup=register_menu()
        )

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == 'register_customer':
        context.user_data['registration_type'] = 'customer'
        await query.message.edit_text(
            "لطفاً شماره موبایل خود را وارد کنید:",
            reply_markup=None
        )
    elif query.data == 'register_salon':
        context.user_data['registration_type'] = 'salon'
        await query.message.edit_text(
            "لطفاً نام سالن خود را وارد کنید:",
            reply_markup=None
        )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if 'registration_type' in context.user_data:
        # پردازش مراحل ثبت‌نام
        registration_type = context.user_data['registration_type']
        message = update.message.text
        
        if registration_type == 'customer':
            # ثبت اطلاعات مشتری
            await update.message.reply_text(
                "ثبت‌نام شما با موفقیت انجام شد!",
                reply_markup=main_menu()
            )
        elif registration_type == 'salon':
            # ثبت اطلاعات سالن
            await update.message.reply_text(
                "اطلاعات سالن شما ثبت شد!",
                reply_markup=main_menu()
            )
async def show_salons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    salons = Salon.objects.all()
    keyboard = []
    for salon in salons:
        keyboard.append([
            InlineKeyboardButton(salon.name, callback_data=f'salon_{salon.id}')
        ])
    await update.callback_query.edit_message_text(
        "سالن‌های موجود:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def handle_salon_selection(update: Update, context: ContextTypes.DEFAULT_TYPE, salon_id):
    salon = Salon.objects.get(id=salon_id)
    await update.callback_query.edit_message_text(
        f"خدمات سالن {salon.name}:",
        reply_markup=salon_services_menu(salon_id)
    )

async def handle_service_selection(update: Update, context: ContextTypes.DEFAULT_TYPE, service_id):
    service = Service.objects.get(id=service_id)
    # نمایش تقویم برای 7 روز آینده
    dates = []
    today = jdatetime.datetime.now()
    keyboard = []
    for i in range(7):
        date = today + timedelta(days=i)
        persian_date = jdatetime.date.fromgregorian(date=date.date())
        keyboard.append([
            InlineKeyboardButton(
                persian_date.strftime("%Y/%m/%d"),
                callback_data=f'date_{service_id}_{date.strftime("%Y-%m-%d")}'
            )
        ])
    await update.callback_query.edit_message_text(
        f"لطفاً تاریخ مورد نظر برای {service.name} را انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
async def show_appointments(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = User.objects.get(telegram_id=str(update.effective_user.id))
    appointments = Appointment.objects.filter(customer=user).order_by('-date', '-time')
    
    if not appointments:
        await update.callback_query.edit_message_text(
            "شما هیچ نوبت فعالی ندارید!",
            reply_markup=main_menu()
        )
        return

    text = "📅 نوبت‌های شما:\n\n"
    for apt in appointments:
        text += f"🏠 سالن: {apt.salon.name}\n"
        text += f"💇‍♀️ خدمت: {apt.service.name}\n"
        text += f"📅 تاریخ: {apt.date}\n"
        text += f"⏰ ساعت: {apt.time}\n"
        text += f"💰 مبلغ: {apt.service.price:,} تومان\n"
        text += f"وضعیت: {apt.get_status_display()}\n"
        text += "─────────────\n"

    await update.callback_query.edit_message_text(
        text,
        reply_markup=appointments_menu()
    )

async def cancel_appointment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = User.objects.get(telegram_id=str(update.effective_user.id))
    active_appointments = Appointment.objects.filter(
        customer=user,
        status='confirmed',
        date__gte=datetime.now().date()
    )
    
    keyboard = []
    for apt in active_appointments:
        keyboard.append([
            InlineKeyboardButton(
                f"{apt.date} - {apt.time} - {apt.service.name}",
                callback_data=f'cancel_{apt.id}'
            )
        ])
    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data='appointments')])
    
    await update.callback_query.edit_message_text(
        "لطفاً نوبتی که می‌خواهید لغو کنید را انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def show_salon_details(update: Update, context: ContextTypes.DEFAULT_TYPE, salon_id):
    salon = Salon.objects.get(id=salon_id)
    services = Service.objects.filter(salon=salon)
    
    text = f"🏠 {salon.name}\n\n"
    text += f"📝 توضیحات:\n{salon.description}\n\n"
    text += "💰 خدمات و قیمت‌ها:\n"
    for service in services:
        text += f"• {service.name}: {service.price:,} تومان\n"
        text += f"⏱ مدت زمان: {service.duration}\n"
        text += "──────────\n"

    await update.callback_query.edit_message_text(
        text,
        reply_markup=salon_details_menu(salon_id)
    )

async def show_salon_gallery(update: Update, context: ContextTypes.DEFAULT_TYPE, salon_id):
    salon = Salon.objects.get(id=salon_id)
    portfolio = Portfolio.objects.filter(salon=salon)
    
    if not portfolio:
        await update.callback_query.edit_message_text(
            "هنوز تصویری برای این سالن ثبت نشده است.",
            reply_markup=salon_details_menu(salon_id)
        )
        return

    # ارسال تصاویر به صورت آلبوم
    media_group = []
    for item in portfolio:
        media_group.append(InputMediaPhoto(item.image.url, caption=item.title))
    
    await update.callback_query.message.reply_media_group(media_group)
    await update.callback_query.message.reply_text(
        "برای بازگشت به منو یکی از گزینه‌ها را انتخاب کنید:",
        reply_markup=salon_details_menu(salon_id)
    )

class PaymentSystem:
    def __init__(self):
        self.api_key = settings.IDPAY_API_KEY
        self.sandbox = settings.IDPAY_SANDBOX
        self.headers = {
            'X-API-KEY': self.api_key,
            'Content-Type': 'application/json'
        }

    async def create_payment(self, amount, appointment_id):
        data = {
            'order_id': str(appointment_id),
            'amount': amount * 10,  # تبدیل به ریال
            'callback': f"{settings.SITE_URL}/verify/{appointment_id}/",
            'name': 'پرداخت نوبت آرایشگاه',
            'desc': f'پرداخت نوبت شماره {appointment_id}'
        }
        
        response = requests.post(
            'https://api.idpay.ir/v1.1/payment',
            json=data,
            headers=self.headers
        )
        
        if response.status_code == 201:
            return response.json().get('link')
        return None

async def process_payment(update: Update, context: ContextTypes.DEFAULT_TYPE, appointment_id):
    try:
        appointment = Appointment.objects.get(id=appointment_id)
        amount = appointment.service.price
        
        payment_system = PaymentSystem()
        payment_url = await payment_system.create_payment(amount, appointment_id)
        
        if payment_url:
            keyboard = [
                [InlineKeyboardButton("💳 پرداخت آنلاین", url=payment_url)],
                [InlineKeyboardButton("❌ انصراف", callback_data=f'cancel_payment_{appointment_id}')]
            ]
            await update.callback_query.edit_message_text(
                f"💰 مبلغ قابل پرداخت: {amount:,} تومان\n"
                "🔄 در حال انتقال به درگاه پرداخت...\n\n"
                "✅ لطفاً روی دکمه پرداخت آنلاین کلیک کنید.",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            await update.callback_query.edit_message_text(
                "❌ متأسفانه در ایجاد لینک پرداخت مشکلی پیش آمده.\n"
                "لطفاً دوباره تلاش کنید.",
                reply_markup=main_menu()
            )
    except Appointment.DoesNotExist:
        await update.callback_query.edit_message_text(
            "❌ نوبت مورد نظر یافت نشد.",
            reply_markup=main_menu()
        )

ai_chat = BeautySalonAI()

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message.text
    user_id = update.effective_user.id
    
    # اگر کاربر در حال ثبت‌نام است
    if 'registration_type' in context.user_data:
        await handle_registration(update, context)
        return
        
    # پاسخ هوشمند به پیام کاربر
    response = ai_chat.get_response(message)
    await update.message.reply_text(response)

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    
    if data.startswith('salon_'):
        salon_id = int(data.split('_')[1])
        await show_salon_details(update, context, salon_id)
    
    elif data.startswith('service_'):
        service_id = int(data.split('_')[1])
        await handle_service_selection(update, context, service_id)
    
    elif data.startswith('book_'):
        appointment_id = int(data.split('_')[1])
        await process_payment(update, context, appointment_id)

async def handle_registration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message.text
    registration_type = context.user_data['registration_type']
    
    if registration_type == 'customer':
        if 'phone' not in context.user_data:
            # بررسی صحت شماره موبایل
            if len(message) == 11 and message.startswith('09'):
                context.user_data['phone'] = message
                await update.message.reply_text("لطفاً نام و نام خانوادگی خود را وارد کنید:")
            else:
                await update.message.reply_text("شماره موبایل نامعتبر است. لطفاً دوباره وارد کنید:")
        else:
            # ذخیره اطلاعات کاربر
            User.objects.create(
                telegram_id=str(update.effective_user.id),
                phone=context.user_data['phone'],
                full_name=message
            )
            del context.user_data['registration_type']
            del context.user_data['phone']
            await update.message.reply_text(
                "ثبت‌نام شما با موفقیت انجام شد!",
                reply_markup=main_menu()
            )


async def show_portfolio(update: Update, context: ContextTypes.DEFAULT_TYPE, salon_id):
    salon = Salon.objects.get(id=salon_id)
    portfolio = Portfolio.objects.filter(salon=salon)
    
    # دسته‌بندی نمونه کارها
    categories = {}
    for item in portfolio:
        if item.category not in categories:
            categories[item.category] = []
        categories[item.category].append(item)
    
    # ساخت آلبوم برای هر دسته
    for category, items in categories.items():
        media_group = []
        category_name = dict(Portfolio._meta.get_field('category').choices)[category]
        await update.callback_query.message.reply_text(f"🎨 {category_name}:")
        
        for item in items:
            media_group.append(
                InputMediaPhoto(
                    item.image.url,
                    caption=f"{item.title}\n{item.description}"
                )
            )
        await update.callback_query.message.reply_media_group(media_group)

async def show_salon_details(update: Update, context: ContextTypes.DEFAULT_TYPE, salon_id):
    salon = Salon.objects.get(id=salon_id)
    text = f"""
🏠 {salon.name}
📍 آدرس: {salon.address}
📞 تلفن: {salon.phone}
⭐️ امتیاز: {salon.rating}

{salon.description}
"""
    await update.callback_query.edit_message_text(
        text,
        reply_markup=salon_details_menu(salon_id)
    )

async def handle_service_selection(update: Update, context: ContextTypes.DEFAULT_TYPE, service_id):
    service = Service.objects.get(id=service_id)
    text = f"""
💇‍♀️ {service.name}
💰 قیمت: {service.price:,} تومان
⏱ مدت زمان: {service.duration} دقیقه

{service.description}
"""
    keyboard = [
        [InlineKeyboardButton("📅 رزرو نوبت", callback_data=f'book_service_{service_id}')],
        [InlineKeyboardButton("🔙 بازگشت", callback_data=f'salon_{service.salon.id}')]
    ]
    await update.callback_query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def show_appointments(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = User.objects.get(telegram_id=str(update.effective_user.id))
    appointments = Appointment.objects.filter(user=user).order_by('-date', '-time')
    
    if not appointments:
        await update.callback_query.edit_message_text(
            "شما هیچ نوبت فعالی ندارید!",
            reply_markup=main_menu()
        )
        return

    text = "📋 نوبت‌های شما:\n\n"
    for apt in appointments:
        text += f"""
🕐 تاریخ: {apt.get_persian_date()}
⏰ ساعت: {apt.time.strftime('%H:%M')}
💇‍♀️ خدمت: {apt.service.name}
💰 مبلغ: {apt.service.price:,} تومان
📍 سالن: {apt.service.salon.name}
وضعیت: {dict(Appointment.STATUS_CHOICES)[apt.status]}
"""
    await update.callback_query.edit_message_text(
        text,
        reply_markup=appointments_menu()
    )
async def show_salons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    salons = Salon.objects.filter(is_active=True)
    text = "🏠 سالن‌های فعال:\n\n"
    keyboard = []
    
    for salon in salons:
        text += f"""
{salon.name}
📍 {salon.address}
⭐️ امتیاز: {salon.rating}
"""
        keyboard.append([InlineKeyboardButton(salon.name, callback_data=f'salon_{salon.id}')])
    
    keyboard.append([InlineKeyboardButton("🔙 منوی اصلی", callback_data='main_menu')])
    await update.callback_query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def show_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = User.objects.get(telegram_id=str(update.effective_user.id))
    text = f"""
👤 پروفایل شما:

نام: {user.full_name}
تلفن: {user.phone}
امتیاز: {user.points}
کیف پول: {user.wallet_balance:,} تومان
"""
    await update.callback_query.edit_message_text(
        text,
        reply_markup=profile_menu()
    )

async def book_service(update: Update, context: ContextTypes.DEFAULT_TYPE, service_id):
    service = Service.objects.get(id=service_id)
    salon = service.salon
    
    # نمایش تقویم برای 7 روز آینده
    today = jdatetime.datetime.now()
    keyboard = []
    
    for i in range(7):
        date = today + timedelta(days=i)
        persian_date = date.strftime("%Y/%m/%d")
        keyboard.append([
            InlineKeyboardButton(
                f"📅 {persian_date}", 
                callback_data=f'select_date_{service_id}_{date.strftime("%Y-%m-%d")}'
            )
        ])
    
    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data=f'service_{service_id}')])
    
    await update.callback_query.edit_message_text(
        f"لطفاً تاریخ مورد نظر برای {service.name} را انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def show_time_slots(update: Update, context: ContextTypes.DEFAULT_TYPE, service_id, date_str):
    service = Service.objects.get(id=service_id)
    salon = service.salon
    
    # ساعت‌های کاری سالن در روز انتخاب شده
    working_hours = WorkingHours.objects.get(
        salon=salon,
        day=jdatetime.datetime.strptime(date_str, '%Y-%m-%d').weekday()
    )
    
    if working_hours.is_closed:
        await update.callback_query.edit_message_text(
            "⚠️ سالن در این روز تعطیل است. لطفاً روز دیگری را انتخاب کنید.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 بازگشت", callback_data=f'book_service_{service_id}')
            ]])
        )
        return
    
    # ایجاد لیست ساعت‌های خالی
    start_time = working_hours.start_time
    end_time = working_hours.end_time
    duration = timedelta(minutes=service.duration)
    
    current_time = datetime.strptime(start_time.strftime('%H:%M'), '%H:%M')
    end = datetime.strptime(end_time.strftime('%H:%M'), '%H:%M')
    
    available_times = []
    while current_time + duration <= end:
        # بررسی تداخل با نوبت‌های دیگر
        if not Appointment.objects.filter(
            service__salon=salon,
            date=date_str,
            time=current_time.time(),
            status__in=['confirmed', 'pending']
        ).exists():
            available_times.append(current_time.strftime('%H:%M'))
        current_time += duration
    
    if not available_times:
        await update.callback_query.edit_message_text(
            "⚠️ متأسفانه در این روز نوبت خالی وجود ندارد. لطفاً روز دیگری را انتخاب کنید.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 بازگشت", callback_data=f'book_service_{service_id}')
            ]])
        )
        return
    
    keyboard = []
    for time in available_times:
        keyboard.append([
            InlineKeyboardButton(
                f"⏰ {time}",
                callback_data=f'confirm_booking_{service_id}_{date_str}_{time}'
            )
        ])
    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data=f'book_service_{service_id}')])
    
    await update.callback_query.edit_message_text(
        "لطفاً ساعت مورد نظر را انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def confirm_booking(update: Update, context: ContextTypes.DEFAULT_TYPE, service_id, date_str, time_str):
    service = Service.objects.get(id=service_id)
    user = User.objects.get(telegram_id=str(update.effective_user.id))
    
    # ایجاد نوبت
    appointment = Appointment.objects.create(
        user=user,
        service=service,
        date=datetime.strptime(date_str, '%Y-%m-%d').date(),
        time=datetime.strptime(time_str, '%H:%M').time(),
        status='pending'
    )
    
    # ارسال به درگاه پرداخت
    await process_payment(update, context, appointment.id)
async def cancel_appointment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = User.objects.get(telegram_id=str(update.effective_user.id))
    active_appointments = Appointment.objects.filter(
        user=user,
        status__in=['confirmed', 'pending'],
        date__gte=timezone.now().date()
    )
    
    if not active_appointments:
        await update.callback_query.edit_message_text(
            "شما هیچ نوبت فعالی برای لغو ندارید!",
            reply_markup=appointments_menu()
        )
        return
    
    keyboard = []
    for apt in active_appointments:
        keyboard.append([
            InlineKeyboardButton(
                f"{apt.service.name} - {apt.get_persian_date()} - {apt.time.strftime('%H:%M')}",
                callback_data=f'cancel_confirm_{apt.id}'
            )
        ])
    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data='appointments')])
    
    await update.callback_query.edit_message_text(
        "لطفاً نوبت مورد نظر برای لغو را انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def confirm_cancellation(update: Update, context: ContextTypes.DEFAULT_TYPE, appointment_id):
    appointment = Appointment.objects.get(id=appointment_id)
    appointment.status = 'cancelled'
    appointment.save()
    
    # برگشت مبلغ به کیف پول در صورت پرداخت شده بودن
    if appointment.is_paid:
        user = appointment.user
        user.wallet_balance += appointment.service.price
        user.save()
    
    await update.callback_query.edit_message_text(
        f"✅ نوبت شما با موفقیت لغو شد.\n"
        f"در صورت پرداخت، مبلغ به کیف پول شما برگشت داده شد.",
        reply_markup=appointments_menu()
    )

async def verify_payment(update: Update, context: ContextTypes.DEFAULT_TYPE, payment_id):
    try:
        payment = Payment.objects.get(id=payment_id)
        appointment = payment.appointment
        
        # بررسی وضعیت پرداخت
        if payment.verify():
            appointment.status = 'confirmed'
            appointment.is_paid = True
            appointment.save()
            
            # افزودن امتیاز به کاربر
            user = appointment.user
            user.points += int(appointment.service.price / 1000)  # هر 1000 تومان 1 امتیاز
            user.save()
            
            await update.callback_query.edit_message_text(
                f"✅ پرداخت با موفقیت انجام شد.\n"
                f"نوبت شما برای تاریخ {appointment.get_persian_date()} "
                f"ساعت {appointment.time.strftime('%H:%M')} تایید شد.",
                reply_markup=main_menu()
            )
        else:
            await update.callback_query.edit_message_text(
                "❌ پرداخت ناموفق بود. لطفاً دوباره تلاش کنید.",
                reply_markup=payment_menu(appointment.id, appointment.service.price)
            )
    except Exception as e:
        await update.callback_query.edit_message_text(
            "❌ خطا در بررسی پرداخت. لطفاً با پشتیبانی تماس بگیرید.",
            reply_markup=main_menu()
        )

async def show_gallery(update: Update, context: ContextTypes.DEFAULT_TYPE, salon_id):
    salon = Salon.objects.get(id=salon_id)
    portfolio_items = Portfolio.objects.filter(salon=salon)
    
    if not portfolio_items:
        await update.callback_query.edit_message_text(
            "هنوز تصویری در گالری این سالن ثبت نشده است.",
            reply_markup=salon_details_menu(salon_id)
        )
        return
    
    media_group = []
    for item in portfolio_items:
        media_group.append(
            InputMediaPhoto(
                media=item.image.url,
                caption=item.description
            )
        )
    
    await update.callback_query.message.reply_media_group(media_group)

async def process_payment(update: Update, context: ContextTypes.DEFAULT_TYPE, appointment_id):
    appointment = Appointment.objects.get(id=appointment_id)
    user = appointment.user
    amount = appointment.service.price

    keyboard = [
        [InlineKeyboardButton("💳 پرداخت آنلاین", callback_data=f'pay_online_{appointment_id}')],
        [InlineKeyboardButton("💰 پرداخت از کیف پول", callback_data=f'pay_wallet_{appointment_id}')]
    ]

    if user.wallet_balance >= amount:
        text = f"موجودی کیف پول شما: {user.wallet_balance:,} تومان\n"
        text += f"مبلغ قابل پرداخت: {amount:,} تومان"
    else:
        text = "موجودی کیف پول شما کافی نیست."

    await update.callback_query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def pay_from_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE, appointment_id):
    appointment = Appointment.objects.get(id=appointment_id)
    user = appointment.user
    amount = appointment.service.price

    if user.wallet_balance >= amount:
        user.wallet_balance -= amount
        user.save()
        appointment.is_paid = True
        appointment.status = 'confirmed'
        appointment.save()

        await update.callback_query.edit_message_text(
            f"✅ پرداخت از کیف پول با موفقیت انجام شد.\n"
            f"موجودی فعلی: {user.wallet_balance:,} تومان",
            reply_markup=main_menu()
        )
    else:
        await update.callback_query.edit_message_text(
            "❌ موجودی کیف پول کافی نیست.",
            reply_markup=payment_menu(appointment_id, amount)
        )

async def process_online_payment(update: Update, context: ContextTypes.DEFAULT_TYPE, appointment_id):
    appointment = Appointment.objects.get(id=appointment_id)
    amount = appointment.service.price
    
    payment_handler = PaymentHandler()
    callback_url = f"{settings.SITE_URL}/verify_payment/{appointment_id}/"
    
    result = payment_handler.request_payment(
        amount=amount,
        callback_url=callback_url,
        description=f"رزرو نوبت {appointment.service.name}"
    )
    
    if result['Status'] == 100:
        payment = Payment.objects.create(
            appointment=appointment,
            amount=amount,
            transaction_id=result['Authority']
        )
        
        keyboard = [[
            InlineKeyboardButton(
                "🔗 رفتن به درگاه پرداخت",
                url=f"https://zarinpal.com/pg/StartPay/{result['Authority']}"
            )
        ]]
        
        await update.callback_query.edit_message_text(
            "لطفاً با کلیک روی دکمه زیر به درگاه پرداخت منتقل شوید.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        await update.callback_query.edit_message_text(
            "❌ خطا در اتصال به درگاه پرداخت. لطفاً دوباره تلاش کنید.",
            reply_markup=payment_menu(appointment_id, amount)
        )

async def show_points(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = User.objects.get(telegram_id=str(update.effective_user.id))
    possible_discount = PointSystem.calculate_discount(user.points)
    
    text = f"""
👤 امتیازات شما:
🎁 تعداد امتیاز: {user.points}
💰 معادل {possible_discount:,} تومان تخفیف
💳 موجودی کیف پول: {user.wallet_balance:,} تومان
"""
    await update.callback_query.edit_message_text(
        text,
        reply_markup=profile_menu()
    )


















def main():
    application = ApplicationBuilder().token(settings.TELEGRAM_BOT_TOKEN).build()
    
    # اضافه کردن هندلرها
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # هندلرهای callback
    application.add_handler(CallbackQueryHandler(handle_callback))
    application.add_handler(CallbackQueryHandler(show_salons, pattern='^salons$'))
    application.add_handler(CallbackQueryHandler(show_profile, pattern='^profile$'))
    application.add_handler(CallbackQueryHandler(show_appointments, pattern='^appointments$'))
    application.add_handler(CallbackQueryHandler(cancel_appointment, pattern='^cancel_appointment$'))
    application.add_handler(CallbackQueryHandler(
        lambda u, c: show_salon_details(u, c, int(u.callback_query.data.split('_')[1])),
        pattern='^salon_\d+$'
    ))
    application.add_handler(CallbackQueryHandler(
        lambda u, c: handle_service_selection(u, c, int(u.callback_query.data.split('_')[1])),
        pattern='^service_\d+$'
    ))
    application.add_handler(CallbackQueryHandler(
        lambda u, c: show_gallery(u, c, int(u.callback_query.data.split('_')[1])),
        pattern='^gallery_\d+$'
    ))
    application.add_handler(CallbackQueryHandler(
        lambda u, c: process_payment(u, c, int(u.callback_query.data.split('_')[1])),
        pattern='^pay_\d+$'
    ))
    
    # شروع بات
    application.run_polling()

if __name__ == '__main__':
    main()
