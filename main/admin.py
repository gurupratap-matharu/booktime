from django.contrib import admin

from . import models


class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'in_stock', 'price')
    list_filter = ('active', 'in_stock', 'date_updated')
    list_editable = ('in_stock', )
    search_fields = ('name', )
    prepopulated_fields = {"slug": ("name",)}


admin.site.register(models.Product, ProductAdmin)
