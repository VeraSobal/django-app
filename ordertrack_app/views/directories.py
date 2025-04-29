from django.shortcuts import render
from django.db.models import Prefetch
from pathlib import Path

from ..models import Client, Supplier, Brand, Product, ProductDetail

template_path = Path("ordertrack_app") / "directories"


def clients(request):
    clients_list = Client.objects.all()
    context = {
        "clients": clients_list,
    }
    return render(request, template_path/"clients.html", context=context)


def brands(request):
    brands_list = Brand.objects.all()
    context = {
        "brands": brands_list,
    }
    return render(request, template_path/"brands.html", context=context)


def suppliers(request):
    suppliers_list = Supplier.objects.all()
    context = {
        "suppliers": suppliers_list,
    }
    return render(request, template_path/"suppliers.html", context=context)


def products(request):
    # Как выбрать price по product_id-supplier_id с самой поздней датой pricelist__starts_from
    # Почему этот запрос выдает корректные результаты в sql,
    # но в products.html выводит все цены , а не те, у которых самая поздняя дата?
    # products_list = Product.objects.annotate(
    #     row_num=Window(
    #         expression=RowNumber(),
    #         partition_by=[F("id"), F("details__pricelist__supplier_id")],
    #         order_by=[F("details__pricelist__starts_from").desc()]
    #     )
    # ).filter(row_num=1).order_by("brand", "id")
    # WITH CTE AS
    # (SELECT ordertrack_app_product.id,
    # ordertrack_app_product.brand_id,
    # ordertrack_app_productdetail.price AS details__price,
    # ordertrack_app_pricelist.starts_from AS details__pricelist__starts_from,
    # ordertrack_app_supplier.name AS details__pricelist__supplier,
    # ROW_NUMBER() OVER (
    # PARTITION BY ordertrack_app_product.id, ordertrack_app_supplier.name
    # ORDER BY ordertrack_app_pricelist.starts_from DESC) as row_num
    # FROM ordertrack_app_product
    # LEFT JOIN ordertrack_app_productdetail ON ordertrack_app_product.id = ordertrack_app_productdetail.product_id
    # LEFT JOIN ordertrack_app_pricelist ON ordertrack_app_productdetail.pricelist_id = ordertrack_app_pricelist.id
    # LEFT JOIN ordertrack_app_supplier ON ordertrack_app_pricelist.supplier_id = ordertrack_app_supplier.id)
    # SELECT * FROM CTE
    # WHERE
    # row_num= 1;

    products_list = Product.objects.filter(state__iexact="valid").prefetch_related(
        Prefetch("details",
                 queryset=ProductDetail.objects.select_related('pricelist').filter(pricelist__state__iexact="valid"))
    )

    context = {
        "products": products_list,
    }
    return render(request, template_path/"products.html", context=context)
