from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from salon.models import User, Salon, Service, Appointment, Payment
from .keyboards import Keyboards
import jdatetime
from datetime import datetime, timedelta

class BeautySalonBot:
    def __init__(self, token):
        self.application = ApplicationBuilder().token(token).build()
        self.setup_handlers()
        self.keyboards = Keyboards()

    def setup_handlers(self):
        # اضافه کردن هندلرهای اصلی
        self.application.add_handler(CommandHandler('start', self.start))
        self.application.add_handler(CommandHandler('help', self.help_command))
        self.application.add_handler(CallbackQueryHandler(self.handle_callback))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        telegram_id = str(user.id)
        
        try:
            db_user = User.objects.get(telegram_id=telegram_id)
            await update.message.reply_text(
                f"خوش آمدید {db_user.get_full_name()}!",
                reply_markup=self.keyboards.main_menu()
            )
        except User.DoesNotExist:
            keyboard = [
                [InlineKeyboardButton("👤 ثبت‌نام مشتری", callback_data='register_customer')],
                [InlineKeyboardButton("💇‍♀️ ثبت‌نام سالن", callback_data='register_salon')]
            ]
            await update.message.reply_text(
                "به سیستم نوبت‌دهی سالن زیبایی خوش آمدید!\n"
                "لطفاً نوع کاربری خود را انتخاب کنید:",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

    async def book_appointment(self, update: Update, context: ContextTypes.DEFAULT_TYPE, salon_id):
        salon = Salon.objects.get(id=salon_id)
        services = Service.objects.filter(salon=salon)
        
        keyboard = []
        for service in services:
            keyboard.append([
                InlineKeyboardButton(
                    f"{service.name} - {service.price:,} تومان",
                    callback_data=f'select_service_{service.id}'
                )
            ])
        keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data=f'salon_{salon_id}')])
        
        await update.callback_query.edit_message_text(
            f"لطفاً خدمت مورد نظر در {salon.name} را انتخاب کنید:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    async def select_date(self, update: Update, context: ContextTypes.DEFAULT_TYPE, service_id):
        service = Service.objects.get(id=service_id)
        today = jdatetime.datetime.now()
        
        keyboard = []
        for i in range(7):
            date = today + timedelta(days=i)
            persian_date = jdatetime.date.fromgregorian(date=date.date())
            keyboard.append([
                InlineKeyboardButton(
                    persian_date.strftime("%Y/%m/%d"),
                    callback_data=f'select_time_{service_id}_{date.strftime("%Y-%m-%d")}'
                )
            ])
            
        await update.callback_query.edit_message_text(
            "لطفاً تاریخ مورد نظر را انتخاب کنید:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    async def handle_payment(self, update: Update, context: ContextTypes.DEFAULT_TYPE, appointment_id):
        appointment = Appointment.objects.get(id=appointment_id)
        amount = appointment.service.price
        commission = 25000

        # اینجا باید به درگاه پرداخت متصل شوید
        # فعلاً به صورت نمایشی پرداخت را تایید می‌کنیم
        
        Payment.objects.create(
            appointment=appointment,
            amount=amount,
            commission=commission,
            transaction_id=f"DEMO_{appointment_id}"
        )
        
        appointment.status = 'confirmed'
        appointment.save()

        await update.callback_query.edit_message_text(
            f"✅ رزرو شما با موفقیت ثبت شد!\n\n"
            f"🏠 سالن: {appointment.salon.name}\n"
            f"💇‍♀️ خدمت: {appointment.service.name}\n"
            f"📅 تاریخ: {appointment.date}\n"
            f"⏰ ساعت: {appointment.time}\n"
            f"💰 مبلغ پرداختی: {amount:,} تومان",
            reply_markup=self.keyboards.main_menu()
        )

    async def show_my_appointments(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = User.objects.get(telegram_id=str(update.effective_user.id))
        appointments = Appointment.objects.filter(customer=user).order_by('-date', '-time')

        if not appointments:
            await update.callback_query.edit_message_text(
                "شما هیچ نوبت فعالی ندارید!",
                reply_markup=self.keyboards.main_menu()
            )
            return

        text = "📅 نوبت‌های شما:\n\n"
        keyboard = []
        
        for apt in appointments:
            text += f"🏠 {apt.salon.name}\n"
            text += f"💇‍♀️ {apt.service.name}\n"
            text += f"📅 {apt.date}\n"
            text += f"⏰ {apt.time}\n"
            text += f"وضعیت: {apt.get_status_display()}\n"
            text += "─────────────\n"
            
            if apt.status == 'confirmed':
                keyboard.append([
                    InlineKeyboardButton(
                        f"❌ لغو نوبت {apt.date}",
                        callback_data=f'cancel_apt_{apt.id}'
                    )
                ])

        keyboard.append([InlineKeyboardButton("🏠 منوی اصلی", callback_data='main_menu')])
        
        await update.callback_query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """
🌟 راهنمای استفاده از ربات:

/start - شروع کار با ربات
/help - نمایش این راهنما

🔹 امکانات:
• جستجو و مشاهده سالن‌ها
• رزرو نوبت
• مشاهده نوبت‌های فعال
• پرداخت آنلاین
• مدیریت پروفایل
    """
    await update.message.reply_text(help_text)