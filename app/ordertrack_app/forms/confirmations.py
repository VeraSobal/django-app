from django import forms
from django.core.exceptions import ValidationError
from django.forms import BaseModelFormSet
from django.db.models import Sum

from datetime import date
import pandas as pd
from io import BytesIO


from ..models import Confirmation, ConfirmationItem, Supplier, Product, Client

import logging

log = logging.getLogger(__name__)


class ConfirmationModelForm(forms.ModelForm):
    class Meta:
        model = Confirmation
        fields = ['name', 'confirmation_code',
                  'confirmation_date', 'supplier', 'order', 'comment']
        labels = {
            'name': 'Name',
            'confirmation_code': "Supplier's code",
            'confirmation_date': 'Date',
            'supplier': 'Supplier',
            'order': 'Order',
            'comment': 'Comment',
        }
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Input confirmation name'}),
            'confirmation_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Input confirmation code'}),
            'confirmation_date': forms.DateInput(attrs={'class': 'form-control', 'placeholder': 'Input confirmation date'}),
            'supplier': forms.Select(attrs={'class': 'form-control', 'data-initial': lambda: Supplier.objects.get(id="T00016")}),
            'order': forms.SelectMultiple(attrs={'class': 'form-control'}),
            'comment': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Input comment'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['supplier'].initial = "T00016"

    def clean_confirmation_date(self):
        confirmation_date = self.cleaned_data.get('confirmation_date')
        if confirmation_date > date.today():
            raise ValidationError("Confirmation date should be past")
        return confirmation_date

    def clean_name(self):
        name = self.cleaned_data.get('name')
        try:
            Confirmation.objects.get(name=name)
            raise ValidationError("There is confirmation with such name")
        except Confirmation.DoesNotExist:
            return name

    def clean_confirmation_code(self):
        confirmation_code = self.cleaned_data.get('confirmation_code')
        id = confirmation_code
        try:
            Confirmation.objects.get(id=id)
            raise ValidationError("There is confirmation with such code")
        except Confirmation.DoesNotExist:
            return confirmation_code


class BaseConfirmationModelForm(forms.ModelForm):
    class Meta:
        model = Confirmation
        fields = ['name', 'order', 'comment']
        labels = {
            'name': '',
            'order': 'Order',
            'comment': 'Comment',
        }
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': ''}),
            'order': forms.SelectMultiple(attrs={'class': 'form-control'}),
            'comment': forms.TextInput(attrs={'class': 'form-control', 'placeholder': ''}),
        }


class ViewConfirmationModelForm(BaseConfirmationModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].widget.attrs['hidden'] = True
        self.fields['order'].widget.attrs['disabled'] = True
        self.fields['comment'].widget.attrs['disabled'] = True


