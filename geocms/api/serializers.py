from rest_framework import serializers, fields

from rest_framework_gis import fields as gis_fields
from rest_framework_hstore import fields as hstore_fields

from terrapyn.geocms import models


class ResourceMetadataSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ResourceMetadata

class DataResourceSerializer(serializers.ModelSerializer):
    metadata = ResourceMetadataSerializer(many=True, required=False, read_only=True)
    driver_config = hstore_fields.HStoreField(required=False)
    metadata_properties = hstore_fields.HStoreField(required=False)
    last_change = fields.DateTimeField(required=False, read_only=True)
    last_refresh = fields.DateTimeField(required=False, read_only=True)
    next_refresh = fields.DateTimeField(required=False, read_only=True)
    bounding_box = gis_fields.GeometryField(required=False, read_only=True)
    import_log = fields.CharField(required=False, read_only=True)

    class Meta:
        model = models.DataResource
        fields = (
            'title',
            'slug',
            'metadata',
            'original_file',
            'resource_url',
            'metadata_url',
            'metadata_xml',
            'driver_config',
            'metadata_properties',
            'last_change',
            'last_refresh',
            'next_refresh',
            'refresh_every',
            'md5sum',
            'bounding_box',
            'import_log',
            'id'
        )

class StyleSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Style
        fields = (
            'title',
            'slug',
            'legend',
            'stylesheet',
            'id'
        )

class LayerSerializer(serializers.ModelSerializer):
    data_resource = serializers.SlugRelatedField(slug_field='slug')
    default_style = serializers.SlugRelatedField(slug_field='slug')
    styles = serializers.SlugRelatedField(many=True, slug_field='slug')

    class Meta:
        model = models.Layer
        fields = (
            'title',
            'slug',
            'data_resource',
            'default_style',
            'default_class',
            'styles',
            'id'
        )