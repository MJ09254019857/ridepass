from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid


class Wallet(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='wallet')
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self): return f"{self.user.username} – ₱{self.balance}"


class Route(models.Model):
    TRANSPORT_CHOICES = [('bus','Bus'),('van','Van'),('multicab','Multicab'),('motorcycle','Motorcycle')]
    name = models.CharField(max_length=200)
    origin = models.CharField(max_length=100)
    destination = models.CharField(max_length=100)
    transport_type = models.CharField(max_length=50, choices=TRANSPORT_CHOICES)
    fare = models.DecimalField(max_digits=8, decimal_places=2)
    duration_minutes = models.IntegerField(default=30)
    is_active = models.BooleanField(default=True)
    def __str__(self): return f"{self.name} ({self.origin} → {self.destination})"


class Ticket(models.Model):
    STATUS_CHOICES = [('active','Active'),('used','Used'),('expired','Expired'),('cancelled','Cancelled')]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tickets')
    route = models.ForeignKey(Route, on_delete=models.CASCADE)
    ticket_code = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    purchased_at = models.DateTimeField(default=timezone.now)
    used_at = models.DateTimeField(null=True, blank=True)
    fare_paid = models.DecimalField(max_digits=8, decimal_places=2)
    def __str__(self): return f"Ticket {str(self.ticket_code)[:8]} – {self.route.name}"
    @property
    def short_code(self): return str(self.ticket_code).upper()[:8]


class Transaction(models.Model):
    TYPE_CHOICES = [('topup','Top Up'),('purchase','Ticket Purchase')]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.CharField(max_length=255)
    created_at = models.DateTimeField(default=timezone.now)
    ticket = models.ForeignKey(Ticket, on_delete=models.SET_NULL, null=True, blank=True)
    class Meta: ordering = ['-created_at']


class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=100)
    message = models.CharField(max_length=255)
    icon = models.CharField(max_length=10, default='🔔')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    class Meta: ordering = ['-created_at']


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField(max_length=20, blank=True)
    address = models.CharField(max_length=255, blank=True)
    is_banned = models.BooleanField(default=False)
    ban_reason = models.CharField(max_length=255, blank=True)
    def __str__(self): return f"Profile of {self.user.username}"
