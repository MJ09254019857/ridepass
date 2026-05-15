from django.db import models
from django.contrib.auth.models import User


class TicketOrder(models.Model):
    """
    Tracks a PayMongo payment for a ticket purchase.
    Created when user clicks Pay, linked to a Ticket after payment confirmed.
    """
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("paid", "Paid"),
        ("failed", "Failed"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="ticket_orders")
    route_id = models.IntegerField()
    route_name = models.CharField(max_length=200)
    amount = models.PositiveIntegerField(help_text="Amount in centavos")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    paymongo_link_id = models.CharField(max_length=100, blank=True)
    checkout_url = models.URLField(blank=True)
    ticket = models.OneToOneField(
        "core.Ticket", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="order"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Order #{self.pk} – {self.route_name} ({self.status})"

    @property
    def amount_in_pesos(self):
        return self.amount / 100
