import pytest
import pandas as pd
from datetime import datetime
from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile

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

import logging

log = logging.getLogger(__name__)


@pytest.fixture()
def clients(amount=2):
    result_dict = {}
    for i in range(amount):
        result_dict.update({str(i): Client.objects.create(
            id=f"C{i}", name=f"Test client {i}")})
    return result_dict


@pytest.fixture()
def brands(amount=2):
    result_dict = {}
    for i in range(amount):
        result_dict.update({str(i): Brand.objects.create(
            id=f"B{i}", name=f"Test brand B{i}")})
    return result_dict


@pytest.fixture()
def supplier(brands):
    created_supplier = Supplier.objects.create(
        id="T00016", name="Test supplier 0")
    created_supplier.brand.add(brands.get("0"), brands.get("1"))
    return created_supplier


@pytest.fixture
def products(brands, amount=2):
    result_dict = {}
    for i in range(amount):
        result_dict.update({str(i):
                            Product.objects.create(
                                second_id=f"TP{i}",
                                name=f"Test product {i}",
                                brand=brands.get("0"),
        )
        })
    return result_dict


@pytest.fixture
def pricelist(supplier):
    return PriceList.objects.create(supplier=supplier)


@pytest.fixture
def productdetail(products, pricelist):
    return ProductDetail.objects.create(
        price=1.01,
        product=products.get("0"),
        pricelist=pricelist,
    )


@pytest.fixture
def orders(supplier, amount=3):
    result_dict = {}
    for i in range(amount):
        result_dict.update({str(i):
                            Order.objects.create(
                                id=f"Order {i}-C0-B0-S0-01-01-2025",
                                name=f"Order {i}-C0 -B0-S0-01-01-2025.xlsx",
                                order_date="2025-01-01",
                                supplier=supplier,
        )
        })
    return result_dict


@pytest.fixture
def orderitems(orders, clients, products, amount=5):
    result_dict = {}
    for i in range(amount):
        result_dict.update({str(i):
                            OrderItem.objects.create(
                                order=orders.get(str(i//2)),
                                client=clients.get(str(i % 2)),
                                product=products.get(str(i % 2)),
                                quantity=(i+1)*10,
        )
        })
    return result_dict


@pytest.fixture
def confirmations(supplier, orders, amount=2):
    result_dict = {}
    for i in range(amount):
        name = f"Confirmation {i} 010125.xlsx"
        dt = name.split(".")[0][-6:]
        confirmation_date = f"20{dt[4:6]}-{dt[2:4]}-{dt[:2]}"
        created_confirmation = Confirmation.objects.create(
            name=name,
            confirmation_code=f"T{i}",
            confirmation_date=confirmation_date,
            supplier=supplier,
        )
        if i*2 < len(orders):
            created_confirmation.order.add(orders.get(str(i*2)))
        if i*2+1 < len(orders):
            created_confirmation.order.add(orders.get(str(i*2+1)))
        result_dict.update({str(i): created_confirmation
                            })
    return result_dict


@pytest.fixture
def confirmationitems(confirmations, clients, products, amount=4):
    result_dict = {}
    for i in range(amount):
        result_dict.update({str(i):
                            ConfirmationItem.objects.create(
                                confirmation=confirmations.get(str(i//2)),
                                client=clients.get(str(i % 2)),
                                product=products.get(str(i % 2)),
                                quantity=(i+1)*10,
                                price=i*10+0.1
        )
        })
    return result_dict


@pytest.fixture
def confirmationdelivery(confirmations, products, amount=3):
    result_dict = {}
    for i in range(amount):
        result_dict.update({str(i):
                            ConfirmationDelivery.objects.create(
                                confirmation=confirmations.get(str(i//2)),
                                product=products.get(str(i % 2)),
                                quantity=i+1,
                                delivery_date="2026-01-01",
        )
        })
    return result_dict


@pytest.fixture
def brandB0():
    return Brand.objects.create(id="B0", name="B0")


@pytest.fixture
def create_test_excel():
    def _create_test_excel(data, filename):
        df = pd.DataFrame(data)
        excel_content = BytesIO()
        df.to_excel(excel_content, index=False)
        excel_content.seek(0)
        yield SimpleUploadedFile(
            filename,
            excel_content.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    return _create_test_excel


@pytest.fixture
def order_excel(create_test_excel):
    data = {
        'product': ['P0', 'P1'],
        'quantity': [10, 20],
        'note': ['C0', 'C1']
    }
    excel_file = next(create_test_excel(
        data, filename="Order 3-C0-B0-T00016-01-01-2025.xlsx"))
    return excel_file


@pytest.fixture
def confirmation_excel(create_test_excel):
    data = {
        'Unnamed: 0': ['', '', 'Pos', '1', '2', ''],
        'Unnamed: 1': ['', '', 'Teilenummer', 'TESTPRODUCT0', 'TESTPRODUCT1', ''],
        'Unnamed: 2': ['', '', 'Menge', 10, 20, 'Total'],
        'Unnamed: 3': ['Ihre Bestellnummer:', '', 'Preise', 10.1, 20.02, 300.2],
        'Unnamed: 4': ['T3', '', 'Liefertermin', datetime.strptime('01.01.2026', '%d.%m.%Y'), '', ''],
        'Unnamed: 5': ['', '', 'Betrag', 101, 400.4, '']
    }
    excel_file = next(create_test_excel(
        data, filename="Confirmation B0 010125.xlsx"))
    return excel_file
