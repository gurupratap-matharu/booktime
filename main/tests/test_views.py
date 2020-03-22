from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from main import models


class TestPage(TestCase):
    def test_home_page_works(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'home.html')
        self.assertContains(response, 'BookTime')

    def test_about_page_works(self):
        response = self.client.get(reverse("about_us"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'about_us.html')
        self.assertContains(response, 'BookTime')

    def test_products_page_returns_active(self):
        models.Product.objects.create(
            name="The cathedral and the bazaar",
            slug="cathedral-bazaar",
            price=Decimal("10.00"),
        )
        models.Product.objects.create(
            name="A tale of two cities",
            slug="tale-two-cities",
            price=Decimal("2.00"),
        )

        response = self.client.get(reverse('products', kwargs={"tag": "all"}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'BookTime')

        product_list = models.Product.objects.active().order_by("name")
        self.assertEqual(list(response.context["object_list"]),
                         list(product_list))

    def test_products_page_filters_by_tags_and_active(self):
        product_1 = models.Product.objects.create(
            name="The cathedral and the bazaar",
            slug="cathedral-bazaar",
            price=Decimal("10.00"),
        )
        product_1.tags.create(name="Open source", slug="opensource")

        models.Product.objects.create(
            name="Microsoft Windows Guide",
            slug="microsoft-windows-guide",
            price=Decimal("12.00"),
        )
        response = self.client.get(reverse('products', kwargs={"tag": "opensource"}))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "BookTime")

        product_list = (models.Product.objects.active().filter(tags__slug="opensource").order_by("name"))

        self.assertEqual(list(product_list), list(response.context['object_list']))
