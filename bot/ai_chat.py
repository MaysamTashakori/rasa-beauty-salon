import openai
from django.conf import settings

class BeautySalonAI:
    def __init__(self):
        openai.api_key = settings.OPENAI_API_KEY
        self.system_prompt = """شما یک دستیار هوشمند سالن زیبایی هستید.
        وظایف شما:
        - پاسخگویی به سوالات درباره خدمات آرایشی و زیبایی
        - راهنمایی برای رزرو نوبت
        - ارائه مشاوره درباره انواع خدمات مو، ناخن، آرایش و پوست
        - اطلاع‌رسانی درباره قیمت‌ها و زمان‌های کاری
        لحن پاسخ‌ها باید دوستانه و حرفه‌ای باشد."""
        
    def get_response(self, user_message):
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.7,
                max_tokens=200
            )
            return response.choices[0].message.content
            
        except Exception as e:
            # پاسخ‌های پیش‌فرض در صورت خطا
            if "قیمت" in user_message:
                return "برای مشاهده لیست کامل قیمت‌ها لطفاً از منوی اصلی گزینه «خدمات و قیمت‌ها» را انتخاب کنید."
            elif "نوبت" in user_message:
                return "برای رزرو نوبت می‌توانید از منوی اصلی گزینه «رزرو نوبت» را انتخاب کنید."
            elif "آدرس" in user_message:
                return "برای مشاهده آدرس و موقعیت سالن‌ها لطفاً از منوی اصلی گزینه «شعب ما» را انتخاب کنید."
            else:
                return "متأسفانه در حال حاضر قادر به پاسخگویی نیستم. لطفاً از منوی اصلی استفاده کنید."

    def handle_beauty_consultation(self, service_type, user_question):
        """مشاوره تخصصی برای خدمات مختلف"""
        prompt = f"""موضوع مشاوره: {service_type}
        سوال مشتری: {user_question}
        لطفاً یک پاسخ تخصصی و کاربردی ارائه دهید."""
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,
                max_tokens=300
            )
            return response.choices[0].message.content
        except:
            return "در حال حاضر امکان ارائه مشاوره تخصصی وجود ندارد. لطفاً با شماره سالن تماس بگیرید."
