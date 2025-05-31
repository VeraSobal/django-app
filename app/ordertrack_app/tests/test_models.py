import pytest
from datetime import date
from decimal import Decimal

from ..models import (
    Client,
    Supplier,
    Brand,
    Product,
    PriceList,
    ProductDetail,
    Order,
    OrderItem,
    Confirmation,
    ConfirmationItem,
    ConfirmationDelivery,
)


@pytest.mark.django_db
def test_client_creation(clients, amount=2):
    client0 = clients.get("0")
    assert Client.objects.count() == amount
    assert client0.id == "C0"
    assert client0.name == "Test client 0"
    assert str(client0) == "Test client 0"


@pytest.mark.django_db
def test_brand_creation(brands, amount=2):
    brand0 = brands.get("0")
    assert Brand.objects.count() == amount
    assert brand0.id == "B0"
    assert brand0.name == "Test brand B0"
    assert str(brand0) == "B0 - Test brand B0"


@pytest.mark.django_db
def test_supplier_creation(supplier, brands):
    assert Supplier.objects.count() == 1
    assert supplier.id == "T00016"
    assert supplier.name == "Test supplier 0"
    assert str(supplier) == "T00016 - Test supplier 0"
    assert supplier.brand.all().count() == 2
    assert brands.get("0").suppliers.all().count() == 1


@pytest.mark.django_db
def test_product_creation(products, brands, amount=2):
    product0 = products.get("0")
    assert Product.objects.count() == amount
    assert product0.id == "TESTPRODUCT0_B0"
    assert product0.name == "Test product 0"
    assert product0.brand == brands.get("0")
    assert str(product0) == "TESTPRODUCT0_B0"


@pytest.mark.django_db
def test_pricelist_creation(pricelist, supplier):
    assert PriceList.objects.count() == 1
    assert pricelist.supplier == supplier
    assert pricelist.state == "Valid"
    assert pricelist.pricelist_date == date.today()
    assert pricelist.starts_from == date.today()


@pytest.mark.django_db
def test_productdetail_creation(productdetail, products, pricelist):
    assert ProductDetail.objects.count() == 1
    assert productdetail.pricelist == pricelist
    assert productdetail.price == 1.01
    assert productdetail.product == products.get("0")
    assert str(productdetail) == "1.01 - Valid"


@pytest.mark.django_db
def test_order_creation(orders, supplier):
    order0 = orders.get("0")
    assert Order.objects.count() == 3
    assert order0.id == "Order 0-C0-B0-S0-01-01-2025"
    assert order0.name == "Order 0-C0 -B0-S0-01-01-2025.xlsx"
    assert order0.supplier == supplier
    assert order0.order_date == "2025-01-01"
    assert str(order0) == "Order 0-C0 -B0-S0-01-01-2025.xlsx"


@pytest.mark.django_db
def test_orderitem_creation(orderitems, orders, clients, products, amount=5):
    orderitem0 = orderitems.get("0")
    assert OrderItem.objects.count() == amount
    assert orderitem0.order == orders.get("0")
    assert orderitem0.client == clients.get("0")
    assert orderitem0.product == products.get("0")
    assert orderitem0.order.items.count() == 2
    assert orderitem0.order.total_quantity == 30


@pytest.mark.django_db
def test_confirmation_creation(confirmations, orders, supplier):
    confirmation0 = confirmations.get("0")
    assert Confirmation.objects.count() == 2
    assert confirmation0.id == "T0"
    assert confirmation0.confirmation_code == "T0"
    assert confirmation0.name == "Confirmation 0 010125.xlsx"
    assert confirmation0.supplier == supplier
    assert confirmation0.confirmation_date == "2025-01-01"
    assert confirmation0.order.all().count() == 2
    assert list(confirmation0.order.all()) == [
        orders.get("0"), orders.get("1")]


@pytest.mark.django_db
def test_confirmationitem_creation(confirmationitems, confirmations, clients, products, amount=4):
    confirmationitem0 = confirmationitems.get("0")
    assert ConfirmationItem.objects.count() == amount
    assert confirmationitem0.confirmation == confirmations.get("0")
    assert confirmationitem0.client == clients.get("0")
    assert confirmationitem0.product == products.get("0")
    assert confirmationitem0.quantity == 10
    assert confirmationitem0.confirmation.items.count() == 2
    assert confirmationitem0.confirmation.total_amount == Decimal("203.00")


@pytest.mark.django_db
def test_confirmationdelivery_creation(confirmationdelivery, confirmations, products, amount=3):
    confirmationdelivery0 = confirmationdelivery.get("0")
    assert ConfirmationDelivery.objects.count() == amount
    assert confirmationdelivery0.confirmation == confirmations.get("0")
    assert confirmationdelivery0.delivery_date == "2026-01-01"
    assert confirmationdelivery0.quantity == 1
    assert confirmationdelivery0.product == products.get("0")
    assert confirmationdelivery0.confirmation.delivery_data.count() == 2
