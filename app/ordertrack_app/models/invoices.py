from django.db import models

from datetime import datetime

from .directories import Supplier
from .confirmations import ConfirmationItem


class Invoice(models.Model):
    name = models.CharField(max_length=250)
    invoice_date = models.DateField(default=datetime.today)
    supplier = models.ForeignKey(
        Supplier, on_delete=models.CASCADE, related_name="invoices")
    comment = models.CharField(
        max_length=450, null=True, blank=True, default=None)

    class Meta:
        unique_together = ("name", "invoice_date")


class InvoiceItem(models.Model):
    invoice = models.ForeignKey(
        Invoice, on_delete=models.CASCADE, related_name="items")
    confirmationitem = models.ForeignKey(
        ConfirmationItem, on_delete=models.CASCADE, related_name="invoiced", null=True)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)


class Cancellation(models.Model):
    cancellation_date = models.DateField(default=datetime.today)
    supplier = models.ForeignKey(
        Supplier, on_delete=models.CASCADE, related_name="cancellations")
    comment = models.CharField(
        max_length=450, null=True, blank=True, default=None)


class CancellationItem(models.Model):
    cancellation = models.ForeignKey(
        Cancellation, on_delete=models.CASCADE, related_name="items")
    cancellation_item = models.ForeignKey(
        ConfirmationItem, on_delete=models.CASCADE, related_name="cancelled")
    quantity = models.PositiveIntegerField()
