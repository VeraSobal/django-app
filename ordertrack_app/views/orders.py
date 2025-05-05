import logging
from pathlib import Path
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.db import transaction

from ..models import Order, OrderItem
from ..forms.orders import (
    OrderModelForm,
    EditOrderModelForm,
    ViewOrderModelForm,
    ViewItemFormSet,
    EditItemFormSet)
from ..forms.uploadfile import UploadFileForm

template_path = Path("ordertrack_app") / "orders"

log = logging.getLogger(__name__)


def orders(request):
    orders_list = Order.objects.all().order_by("-order_date", "name")
    context = {
        "orders": orders_list,
    }
    return render(request, template_path/"orders.html", context=context)


def view_order(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    order_items = OrderItem.objects.filter(order_id=order_id)
    order_form = ViewOrderModelForm(instance=order)
    order_items_formset = ViewItemFormSet(queryset=order_items)
    context = {
        'order_form': order_form,
        'formset': order_items_formset
    }
    return render(request, template_path/"vieworder.html", context=context)


def edit_order(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    order_items = OrderItem.objects.filter(order_id=order_id)

    if request.method == 'POST':
        if 'save' in request.POST:
            order_form = EditOrderModelForm(request.POST, instance=order)
            order_items_formset = EditItemFormSet(
                request.POST, queryset=order_items)
            if order_form.is_valid() and order_items_formset.is_valid():
                order_form.save()
                order_items_formset.save()
                return redirect(reverse('vieworder', args=[order_form.instance.id]))

    order_form = EditOrderModelForm(instance=order)
    order_items_formset = EditItemFormSet(queryset=order_items)
    context = {
        'order_form': order_form,
        'formset': order_items_formset
    }
    return render(request, template_path/"vieworder.html", context=context)


def delete_order(request, order_id):
    if request.method == 'POST':
        order = Order.objects.get(id=order_id)
        order.delete()
    return redirect(reverse('orders'))


def new_order(request):
    if request.method == 'POST':
        form = OrderModelForm(request.POST)
        loadform = UploadFileForm(request.POST, request.FILES)
        context = {'form': form, 'loadform': loadform, 'title': 'New Order'}
        action = request.POST.get('action')
        if form.is_valid():
            if action == 'preview':
                if uploaded_file := request.FILES.get('file'):
                    try:
                        supplier = form.cleaned_data["supplier"]
                        # brands = form.cleaned_data.get("brand", [])
                        order_data = loadform.load_excel_order(
                            uploaded_file, supplier=supplier)
                        request.session['order_data_json'] = loadform.order_data_json(
                            order_data)
                        context['orderdata'] = order_data
                        context['add_order_disabled'] = False
                    except Exception as e:
                        context['orderdata'] = f'Cannot upload data from {uploaded_file}, {e}'
                        context['add_order_disabled'] = True
                else:
                    context['orderdata'] = f'No file selected. Choose file'
                    context['add_order_disabled'] = True
                return render(request, template_path/"neworder.html", context)
            elif action == 'add':
                if form.is_valid() and loadform.is_valid():
                    order_data_json = json.loads(
                        request.session.get('order_data_json'))
                    order = form.save()
                    loadform.save_order_items(
                        order_data_json=order_data_json, order=order)
                    del request.session['order_data_json']
                    return redirect(reverse('orders'))

    else:
        form = OrderModelForm()
        loadform = UploadFileForm()
        context = {'form': form, 'loadform': loadform,
                   'title': 'New Order', 'add_order_disabled': True}

    return render(request, template_path/"neworder.html", context)
