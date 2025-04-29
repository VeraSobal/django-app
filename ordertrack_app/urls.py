from django.urls import path
from .views import views, directories, orders, confirmations, invoices


urlpatterns = [
    path("", views.index, name="index"),
    path('clients/', directories.clients, name="clients"),
    path('brands/', directories.brands, name="brands"),
    path('suppliers/', directories.suppliers, name="suppliers"),
    path('products/', directories.products, name="products"),
    path('orders/', orders.orders, name="orders"),
    path('orders/<str:order_id>', orders.orderitems, name="orderitems"),
    path('confirmations/', confirmations.confirmations, name="orders"),
    path('confirmations/<str:confirmation_id>',
         confirmations.confirmationitems, name="confirmationitems"),
    path('invoices/', invoices.invoices, name="invoices"),
    path('invoices/<str:invoice_id>', invoices.invoiceitems, name="invoiceitems"),
]
