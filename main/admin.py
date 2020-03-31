import logging
from datetime import datetime, timedelta

from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.db.models import Avg, Count, Min, Sum
from django.db.models.functions import TruncDay
from django.template.response import TemplateResponse
from django.urls import path
from django.utils.html import format_html

from . import models

logger = logging.getLogger(__name__)


@admin.register(models.User)
class UserAdmin(DjangoUserAdmin):
    fieldsets = (

        (None, {"fields": ("email", "password")}),
        (
            "Personal info",
            {
                "fields": ("first_name", "last_name"),
            },
        ),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            }
        ),
        (
            "Important dates",
            {
                "fields": ("last_login", "date_joined"),
            },
        ),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "password1", "password2",),
            },
        ),
    )
    list_display = ('email', 'first_name', 'last_name', 'is_staff',)
    search_fields = ('email', 'first_name', 'last_name',)
    ordering = ('email',)


class AddressAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "name",
        "address1",
        "address2",
        "city",
        "country",
    )
    readonly_fields = ("user",)


class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'in_stock', 'price')
    list_filter = ('active', 'in_stock', 'date_updated')
    list_editable = ('in_stock', )
    search_fields = ('name', )
    prepopulated_fields = {"slug": ("name",)}
    autocomplete_fields = ('tags',)

    def get_readonly_fields(self, request, obj=None):
        if request.user.is_superuser:
            return self.readonly_fields
        return list(self.readonly_fields) + ["slug", "name"]

    def get_prepopulated_fields(self, request, obj=None):
        if request.user.is_superuser:
            return self.prepopulated_fields
        return {}


admin.site.register(models.Product, ProductAdmin)


class ProductTagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    list_filter = ('active', )
    search_fields = ('name',)
    prepopulated_fields = {"slug": ("name",)}

    def get_readonly_fields(self, request, obj=None):
        if request.user.is_superuser:
            return self.readonly_fields
        return list(self.readonly_fields) + ["slug", "name"]

    def get_prepopulated_fields(self, request, obj=None):
        if request.user.is_superuser:
            return self.prepopulated_fields
        return {}


admin.site.register(models.ProductTag, ProductTagAdmin)


class ProductImageAdmin(admin.ModelAdmin):
    list_display = ('thumbnail_tag', 'product_name')
    readonly_fields = ('thumbnail',)
    search_fields = ('product__name',)

    def thumbnail_tag(self, obj):
        if obj.thumbnail:
            return format_html('<img src="%s"/>' % obj.thumbnail.url)
        return "-"
    thumbnail_tag.short_description = "Thumbnail"

    def product_name(self, obj):
        return obj.product.name


admin.site.register(models.ProductImage, ProductImageAdmin)


class BasketLineInline(admin.TabularInline):
    model = models.BasketLine
    raw_id_fields = ("product",)


@admin.register(models.Basket)
class BasketAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "status", "count")
    list_editable = ("status",)
    list_filter = ("status",)
    inlines = (BasketLineInline,)


class OrderLineInline(admin.TabularInline):
    model = models.OrderLine
    raw_id_fields = ("product",)


@admin.register(models.Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "status")
    list_editable = ("status",)
    list_filter = ("status", "shipping_country", "date_added")
    inlines = (OrderLineInline,)
    fieldsets = (
        (None, {
            "fields": (("user", "status"))
        }),
        (
            "Billing info",
            {
                "fields": (("billing_name",
                            "billing_address1",
                            "billing_address2"),
                           ("billing_zip_code",
                            "billing_city",
                            "billing_country")
                           )
            }),
        (
            "Shipping info", {
                "fields": (
                    ("shipping_name",
                     "shipping_address1",
                     "shipping_address2",),
                    ("shipping_zip_code",
                     "shipping_city",
                     "shipping_country",)
                )},
        ),
    )


class CentralOfficeOrderLineInline(admin.TabularInline):
    model = models.OrderLine
    readonly_fields = ("product",)


class CentralOfficeOrderAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "status")
    list_editable = ("status",)
    readonly_fields = ("user",)
    list_filter = ("status", "shipping_country", "date_added")
    inlines = (CentralOfficeOrderLineInline,)
    fieldsets = (
        ("Main", {"fields": ("user", "status")}),
        (
            "Billing info",
            {
                "fields": (
                    ("billing_name",
                     "billing_address1",
                     "billing_address2"),
                    ("billing_zip_code",
                     "billing_city",
                     "billing_country"),
                )
            },
        ),
        (
            "Shipping info",
            {
                "fields": (
                    ("shipping_name",
                     "shipping_address1",
                     "shipping_address2"),
                    ("shipping_zip_code",
                     "shipping_city",
                     "shipping_country"),
                )
            },
        ),
    )


class DispatchersProductAdmin(ProductAdmin):
    readonly_fields = ("description", "price", "tags", "active")
    prepopulated_fields = {}
    autocomplete_fields = ()


