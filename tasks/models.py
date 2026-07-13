from django.db import models
from django.utils import timezone
from riders.models import Rider
from decimal import Decimal


def calculate_earnings(num_tasks, time_minutes, distance_km):
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


class CustomerWallet(models.Model):
    customer_name = models.CharField(max_length=100)
    customer_mobile = models.CharField(max_length=15, unique=True)
    available_tasks = models.IntegerField(default=0)      # Int (minus ho sakta hai)
    available_minutes = models.IntegerField(default=0)    # Int (minus ho sakta hai)
    available_km = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    total_recharged = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_spent = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    pending_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.customer_name} ({self.customer_mobile})"

    @property
    def is_in_deficit(self):
        return self.available_tasks < 0 or self.available_minutes < 0 or self.available_km < 0

    class Meta:
        ordering = ['-created_at']


class CustomerRecharge(models.Model):
    RECHARGE_TYPES = [
        ('manual', 'Manual Recharge'),
        ('base', 'Base Plan Rs.49'),
        ('topup_task', 'Task Top-up'),
        ('topup_time', 'Time Top-up'),
        ('topup_km', 'KM Top-up'),
        ('custom', 'Custom Recharge'),
    ]
    wallet = models.ForeignKey(
        CustomerWallet, on_delete=models.CASCADE, related_name='recharges')
    recharge_type = models.CharField(max_length=20, choices=RECHARGE_TYPES, default='manual')
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tasks_added = models.IntegerField(default=0)
    minutes_added = models.IntegerField(default=0)
    km_added = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new:
            self.wallet.available_tasks += self.tasks_added
            self.wallet.available_minutes += self.minutes_added
            self.wallet.available_km += self.km_added
            self.wallet.total_recharged += self.amount_paid
            self.wallet.save()

    def __str__(self):
        return f"{self.wallet.customer_name} - {self.get_recharge_type_display()}"

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new:
            # Only add to wallet on first save
            self.wallet.available_tasks += self.tasks_added
            self.wallet.available_minutes += self.minutes_added
            self.wallet.available_km += self.km_added
            self.wallet.total_recharged += self.amount_paid
            self.wallet.save()

    def __str__(self):
        return f"{self.wallet.customer_name} - {self.get_recharge_type_display()}"

    class Meta:
        ordering = ['-created_at']
    def __str__(self):
        return f"{self.wallet.customer_name} - {self.get_recharge_type_display()}"

    class Meta:
        ordering = ['-created_at']


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
    rider = models.ForeignKey(
        Rider, on_delete=models.SET_NULL, null=True, related_name='tasks')
    customer_wallet = models.ForeignKey(
        CustomerWallet, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='tasks')
    task_date = models.DateField(default=timezone.now)
    task_type = models.CharField(max_length=30, choices=TASK_TYPES, default='delivery')
    num_tasks = models.PositiveIntegerField(default=1)
    time_taken = models.PositiveIntegerField(default=10)
    distance_km = models.DecimalField(max_digits=6, decimal_places=2, default=2.0)
    customer_name = models.CharField(max_length=100, blank=True)
    customer_number = models.CharField(max_length=15, blank=True)
    customer_beta_id = models.CharField(max_length=30, blank=True)
    task_work_id = models.CharField(max_length=30, blank=True)
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
        if self.status == 'completed' and self.customer_wallet:
            w = self.customer_wallet
            w.available_tasks -= self.num_tasks
            w.available_minutes -= self.time_taken
            w.available_km -= self.distance_km
            w.total_spent += self.earnings
            # Pending amount calculate karo agar minus mein gaya
            pending = 0
            if w.available_tasks < 0:
                pending += abs(w.available_tasks) * 25
            if w.available_minutes < 0:
                pending += abs(w.available_minutes) * 1
            if w.available_km < 0:
                pending += abs(float(w.available_km)) * 10
            w.pending_amount = pending
            w.save()
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