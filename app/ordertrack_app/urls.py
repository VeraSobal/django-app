from django.urls import path

from .views import views, directories, orders, confirmations, invoices


urlpatterns = [
    path("", views.index, name="index"),
    path('clients/', directories.ClientListView.as_view(), name="clients"),
    path('brands/', directories.BrandListView.as_view(), name="brands"),
    path('suppliers/', directories.SupplierListView.as_view(), name="suppliers"),
    path('products/', directories.ProductListView.as_view(), name="products"),

    path('orders/', orders.OrderListView.as_view(), name="orders"),
    path('orders/add', orders.OrderCreateView.as_view(), name="addorder"),
    path('orders/<str:pk>', orders.OrderDetailView.as_view(), name="vieworder"),
    path('orders/<str:pk>/edit/',
         orders.OrderUpdateView.as_view(), name="editorder"),
    path('orders/<str:pk>/delete/',
         orders.OrderDeleteView.as_view(), name="deleteorder"),

    path('confirmations/', confirmations.ConfirmationListView.as_view(),
         name="confirmations"),
    path('confirmation/add', confirmations.ConfirmationCreateView.as_view(),
         name="addconfirmation"),
    path('confirmations/<str:pk>',
         confirmations.ConfirmationDetailView.as_view(), name="viewconfirmation"),
    path('confirmations/<str:pk>/delete/',
         confirmations.ConfirmationDeleteView.as_view(), name="deleteconfirmation"),
    path('confirmations/<str:pk>/edit/',
         confirmations.ConfirmationUpdateView.as_view(), name="editconfirmation"),

    path('confirmations/<str:pk>/exporttoexcel/',
         confirmations.export_to_excel, name="exportconfirmationtoexcel"),
    path('invoices/', invoices.invoices, name="invoices"),
    path('invoices/<str:invoice_id>', invoices.invoice_items, name="invoiceitems"),
]
