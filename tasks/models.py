from django.db import models
from django.utils import timezone
from riders.models import Rider
from decimal import Decimal


def calculate_earnings(num_tasks, time_minutes, distance_km):
    """
    Base: 1 task, 10 min, 2 KM = ₹24.50
    Extra: ₹0.5/min, ₹5/km, ₹12.5/task
    """
    base = Decimal('24.50')
    extra_tasks = max(0, num_tasks - 1)
    extra_time = max(0, time_minutes - 10)
    extra_dist = max(0, distance_km - 2)
    total = (
        base
        + (Decimal(extra_tasks) * Decimal('12.5'))
        + (Decimal(extra_time) * Decimal('0.5'))
        + (Decimal(extra_dist) * Decimal('5'))
    )
    return round(total, 2)


class Task(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    TASK_TYPES = [
        ('delivery', 'Delivery'),
        ('pickup', 'Pickup'),
        ('pickup_delivery', 'Pickup & Delivery'),
        ('other', 'Other'),
    ]
    CANCELLED_BY = [
        ('rider', 'Rider'),
        ('customer', 'Customer'),
        ('company', 'Company'),
    ]
    task_id = models.CharField(max_length=20, unique=True, blank=True)
    rider = models.ForeignKey(Rider, on_delete=models.SET_NULL, null=True, related_name='tasks')
    task_date = models.DateField(default=timezone.now)
    task_type = models.CharField(max_length=30, choices=TASK_TYPES, default='delivery')
    num_tasks = models.PositiveIntegerField(default=1)
    time_taken = models.PositiveIntegerField(default=10)
    distance_km = models.DecimalField(max_digits=6, decimal_places=2, default=2.0)
    customer_name = models.CharField(max_length=100, blank=True)
    customer_number = models.CharField(max_length=15, blank=True)
    pickup_address = models.TextField(blank=True)
    drop_address = models.TextField(blank=True)
    remarks = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    earnings = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    cancelled_by = models.CharField(max_length=20, choices=CANCELLED_BY, blank=True)
    cancellation_reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.task_id:
            last = Task.objects.order_by('-id').first()
            num = (last.id + 1) if last else 1
            self.task_id = f'B24-{num:04d}'
        if self.status == 'completed':
            self.earnings = calculate_earnings(
                self.num_tasks, self.time_taken, float(self.distance_km))
        super().save(*args, **kwargs)
        if self.status == 'completed' and self.rider and self.earnings > 0:
            from riders.models import WalletTransaction
            if not WalletTransaction.objects.filter(
                    rider=self.rider,
                    description=f'Task {self.task_id}').exists():
                WalletTransaction.objects.create(
                    rider=self.rider, txn_type='credit',
                    amount=self.earnings,
                    description=f'Task {self.task_id}')
                self.rider.wallet_balance += self.earnings
                self.rider.save(update_fields=['wallet_balance'])

    def __str__(self):
        return f"{self.task_id}"

    class Meta:
        ordering = ['-task_date', '-created_at']