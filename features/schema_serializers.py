
from rest_framework import serializers
from .schema import *

class GeometryFieldSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100, default='geometry')
    kind = serializers.ChoiceField(required=True, choices=(
        ('POINT','Point'),
        ('LINESTRING', 'LineString'),
        ('POLYGON','Polygon'),
        ('MULTIPOINT','MultiPoint'),
        ('MULTILINESTRING', 'MultiLineString'),
        ('MULTIPOLYGON','MultiPolygon'),
        ('GEOMETRY','Generic Geometry'),
        ('GEOMETRYCOLLECTION','Generic Geometry Collection'),
    ))
    srid = serializers.IntegerField(default=4326)
    index = serializers.BooleanField(default=True)

    def create(self, validated_data):
        return GeometryField(**validated_data)

    def update(self, instance, validated_data):
        for k, v in validated_data.items():
            setattr(instance, k, v)


class SimpleFieldSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100, required=True)
    kind = serializers.ChoiceField(required=True, choices=(
        ('int','Integer'),
        ('float', 'Float'),
        ('text', 'Text'),
        ('date', 'Date'),
        ('json', 'JSON'),
        ('hstore', 'Key Value Pairs'),
    ))
    index = serializers.BooleanField(default=False)
    unique = serializers.BooleanField(default=False)

    def create(self, validated_data):
        return SimpleField(**validated_data)

    def update(self, instance, validated_data):
        for k, v in validated_data.items():
            setattr(instance, k, v)


class FieldOrderingSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100, required=True)
    relative_order = serializers.IntegerField(required=True)

    def create(self, validated_data):
        return FieldOrdering(**validated_data)

    def update(self, instance, validated_data):
        for k, v in validated_data.items():
            setattr(instance, k, v)


class ForeignKeySerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100, required=True)
    rel_name = serializers.CharField(max_length=100, required=True)
    rel_field = serializers.CharField(max_length=100, allow_null=True, required=False)
    index = serializers.BooleanField(default=True)

    def create(self, validated_data):
        return ForeignKey(**validated_data)

    def update(self, instance, validated_data):
        for k, v in validated_data.items():
            setattr(instance, k, v)


class ManyToManySerializer(serializers.Serializer):
    rel_name = serializers.CharField(max_length=100, required=True)
    rel_field = serializers.CharField(max_length=100, allow_null=True, required=False)
    through = serializers.CharField(max_length=100, allow_null=True, required=False)
    through_from_key_name = serializers.CharField(max_length=100, allow_null=True, required=False)
    through_to_key_name = serializers.CharField(max_length=100, allow_null=True, required=False)

    def create(self, validated_data):
        return ManyToMany(**validated_data)

    def update(self, instance, validated_data):
        for k, v in validated_data.items():
            setattr(instance, k, v)


class StructuredDatasetSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100, required=True)
    primary_key = serializers.CharField(max_length=100, allow_null=True, required=False)
    geometry_fields = GeometryFieldSerializer(many=True)
    simple_fields = SimpleFieldSerializer(many=True)
    foreign_keys = ForeignKeySerializer(many=True)
    relationships = ManyToManySerializer(many=True)
    ordering = FieldOrderingSerializer(many=True)

    def create(self, validated_data):
        geometry_fields = GeometryFieldSerializer(many=True, data=validated_data.pop('geometry_fields'))
        simple_fields = SimpleFieldSerializer(many=True, data=validated_data.pop('simple_fields'))
        foreign_keys = ForeignKeySerializer(many=True, data=validated_data.pop('foreign_keys'))
        relationships = ManyToManySerializer(many=True, data=validated_data.pop('relationships'))
        ordering = FieldOrderingSerializer(many=True, data=validated_data.pop('ordering'))

        assert geometry_fields.is_valid()
        assert simple_fields.is_valid()
        assert foreign_keys.is_valid()
        assert relationships.is_valid()
        assert ordering.is_valid()

        return StructuredDataset(
            name = validated_data['name'],
            primary_key=validated_data['primary_key'],
            geometry_fields=geometry_fields.save(),
            simple_fields=simple_fields.save(),
            foreign_keys=foreign_keys.save(),
            relationships=relationships.save(),
            ordering=ordering.save()
        )

    def update(self, instance, validated_data):
        for k, v in validated_data.items():
            setattr(instance, k, v)



# def testme():
#     dataset1 = StructuredDataset(
#         "sample",
#         geometry_fields=[GeometryField('geometry', 'POINT')],
#         simple_fields=[
#             SimpleField('OGC_FID', 'int'),
#             SimpleField('name', 'text'),
#         ],
#     )
#     dataset2 = StructuredDataset(
#         'sample_foreign',
#         simple_fields=[SimpleField('name2', 'text')],
#         foreign_keys=[ForeignKey('sample', 'sample_id', 'OGC_FID')],
#         primary_key='id'
#     )
#     dataset3 = StructuredDataset(
#         'sample_many',
#         simple_fields=[SimpleField('name3', 'text')],
#         foreign_keys=[],
#         relationships=[ManyToMany('sample')],
#         primary_key='id'
#     )
#
#     print dataset1.all
#     print dataset2.all
#     print dataset3.all
#
#     from rest_framework.renderers import JSONRenderer
#     from rest_framework.parsers import JSONParser
#     from django.utils.six import BytesIO
#     js = JSONRenderer().render(StructuredDatasetSerializer(many=True, instance=[dataset1,dataset2,dataset3]).data)
#     thaw = StructuredDatasetSerializer(many=True, data=JSONParser().parse(BytesIO(js)))
#     print thaw.is_valid()
#
#     for x in thaw.save():
#         print x.to_postgres()