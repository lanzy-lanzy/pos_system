from django.db import models
from django.contrib.auth.models import User
import uuid
from django.db.models import Sum, Count

class Product(models.Model):
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock_quantity = models.IntegerField()
    barcode = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return f"{self.name} - ${self.price}"

class Transaction(models.Model):
    transaction_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    date_time = models.DateTimeField(auto_now_add=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    completed = models.BooleanField(default=False)
    status = models.CharField(max_length=20, default='pending')

    def __str__(self):
        return f"Transaction {self.transaction_id} - ${self.total_amount} on {self.date_time.strftime('%Y-%m-%d %H:%M')}"

    def mark_as_complete(self):
        self.status = 'completed'
        self.save()

class TransactionItem(models.Model):
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.product.name} x{self.quantity} in Transaction {self.transaction.transaction_id}"


