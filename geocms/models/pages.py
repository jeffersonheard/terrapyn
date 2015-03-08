import datetime
from logging import getLogger
import json

from django.contrib.auth.models import User, Group
from django.db.models.signals import post_save
from django.contrib.gis.db import models
from django.utils.timezone import utc
from mezzanine.pages.models import Page
from mezzanine.core.models import RichText
from mezzanine.conf import settings as s
from timedelta.fields import TimedeltaField
import sh
import os
from osgeo import osr
import importlib

_log = getLogger('terrapyn.driver_messages')

def get_user(request):
    """authorize user based on API key if it was passed, otherwise just use the request's user.

    :param request:
    :return: django.contrib.auth.User
    """
    if isinstance(request, User):
        return request

    from tastypie.models import ApiKey
    if isinstance(request, basestring):
        try:
            return User.objects.get(username=request)
        except:
            return User.objects.get(email=request)
    elif isinstance(request, int):
        return User.objects.get(pk=request)

    elif 'api_key' in request.REQUEST:
        api_key = ApiKey.objects.get(key=request.REQUEST['api_key'])
        return api_key.user
    elif request.user.is_authenticated():
        return User.objects.get(pk=request.user.pk)
    else:
        return request.user


class DirectoryEntry(Page):
    """Maintains an ordered catalog of data.  These pages are rendered specially but otherwise are not special."""

    class Meta:
        ordering = ['title']

    @property
    def siblings(self):
        if self.parent:
            return set(self.parent.children.all()) - {self}
        else:
            return set()

    @classmethod
    def ensure_page(cls, *titles, **kwargs):
        parent = kwargs.get('parent', None)
        child = kwargs.get('child', None)
        if child:
            del kwargs['child']
        if parent:
            del kwargs['parent']

        if not cls.objects.filter(title=titles[0], parent=parent).exists():
            p = cls.objects.create(title=titles[0], parent=parent, **kwargs)
        else:
            p = cls.objects.get(title=titles[0], parent=parent)

        for title in titles[1:]:
            if not cls.objects.filter(title=title, parent=p).exists():
                p = cls.objects.create(title=title, parent=p, **kwargs)
            else:
                p = cls.objects.get(title=title, parent=p)

        if child:
            child.parent = p
            child.save()

        return p

    def can_add(self, request):
        return request.user.is_authenticated()

    def can_change(self, request):
        return request.user.is_authenticated()

    def can_delete(self, request):
        return request.user.is_authenticated()


def set_permissions_for_new_catalog_page(sender, instance, created, *args, **kwargs):
    if instance.parent and created:
        instance.copy_permissions_from_parent()

set_permissions = post_save.connect(set_permissions_for_new_catalog_page, sender=DirectoryEntry, weak=False)




