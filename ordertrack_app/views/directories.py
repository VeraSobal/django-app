from django.shortcuts import render
from django.db.models import Prefetch, Window, F
from django.db.models.functions import RowNumber
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
    products_list = Product.objects.prefetch_related(
        Prefetch("details",
                 queryset=ProductDetail.objects.annotate(
                     row_num=Window(
                         expression=RowNumber(),
                         partition_by=[F("product_id"), F(
                             "pricelist__supplier_id")],
                         order_by=[F("pricelist__starts_from").desc()]
                     )).filter(row_num=1),
                 to_attr='prefetched_details')
    ).order_by("brand", "id")
    context = {
        "products": products_list,
    }
    return render(request, template_path/"products.html", context=context)
