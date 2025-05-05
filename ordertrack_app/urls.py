from django.urls import path
from .views import views, directories, orders, confirmations, invoices


urlpatterns = [
    path("", views.index, name="index"),
    path('clients/', directories.clients, name="clients"),
    path('brands/', directories.brands, name="brands"),
    path('suppliers/', directories.suppliers, name="suppliers"),
    path('products/', directories.products, name="products"),
    path('orders/', orders.orders, name="orders"),
    path('neworder/', orders.new_order, name="neworder"),
    path('orders/<str:order_id>', orders.view_order, name="vieworder"),
    path('orders/<str:order_id>/edit/', orders.edit_order, name="editorder"),
    path('orders/<str:order_id>/delete/',
         orders.delete_order, name="deleteorder"),
    path('confirmations/', confirmations.confirmations, name="confirmations"),
    path('confirmations/<str:confirmation_id>',
         confirmations.confirmation_items, name="confirmationitems"),
    path('invoices/', invoices.invoices, name="invoices"),
    path('invoices/<str:invoice_id>', invoices.invoice_items, name="invoiceitems"),
]
