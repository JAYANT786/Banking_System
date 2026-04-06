from django.utils import timezone
from datetime import timedelta
from django.db import models
from django.contrib.auth.models import User
import random

# Create your models here.

class Account(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    account_number = models.CharField(max_length=12, unique=True)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
     if not self.account_number:
        while True:
            acc = str(random.randint(100000000000, 999999999999))
            if not Account.objects.filter(account_number=acc).exists():
                self.account_number = acc
                break
        super().save(*args, **kwargs)
    def __str__(self):
        return self.user.username

from django.db import models
from .models import Account


class Transaction(models.Model):

    TRANSACTION_TYPE = (
        ('DEPOSIT', 'Deposit'),
        ('WITHDRAW', 'Withdraw'),
        ('TRANSFER_SENT', 'Transfer Sent'),
        ('TRANSFER_RECEIVED', 'Transfer Received'),
    )

    # 👤 Owner of this transaction (whose passbook this entry belongs to)
    account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name='transactions'
    )

    # 👤 Sender (who sent money)
    sender = models.ForeignKey(
        Account,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sent_transactions'
    )

    # 👤 Receiver (who received money)
    receiver = models.ForeignKey(
        Account,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='received_transactions'
    )

    # 💰 Amount
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    # 📌 Type of transaction
    transaction_type = models.CharField(
        max_length=20,
        choices=TRANSACTION_TYPE
    )

    # 🕒 Timestamp
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.account.user.username} - {self.transaction_type} - {self.amount}"

    class Meta:
        ordering = ['-timestamp']  # latest first

class OTP(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_expired(self):
        return timezone.now() > self.created_at + timedelta(minutes=5)

    def __str__(self):
        return self.user.username