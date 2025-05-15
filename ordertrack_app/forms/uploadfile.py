from django import forms
from django.shortcuts import get_list_or_404
from django.db.models import F, Sum, Case, When, Subquery

from itertools import groupby
from datetime import datetime
import pandas as pd
from ..models import (
    Product,
    OrderItem,
    ConfirmationItem,
    ConfirmationDelivery,
    Brand,
    Client,
)
import logging

log = logging.getLogger(__name__)


class UploadFileForm(forms.Form):
    file = forms.FileField(label="", required=False, widget=forms.ClearableFileInput(attrs={
        'accept': '.xls,.xlsx',
        'multiple': False
    }))

    @staticmethod
    def data_json(data):
        return data.to_json(orient='records')


class UploadOrderForm(UploadFileForm):

    @staticmethod
    def __load_excel_order_T00016(uploaded_file):
        brand = uploaded_file.name.split(
            "-")[2].replace(".", "").replace(" ", "").upper()
        client = uploaded_file.name.split(
            "-")[1].replace(".", "").replace(" ", "").upper()
        df = pd.read_excel(uploaded_file, parse_dates=True, dtype=str,)
        df.columns = df.columns.str.lower()
        df.dropna(inplace=True)
        if "note" not in df.columns.values:
            df["client"] = client
        else:
            df["client"] = df["note"].apply(
                lambda x: f'{x.replace(".", "").upper()}')
        df.rename(columns={df.columns.values[0]: 'product'}, inplace=True)
        df['product'] = df['product'].astype(
            str).str.replace(".", "") + f"_{brand}"
        if df.columns.get_loc('quantity') == 2:
            df.rename(
                columns={df.columns.values[1]: 'second_id'}, inplace=True)
            df["second_id"] = df["second_id"].astype(
                str).str.replace(".", "") + f"_{brand}"
        else:
            df["second_id"] = df["product"]
        df['quantity'] = pd.to_numeric(df['quantity'])
        if brand == "B05":
            df['product'] = df['product'].str.zfill(14)
        df = df.groupby(["product", "second_id", "client", ])[
            "quantity"].sum()
        df.loc['total'] = df.sum()
        df = df.reset_index()
        df.columns = ['product', "second_id", 'client', 'quantity',]
        print(df)
        return df

    @staticmethod
    def load_excel_order(uploaded_file, supplier):
        if supplier.id == "T00016":
            order_data = UploadOrderForm.__load_excel_order_T00016(
                uploaded_file)
        return order_data

    @staticmethod
    def save_order_items(order_data_json, order):
        for item in order_data_json:
            product_id = item.get("product")
            if product_id != "total":
                second_id = item.get("second_id")
                if product_id == second_id:
                    second_id = None
                brand_id = product_id[-3:]
                client_id = item.get("client")
                quantity = item.get("quantity")
                product, created = Product.objects.get_or_create(
                    id=product_id, second_id=second_id, brand_id=brand_id)
                print(product, created)
                OrderItem.objects.create(
                    order_id=order.id, client_id=client_id, product_id=product_id, quantity=quantity)


