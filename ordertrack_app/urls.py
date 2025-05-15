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
    path('newconfirmation/', confirmations.new_confirmation, name="newconfirmation"),
    path('confirmations/<str:confirmation_id>',
         confirmations.view_confirmation, name="viewconfirmation"),
    path('confirmations/<str:confirmation_id>/edit/',
         confirmations.edit_confirmation, name="editconfirmation"),
    path('confirmations/<str:confirmation_id>/delete/',
         confirmations.delete_confirmation, name="deleteconfirmation"),
    path('confirmations/<str:confirmation_id>/exporttoexcel/',
         confirmations.export_to_excel, name="exportconfirmationtoexcel"),
    path('invoices/', invoices.invoices, name="invoices"),
    path('invoices/<str:invoice_id>', invoices.invoice_items, name="invoiceitems"),
]
