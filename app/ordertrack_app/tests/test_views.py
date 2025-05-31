import pytest
from decimal import Decimal
from datetime import date

from django.urls import reverse

from ..models import (
    Order,
    OrderItem,
    Confirmation,
    ConfirmationItem,
)

import logging

log = logging.getLogger(__name__)


@pytest.mark.parametrize("value,expected", [
    ("Order 0-C0-B0-S0-01-01-2025", True),
    ("Order 10-C0-B0-S0-01-01-2025", False),
])
@pytest.mark.django_db
def test_order_delete(value, expected, client, orders):
    url = reverse('deleteorder', kwargs={'pk': value})
    response = client.get(url)
    assert Order.objects.filter(pk=value).exists() == expected


@pytest.mark.parametrize("value,expected", [
    ("T0", True),
    ("T10", False),
])
@pytest.mark.django_db
def test_confirmation_delete(value, expected, client, confirmations):
    url = reverse('deleteconfirmation', kwargs={'pk': value})
    response = client.get(url)
    assert Confirmation.objects.filter(pk=value).exists() == expected


@pytest.mark.django_db
def test_order_update(client, orders, orderitems):
    order_id = "Order 0-C0-B0-S0-01-01-2025"
    forms_amount = OrderItem.objects.filter(order=order_id).count()
    url = reverse('editorder', kwargs={'pk': order_id})
    response = client.get(url)
    data = {
        'save': [''],
        'csrfmiddlewaretoken': response.context['csrf_token'],
        'form-TOTAL_FORMS': forms_amount+1,
        'form-INITIAL_FORMS': forms_amount,
        'form-MIN_NUM_FORMS': '0',
        'form-MAX_NUM_FORMS': '1000',
        'name': orders.get("0").name,
        'comment': 'Test comment',
        'form-0-order': [order_id],
        'form-0-client': [orderitems.get("0").client.id],
        'form-0-product': [orderitems.get("0").product.id],
        'form-0-quantity': [orderitems.get("0").quantity],
        'form-0-id': [orderitems.get("0").id],
        'form-0-DELETE': 'on',
        'form-1-order': [order_id],
        'form-1-client': [orderitems.get("1").client.id],
        'form-1-product': [orderitems.get("1").product.id],
        'form-1-quantity': [30],
        'form-1-id': [orderitems.get("1").id],
        'form-2-order': [order_id],
        'form-2-client':  [''],
        'form-2-product':  [''],
        'form-2-quantity': [''],
        'form-2-id': [''],
    }
    response = client.post(url, data)
    updated_order = Order.objects.get(pk=order_id)
    updated_items = list(OrderItem.objects.filter(order=order_id).values())
    updated_items_expected = [{'id': 2,
                               'order_id': "Order 0-C0-B0-S0-01-01-2025",
                               'client_id': 'C1',
                               'product_id': 'TESTPRODUCT1_B0',
                               'quantity': 30,
                               }]
    assert updated_order == orders.get("0")
    assert updated_order.comment == "Test comment"
    assert len(updated_items) == 1
    assert updated_items == updated_items_expected


@pytest.mark.django_db
def test_confirmation_update(client, confirmations, confirmationitems):
    confirmation_id = "T0"
    forms_amount = ConfirmationItem.objects.filter(
        confirmation=confirmation_id).count()
    url = reverse('editconfirmation', kwargs={'pk': confirmation_id})
    response = client.get(url)
    data = {
        'save': [''],
        'csrfmiddlewaretoken': response.context['csrf_token'],
        'form-TOTAL_FORMS':  forms_amount+1,
        'form-INITIAL_FORMS': forms_amount,
        'form-MIN_NUM_FORMS': '0',
        'form-MAX_NUM_FORMS': '1000',
        'name': confirmations.get("0").name,
        'order': [order.id for order in confirmations.get("0").order.all()],
        'comment': 'Test comment',
        'form-0-client': [confirmationitems.get("0").client.id],
        'form-0-product': [confirmationitems.get("0").product.id],
        'form-0-quantity': [confirmationitems.get("0").quantity-6],
        'form-0-price': [confirmationitems.get("0").price],
        'form-0-id': [confirmationitems.get("0").id],
        'form-1-client': [confirmationitems.get("1").client.id],
        'form-1-product': [confirmationitems.get("1").product.id],
        'form-1-quantity': [confirmationitems.get("1").quantity],
        'form-1-price': [confirmationitems.get("1").price],
        'form-1-id': [confirmationitems.get("1").id],
        'form-2-client': [confirmationitems.get("1").client.id],
        'form-2-product': [confirmationitems.get("0").product.id],
        'form-2-quantity': [6],
        'form-2-price': [confirmationitems.get("0").price],
        'form-2-id': [''],
    }
    response = client.post(url, data)
    updated_confirmation = Confirmation.objects.get(pk=confirmation_id)
    updated_items = list(ConfirmationItem.objects.filter(
        confirmation=confirmation_id).values())
    updated_items_expected = [{'id': 1,
                               'confirmation_id': "T0",
                               'client_id': 'C0',
                               'comment': None,
                               'product_id': 'TESTPRODUCT0_B0',
                               'quantity': 4,
                               'price': Decimal('0.10'),
                               },
                              {'id': 5,
                               'confirmation_id': "T0",
                               'client_id': 'C1',
                               'comment': None,
                               'product_id': 'TESTPRODUCT0_B0',
                               'quantity': 6,
                               'price': Decimal('0.10'),
                               },
                              {'id': 2,
                               'confirmation_id': "T0",
                               'client_id': 'C1',
                               'comment': None,
                               'product_id': 'TESTPRODUCT1_B0',
                               'quantity': 20,
                               'price': Decimal('10.10')
                               },]
    assert updated_confirmation == confirmations.get("0")
    assert updated_confirmation.comment == "Test comment"
    assert len(updated_items) == 3
    assert updated_items == updated_items_expected


