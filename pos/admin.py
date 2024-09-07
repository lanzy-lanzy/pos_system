from django.contrib import admin
from .models import Product, Transaction, TransactionItem
from pos_system.admin import pos_admin_site

@admin.register(Product, site=pos_admin_site)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'barcode')
    search_fields = ('name', 'barcode')

@admin.register(Transaction, site=pos_admin_site)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'total_amount')
    # Remove list_filter for now until we know the correct field to filter on

@admin.register(TransactionItem, site=pos_admin_site)
class TransactionItemAdmin(admin.ModelAdmin):
    list_display = ('transaction', 'product', 'quantity', 'get_subtotal')
    # Remove list_filter for now until we know the correct field to filter on

    def get_subtotal(self, obj):
        return obj.quantity * obj.product.price
    get_subtotal.short_description = 'Subtotal'    
