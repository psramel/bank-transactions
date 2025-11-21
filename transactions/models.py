# django ORM
from django.db import models


class Transaction(models.Model):
    # texet field is unique
    reference = models.CharField(max_length=32, unique=True)
    timestamp = models.DateTimeField()
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3)
    description = models.TextField(blank=True)

    # when we have created the record (automatically set during INSERT)
    # Good for audit to find out when it was inserted
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # descending (-) timestamp so
        # Transaction.objects.all()
        # is same as 
        # SELECT * FROM transaction ORDER BY timestamp DESC;
        ordering = ["-timestamp"]

    def __str__(self) -> str:
        return f"{self.reference} {self.amount} {self.currency}"
