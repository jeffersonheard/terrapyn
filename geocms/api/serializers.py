from rest_framework import serializers, fields
from mezzanine.pages.models import Page

from rest_framework_gis import fields as gis_fields
# from rest_framework_hstore import fields as hstore_fields

from terrapyn.geocms import models

class PageShortSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='terrapyn-page-detail', lookup_field='slug')

    class Meta:
        model = Page
        fields = (
            'url',
            'title',
            'titles',
        )

class ResourceMetadataSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ResourceMetadata

class DataResourceSerializer(serializers.ModelSerializer):
    metadata = ResourceMetadataSerializer(many=True, required=False, read_only=True)
    #driver_config = hstore_fields.HStoreField(required=False)
    #metadata_properties = hstore_fields.HStoreField(required=False)
    last_change = fields.DateTimeField(required=False, read_only=True)
    last_refresh = fields.DateTimeField(required=False, read_only=True)
    next_refresh = fields.DateTimeField(required=False, read_only=True)
    bounding_box = gis_fields.GeometryField(required=False, read_only=True)
    import_log = fields.CharField(required=False, read_only=True)
    url = serializers.HyperlinkedIdentityField(view_name='data-resource-detail', lookup_field='slug')
    associated_pages = PageShortSerializer(many=True)

    class Meta:
        model = models.DataResource
        fields = (
            'url',
            'title',
            'slug',
            'metadata',
            'original_file',
            'resource_url',
            'metadata_url',
            'metadata_xml',
            #'driver_config',
            #'metadata_properties',
            'last_change',
            'last_refresh',
            'next_refresh',
            'refresh_every',
            'md5sum',
            'bounding_box',
            'import_log',
            'id',
            'associated_pages',
        )

class StyleSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='style-detail', lookup_field='slug')
    associated_pages = PageShortSerializer(many=True)

    class Meta:
        model = models.Style
        fields = (
            'url',
            'title',
            'slug',
            'legend',
            'stylesheet',
            'id',
            'associated_pages',
        )


class LayerSerializer(serializers.ModelSerializer):
    data_resource = serializers.SlugRelatedField(slug_field='slug', queryset=models.DataResource.objects.all())
    default_style = serializers.SlugRelatedField(slug_field='slug', queryset=models.Style.objects.all())
    styles = serializers.SlugRelatedField(many=True, slug_field='slug', queryset=models.Style.objects.all())
    url = serializers.HyperlinkedIdentityField(view_name='layer-detail', lookup_field='slug')
    associated_pages = PageShortSerializer(many=True)

    class Meta:
        model = models.Layer
        fields = (
            'url',
            'title',
            'slug',
            'data_resource',
            'default_style',
            'default_class',
            'styles',
            'id',
            'associated_pages'
        )


# class DirectoryEntryShortSerializer(serializers.ModelSerializer):
#     url = serializers.HyperlinkedIdentityField(view_name='directoryentry-detail', lookup_field='slug')
#
#     class Meta:
#         model = models.DirectoryEntry
#         fields = (
#             'url',
#             'title',
#         )
#
#
# class DirectoryEntrySerializer(serializers.ModelSerializer):
#     children = DirectoryEntryShortSerializer(many=True)
#     parent = serializers.HyperlinkedRelatedField(read_only=True, view_name='directoryentry-detail', lookup_field='slug')
#     resources = serializers.HyperlinkedRelatedField(many=True, read_only=True, view_name='resource-page', lookup_field='slug')
#     styles = serializers.HyperlinkedRelatedField(many=True, queryset=models.Style.objects.all(), view_name='style-page', lookup_field='slug')
#     layers = serializers.HyperlinkedRelatedField(many=True, queryset=models.Layer.objects.all(), view_name='layer-page', lookup_field='slug')
#     url = serializers.HyperlinkedIdentityField(view_name='directoryentry-detail', lookup_field='slug')
#
#     class Meta:
#         model = models.DirectoryEntry
#         fields = (
#             'url',
#             'title',
#             'slug',
#             'children',
#             'parent',
#             'resources',
#             'styles',
#             'layers',
#         )





class LayerShortSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='layer-page', lookup_field='slug')

    class Meta:
        model = Page
        fields = (
            'url',
            'title',
            'titles',
        )


class ResourceShortSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='resource-page', lookup_field='slug')

    class Meta:
        model = Page
        fields = (
            'url',
            'title',
            'titles',
        )


class StyleShortSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='style-page', lookup_field='slug')

    class Meta:
        model = Page
        fields = (
            'url',
            'title',
            'titles',
        )


class LayerCollectionShortSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='layercollection-page', lookup_field='slug')

    class Meta:
        model = Page
        fields = (
            'url',
            'title',
            'titles',
        )



class PageSerializer(serializers.ModelSerializer):
    children = PageShortSerializer(many=True)
    parent = serializers.HyperlinkedRelatedField(read_only=True, view_name='terrapyn-page-detail', lookup_field='slug')
    data_resources = ResourceShortSerializer(many=True)
    layer_collections = LayerCollectionShortSerializer(many=True)
    styles = StyleShortSerializer(many=True)
    layers = LayerShortSerializer(many=True)
    url = serializers.HyperlinkedIdentityField(view_name='terrapyn-page-detail', lookup_field='slug')

    class Meta:
        model = Page
        fields = (
            'url',
            'title',
            'slug',
            'children',
            'parent',
            'data_resources',
            'styles',
            'layers',
            'layer_collections',
        )


class LayerCollectionSerializer(serializers.ModelSerializer):
    associated_pages = PageShortSerializer(many=True)
    url = serializers.HyperlinkedIdentityField(view_name='style-detail', lookup_field='slug')

    class Meta:
        model = models.Style
        fields = (
            'url',
            'title',
            'slug',
            'legend',
            'stylesheet',
            'id',
            'associated_pages',
        )