from django.contrib.gis.db import models
from django.conf import settings
from django_hstore.fields import DictionaryField
from mezzanine.core.models import Displayable
from timedelta import TimedeltaField
from osgeo import osr
from django.core.urlresolvers import reverse

from terrapyn.geocms.drivers import get_driver


class DataResource(Displayable):
    """Represents a file that has been uploaded to Geoanalytics for representation"""
    original_file = models.FileField(upload_to='geographica_resources', null=True, blank=True)
    resource_file = models.FileField(upload_to='geographica_resources', null=True, blank=True)
    resource_url = models.URLField(null=True, blank=True)
    metadata_url = models.URLField(null=True, blank=True)
    metadata_xml = models.TextField(null=True, blank=True)
    driver_config = DictionaryField(null=True, blank=True)
    metadata_properties = DictionaryField(null=True, blank=True)
    last_change = models.DateTimeField(null=True, blank=True, auto_now=True)
    last_refresh = models.DateTimeField(null=True, blank=True) # updates happen only to geocms that were not uploaded by the user.
    next_refresh = models.DateTimeField(null=True, blank=True, db_index=True) # will be populated every time the update manager runs
    refresh_every = TimedeltaField(null=True, blank=True)
    md5sum = models.CharField(max_length=64, blank=True, null=True) # the unique md5 sum of the data
    bounding_box = models.PolygonField(null=True, srid=4326, blank=True)
    import_log = models.TextField(null=True, blank=True)
    associated_pages = models.ManyToManyField("pages.Page", blank=True, null=True, related_name='data_resources')

    driver = models.CharField(
        default='terrapyn.geocms.drivers.spatialite',
        max_length=255,
        null=False,
        blank=False,
        choices=getattr(settings, 'INSTALLED_DATARESOURCE_DRIVERS', (
            ('terrapyn.geocms.drivers.spatialite', 'Spatialite (universal vector)'),
            ('terrapyn.geocms.drivers.shapefile', 'Shapefile'),
            ('terrapyn.geocms.drivers.geotiff', 'GeoTIFF'),
            ('terrapyn.geocms.drivers.postgis', 'PostGIS'),
            ('terrapyn.geocms.drivers.kmz', 'Google Earth KMZ'),
            ('terrapyn.geocms.drivers.ogr', 'OGR DataSource'),
        )))

    big = models.BooleanField(default=False, help_text='Set this to be true if the dataset is more than 100MB') # causes certain drivers to optimize for datasets larger than memory

    def get_absolute_url(self):
        return reverse('resource-page', kwargs={'slug': self.slug})

    @property
    def srs(self):
        if not self.metadata.native_srs:
            self.driver_instance.compute_spatial_metadata()
        srs = osr.SpatialReference()
        srs.ImportFromProj4(self.metadata.native_srs.encode('ascii'))
        return srs

    @property
    def driver_instance(self):
        if not hasattr(self, '_driver_instance'):
            self._driver_instance = get_driver(self.driver)(self)
        return self._driver_instance

    def __unicode__(self):
        return self.title

    class Meta:
        permissions = (
            ('view_dataresource', "View data resource"),  # to add beyond the default
        )



class ResourceMetadata(models.Model):
    resource = models.ForeignKey(DataResource, related_name='metadata')
    table = models.TextField()
    last_change = models.DateTimeField(null=True, blank=True, auto_now=True)
    native_bounding_box = models.PolygonField(null=True, blank=True)
    bounding_box = models.PolygonField(null=True, srid=4326, blank=True)
    three_d = models.BooleanField(default=False)
    native_srs = models.TextField(null=True, blank=True)

    def __unicode__(self):
        return str(self.resource) + "metadata object"

    class Meta:
        permissions = (
            ('view_metadata', "View data resource metadata"),
        )


class Style(Displayable):
    legend = models.ImageField(upload_to='terrapyn.styles.legends', width_field='legend_width', height_field='legend_height', null=True, blank=True)
    legend_width = models.IntegerField(null=True, blank=True)
    legend_height = models.IntegerField(null=True, blank=True)
    stylesheet = models.TextField()
    associated_pages = models.ManyToManyField("pages.Page", blank=True, null=True, related_name='styles')

    def __unicode__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('style-page', kwargs={'slug': self.slug})

    class Meta:
        permissions = (
            ('view_style', "View stylesheet"),
        )


class Layer(Displayable):
    data_resource = models.ForeignKey(DataResource)
    default_style = models.ForeignKey(Style, related_name='default_for_layer')
    default_class = models.CharField(max_length=255, default='default')
    styles = models.ManyToManyField(Style, null=True, blank=True)
    associated_pages = models.ManyToManyField("pages.Page", blank=True, null=True, related_name='layers')

    def __unicode__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('layer-page', kwargs={'slug': self.slug})

    class Meta:
        permissions = (
            ('view_layer', "View layer"),
        )


class LayerOrdering(models.Model):
    lyaer_collection = models.ForeignKey("geocms.LayerCollection")
    layer = models.ForeignKey(Layer)
    order = models.IntegerField()

    class Meta:
        ordering = ('order',)


class LayerCollection(Displayable):
    layers = models.ManyToManyField(Layer, through=LayerOrdering)
    associated_pages = models.ManyToManyField("pages.Page", blank=True, null=True, related_name='layer_collections')

    class Meta:
        permissions = (
            ('view_layercollection', "View layer collection"),
        )
