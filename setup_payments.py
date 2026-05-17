import os

os.makedirs('payments/migrations', exist_ok=True)
os.makedirs('payments/templates/payments', exist_ok=True)

files = {
'payments/__init__.py': '',
'payments/migrations/__init__.py': '',

'payments/models.py': '''from django.db import models
from django.contrib.auth.models import User

class TopUpOrder(models.Model):
    STATUS_CHOICES = [('pending','Pending'),('paid','Paid'),('failed','Failed')]
    METHOD_CHOICES = [('gcash','GCash'),('paymaya','Maya'),('card','Credit/Debit Card'),('grab_pay','GrabPay')]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="topup_orders")
    amount = models.PositiveIntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    payment_method = models.CharField(max_length=20, choices=METHOD_CHOICES, default="gcash")
    paymongo_link_id = models.CharField(max_length=100, blank=True)
    checkout_url = models.URLField(blank=True)
    reference_number = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        ordering = ["-created_at"]
    @property
    def amount_in_pesos(self):
        return self.amount / 100
    @property
    def amount_display(self):
        return f"PHP {self.amount_in_pesos:,.2f}"
''',

'payments/paymongo.py': '''import base64
import requests
from django.conf import settings

PAYMONGO_BASE_URL = "https://api.paymongo.com/v1"

def get_auth_header():
    secret = settings.PAYMONGO_SECRET_KEY
    encoded = base64.b64encode(f"{secret}:".encode()).decode()
    return {"Authorization": f"Basic {encoded}", "Content-Type": "application/json"}

def create_payment_link(amount_centavos, description, success_url, cancel_url):
    payload = {"data": {"attributes": {
        "amount": amount_centavos,
        "description": description,
        "currency": "PHP",
        "redirect": {"success": success_url, "failed": cancel_url}
    }}}
    response = requests.post(f"{PAYMONGO_BASE_URL}/links", json=payload, headers=get_auth_header(), timeout=30)
    response.raise_for_status()
    data = response.json()["data"]
    return {
        "link_id": data["id"],
        "checkout_url": data["attributes"]["checkout_url"],
        "reference_number": data["attributes"].get("reference_number", "")
    }

def get_payment_status(link_id):
    try:
        response = requests.get(f"{PAYMONGO_BASE_URL}/links/{link_id}", headers=get_auth_header(), timeout=30)
        data = response.json()["data"]
        payments = data["attributes"].get("payments", [])
        if payments:
            return payments[0]["attributes"].get("status", "pending")
        return data["attributes"].get("status", "unpaid")
    except:
        return "unknown"
''',

'payments/urls.py': '''from django.urls import path
from . import views

urlpatterns = [
    path("topup/", views.topup_view, name="topup"),
    path("topup/result/<int:order_id>/", views.topup_result, name="topup_result"),
]
''',

'payments/apps.py': '''from django.apps import AppConfig

class PaymentsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "payments"
''',

'payments/templates/payments/result.html': '''{% extends "core/base.html" %}
{% block title %}Payment Result{% endblock %}
{% block page_title %}Payment Result{% endblock %}
{% block content %}
<div style="max-width:480px;margin:0 auto;text-align:center;">
{% if order.status == "paid" %}
<div style="background:linear-gradient(135deg,#2a8f46,#1a6fb5);border-radius:20px;padding:2.5rem;color:white;margin-bottom:1.5rem;">
  <div style="font-size:4rem;">🎉</div>
  <div style="font-size:1.5rem;font-weight:800;">Payment Successful!</div>
  <div style="font-size:2rem;font-weight:800;margin-top:1rem;">{{ order.amount_display }}</div>
</div>
<div class="card" style="margin-bottom:1rem;"><div class="card-body">
  <table style="width:100%;">
    <tr><td style="color:var(--gray);font-size:13px;">New Balance</td><td style="font-weight:800;color:var(--green);text-align:right;">PHP {{ wallet.balance|floatformat:2 }}</td></tr>
    <tr><td style="color:var(--gray);font-size:13px;border-top:1px solid var(--border);">Method</td><td style="font-weight:700;text-align:right;border-top:1px solid var(--border);">{{ order.get_payment_method_display }}</td></tr>
  </table>
</div></div>
<div style="display:flex;gap:.75rem;">
  <a href="/routes/" class="btn btn-green" style="flex:1;justify-content:center;">Buy Ticket</a>
  <a href="/dashboard/" class="btn btn-outline" style="flex:1;justify-content:center;">Dashboard</a>
</div>
{% elif order.status == "failed" %}
<div style="background:linear-gradient(135deg,#dc2626,#991b1b);border-radius:20px;padding:2.5rem;color:white;margin-bottom:1.5rem;">
  <div style="font-size:4rem;">❌</div>
  <div style="font-size:1.5rem;font-weight:800;">Payment Failed</div>
</div>
<div style="display:flex;gap:.75rem;">
  <a href="/topup/" class="btn btn-green" style="flex:1;justify-content:center;">Try Again</a>
  <a href="/dashboard/" class="btn btn-outline" style="flex:1;justify-content:center;">Dashboard</a>
</div>
{% else %}
<div style="background:linear-gradient(135deg,#f59e0b,#d97706);border-radius:20px;padding:2.5rem;color:white;margin-bottom:1.5rem;">
  <div style="font-size:4rem;">⏳</div>
  <div style="font-size:1.5rem;font-weight:800;">Payment Pending</div>
</div>
<a href="/dashboard/" class="btn btn-green" style="display:block;text-align:center;">Go to Dashboard</a>
{% endif %}
</div>
{% endblock %}
''',
}

for path, content in files.items():
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f'Created {path}')

print('\nAll files created! Now run:')
print('  python manage.py makemigrations payments')
print('  python manage.py migrate')