class DispatchersOrderAdmin(admin.ModelAdmin):
    list_display = ("id", "shipping_name", "date_added", "status",)
    list_filter = ("status", "shipping_country", "date_added")
    inlines = (CentralOfficeOrderLineInline,)
    fieldsets = (
        (
            "Shipping info",
            {
                "fields": (
                    "shipping_name",
                    "shipping_address1",
                    "shipping_address2",
                    "shipping_zip_code",
                    "shipping_city",
                    "shipping_country",
                )
            },

        ),
    )

    def get_queryset(self, request):
        """Dispatchers are supposed to see orders that are ready to be shipped"""

        qs = super().get_queryset(request)
        return qs.filter(status=models.Order.PAID)


class ColoredAdminSite(admin.sites.AdminSite):
    """The class will pass Django admin templates some extra values that represent 
    colors of headings."""

    def each_context(self, request):
        context = super().each_context(request)
        context["site_header_color"] = getattr(self, "site_header_color", None)
        context["module_caption_color"] = getattr(self, "module_caption_color", None)
        return context


class PeriodSelectForm(forms.Form):
    PERIODS = ((30, "30 days"), (60, "60 days"), (90, "90 days"))
    period = forms.TypedChoiceField(choices=PERIODS, coerce=int, required=True)


class ReportingColoredAdminSite(ColoredAdminSite):
    """Add reporting views ot the list of available urls and add them
    to the index page."""

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path("orders_per_day/", self.admin_view(self.orders_per_day), name="orders_per_day"),
            path("most_bought_products/", self.admin_view(self.most_bought_products), name="most_bought_products"),
        ]
        return my_urls + urls

    def orders_per_day(self, request):
        starting_day = datetime.now() - timedelta(days=180)
        order_data = (models.Order.objects.filter(
            date_added__gt=starting_day).annotate(
                day=TruncDay("date_added")
        ).values("day").annotate(c=Count("id")))

        labels = [x["day"].strftime("%Y-%m-%d") for x in order_data]
        values = [x["c"] for x in order_data]
        context = dict(
            self.each_context(request),
            title="Orders per day",
            labels=labels,
            values=values,
        )
        return TemplateResponse(request, "order_per_day.html", context)

    def most_bought_products(self, request):
        if request.method == "POST":
            form = PeriodSelectForm(request.POST)
            if form.is_valid():
                days = form.cleaned_data["period"]
                starting_day = datetime.now() - timedelta(days=days)

                data = (models.OrderLine.objects.filter(order__date_added__gt=starting_day)
                        .values("product__name")
                        .annotate(c=Count("id"))
                        )

                logger.info("most_bought_products query: %s", data.query)
                labels = [x["product__name"] for x in data]
                values = [x["c"] for x in data]
        else:
            form = PeriodSelectForm()
            labels = None
            values = None

        context = dict(
            self.each_context(request),
            title="Most bought products",
            form=form,
            labels=labels,
            values=values,
        )
        return TemplateResponse(request, "most_bought_products.html", context)

    def index(self, request, extra_content=None):
        reporting_pages = [
            {
                "name": "Orders per day",
                "link": "orders_per_day/",
            },
            {
                "name": "Most bought products",
                "link": "most_bought_products/"
            }
        ]
        if not extra_content:
            extra_content = {}
        extra_content = {"reporting_pages": reporting_pages}
        return super().index(request, extra_content)


class OwnersAdminSite(ReportingColoredAdminSite):
    site_header = "BookTime owners administration"
    site_header_color = "black"
    module_caption_color = "grey"

    def has_permission(self, request):
        return (request.user.is_active and request.user.is_superuser)


class CentralOfficeAdminSite(ReportingColoredAdminSite):
    site_header = "BookTime central office administration"
    site_header_color = "purple"
    module_caption_color = "pink"

    def has_permission(self, request):
        return (
            request.user.is_active and request.user.is_employee
        )


class DispatchersAdminSite(ReportingColoredAdminSite):
    site_header = "Bootime central dispatchers administration"
    site_header_color = "green"
    moule_caption_color = "lightgreen"

    def has_permission(self, request):
        return (
            request.user.is_active and request.user.is_dispatcher
        )


main_admin = OwnersAdminSite()
main_admin.register(models.Product, ProductAdmin)
main_admin.register(models.ProductImage, ProductImageAdmin)
main_admin.register(models.ProductTag, ProductTagAdmin)
main_admin.register(models.User, UserAdmin)
main_admin.register(models.Address, AddressAdmin)
main_admin.register(models.Basket, BasketAdmin)
main_admin.register(models.Order, OrderAdmin)


central_office_admin = CentralOfficeAdminSite("central-office-admin")
central_office_admin.register(models.Product, ProductAdmin)
central_office_admin.register(models.ProductTag, ProductTagAdmin)
central_office_admin.register(models.ProductImage, ProductImageAdmin)
central_office_admin.register(models.Order, CentralOfficeOrderAdmin)
central_office_admin.register(models.Address, AddressAdmin)
dispatchers_admin = DispatchersAdminSite("dispatchers-admin")
dispatchers_admin.register(models.Product, DispatchersProductAdmin)
dispatchers_admin.register(models.ProductTag, ProductTagAdmin)
dispatchers_admin.register(models.Order, DispatchersOrderAdmin)