@pytest.mark.django_db
def test_order_create(client, order_excel, clients, supplier):
    url = reverse('addorder')
    response = client.get(url)
    file_name_splitted = order_excel.name.split(".")[0].split("-")
    order_date = "-".join(file_name_splitted[:3:-1])
    supplier_id = file_name_splitted[3]
    data = {
        'csrfmiddlewaretoken': response.context['csrf_token'],
        'name': [order_excel.name],
        'order_date': order_date,
        'supplier': [supplier_id],
        'comment': [''],
        'action': ['preview'],
        'file': order_excel
    }
    response = client.post(url, data=data,)
    response = client.get(url)
    data.update({
        'csrfmiddlewaretoken': response.context['csrf_token'],
        'file': [''],
        'action': ['add'],
    })
    response = client.post(url, data=data)
    order_id = Order.name_into_id(order_excel.name)
    new_order = Order.objects.filter(pk=order_id)
    new_items = list(OrderItem.objects.filter(order=order_id).values())
    expected_order = [{
        'id': "Order 3-C0-B0-T00016-01-01-2025",
        'name': "Order 3-C0-B0-T00016-01-01-2025.xlsx",
        'order_date': date(2025, 1, 1),
        'supplier_id': 'T00016',
        'comment': None
    }]
    expected_items = [
        {'id': 1,
         'order_id': 'Order 3-C0-B0-T00016-01-01-2025',
         'client_id': 'C0',
         'product_id': 'P0_B0',
         'quantity': 10},
        {'id': 2,
         'order_id': 'Order 3-C0-B0-T00016-01-01-2025',
         'client_id': 'C1',
         'product_id': 'P1_B0',
         'quantity': 20}]
    assert new_order.exists()
    assert list(new_order.values()) == expected_order
    assert new_items == expected_items


@pytest.mark.django_db
def test_confirmation_create(client, confirmation_excel, orders, supplier, orderitems):
    confirmation_id = 'T3'
    url = reverse('addconfirmation')
    response = client.get(url)
    dt = confirmation_excel.name.split(".")[0][-6:]
    confirmation_date = f"20{dt[4:6]}-{dt[2:4]}-{dt[:2]}"
    data = {
        'csrfmiddlewaretoken': response.context['csrf_token'],
        'name': [confirmation_excel.name],
        'confirmation_date': [confirmation_date],
        'initial-confirmation_date': [date.today()],
        'confirmation_code': ['Preview'],
        'supplier': [supplier.id],
        'order': [orders.get('0').id],
        'comment': [''],
        'action': ['preview'],
        'file': [confirmation_excel]
    }
    response = client.post(url, data=data,)
    response = client.get(url)
    data.update({
        'csrfmiddlewaretoken': response.context['csrf_token'],
        'confirmation_code': [confirmation_id],
        'initial-confirmation_date': [confirmation_date],
        'file': [''],
        'action': ['add'],
    })
    response = client.post(url, data=data)
    new_confirmation = Confirmation.objects.filter(pk=confirmation_id)
    new_items = list(ConfirmationItem.objects.filter(
        confirmation=confirmation_id).values())
    expected_confirmation = [{
        'id': "T3",
        'confirmation_code': 'T3',
        'name': "Confirmation B0 010125.xlsx",
        'confirmation_date': date(2025, 1, 1),
        'supplier_id': 'T00016',
        'comment': None
    }]
    expected_items = [
        {'id': 1,
         'confirmation_id': 'T3',
         'client_id': 'C0',
         'product_id': 'TESTPRODUCT0_B0',
         'quantity': 10,
         'price': Decimal('10.10'),
         'comment': None},
        {'id': 2,
         'confirmation_id': 'T3',
         'client_id': 'C1',
         'product_id': 'TESTPRODUCT1_B0',
         'quantity': 20,
         'price': Decimal('20.02'),
         'comment': None}
    ]
    assert new_confirmation.exists()
    assert list(new_confirmation.values()) == expected_confirmation
    assert new_items == expected_items


@pytest.mark.django_db
def test_order_view(client, orders, orderitems):
    order_id = "Order 0-C0-B0-S0-01-01-2025"
    url = reverse('editorder', kwargs={'pk': order_id})
    response = client.get(url)
    log.info(response.content)
    assert response.status_code == 200
    assert orders.get("0").id.encode() in response.content
    assert orders.get("0").name.encode() in response.content
    for item in OrderItem.objects.filter(order_id=order_id):
        assert item.product.id.encode() in response.content
        assert item.client.id.encode() in response.content
        assert str(item.quantity).encode() in response.content


@pytest.mark.django_db
def test_confirmation_view(client, confirmations, confirmationitems):
    confirmation_id = "T0"
    url = reverse('editconfirmation', kwargs={'pk': confirmation_id})
    response = client.get(url)
    log.info(response.content)
    assert response.status_code == 200
    assert confirmations.get("0").id.encode() in response.content
    assert confirmations.get("0").name.encode() in response.content
    for item in ConfirmationItem.objects.filter(confirmation_id=confirmation_id):
        assert item.product.id.encode() in response.content
        assert item.client.id.encode() in response.content
        assert str(item.quantity).encode() in response.content
        assert str(item.price).encode() in response.content
