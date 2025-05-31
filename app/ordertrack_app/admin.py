from django.contrib import admin
from django.http import HttpResponse
from django.core import serializers

from .models import (
    Client,
    Brand,
    Supplier,
    Product,
    ProductDetail,
    PriceList,
    Order,
    OrderItem,
    Confirmation,
    ConfirmationItem,
    ConfirmationDelivery,
)


@admin.action(description='Export selected')
def export_selected(modelAdmin, request, queryset):
    response = HttpResponse(content_type="application/json")
    serializers.serialize("json", queryset, stream=response)
    return response


admin.site.add_action(export_selected)


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
    list_display = ("id", "second_id", "name", "description", "brand",
                    "prices", "state", "comment", )
    ordering = ("brand", "id",)
    search_fields = ("id", "second_id", "name",)
    search_help_text = ("Search product id or name")
    list_filter = ("brand__name",)
    show_full_result_count = True
    fields = ("id", "second_id", "name", "description", "brand", "comment",)

    @admin.action(description='Revert state')
    def revert_state(self, request, queryset):
        for product in queryset:
            if product.state == "Valid":
                product.state = "Invalid"
            else:
                product.state = "Valid"
            product.save()
        self.message_user(request, "State reverted")

    actions = (revert_state,)

    def prices(self, obj):
        return [f"{o.price} - {o.pricelist.state} " for o in obj.details.all()]


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

    @admin.action(description='Revert state')
    def revert_state(self, request, queryset):
        for pricelist in queryset:
            if pricelist.state == "Valid":
                pricelist.state = "Invalid"
            else:
                pricelist.state = "Valid"
            pricelist.save()
        self.message_user(request, "State reverted")

    actions = (revert_state,)


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
                    "client__name", "product__id", "quantity")
    ordering = ("order__order_date", "client__name")
    search_fields = ("order__id",)
    search_help_text = ("Search name")
    list_filter = ("order__name", "order__order_date", "client__name")
    show_full_result_count = True
    fields = ("order", "client", "product", "quantity",)


@admin.register(Confirmation)
class ConfirmationAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "confirmation_code",
                    "confirmation_date", "supplier__name", "order__name", "comment")
    ordering = ("confirmation_date", "supplier")
    search_fields = ("name", "confirmation_code")
    search_help_text = ("Search name")
    list_filter = ("supplier__name",)
    show_full_result_count = True
    fields = ("id", "name", "confirmation_code",
              "confirmation_date", "supplier", "comment",)


@admin.register(ConfirmationItem)
class ConfirmationItemAdmin(admin.ModelAdmin):
    list_display = ("confirmation__confirmation_code",
                    "client__name", "product__id", "quantity", "price", "comment")
    ordering = ("confirmation__confirmation_date", "client__name")
    search_fields = ("confirmation__confirmation_code",)
    search_help_text = ("Search name")
    list_filter = ("confirmation__confirmation_code", "client__name")
    show_full_result_count = True
    fields = ("confirmation", "client", "product",
              "quantity", "price", "comment",)


@admin.register(ConfirmationDelivery)
class ConfirmationDeliveryAdmin(admin.ModelAdmin):
    list_display = ("confirmation__confirmation_code",
                    "product__id", "quantity", "delivery_date")
    ordering = ("-delivery_date", "confirmation__confirmation_date")
    search_fields = ("confirmation__confirmation_code",)
    search_help_text = ("Search name")
    list_filter = ("confirmation__confirmation_code",)
    show_full_result_count = True
    fields = ("confirmation", "product", "quantity", "delivery_date", )
    verbose_name = "ConfirmationDelivery"
    verbose_name_plural = "ConfirmationDeliveries"