class EditConfirmationModelForm(ViewConfirmationModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['order'].widget.attrs['disabled'] = False
        self.fields['comment'].widget.attrs['disabled'] = False


class ProductPriceSelectWidget(forms.Select):
    def __init__(self, confirmation=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.confirmation = confirmation

    def create_option(self, name, value, label, selected, index, **kwargs):
        option = super().create_option(name, value, label, selected, index, **kwargs)
        if value and self.confirmation:
            try:
                confirmation_item = ConfirmationItem.objects.filter(
                    confirmation=self.confirmation,
                    product_id=value
                ).first()
                if confirmation_item:
                    price = confirmation_item.price
                    option['attrs']['data-price'] = f'{price}'
            except Exception as e:
                log.info(
                    'No price for %s : %s', value, str(e))
        return option


class BaseConfirmationItemModelForm(forms.ModelForm):
    class Meta:
        model = ConfirmationItem
        fields = ['client', 'product', 'quantity', 'price', ]
        labels = {
            'client': 'Client',
            'product': 'Product',
            'quantity': 'Quantity',
            'price': 'Price',
        }
        widgets = {
            'product': ProductPriceSelectWidget(confirmation=None, attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 100000,
                'step': 1
            }),
            'price':  forms.NumberInput(attrs={
                'class': 'form-control'}),
            'client': forms.Select(attrs={'class': 'form-control'}),
        }


class ViewConfirmationItemModelForm(BaseConfirmationItemModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['client'].widget.attrs['disabled'] = True
        self.fields['product'].widget.attrs['disabled'] = True
        self.fields['quantity'].widget.attrs['disabled'] = True
        self.fields['price'].widget.attrs['disabled'] = True


class EditConfirmationItemModelForm(ViewConfirmationItemModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['quantity'].widget.attrs['disabled'] = False
        self.fields['client'].widget.attrs['disabled'] = False
        self.fields['price'].widget.attrs['disabled'] = False
        self.fields['price'].widget.attrs['readonly'] = True
        self.fields['product'].widget.attrs['disabled'] = False


class ConfirmationItemFormSet(BaseModelFormSet):
    def __init__(self, *args, **kwargs):
        confirmation = kwargs.pop('form_kwargs', {}).get('confirmation')
        super().__init__(*args, **kwargs)
        self.confirmation = confirmation
        self.queryset = ConfirmationItem.objects.filter(
            confirmation=confirmation)
        self.deletion_widget = forms.CheckboxInput({
            'onclick': 'return confirm("Do you really want to delete the record?");'
        })
        self._initialize_widgets()

    def _initialize_widgets(self):
        products = Product.objects.filter(
            confirmed__confirmation=self.confirmation
        ).distinct()
        clients = Client.objects.filter(
            confirmed_products__confirmation=self.confirmation
        ).distinct()
        for form in self.forms:
            form.fields['product'].widget.confirmation = self.confirmation
            form.fields['product'].queryset = products
            form.fields['client'].queryset = clients

    def add_fields(self, form, index):
        super().add_fields(form, index)
        form.formset = self
        if not form.instance.pk:
            form.instance.confirmation = self.confirmation

    def get_deletion_widget(self):
        return forms.CheckboxInput(attrs={
            'title': 'delete',
            # 'onclick': 'return confirm("Do you really want to delete the record");'
        })

    def get_total(self, fieldname):
        total = 0
        for form in self.forms:
            value = getattr(form.instance, fieldname)
            if value is not None:
                total += value
        return total

    def __check_items_initial(self):
        product_quantity_dict = dict(self.confirmation.items.values_list(
            'product').annotate(quantity=Sum('quantity')))
        for form in self.forms:
            if self.can_delete and self._should_delete_form(form):
                continue
            if product := form.cleaned_data.get("product"):
                quantity = form.cleaned_data.get("quantity")
                product_quantity_dict[product.id] -= quantity
        if all([value == 0 for value in product_quantity_dict.values()]):
            return
        raise ValidationError(
            f"{[f'Must be {value} of {key}' for key, value in product_quantity_dict.items() if value != 0]}")

    def __check_client_product_unique(self):
        client_product_set = set()
        for form in self.forms:
            if self.can_delete and self._should_delete_form(form):
                continue
            client_product = (form.cleaned_data.get("client"),
                              form.cleaned_data.get("product"))
            if client_product in client_product_set:
                raise ValidationError(
                    "Product-Client must be distinct.")
            client_product_set.add(client_product)

    def clean(self):
        if any(self.errors):
            return
        self.__check_items_initial()
        self.__check_client_product_unique()

    def export_to_excel(self):
        df = pd.DataFrame([
            dict(form.initial.items())
            for form in self.forms
        ])
        if df.empty:
            return None
        excel_file = BytesIO()
        df.to_excel(excel_file, index=False)
        excel_file.seek(0)
        return excel_file


ViewConfirmationItemFormSet = forms.modelformset_factory(
    ConfirmationItem,
    form=ViewConfirmationItemModelForm,
    formset=ConfirmationItemFormSet,
    extra=0,
)


EditConfirmationItemFormSet = forms.modelformset_factory(
    ConfirmationItem,
    form=EditConfirmationItemModelForm,
    formset=ConfirmationItemFormSet,
    can_delete=True,
)
