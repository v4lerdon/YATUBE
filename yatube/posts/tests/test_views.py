import shutil
import tempfile
from xml.etree.ElementTree import Comment

from django import forms
from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Comment, Follow, Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='user')
        cls.group = Group.objects.create(
            title='Название группы',
            slug='test-slug',
        )
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.image = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовая запись',
            group=cls.group,
            image=cls.image
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.user,
            text='Тестовый комментарий'
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.post.author)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_page_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list', kwargs={'slug': self.post.group.slug}):
                'posts/group_list.html',
            reverse('posts:profile', kwargs={'username': self.post.author}):
                'posts/profile.html',
            reverse('posts:post_detail', kwargs={'post_id': self.post.pk}):
                'posts/post_detail.html',
            reverse('posts:post_create'):
                'posts/create_post.html',
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk}):
                'posts/create_post.html',
        }
        for namespace_name, template in templates_page_names.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(namespace_name)
                self.assertTemplateUsed(response, template)

    def test_index_pages_show_correct_context(self):
        """Шаблон index содержит список постов."""
        response = self.authorized_client.get(reverse('posts:index'))
        context = response.context.get('page_obj').object_list[0]
        posts = self.post
        self.assertEqual(context, posts)

    def test_group_list_pages_show_correct_context(self):
        """Шаблон group_list содержит список постов по группам."""
        response = self.authorized_client.get(reverse(
            'posts:group_list',
            kwargs={'slug': self.post.group.slug}
        )
        )
        context = response.context['group']
        group_title = context.title
        group_slug = context.slug
        self.assertEqual(group_title, self.group.title)
        self.assertEqual(group_slug, self.group.slug)

    def test_profile_pages_show_correct_context(self):
        """Шаблон profile содержит список постов по пользователю."""
        response = self.authorized_client.get(reverse(
            'posts:profile',
            kwargs={'username': self.post.author}
        )
        )
        first_object = response.context['page_obj'][0]
        text = first_object.text
        self.assertEqual(
            response.context['author'].username,
            self.post.author.username
        )
        self.assertEqual(text, self.post.text)

    def test_post_detail_pages_show_correct_context(self):
        """Шаблон post_detail содержит один пост по id
        и комментарий к нему."""
        response = self.authorized_client.get(reverse(
            'posts:post_detail',
            kwargs={'post_id': self.post.pk}
        )
        )
        context = response.context['post']
        post_id = context.id
        self.assertEqual(post_id, self.post.id)
        context_comment = response.context['comments'][0]
        text_comment = context_comment.text
        self.assertEqual(text_comment, self.comment.text)

    def test_post_edit_page_show_correct_context(self):
        """Шаблон create_post сформирован с правильным
           контекстом при редактировании поста."""
        response = self.authorized_client.get(reverse(
            'posts:post_edit',
            kwargs={'post_id': self.post.pk}
        )
        )
        form_fields = {
            'text': forms.fields.CharField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)
        context = response.context['is_edit']
        self.assertEqual(context, True)
        post = response.context['post']
        self.assertEqual(post.text, self.post.text)

    def test_post_create_page_show_correct_context(self):
        """Шаблон create_post сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_post_show_on_template(self):
        """Шаблоны index, group_list и profile содержат пост."""
        response_index = self.authorized_client.get(reverse('posts:index'))
        context_index = response_index.context.get('page_obj').object_list[0]
        self.assertEqual(context_index, self.post)
        response_group = self.authorized_client.get(reverse(
            'posts:group_list',
            kwargs={'slug': self.post.group.slug}
        )
        )
        context_group = response_group.context.get('page_obj').object_list[0]
        self.assertEqual(context_group, self.post)
        response_profile = self.authorized_client.get(reverse(
            'posts:profile',
            kwargs={'username': self.post.author}
        )
        )
        context_profile = (
            response_profile.context.get('page_obj').object_list[0]
        )
        self.assertEqual(context_profile, self.post)

    def test_image_show_on_template(self):
        """Картинка поста передается в контекст profile, index, group_posts,
        post_detail."""
        response_profile = self.authorized_client.get(reverse(
            'posts:profile',
            kwargs={'username': self.post.author}
        )
        )
        first_object_profile = response_profile.context['page_obj'][0]
        profile_post_image = first_object_profile.image
        self.assertEqual(profile_post_image, self.post.image)
        response_index = self.authorized_client.get(reverse('posts:index'))
        first_object_index = response_index.context['page_obj'][0]
        index_post_image = first_object_index.image
        self.assertEqual(index_post_image, self.post.image)
        response_group = self.authorized_client.get(reverse(
            'posts:group_list',
            kwargs={'slug': self.post.group.slug}
        )
        )
        first_object_group = response_group.context['page_obj'][0]
        group_post_image = first_object_group.image
        self.assertEqual(group_post_image, self.post.image)
        response_post_detail = self.authorized_client.get(reverse(
            'posts:post_detail',
            kwargs={'post_id': self.post.pk}
        )
        )
        first_object_post_detail = response_post_detail.context['post']
        post_detail_image = first_object_post_detail.image
        self.assertEqual(post_detail_image, self.post.image)

    def test_post_another_group(self):
        """Пост попал в правильную группу."""
        response = self.authorized_client.get(reverse(
            'posts:group_list',
            kwargs={'slug': self.post.group.slug}
        )
        )
        context = response.context['page_obj'][0]
        context_text = context.text
        self.assertEqual(context_text, self.post.text)

    def test_template_cache(self):
        """Проверка кэширования index."""
        response_content = self.authorized_client.get(
            reverse('posts:index')
        ).content
        self.post.delete()
        response_del_content = self.authorized_client.get(
            reverse('posts:index')
        ).content
        self.assertEqual(response_content, response_del_content)
        cache.clear()
        response_true_del_content = self.authorized_client.get(
            reverse('posts:index')
        ).content
        self.assertNotEqual(response_content, response_true_del_content)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='user')
        cls.group = Group.objects.create(
            title='Название группы',
            slug='test-slug',
        )
        cls.post = []
        for i in range(13):
            cls.post.append(Post(
                text=f'Тестовый пост {i}',
                author=cls.user,
                group=cls.group
            )
            )
        Post.objects.bulk_create(cls.post)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_first_page_contains_ten_records(self):
        """Первая страница index, group_list и profile содержит 10 постов."""
        urls = {
            reverse('posts:index'): 'index',
            reverse(
                'posts:group_list',
                kwargs={'slug': self.group.slug}
            ):
                'posts:group_list',
            reverse(
                'posts:profile',
                kwargs={'username': self.user.username}
            ):
                'posts:profile'
        }
        for url in urls.keys():
            response = self.authorized_client.get(url)
            self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_page_contains_three_posts(self):
        """Вторая страница index, group_list и profile содержит 3 поста."""
        urls = {
            reverse('posts:index') + '?page=2': 'index',
            reverse(
                'posts:group_list',
                kwargs={'slug': self.group.slug}
            ) + '?page=2': 'posts:group_list',
            reverse(
                'posts:profile',
                kwargs={'username': self.user.username}
            ) + '?page=2': 'posts:profile'
        }
        for url in urls.keys():
            response = self.authorized_client.get(url)
            self.assertEqual(len(response.context['page_obj']), 3)


class FollowViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.follower = User.objects.create_user(username='follower')
        cls.following = User.objects.create_user(username='following')
        cls.post = Post.objects.create(
            author=cls.following,
            text='Тестовая запись для ленты подписок'
        )

    def setUp(self):
        self.autorized_client_follower = Client()
        self.autorized_client_following = Client()
        self.autorized_client_follower.force_login(self.follower)
        self.autorized_client_following.force_login(self.following)

    def test_follow_unfollow_auth(self):
        """Авторизованный пользователь может
        подписываться на авторов и отписываться."""
        follower_count = Follow.objects.count()
        self.autorized_client_follower.get(reverse(
            'posts:profile_follow',
            kwargs={'username': self.following.username}
        )
        )
        self.assertEqual(Follow.objects.count(), follower_count + 1)
        self.autorized_client_follower.get(reverse(
            'posts:profile_unfollow',
            kwargs={'username': self.following.username}
        )
        )
        self.assertEqual(Follow.objects.count(), follower_count)

    def test_follow_index(self):
        """Новая запись пользователя появляется в ленте тех,
        кто на него подписан и не появляется в ленте тех, кто не подписан."""
        Follow.objects.create(user=self.follower, author=self.following)
        response_follower = self.autorized_client_follower.get(
            reverse('posts:follow_index')
        )
        text_sub = response_follower.context['page_obj'][0].text
        self.assertEqual(text_sub, self.post.text)
        response_following = self.autorized_client_following.get(
            reverse('posts:follow_index')
        )
        self.assertNotContains(response_following, self.post.text)
