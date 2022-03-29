from django import forms

from .models import Comment, Post


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')
        labels = {
            'text': 'Текст',
            'group': 'Группа',
            'image': 'Картинка'
        }
        help_texts = {
            'text': 'Текст нового поста',
            'group': 'Группа, к которой будет относиться пост',
            'image': 'Картинка поста'
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = {'text'}
        labels = {'text': 'Текст'}
        help_texts = {'text': 'Текст комментария'}