class UploadConfirmationForm(UploadFileForm):

    def __find_next_value(df, target_value):
        for column in df.columns.values:
            if df[column].str.contains(target_value).any():
                idx = df[column].str.contains(target_value).idxmax()
                next_col = df.columns[df.columns.get_loc(column) + 1]
                return df.loc[idx, next_col]

    @staticmethod
    def __load_excel_confirmation_T00016(uploaded_file):
        brand = uploaded_file.name.split(" ")[1]
        brand_id = Brand.objects.filter(
            name__icontains=brand).first().id
        if brand_id is None:
            brand_id = "None"  # или указать ошибку!!!
        df = pd.read_excel(uploaded_file, parse_dates=True, dtype={},)
        df = df.map(lambda x: x.strip() if isinstance(x, str) else x)
        confirmation_code = UploadConfirmationForm.__find_next_value(
            df, 'Ihre Bestellnummer:')
        start_str = 'Pos'
        start_index = df.loc[df['Unnamed: 0'] == start_str].index[0]
        end_index = df['Unnamed: 0'].iloc[start_index:].isna().idxmax()
        df = df.iloc[start_index: end_index].reset_index(
            drop=True)
        df.columns = df.iloc[0]
        df = df.drop(index=[0]).reset_index(drop=True).drop('Pos', axis=1)
        df.index = df.index + 1
        df['Teilenummer'] = df['Teilenummer'].astype(
            str).str.replace(".", "") + f"_{brand_id}"
        df.rename(columns={'Teilenummer': 'product'}, inplace=True)
        df.rename(columns={'Bezeichnung': 'product_name'}, inplace=True)
        df.rename(columns={'Menge': 'quantity'}, inplace=True)
        df.rename(columns={'Preise': 'price'}, inplace=True)
        df.rename(columns={'Liefertermin': 'delivery_date'}, inplace=True)
        df.rename(columns={'Betrag': 'total_price'}, inplace=True)
        df.loc['total', 'total_price'] = df['total_price'].sum()
        df = df.fillna('').replace('unknown', None).infer_objects(copy=False)
        # FutureWarning: Downcasting object dtype arrays on .fillna, .ffill, .bfill is deprecated
        # and will change in a future version. Call result.infer_objects(copy=False) instead.
        # To opt-in to the future behavior, set `pd.set_option('future.no_silent_downcasting', True)`
        return confirmation_code, df

    @staticmethod
    def load_excel_confirmation(uploaded_file, supplier):
        if supplier.id == "T00016":
            confirmation_code, confirmation_data = UploadConfirmationForm.__load_excel_confirmation_T00016(
                uploaded_file)
        return confirmation_code, confirmation_data

    @staticmethod
    def __get_left_quantity_per_client(product_id, ordered_items, confirmed_items):
        # может быть, это нужно переписать в вид типа client_list = Client.objects.filter(
        # ordered_products__order__confirmations=confirmation
        # ).distinct()

        # Ищем количество товара в разрезе клиентов: заказанное количество минус подтвержденное
        ordered_quantity_per_client = ordered_items.filter(
            product_id=product_id).values('client_id').annotate(
            quantity=Sum('quantity')
        ).order_by('client_id')
        confirmed_quantity_per_client = confirmed_items.filter(
            product_id=product_id).values('client_id').annotate(
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

    @staticmethod
    def save_confirmation_delivery(confirmation_data_json, confirmation):
        filtered_data = [
            item for item in confirmation_data_json if item['product'] != "" and item['delivery_date'] != ""]
        sorted_data = sorted(filtered_data,
                             key=lambda x: (x['product'], x['delivery_date']))
        grouped = groupby(
            sorted_data,
            key=lambda x: (x['product'], x['delivery_date']))
        for (product, delivery), group in grouped:
            items = list(group)
            product, delivery = (product, delivery)
            delivery_date = datetime.fromtimestamp(
                delivery / 1000).strftime('%Y-%m-%d')
            print(confirmation.id, product, delivery_date)
            quantity = sum([item['quantity'] for item in items])
            ConfirmationDelivery.objects.create(
                confirmation_id=confirmation.id, product_id=product, delivery_date=delivery_date, quantity=quantity)

    @staticmethod
    def save_confirmation_items(confirmation_data_json, confirmation):
       # получаем товары из отмеченных в подтверждении заказов
        orders_ids = confirmation.order.all().values_list('id', flat=True)
        ordered_items = OrderItem.objects.filter(
            order__id__in=orders_ids).select_related('order')

        # Находим confirmation_item, где confirmation.order содержит любой из этих заказов
        confirmed_items = ConfirmationItem.objects.filter(
            confirmation__order__id__in=orders_ids
        )

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
            brand_id = product_id[-3:]
            product_name = items[0].get("product_name")
            defaults = {
                'name': product_name,
                'brand_id': brand_id

            }
            Product.objects.update_or_create(
                id=product_id, defaults=defaults)
            price = items[0].get("price")
            # если такой продукт есть в заказе, т.е. известен клиент
            left_quantity_per_client = UploadConfirmationForm.__get_left_quantity_per_client(
                product_id, ordered_items, confirmed_items)
            if left_quantity_per_client:
                for item in left_quantity_per_client:
                    client_id = item['client_id']
                    quantity = item['quantity']
                    ConfirmationItem.objects.create(
                        confirmation_id=confirmation.id,
                        client_id=client_id,
                        product_id=product_id,
                        quantity=quantity,
                        price=price)
            else:
                print(f"{product_id} не найден в заказах {orders_ids}")
                client, _ = Client.objects.get_or_create(id="Unknown")
                print(client)
                ConfirmationItem.objects.create(
                    confirmation_id=confirmation.id,
                    client_id=client.id,
                    product_id=product_id,
                    quantity=total_quantity,
                    price=price,)
                # если продукта в заказе нет, то нужно открыть форму update и с пустым значением в графе клиент для вставки вручную

        UploadConfirmationForm.save_confirmation_delivery(
            confirmation_data_json, confirmation)
