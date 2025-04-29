import logging
from pathlib import Path
from django.shortcuts import render, get_list_or_404


from ..models import Order, OrderItem

template_path = Path("ordertrack_app") / "orders"
log = logging.getLogger(__name__)


def orders(request):
    orders_list = Order.objects.all()
    context = {
        "orders": orders_list,
    }
    return render(request, template_path/"orders.html", context=context)


def orderitems(request, order_id):
    order_items = get_list_or_404(OrderItem, order_id=order_id)
    context = {
        "orderitems": order_items
    }
    return render(request, template_path/"orderitems.html", context=context)
