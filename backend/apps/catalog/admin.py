from django.contrib import admin

from .models import PriceRecord, Product, Retailer


@admin.register(Retailer)
class RetailerAdmin(admin.ModelAdmin):
    list_display = ["name", "integration_type", "is_active", "base_url"]
    list_filter = ["integration_type", "is_active"]


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ["name", "category"]
    list_filter = ["category"]
    search_fields = ["name", "description"]


@admin.register(PriceRecord)
class PriceRecordAdmin(admin.ModelAdmin):
    list_display = ["product", "retailer", "price", "delivery_cost", "retrieved_at"]
    list_filter = ["retailer"]
