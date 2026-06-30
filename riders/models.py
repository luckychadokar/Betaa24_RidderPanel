from django.db import models
from django.utils import timezone


class Rider(models.Model):
    STATUS_CHOICES = [
        ('new', 'New'),
        ('training_pending', 'Training Pending'),
        ('documents_pending', 'Documents Pending'),
        ('ready', 'Ready for Activation'),
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ]
    beta_code = models.CharField(max_length=30, blank=True, unique=False, null=True)
    name = models.CharField(max_length=100)
    mobile = models.CharField(max_length=15, unique=True)
    email = models.EmailField(blank=True)
    state = models.CharField(max_length=100, default='Madhya Pradesh', blank=True)
    city = models.CharField(max_length=100, default='Bhopal')
    vehicle_type = models.CharField(max_length=50, default='Bike')
    joining_date = models.DateField(default=timezone.now)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='new')
    wallet_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    rating = models.DecimalField(max_digits=3, decimal_places=1, default=5.0)
    profile_photo = models.ImageField(upload_to='riders/photos/', blank=True, null=True)
    address = models.TextField(blank=True)
    emergency_contact = models.CharField(max_length=15, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def __str__(self):
        return f"{self.name} ({self.mobile})"

    @property
    def total_earnings(self):
        return self.wallet_transactions.filter(txn_type='credit').aggregate(
            total=models.Sum('amount'))['total'] or 0

    @property
    def total_paid(self):
        return self.payouts.filter(status='paid').aggregate(
            total=models.Sum('amount'))['total'] or 0

    @property
    def pending_amount(self):
        return self.total_earnings - self.total_paid

    @property
    def total_tasks(self):
        return self.tasks.filter(status='completed').count()

    class Meta:
        ordering = ['-created_at']


class RiderTraining(models.Model):
    TRAINING_STATUS = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('rejected', 'Rejected'),
    ]
    NOT_DONE_REASONS = [
        ('not_interested', 'Not Interested'),
        ('not_reachable', 'Phone Not Reachable'),
        ('docs_missing', 'Documents Missing'),
        ('failed_verification', 'Failed Verification'),
        ('other', 'Other'),
    ]
    rider = models.OneToOneField(Rider, on_delete=models.CASCADE, related_name='training')
    status = models.CharField(max_length=20, choices=TRAINING_STATUS, default='pending')
    reason = models.CharField(max_length=50, choices=NOT_DONE_REASONS, blank=True)
    reason_detail = models.TextField(blank=True)
    training_date = models.DateField(null=True, blank=True)

    # New fields from training sheet
    alternate_number = models.CharField(max_length=15, blank=True)
    location = models.CharField(max_length=150, blank=True)
    state = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    training_done_by = models.CharField(max_length=100, blank=True)
    final_remark = models.TextField(blank=True)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.rider.name} - {self.status}"


