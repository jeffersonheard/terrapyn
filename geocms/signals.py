from django.db.models.signals import post_save, pre_delete, pre_save
import logging
import datetime
from django.utils.timezone import utc

from terrapyn.geocms.cache import CacheManager
from .models import DataResource, Style, Layer
from . import dispatch

_log = logging.getLogger('terrapyn.driver_messages')


def dataresource_compute_metadata_post_create(sender, instance, created=False, *args, **kwargs):
    if created:
        ds = instance.driver_instance  # force computation of resource metadata

compute_metadata = post_save.connect(dataresource_compute_metadata_post_create, DataResource, weak=False)


def delete_caches(sender, instance, **kwargs):
    _log.debug('Deleting caches for {0}'.format(instance.title))

    if isinstance(instance, Style):
        CacheManager.get().remove_caches_for_style(instance.slug)
    elif isinstance(instance, Layer):
        CacheManager.get().remove_caches_for_layer(instance.slug)

def delete_data(sender, instance, **kwargs):
    _log.debug('Deleting data for {0}'.format(instance.title))
    try:
        if instance.original_file:
            instance.original_file.delete()
        if instance.resource_file:
            instance.resource_file.delete()
    except:
        _log.error("Cannot delete data for {0}".format(instance.title))

def dataresource_pre_save(sender, instance, *args, **kwargs):
    if 'created' in kwargs and kwargs['created']:
        instance.last_refresh = instance.last_refresh or datetime.datetime.utcnow().replace(tzinfo=utc)
        if instance.refresh_every:
            instance.next_refresh = instance.last_refresh + instance.refresh_every


def dataresource_post_save(sender, instance, created=False, *args, **kwargs):
    if created and  not instance.metadata.all().exists():
        instance.driver_instance.compute_spatial_metadata()



def shave_tile_caches(sender, instance, bbox, *args, **kwargs):
     CacheManager.get().shave_caches(instance, bbox)


def trim_tile_caches(sender, instance, *args, **kwargs):
    if sender is Style:
        CacheManager.get().remove_caches_for_style(instance)
    elif sender is Layer:
        CacheManager.get().remove_caches_for_layer(instance)

pre_save.connect(dataresource_pre_save, sender=DataResource, weak=False)
post_save.connect(dataresource_post_save, sender=DataResource, weak=False)

dispatch.features_updated.connect(shave_tile_caches, weak=False)
dispatch.features_created.connect(shave_tile_caches, weak=False)
dispatch.features_deleted.connect(shave_tile_caches, weak=False)

post_save.connect(trim_tile_caches, sender=Style, weak=False)
pre_delete.connect(trim_tile_caches, sender=DataResource, weak=False)
pre_delete.connect(trim_tile_caches, sender=Style, weak=False)
pre_delete.connect(trim_tile_caches, sender=Layer, weak=False)

pre_delete.connect(delete_data, sender=DataResource, weak=False)
pre_delete.connect(delete_caches, sender=Layer, weak=False)
pre_delete.connect(delete_caches, sender=Style, weak=False)

