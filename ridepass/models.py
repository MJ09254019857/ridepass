from django.db import models
 
 
class Order(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("paid", "Paid"),
        ("failed", "Failed"),
    ]
 
    description = models.CharField(max_length=255)
    amount = models.PositiveIntegerField(help_text="Amount in centavos")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    paymongo_link_id = models.CharField(max_length=100, blank=True)
    checkout_url = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
