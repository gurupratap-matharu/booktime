from decimal import Decimal
from unittest.mock import patch

from django.contrib import auth
from django.test import TestCase
from django.urls import reverse

from main import forms, models


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

    def test_user_signup_page_loads_correctly(self):
        response = self.client.get(reverse("signup"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "signup.html")
        self.assertContains(response, "BookTime")
        self.assertIsInstance(response.context["form"], forms.UserCreationForm)

    def test_user_signup_page_submission_works(self):
        post_data = {
            "email": "user@domain.com",
            "password1": "abcabcabc",
            "password2": "abcabcabc",
        }
        with patch.object(forms.UserCreationForm, "send_mail") as mock_send:
            response = self.client.post(reverse("signup"), post_data)

        self.assertEqual(response.status_code, 302)
        self.assertTrue(models.User.objects.filter(email="user@domain.com").exists())
        self.assertTrue(auth.get_user(self.client).is_authenticated)
        mock_send.assert_called_once()

    def test_address_list_page_returns_only_owned(self):
        user1 = models.User.objects.create_user("user1", "pw432joij")
        user2 = models.User.objects.create_user("user2", "ps432joij")
        models.Address.objects.create(
            user=user1,
            name="john kimball",
            address1="flat2",
            address2="12 Stralz avenue",
            city="London",
            country="uk",
        )
        models.Address.objects.create(
            user=user2,
            name="marc kimball",
            address1="123 Decan road",
            address2="London",
            country="uk",
        )
        self.client.force_login(user2)
        response = self.client.get(reverse("address_list"))
        self.assertEqual(response.status_code, 200)

        address_list = models.Address.objects.filter(user=user2)
        self.assertEqual(list(address_list), list(response.context["object_list"]))

    def test_address_create_stores_user(self):
        user1 = models.User.objects.create_user("user1", "pw432joij")
        post_data = {
            "name": "john kercher",
            "address1": "1 av st",
            "address2": "",
            "zip_code": "MA12GS",
            "city": "Manchester",
            "country": "uk",
        }
        self.client.force_login(user1)
        self.client.post(reverse("address_create"), post_data)
        self.assertTrue(models.Address.objects.filter(user=user1).exists())

    def test_add_to_basket_loggedin_works(self):
        user1 = models.User.objects.create_user("veerplaying@gmail.com", "pw432joij")
        book1 = models.Product.objects.create(
            name="One upon a time in Buenos Aires",
            slug="once-upon-a-time-in-buenos-aires",
            price=Decimal("150.00"),
        )
        book2 = models.Product.objects.create(
            name="Elon Musk",
            slug="elon-musk",
            price=Decimal("3.00"),
        )

        self.client.force_login(user1)
        response = self.client.get(reverse("add_to_basket"), {"product_id": book1.id})
        response = self.client.get(reverse("add_to_basket"), {"product_id": book1.id})
        self.assertTrue(
            models.Basket.objects.filter(user=user1).exists()
        )
        self.assertEquals(models.BasketLine.objects.filter(basket__user=user1).count(), 1)

        response = self.client.get(reverse("add_to_basket"), {"product_id": book2.id})
        self.assertEquals(models.BasketLine.objects.filter(basket__user=user1).count(), 2)
