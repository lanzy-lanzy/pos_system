from django.urls import path, include
from pos import views
from .admin import pos_admin_site

urlpatterns = [
    path('admin/', pos_admin_site.urls),
    path('', views.scan_product, name='scan_product'),
    path('get-transaction-details/', views.get_transaction_details, name='get_transaction_details'),

    path('cart/', views.view_cart, name='view_cart'),
    path('remove/<int:product_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('process-payment/', views.process_payment, name='process_payment'),
    path('transaction-history/', views.transaction_history, name='transaction_history'),
    # path('search/', views.search_product, name='search_product'),
    # path('add-to-cart/', views.add_to_cart, name='add_to_cart'),
    path('update-cart-item/', views.update_cart_item, name='update_cart_item'),
    path('delete-cart-item/', views.delete_cart_item, name='delete_cart_item'),
    path('delete-transaction/<uuid:transaction_id>/', views.delete_transaction, name='delete_transaction'),
    path('sales-report/', views.sales_report, name='sales_report'),
    path('generate-sales-report-pdf/', views.generate_sales_report_pdf, name='generate_sales_report_pdf'),
]