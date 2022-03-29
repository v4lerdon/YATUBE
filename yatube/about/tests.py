from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse


class AboutPagesTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_page_accessible_by_names(self):
        """Проверка доступности страниц и шаблонов."""
        templates_url_names = {
            '/about/author/': 'about/author.html',
            '/about/tech/': 'about/tech.html'
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertTemplateUsed(response, template)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_page_uses_correct_template(self):
        """Проверка шаблонов при запросе к namespace в приложении about."""
        templates_page_names = {
            reverse('about:author'): 'about/author.html',
            reverse('about:tech'): 'about/tech.html'
        }
        for namespace_name, template in templates_page_names.items():
            with self.subTest(template=template):
                response = self.guest_client.get(namespace_name)
                self.assertTemplateUsed(response, template)
