from django.test import Client, TestCase


class CorePagesTest(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_404_pages_uses_custom_template(self):
        """Страница 404 отдает кастомный шаблон."""
        response = self.guest_client.get('/unexisting_page/')
        self.assertTemplateUsed(response, 'core/404.html')
