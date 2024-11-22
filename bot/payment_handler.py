import requests
from django.conf import settings
from salon.models import Payment

class PaymentHandler:
    def __init__(self, merchant_id=settings.ZARINPAL_MERCHANT_ID):
        self.merchant_id = merchant_id
        self.sandbox = settings.PAYMENT_SANDBOX
        
    def request_payment(self, amount, callback_url, description):
        if self.sandbox:
            url = 'https://sandbox.zarinpal.com/pg/rest/WebGate/PaymentRequest.json'
        else:
            url = 'https://api.zarinpal.com/pg/v4/payment/request.json'
            
        data = {
            'merchant_id': self.merchant_id,
            'amount': amount,
            'callback_url': callback_url,
            'description': description
        }
        
        response = requests.post(url, json=data)
        return response.json()
    
    def verify_payment(self, authority, amount):
        if self.sandbox:
            url = 'https://sandbox.zarinpal.com/pg/rest/WebGate/PaymentVerification.json'
        else:
            url = 'https://api.zarinpal.com/pg/v4/payment/verify.json'
            
        data = {
            'merchant_id': self.merchant_id,
            'authority': authority,
            'amount': amount
        }
        
        response = requests.post(url, json=data)
        return response.json()
