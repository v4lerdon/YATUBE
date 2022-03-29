import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.forms import PostForm
from posts.models import Comment, Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='user')
        cls.guest = User.objects.create_user(username='HasNoName')
        cls.group = Group.objects.create(
            title='Название группы',
            slug='test-slug',
        )
        cls.form = PostForm()
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовая запись',
            group=cls.group
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        posts_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Тестовая запись из формы',
            'image': uploaded
        }
        response = self.authorized_client.post(reverse(
            'posts:post_create',

        ),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:profile',
            kwargs={'username': self.user}
        )
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(Post.objects.filter(
            text='Тестовая запись из формы',
            image='posts/small.gif').exists()
        )

    def test_create_post_guest(self):
        """Гость не создает запись в Post."""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Тестовая запись из формы от гостя'
        }
        response = self.guest_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        redirect_url = '/auth/login/?next=/create/'
        self.assertRedirects(response, redirect_url)
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertFalse(Post.objects.filter(
            text='Тестовая запись из формы от гостя').exists()
        )

    def test_update_post(self):
        """Валидная форма редактирует запись в Post."""
        form_data = {
            'text': 'Тестовая запись из формы2',
            'group': self.group.id
        }
        self.authorized_client.post(reverse(
            'posts:post_create'
        ),
            data=form_data,
            follow=True
        )
        edited_post = Post.objects.get(id=self.group.id)
        self.authorized_client.get(f'/posts/{edited_post.id}/edit/')
        form_data = {
            'text': 'Измененная тестовая запись из формы',
            'group': self.group.id
        }
        self.authorized_client.post(reverse(
            'posts:post_edit',
            kwargs={'post_id': edited_post.id}
        ),
            data=form_data,
            follow=True
        )
        edited_post = Post.objects.get(id=self.group.id)
        self.assertEqual(
            edited_post.text,
            'Измененная тестовая запись из формы'
        )

    def test_create_comment(self):
        """Авторизованный пользователь создает
        комментарий на странице поста."""
        comments_count = Comment.objects.count()
        form_data = {
            'text': 'Тестовый комментарий',
        }
        self.authorized_client.post(reverse(
            'posts:add_comment',
            kwargs={'post_id': self.post.id}
        ),
            data=form_data,
            follow=True
        )
        self.assertEqual(Comment.objects.count(), comments_count + 1)

    def test_create_comment_guest(self):
        """Гость не может написать комментарий"""
        comments_count = Comment.objects.count()
        form_data = {
            'text': 'Тестовый комментарий гостя',
        }
        self.guest_client.post(reverse(
            'posts:add_comment',
            kwargs={'post_id': self.post.id}
        ),
            data=form_data,
            follow=True
        )
        self.assertEqual(Comment.objects.count(), comments_count)
