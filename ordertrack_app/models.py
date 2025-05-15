from django.db import models
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.core.exceptions import ObjectDoesNotExist

from datetime import datetime


class Client(models.Model):
    id = models.CharField(max_length=10, primary_key=True, null=False)
    name = models.CharField(max_length=100)
    comment = models.CharField(
        max_length=450, null=True, blank=True, default=None)

    def __str__(self):
        return self.name


class Supplier (models.Model):
    id = models.CharField(max_length=10, primary_key=True, null=False)
    name = models.CharField(max_length=100)
    comment = models.CharField(
        max_length=450, null=True, blank=True, default=None)
    brand = models.ManyToManyField("Brand", related_name="suppliers")

    def __str__(self):
        return f'{self.id} - {self.name}'


class Brand(models.Model):
    id = models.CharField(max_length=10, primary_key=True, null=False)
    name = models.CharField(max_length=100)
    comment = models.CharField(
        max_length=450, null=True, blank=True, default=None)

    def __str__(self):
        return f'{self.id} - {self.name}'


class Product(models.Model):
    class State(models.TextChoices):
        VALID = "Valid"
        INVALID = "Invalid"
    id = models.CharField(max_length=200, primary_key=True, null=False)
    second_id = models.CharField(max_length=200, unique=True, null=True)
    name = models.CharField(null=True, blank=True)  # с точками и -
    description = models.CharField(null=True, blank=True)
    brand = models.ForeignKey(
        Brand, on_delete=models.CASCADE, related_name="products")
    state = models.CharField(
        max_length=50, choices=State.choices, default=State.VALID)
    comment = models.CharField(
        max_length=450, null=True, blank=True, default=None)

    def __str__(self):
        return self.id


@receiver(pre_save, sender=Product)
def set_id(sender, instance, **kwargs):
    if not instance.id:
        code = instance.name.replace(".", "").replace("-", "").upper()
        if code.isascii():
            instance.id = code+"_"+instance.brand.id


class PriceList(models.Model):
    class State(models.TextChoices):
        VALID = "Valid"
        INVALID = "Invalid"
    supplier = models.ForeignKey(
        Supplier, on_delete=models.CASCADE, related_name="pricelists")
    pricelist_date = models.DateField(default=datetime.today)
    state = models.CharField(
        max_length=50, choices=State.choices, default=State.VALID)
    starts_from = models.DateField(default=datetime.today)
    comment = models.CharField(
        max_length=450, null=True, blank=True, default=None)

    def __str__(self):
        return f"{self.supplier.name}"


class ProductDetail(models.Model):
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="details")
    pricelist = models.ForeignKey(
        PriceList, on_delete=models.CASCADE, related_name="products")

    def __str__(self):
        return f"{self.price} - {self.pricelist.state}"


class Order(models.Model):
    id = models.CharField(primary_key=True, null=False, max_length=450)
    name = models.CharField(null=False, blank=False, max_length=450)
    order_date = models.DateField()
    supplier = models.ForeignKey(
        Supplier, on_delete=models.CASCADE, related_name="orders")
    comment = models.CharField(
        max_length=450, null=True, blank=True, default=None)

    @property
    def total_quantity(self):
        return sum(item.quantity for item in self.items.all())

    class Meta:
        ordering = ['-order_date']

    @staticmethod
    def name_into_id(filename):
        filename_without_extension = ".".join(filename.split(".")[:-1])
        name_ends = "-".join(filename_without_extension.upper().replace(
            " ", "").replace(".", "").split("-")[1:])
        name_starts = filename_without_extension.split("-")[0].strip()
        return "-".join([name_starts, name_ends])

    def __str__(self):
        return self.name


@receiver(pre_save, sender=Order)
def set_id(sender, instance, **kwargs):
    if not instance.id:
        instance.id = instance.name_into_id(instance.name)


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="items")
    client = models.ForeignKey(
        Client, on_delete=models.CASCADE, related_name="ordered_products")
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="ordered")
    quantity = models.PositiveIntegerField()

    class Meta:
        unique_together = ("order", "client", "product")


class Confirmation(models.Model):
    id = models.CharField(primary_key=True, null=False, max_length=100)
    name = models.CharField(max_length=250)
    confirmation_code = models.CharField(max_length=10, unique=True)
    confirmation_date = models.DateField(default=datetime.today)
    supplier = models.ForeignKey(
        Supplier, on_delete=models.CASCADE, related_name="confirmations")
    order = models.ManyToManyField(
        "Order", related_name="confirmations")
    comment = models.CharField(
        max_length=450, null=True, blank=True, default=None)

    @property
    def total_amount(self):
        return sum(item.total_amount for item in self.items.all())

    class Meta:
        ordering = ['-confirmation_date']


@receiver(pre_save, sender=Confirmation)
def set_id(sender, instance, **kwargs):
    if not instance.id:
        instance.id = instance.confirmation_code


class ConfirmationItem(models.Model):
    confirmation = models.ForeignKey(
        Confirmation, on_delete=models.CASCADE, related_name="items")
    client = models.ForeignKey(
        Client, on_delete=models.CASCADE, related_name="confirmed_products")
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="confirmed")
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    comment = models.CharField(
        max_length=450, null=True, blank=True, default=None)

    @property
    def total_amount(self):
        if self.price and self.quantity:
            return self.price * self.quantity
        return 0

    class Meta:
        unique_together = ("confirmation", "client", "product")


class ConfirmationDelivery(models.Model):
    confirmation = models.ForeignKey(
        Confirmation, on_delete=models.CASCADE, related_name="delivery_data")
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="delivery_data")
    quantity = models.PositiveIntegerField()
    delivery_date = models.DateField(null=True, blank=True)

    class Meta:
        unique_together = ("confirmation", "product", "delivery_date")


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
