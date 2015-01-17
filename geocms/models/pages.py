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


class PagePermissionsMixin(models.Model):
    owner = models.ForeignKey(User, related_name='owned_%(app_label)s_%(class)s', null=True)
    public = models.BooleanField(default=True)
    edit_users = models.ManyToManyField(User, related_name='editable_%(app_label)s_%(class)s', null=True, blank=True)
    view_users = models.ManyToManyField(User, related_name='viewable_%(app_label)s_%(class)s', null=True, blank=True)
    edit_groups = models.ManyToManyField(Group, related_name='group_editable_%(app_label)s_%(class)s', null=True, blank=True)
    view_groups = models.ManyToManyField(Group, related_name='group_viewable_%(app_label)s_%(class)s', null=True, blank=True)

    def can_add(self, request):
        return self.can_change(request)

    def can_delete(self, request):
        return self.can_change(request)

    def can_change(self, request):
        user = get_user(request)

        if user.is_authenticated():
            if user.is_superuser:
                ret = True
            elif user.pk == self.owner.pk:
                ret = True
            else:
                if self.edit_users.filter(pk=user.pk).exists():
                    ret = True
                elif self.edit_groups.filter(pk__in=[g.pk for g in user.groups.all()]):
                    ret = True
                else:
                    ret =  False
        else:
            ret = False

        return ret

    def can_view(self, request):
        user = get_user(request)

        if self.public or not self.owner:
            return True

        if user.is_authenticated():
            if user.is_superuser:
                ret = True
            elif user.pk == self.owner.pk:
                ret = True
            else:
                if self.view_users.filter(pk=user.pk).exists():
                    ret = True
                elif self.view_groups.filter(pk__in=[g.pk for g in user.groups.all()]):
                    ret = True
                else:
                    ret = False
        else:
            ret = False

        return ret

    def copy_permissions_to_children(self, recurse=False):
        # pedantically implemented.  should use set logic to minimize changes, but ptobably not important
        for child in self.children.all():
            if isinstance(child, PagePermissionsMixin):
                child.edit_users = [u for u in self.edit_users.all()]
                child.view_users = [u for u in self.view_users.all()]
                child.edit_groups = [g for g in self.edit_groups.all()]
                child.view_groups = [g for g in self.view_groups.all()]
                child.publicly_viewable = self.publicly_viewable
                child.owner = self.owner
                child.save()

                if recurse:
                    child.copy_permissions_to_children(recurse=True)


    def copy_permissions_from_parent(self):
        if self.parent:
            parent = self.parent.get_content_model()
            if isinstance(parent, PagePermissionsMixin):
                self.view_groups = [g for g in self.parent.view_groups.all()]
                self.edit_groups = [g for g in self.parent.edit_groups.all()]
                self.view_users = [u for u in self.parent.view_users.all()]
                self.edit_users = [u for u in self.parent.edit_users.all()]
                self.public = self.parent.public
                self.owner = self.parent.owner
                self.save()

    class Meta:
        abstract = True


class CatalogPage(Page, PagePermissionsMixin):
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
        return PagePermissionsMixin.can_add(self, request)

    def can_change(self, request):
        return PagePermissionsMixin.can_change(self, request)

    def can_delete(self, request):
        return PagePermissionsMixin.can_delete(self, request)


def set_permissions_for_new_catalog_page(sender, instance, created, *args, **kwargs):
    if instance.parent and created:
        instance.copy_permissions_from_parent()

set_permissions = post_save.connect(set_permissions_for_new_catalog_page, sender=CatalogPage, weak=False)




