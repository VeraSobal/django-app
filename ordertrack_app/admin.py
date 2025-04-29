from django.contrib import admin

from .models import (
    Client,
    Brand,
    Supplier,
    Product,
    ProductDetail,
    PriceList,
    Order,
    OrderItem
)


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "comment")
    ordering = ("id",)
    search_fields = ("id", "name")
    search_help_text = ("Search client id or name")
    show_full_result_count = True
    fields = ("id", "name", "comment",)


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "comment")
    ordering = ("id",)
    search_fields = ("id", "name")
    search_help_text = ("Search brand id or name")
    show_full_result_count = True
    fields = ("id", "name", "comment",)


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "comment")
    ordering = ("id",)
    search_fields = ("id", "name")
    search_help_text = ("Search supplier id or name")
    show_full_result_count = True
    fields = ("id", "name", "comment",)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "description", "brand",
                    "prices", "state", "comment", )
    ordering = ("brand", "id",)
    search_fields = ("id", "name",)
    search_help_text = ("Search product id or name")
    list_filter = ("brand__name",)
    show_full_result_count = True
    fields = ("id", "name", "description", "brand", "comment",)

    def prices(self, obj):

        return [(o.price, o.pricelist.state) for o in obj.details.all()]


@admin.register(ProductDetail)
class ProductDetailAdmin(admin.ModelAdmin):
    list_display = ("product", "price", "pricelist__starts_from",
                    "pricelist__state", "pricelist")
    ordering = ("product__brand", "product__name",)
    search_fields = ("product__name", "product__brand__name",)
    search_help_text = ("Search product brand or name")
    list_filter = ("product__brand__name",)
    show_full_result_count = True
    fields = ("product", "pricelist", "price",)

    def prices(self, obj):

        return [(o.price, o.pricelist.state) for o in obj.details.all()]


@admin.register(PriceList)
class PriceListAdmin(admin.ModelAdmin):
    list_display = ("supplier__name", "pricelist_date",
                    "state", "starts_from", "comment")
    ordering = ("supplier", "pricelist_date")
    search_fields = ("supplier",)
    search_help_text = ("Search supplier")
    list_filter = ("supplier__name",)
    show_full_result_count = True
    fields = ("pricelist_date", "state", "starts_from", "comment",)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "order_date", "supplier__name", "comment")
    ordering = ("order_date", "supplier")
    search_fields = ("name",)
    search_help_text = ("Search name")
    list_filter = ("supplier__name",)
    show_full_result_count = True
    fields = ("id", "name", "order_date", "supplier", "comment",)


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ("order__id", "order__order_date",
                    "client__name", "product__name", "quantity")
    ordering = ("order__order_date", "client__name")
    search_fields = ("order__id",)
    search_help_text = ("Search name")
    list_filter = ("order__name", "order__order_date", "client__name")
    show_full_result_count = True
    fields = ("order", "client", "product", "quantity",)
