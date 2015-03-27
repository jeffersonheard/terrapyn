from terrapyn.features import models
from functools import partial

class StructuredFeatureCollection(object):
    def __init__(self, ds, serializer):
        self.ds = ds
        self.serializer = serializer

class GeoJSONSerializer(object):
    def __init__(self, ds):
        self.ds = ds
        self.columns = tuple(enumerate(ds))
        self.lookup = {k.name: i for i, k in self.columns}
        self.primary_key_is_id = self.ds.primary_key == 'id'

    def serialize(self, cursor):
        return self.serialize_secondpass(self.serialize_firstpass(cursor))

    def serialize_secondpass(self, record):
        pass

    def serialize_firstpass(self, cursor):
        if self.ds.primary_geometry_field:
            return [self.serialize_feature_firstpass(r) for r in cursor.fetchall()]
        else:
            return [self.serialize_record_firstpass(r) for r in cursor.fetchall()]

    def serialize_feature_firstpass(self, values):
        if self.primary_key_is_id:
            primary_key = values[0]
        else:
            key_index= self.lookup[self.ds.primary_key]
            primary_key = self.columns[key_index].extract(values[key_index])

        ret = {
            'type': 'Feature',
            'geometry': None,
            'id': primary_key
        }

        properties = {
            'id': primary_key
        }

        for i, column in self.columns:
            if column.name != self.ds.primary_geometry_field:
                properties[column.name] = column.extract(values[i], primary_key)
            else:
                ret['geometry'] = column.extract(values[i], primary_key)
        ret['properties'] = properties
        return ret

    def serialize_record_firstpass(self, values):
        if self.primary_key_is_id:
            primary_key = values[0]
        else:
            key_index= self.lookup[self.ds.primary_key]
            primary_key = self.columns[key_index].extract(values[key_index])

        ret = {
            'id': primary_key
        }

        for i, column in self.columns:
            ret[column.name] = column.extract(values[i], primary_key)

        return ret
