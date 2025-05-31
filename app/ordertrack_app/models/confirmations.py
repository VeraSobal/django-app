from django.db import models
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.db.models import Sum

from itertools import groupby
from datetime import datetime

from .orders import Supplier, Client, Product, OrderItem

import logging

log = logging.getLogger(__name__)


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

    class Meta:
        unique_together = ("confirmation", "client", "product")

    @property
    def total_amount(self):
        if self.price and self.quantity:
            return self.price * self.quantity
        return 0

    @staticmethod
    def get_left_quantity_per_client(confirmation, product):
        # получаем товары из отмеченных в подтверждении заказов
        orders_ids = confirmation.order.all().values_list(
            'id', flat=True)
        ordered_items = OrderItem.objects.filter(
            order__id__in=orders_ids).select_related('order')

        # Находим confirmation_item, где confirmation.order содержит любой из этих заказов
        confirmed_items = ConfirmationItem.objects.filter(
            confirmation__order__id__in=orders_ids
        )
        # Ищем количество товара в разрезе клиентов: заказанное количество минус подтвержденное
        ordered_quantity_per_client = ordered_items.filter(
            product=product).values('client_id').annotate(
            quantity=Sum('quantity')
        ).order_by('client_id')
        confirmed_quantity_per_client = confirmed_items.filter(
            product=product).values('client_id').annotate(
            quantity=Sum('quantity')
        ).order_by('client_id')
        ordered_quantity = ordered_quantity_per_client.aggregate(
            total=Sum("quantity", default=0))['total']
        confirmed_quantity = confirmed_quantity_per_client.aggregate(
            total=Sum("quantity", default=0))['total']
        # список вида: [{client_id:value, quantity: value}]
        left_quantity_per_client = []
        if ordered_quantity-confirmed_quantity > 0:
            for item in ordered_quantity_per_client:
                total = sum(item['quantity'] for item in confirmed_quantity_per_client
                            if item.get('client_id') == item["client_id"])
                left_quantity_per_client.append(
                    {"client_id": item["client_id"], "quantity": item["quantity"]-total})
        return left_quantity_per_client

    @classmethod
    def save_confirmation_items(cls, confirmation_data_json, confirmation):
        # группируем товары в подтверждении
        filtered_data = [
            item for item in confirmation_data_json if item['product'] != ""]

        sorted_data = sorted(filtered_data,
                             key=lambda x: x['product'])
        grouped = groupby(sorted_data, key=lambda x: x['product'])

        for product_id, group in grouped:
            items = list(group)
            total_quantity = sum([item['quantity'] for item in items])

            # Обновляем имя по продукту
            product_id = items[0].get("product")
            brand_id = product_id.split("_")[1]
            product_name = items[0].get("product_name")
            defaults = {
                'name': product_name,
                'brand_id': brand_id

            }
            product, created = Product.objects.update_or_create(
                id=product_id, defaults=defaults)
            price = items[0].get("price")
            # если такой продукт есть в заказе, т.е. известен клиент
            left_quantity_per_client = cls.get_left_quantity_per_client(confirmation,
                                                                        product)
            if left_quantity_per_client:
                for item in left_quantity_per_client:
                    client_id = item['client_id']
                    quantity = item['quantity']
                    cls.objects.create(
                        confirmation_id=confirmation.id,
                        client_id=client_id,
                        product_id=product.id,
                        quantity=quantity,
                        price=price)
            else:
                client, _ = Client.objects.get_or_create(id="Unknown")
                cls.objects.create(
                    confirmation_id=confirmation.id,
                    client_id=client.id,
                    product_id=product_id,
                    quantity=total_quantity,
                    price=price,)


class ConfirmationDelivery(models.Model):
    confirmation = models.ForeignKey(
        Confirmation, on_delete=models.CASCADE, related_name="delivery_data")
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="delivery_data")
    quantity = models.PositiveIntegerField()
    delivery_date = models.DateField(null=True, blank=True)

    class Meta:
        unique_together = ("confirmation", "product", "delivery_date")

    @classmethod
    def save_confirmation_delivery(cls, confirmation_data_json, confirmation):
        filtered_data = [
            item for item in confirmation_data_json if item['product'] != "" and
            item['delivery_date'] != "" and item['delivery_date'] != "None"]
        sorted_data = sorted(filtered_data,
                             key=lambda x: (x['product'], x['delivery_date']))
        grouped = groupby(
            sorted_data,
            key=lambda x: (x['product'], x['delivery_date']))
        for (product, delivery), group in grouped:
            items = list(group)
            product, delivery = (product, delivery)
            try:
                delivery_date = datetime.fromtimestamp(
                    delivery / 1000).strftime('%Y-%m-%d')
            except Exception as e:
                log.info(e)
            except all():
                delivery_date = None
            quantity = sum([item['quantity'] for item in items])
            cls.objects.create(
                confirmation_id=confirmation.id, product_id=product, delivery_date=delivery_date, quantity=quantity)
