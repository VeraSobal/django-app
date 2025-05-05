from django import forms
import pandas as pd
from ..models import Product, OrderItem, Brand, Client, Order
import logging

log = logging.getLogger(__name__)


class UploadFileForm(forms.Form):
    file = forms.FileField(label="", required=False, widget=forms.ClearableFileInput(attrs={
        'accept': '.xls,.xlsx',
        'multiple': False
    }))

    @staticmethod
    def __load_excel_order_T00016(uploaded_file):
        brand = uploaded_file.name.split(
            "-")[2].replace(".", "").replace(" ", "").upper()
        client = uploaded_file.name.split(
            "-")[1].replace(".", "").replace(" ", "").upper()
        df = pd.read_excel(uploaded_file, parse_dates=True, dtype=str,)
        df.dropna(inplace=True)
        df.columns = df.columns.str.lower()
        if "note" not in df.columns.values:
            df["client"] = client
        else:
            df["client"] = df["note"].apply(
                lambda x: f'{x.replace(".", "").upper()}')
        df.columns.values[0] = "product"
        df['product'] = df['product'].astype(
            str).str.replace(".", "") + f"_{brand}"
        df['quantity'] = pd.to_numeric(df['quantity'])
        if brand == "B05":
            df['product'] = df['product'].str.zfill(14)
        order_data = df.groupby(["product", "client"])[
            "quantity"].sum()
        order_data.loc['total'] = order_data.sum()
        order_data = order_data.reset_index()
        order_data.columns = ['product', 'client', 'quantity']
        return order_data

    @staticmethod
    def load_excel_order(uploaded_file, supplier):
        if supplier.id == "T00016":
            order_data = UploadFileForm.__load_excel_order_T00016(
                uploaded_file)
        return order_data

    @staticmethod
    def order_data_json(order_data):
        return order_data.to_json(orient='records')

    @staticmethod
    def save_order_items(order_data_json, order):
        for item in order_data_json:
            product_id = item.get("product")
            if product_id != "total":
                brand_id = product_id[-3:]
                client_id = item.get("client")
                quantity = item.get("quantity")
                Product.objects.get_or_create(
                    id=product_id, brand_id=brand_id)
                OrderItem.objects.create(
                    order_id=order.id, client_id=client_id, product_id=product_id, quantity=quantity)
