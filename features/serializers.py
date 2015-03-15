from rest_framework import serializers
from . import models

class FieldOrderingSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.FieldOrdering


class ForeignKeySerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ForeignKey


class GeometryFieldSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.GeometryField


class ManyToManySerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ManyToMany


class SimpleFieldSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.SimpleField


class StructuredDatasetSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedRelatedField(view_name='structured-dataset-detail')
    simple_fields = SimpleFieldSerializer(many=True)
    geometry_fields = GeometryFieldSerializer(many=True)
    foreign_keys = ForeignKeySerializer(many=True)
    relationships = ManyToManySerializer(many=True)
    field_order = FieldOrderingSerializer(many=True)

    class Meta:
        model = models.StructuredDataset
        fields = (
            'id',
            'url',
            'name',
            'primary_key',
            'simple_fields',
            'foreign_keys',
            'relationships',
            'field_order',
        )