class RiderDocument(models.Model):
    DOC_STATUS = [
        ('pending', 'Pending'),
        ('uploaded', 'Uploaded'),
        ('rejected', 'Rejected'),
        ('approved', 'Approved'),
    ]
    rider = models.OneToOneField(Rider, on_delete=models.CASCADE, related_name='documents')

    # Aadhaar Card
    aadhaar_number = models.CharField(max_length=20, blank=True)
    aadhaar_front = models.ImageField(upload_to='docs/aadhaar/', blank=True, null=True)
    aadhaar_back = models.ImageField(upload_to='docs/aadhaar/', blank=True, null=True)
    aadhaar_status = models.CharField(max_length=20, choices=DOC_STATUS, default='pending')

    # Driving License
    dl_number = models.CharField(max_length=30, blank=True)
    dl_front = models.ImageField(upload_to='docs/dl/', blank=True, null=True)
    dl_back = models.ImageField(upload_to='docs/dl/', blank=True, null=True)
    dl_status = models.CharField(max_length=20, choices=DOC_STATUS, default='pending')

    # RC Card (Vehicle Registration)
    rc_number = models.CharField(max_length=30, blank=True)
    rc_front = models.ImageField(upload_to='docs/rc/', blank=True, null=True)
    rc_status = models.CharField(max_length=20, choices=DOC_STATUS, default='pending')

    # Vehicle Insurance
    insurance_number = models.CharField(max_length=40, blank=True)
    insurance_doc = models.ImageField(upload_to='docs/insurance/', blank=True, null=True)
    insurance_expiry = models.DateField(null=True, blank=True)
    insurance_status = models.CharField(max_length=20, choices=DOC_STATUS, default='pending')

    # Marksheet / Education Proof
    marksheet_doc = models.ImageField(upload_to='docs/marksheet/', blank=True, null=True)
    marksheet_status = models.CharField(max_length=20, choices=DOC_STATUS, default='pending')

    # Police Verification
    police_verification_doc = models.ImageField(upload_to='docs/police/', blank=True, null=True)
    police_verification_status = models.CharField(max_length=20, choices=DOC_STATUS, default='pending')

    # PAN Card
    pan_number = models.CharField(max_length=20, blank=True)
    pan_doc = models.ImageField(upload_to='docs/pan/', blank=True, null=True)
    pan_status = models.CharField(max_length=20, choices=DOC_STATUS, default='pending')

    overall_status = models.CharField(max_length=20, choices=DOC_STATUS, default='pending')
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Docs - {self.rider.name}"


class BankDetail(models.Model):
    ACCOUNT_TYPES = [
        ('savings', 'Savings'),
        ('current', 'Current'),
    ]
    VERIFY_STATUS = [
        ('pending', 'Pending'),
        ('verified', 'Verified'),
        ('mismatch', 'Mismatch'),
    ]
    rider = models.OneToOneField(Rider, on_delete=models.CASCADE, related_name='bank_detail')
    account_holder_name = models.CharField(max_length=150, blank=True)
    account_number = models.CharField(max_length=30, blank=True)
    account_number_confirm = models.CharField(max_length=30, blank=True)
    ifsc_code = models.CharField(max_length=15, blank=True)
    bank_name = models.CharField(max_length=150, blank=True)
    branch_name = models.CharField(max_length=150, blank=True)
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPES, default='savings')
    passbook_image = models.ImageField(upload_to='docs/passbook/', blank=True, null=True)
    verify_status = models.CharField(max_length=20, choices=VERIFY_STATUS, default='pending')
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Bank - {self.rider.name}"


class WalletTransaction(models.Model):
    TXN_TYPES = [('credit', 'Credit'), ('debit', 'Debit')]
    rider = models.ForeignKey(Rider, on_delete=models.CASCADE, related_name='wallet_transactions')
    txn_type = models.CharField(max_length=10, choices=TXN_TYPES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.rider.name} {self.txn_type} ₹{self.amount}"

    class Meta:
        ordering = ['-created_at']
class RiderTraining(models.Model):
    TRAINING_STATUS = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('rejected', 'Rejected'),
    ]
    NOT_DONE_REASONS = [
        ('not_interested', 'Not Interested'),
        ('not_reachable', 'Phone Not Reachable'),
        ('docs_missing', 'Documents Missing'),
        ('failed_verification', 'Failed Verification'),
        ('other', 'Other'),
    ]
    rider = models.OneToOneField(Rider, on_delete=models.CASCADE, related_name='training')
    status = models.CharField(max_length=20, choices=TRAINING_STATUS, default='pending')
    reason = models.CharField(max_length=50, choices=NOT_DONE_REASONS, blank=True)
    reason_detail = models.TextField(blank=True)
    training_date = models.DateField(null=True, blank=True)
    alternate_number = models.CharField(max_length=15, blank=True)
    location = models.CharField(max_length=150, blank=True)
    state = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    training_done_by = models.CharField(max_length=100, blank=True)
    final_remark = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Auto-promote rider to active when training is completed
        if self.status == 'completed' and self.rider.status != 'active':
            self.rider.status = 'active'
            self.rider.save(update_fields=['status'])

    def __str__(self):
        return f"{self.rider.name} - {self.status}"
