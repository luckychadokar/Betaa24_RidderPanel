from django.db import models
from riders.models import Rider
from django.utils import timezone


class Payout(models.Model):
    STATUS = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
    ]
    rider = models.ForeignKey(Rider, on_delete=models.CASCADE, related_name='payouts')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS, default='pending')
    payout_date = models.DateField(default=timezone.now)
    week_start = models.DateField(null=True, blank=True)
    week_end = models.DateField(null=True, blank=True)
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.rider.name} - ₹{self.amount} ({self.status})"

    class Meta:
        ordering = ['-created_at']