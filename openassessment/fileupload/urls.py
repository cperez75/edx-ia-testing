""" Urls for fileupload app. """

from django.urls import re_path

from ieia.fileupload import views_django_storage, views_filesystem

urlpatterns = [
    re_path(r'^django/(?P<key>.+)/$', views_django_storage.django_storage,
            name='ieia-django-storage'),
    re_path(r'^(?P<key>.+)/$', views_filesystem.filesystem_storage,
            name='ieia-filesystem-storage'),
]
