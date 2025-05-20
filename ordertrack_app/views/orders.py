import logging
from pathlib import Path
import json
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.db import transaction
from django.contrib import messages
from django.shortcuts import redirect


from ..models import Order, OrderItem
from ..forms.orders import (
    OrderModelForm,
    EditOrderModelForm,
    ViewOrderModelForm,
    ViewOrderItemFormSet,
    EditOrderItemFormSet,
)
from ..forms.uploadfile import UploadOrderForm

template_path = Path("ordertrack_app") / "orders"

log = logging.getLogger(__name__)


class OrderListView(ListView):
    model = Order
    template_name = template_path/"orders.html"
    context_object_name = "orders"

    def get_queryset(self):
        return super().get_queryset().order_by("-order_date", "name")


class OrderDetailView(DetailView):
    model = Order
    model_item = OrderItem
    form_class = ViewOrderModelForm
    formset_class = ViewOrderItemFormSet
    template_name = template_path/"vieworder.html"
    context_object_name = 'vieworder'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        order = self.get_object()
        order_items = self.model_item.objects.select_related(
            'client',
            'product'
        ).filter(order=order)
        order_form = self.form_class(instance=order)
        order_items_formset = self.formset_class(queryset=order_items)
        context.update({
            'order_form': order_form,
            'formset': order_items_formset,
            'view_order': True,
        })
        return context


class OrderDeleteView(DeleteView):
    model = Order
    success_url = reverse_lazy('orders')

    def form_valid(self, form):
        if self.object.confirmations.exists():
            messages.error(
                self.request,
                f"Cannot delete order {self.object.pk}, as it has confirmations"
            )
            return redirect(self.request.META.get('HTTP_REFERER', '/'))
        messages.success(self.request, f'Order {self.object.pk} was deleted')
        return super().form_valid(form)


class OrderUpdateView(UpdateView):
    model = Order
    model_item = OrderItem
    form_class = EditOrderModelForm
    formset_class = EditOrderItemFormSet
    template_name = template_path/"vieworder.html"
    context_object_name = 'editorder'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        order = self.get_object()
        order_items = self.model_item.objects.select_related(
            'client',
            'product'
        ).filter(order=order)
        order_items_formset = self.formset_class(
            queryset=order_items, initial=[{'order': order}],)
        context.update({
            'order_form': self.get_form(),
            'formset': order_items_formset,
        })
        return context

    def get_success_url(self):
        return reverse_lazy('vieworder', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        context = self.get_context_data()
        if 'save' in self.request.POST:
            order_items_formset = self.formset_class(
                self.request.POST,
                queryset=self.model_item.objects.filter(
                    order=self.get_object()),
                initial=[{'order': self.get_object()}],)
            if form.is_valid() and order_items_formset.is_valid():
                form.save()
                order_items_formset.save()
                messages.success(self.request, 'Order is updated')
                return super().form_valid(form)
            context.update({
                'order_form': form,
                'formset': order_items_formset,
            })
            return self.render_to_response(context)


class OrderCreateView(CreateView):
    model = Order
    model_item = OrderItem
    form_class = OrderModelForm
    loadform_class = UploadOrderForm
    template_name = template_path/"addorder.html"
    context_object_name = 'addorder'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        loadform = self.loadform_class
        context.update({
            'form': self.get_form(),
            'loadform': loadform,
            'title': 'New Order',
            'add_order_disabled': True,
        })
        return context

    def get_success_url(self):
        return reverse_lazy('orders')

    def form_valid(self, form):
        context = self.get_context_data()
        loadform = self.loadform_class(self.request.POST, self.request.FILES)
        action = self.request.POST.get('action')
        if action == 'preview':
            if uploaded_file := self.request.FILES.get('file'):
                try:
                    supplier = form.cleaned_data["supplier"]
                    # brands = form.cleaned_data.get("brand", [])
                    order_data = loadform.load_excel_order(
                        uploaded_file, supplier=supplier)
                    self.request.session['order_data_json'] = loadform.data_json(
                        order_data)
                    context.update({
                        'orderdata': order_data,
                        'add_order_disabled': False,
                    })
                except Exception as e:
                    messages.error(
                        self.request, f'Cannot upload data from {uploaded_file}, {str(e)}')
                    context.update({
                        'add_order_disabled': True,
                    })
            else:
                messages.error(self.request, f'No file selected. Choose file')
                context.update({
                    'add_order_disabled': True,
                })
            return self.render_to_response(context)
        elif action == 'add':
            if form.is_valid() and loadform.is_valid():
                order_data_json = json.loads(
                    self.request.session.get('order_data_json'))
                try:
                    with transaction.atomic():
                        order = form.save()
                        self.model_item.save_order_items(
                            order_data_json=order_data_json, order=order)
                except Exception as e:
                    messages.error(self.request, f'Cannot save data, {e}')
                    context.update({
                        'add_order_disabled': True,
                    })
                    return self.render_to_response(context)
                del self.request.session['order_data_json']
                messages.success(self.request, 'Order is created')
                return super().form_valid(form)
