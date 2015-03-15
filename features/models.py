from django.contrib.gis.db import models
from django.db import connections
from django.db.models import Max, Manager
from django.conf import settings
from django.utils.dateparse import parse_datetime, parse_date, parse_time
import json

from shapely import wkb
from collections import OrderedDict
from django.core.exceptions import ImproperlyConfigured
from django.utils.decorators import method_decorator
from django.db.transaction import atomic
from terrapyn.features.schema import SimpleFeatureSet

__all__ = (
    "GeometryField","SimpleField",'FieldOrdering','ForeignKey','ManyToMany','StructuredDataset'
)

dbms_choices = getattr(settings, 'TERRAPYN_DATABASES', settings.DATABASES).keys()
default_dbms = getattr(settings, 'TERRAPYN_DEFAULT_DATABASE', 'default')

class StructuredDatasetManager(Manager):
    @method_decorator(atomic)
    def create_dataset(self, *fields, **kwargs):
        sds = StructuredDataset.objects.create(**kwargs)

        n = 0
        for field in fields:
            if field.dataset:
                raise ImproperlyConfigured("You must create structureddatasets with brand new fields.")
            field.dataset = sds
            field.save()
            FieldOrdering.objects.create(dataset=sds, name=field.name, relative_order=n)
            n += 1

        sds.create_tables()
        sds.ready()
        return sds


class StructuredDataset(models.Model):
    """
    A model for a FeatureCollection backended by a structured database (currently only POSTGIS).
    """
    OWNER_MODEL = getattr(settings, 'AUTH_USER_MODEL', 'auth.User')

    dbms = models.CharField(max_length=100, choices=dbms_choices, default=default_dbms,
        help_text='The database alias to use. Generally stick with the default.')
    name = models.CharField(max_length=100,
        help_text="The name of the collection, must be a valid SQL name")
    primary_key = models.CharField(max_length=100, default='id',
        help_text='The field name for the primary key of the dataset. For geographic data, this may be OGC_FID')
    owner = models.ForeignKey(OWNER_MODEL, null=True, blank=True)

    objects = StructuredDatasetManager()

    class Meta:
        permissions = (
            ('modify_structuredataset', "Modify records in a structured dataset."),
            ('view_structuredataset', "View records in a structured dataset."),
        )

    @staticmethod
    def create_user(user, dbms):
        with connections[dbms].cursor() as c:
            c.execute('create schema if not exists {0}'.format(user.username))

    @staticmethod
    def delete_user(user, dbms):
        with connections[dbms].cursor() as c:
            c.execute('drop schema if exists {0} cascade'.format(user.username))

    def delete(self, using=None):
        self.drop_tables()
        return super(StructuredDataset).delete(using)

    def __init__(self, *args, **kwargs):
        super(StructuredDataset, self).__init__(*args, **kwargs)
        self.ready()

    def __iter__(self):
        return iter(self._by_field_index)

    def __getitem__(self, item):
        if isinstance(item, int):
            return self._by_field_index[item]
        else:
            return self._by_field_name[item]

    def __cmp__(self, other):
        return cmp(self.name, other.name)

    def get_cursor(self):
        return connections[self.dbms].cursor()

    def ready(self):
        self._by_field_name = {f.name: f for f in self.geometry_fields.all()}
        self._by_field_name.update({f.name: f for f in self.simple_fields.all()})
        self._by_field_name.update({f.name: f for f in self.foreign_keys.all()})
        self._by_field_index = [self._by_field_name[o.name] for o in self.field_order.all()]

    def execute_sql(self, *sql):
        with self.get_cursor() as c:
            for query in sql:
                c.execute(query)
        self.ready()

    @property
    def reverse_keys(self):
        return ForeignKey.objects.filter(rel_dataset=self)

    @property
    def sql_flavor(self):
        return getattr(settings, 'TERRAPYN_SQL_FLAVOR', 'postgis')

    @property
    def schema_name(self):
        if not hasattr(self, '_schema_name'):
            self._schema_name = self.owner.username if self.owner else 'tp_sds'

        return self._schema_name

    @property
    def table_name(self):
        if not hasattr(self, '_table_name'):
            self._table_name = "{0}.{1}".format(self._schema_name, self.name)

        return self._table_name

    def get_create_statements(self):
        fields = [x for x in (x.get_create_table_parameters(self) for x in self) if x is not None]
        fields = ', '.join(fields)

        statements = [
            "create schema if not exists {schema}".format(self.schema_name),
            "create table {name} ({fields});".format(name=self.table_name, fields=fields)
        ]
        map(lambda x: statements.extend(x.get_post_create_table_statements(self)), self)
        map(lambda x: statements.extend(x.get_post_create_table_statements(self)), self.relationships)
        return statements

    def get_drop_statements(self):
        return ['drop table {name} cascade'.format(name=self.table_name)]

    def create_tables(self):
        self.execute_sql(*self.get_create_statements())

    def drop_tables(self):
        for fk in self.foreign_keys.all():  # we have to handle the cascading ourselves.
            fk.dataset.delete()
        self.execute_sql(*self.get_drop_statements())

    @property
    def is_layer(self):
        return self.geometry_fields and (len(self.geometry_fields.all()) > 0)

    def default_ordering(self):
        val = 0

        for f in self.geometry_fields.all():
            yield FieldOrdering(f.name, val)
            val += 1

        for f in self.simple_fields.all():
            yield FieldOrdering(f.name, val)
            val += 1

        for f in self.foreign_keys.all():
            yield FieldOrdering(f.name, val)
            val += 1

    def add(self, field):
        """
        Always use this method to add a field to the dataset after it's been created. Adds a
        field, appending it to the featureset, and initializing it to null.

        :raises: KeyError if the field name is already on the table.
        :param field: An instance of SimpleField, ForeignKey, GeometryField, or ManyToMany
        :return: None
        """
        if field.name not in self._by_field_name:
            max_order = FieldOrdering.objects.filter(dataset=self).aggregate(
                Max('relative_order'))['relative_order__max']

            if field.dataset != self:
                field.dataset=self
                field.save()

            field.add()
            FieldOrdering.objects.create(
                dataset=self,
                name=field.name,
                relative_order=max_order + 1
            )
            self.ready()
        else:
            raise KeyError(field.name)

    def drop(self, name):
        """
        Always use this method to remove a field from the dataset.  Removes the
        named field.

        :raises: KeyError if the field is not found
        :param name:
        :return:
        """
        if name in self._by_field_name:
            field = self[name]
            field.drop()
            field.delete()
            FieldOrdering.objects.get(dataset=self, name=name).delete()
        else:
            raise KeyError(name)

    def empty_feature(self, feature):
        """Get a new empty feature with nulls and defaults populating the fields"""
        raise NotImplemented()

    def add_feature(self, feature):
        """Add a new feature to the database"""
        raise NotImplemented()

    def add_features(self, features):
        """Add a feature collection to the database"""
        raise NotImplemented()

    def delete_feature(self, pk):
        """Delete a feature from the database"""
        with self.get_cursor() as c:
            c.execute("drop from {table_name} where {pk}=%s".format(
                table_name=self.table_name,
                pk=self.primary_key
            ), pk)

    def feature(self, pk=None, record=None, parents=True, ignore_children=None):
        """Get a feature from the database"""
        ignore_children = ignore_children or []
        feature = {}

        if not record:
            select_order = ','.join(field.select_name for field in self)
            sql = "select {select_order} from {table_name} where {pk}=%s".format(
                select_order=select_order,
                table_name=self.table_name
            )
            with self.get_cursor() as c:
                c.execute(sql, pk)
                record = c.fetchone()

        for i, f in enumerate(self):
            if not (parents and isinstance(f, ForeignKey)):
                feature[f.name] = f.extract(record[i])
            else:
                feature[f.name] = f.dataset.feature(record[i], ignore_children=ignore_children + [self])

        for f in self.reverse_keys:
            if f.rel_field:
                key = f.rel_field.name
            else:
                key = f.dataset.primary_key

            feature[f.reverse_name] = f.dataset.features().filter(**{f.name: feature[key]})

        for f in self.relationships.all():
            feature[f.name] = []
            if f.through:
                with f.through.get_cursor() as c:
                    sql = "select {b} from {relation} where {key}=%s".format(
                        relation=f.through.table_name,
                        b=f.rel_dataset.primary_key,
                        key=f.dataset.primary_key
                    )
                    c.execute(sql, pk)
                    for row in c.fetchall():
                        k = row[0]
                        feature[f.name].append(f.rel_dataset.feature(k, parents=False))

        return feature


    def features(self, offset=None, limit=None, *filters):
        """Get a featureset. Similar to a queryset in that you can filter, etc based on it"""
        return SimpleFeatureSet(self, filters, offset=offset, limit=limit)


class FieldOrdering(models.Model):
    dataset = models.ForeignKey(StructuredDataset, related_name='field_order')
    name = models.CharField(max_length=100)
    relative_order = models.PositiveSmallIntegerField()

    def __cmp__(self, other):
        return cmp(self.relative_order, other.relative_order)


class GeometryField(models.Model):
    dataset = models.ForeignKey(StructuredDataset, related_name='geometry_fields')
    name = models.CharField(max_length=100)
    kind = models.CharField(max_length=10, choices=(
        ('Point','Point'),
        ('LineString','LineString'),
        ('Polygon','Polygon'),
        ('MultiPoint','MultiPoint'),
        ('MultiLineString','MultiLineString'),
        ('MultiPolygon','MultiPolygon'),
        ('Geometry','Geometry'),
        ('GeometryCollection','GeometryCollection'),
    ))
    srid = models.IntegerField(default=4326)
    index = models.BooleanField(default=True)
    dimension = models.PositiveSmallIntegerField(default=2)
    not_null = models.BooleanField(default=False)
    default_value = models.GeometryField(null=True, blank=True)

    @property
    def selection_name(self):
        return "ST_AsBinary({name})".format(self.name)

    @property
    def default(self):
        return wkb.loads(self.default_value) if self.default_value else None

    def extract(self, record, missing_data_value=None):
        if record[self.name] or not missing_data_value:
            return wkb.loads(record[self.name]) if record[self.name] else None
        else:
            return missing_data_value


    def get_create_table_parameters(self):
        return None

    def get_post_create_table_statements(self):
        if self.index:
            return [self.get_create_index_postgis()]
        else:
            return []

    def get_add_postgis(self):
        return "SELECT AddGeometryColumn('{table_name}, '{name}', {srid}, '{type}', {dimension})".format(
            table_name=self.dataset.table_name,
            name=self.name,
            srid=self.srid,
            type=self.kind,
            dimension=self.dimension
        )

    def get_drop_postgis(self):
        return "select DropGeometryColumn('{table_name}', '{name}')".format(
            table_name=self.dataset.table_name,
            name=self.name,
        )

    def get_create_index_postgis(self):
        return "CREATE INDEX {table_name}_{name}_idx ON {table_name} USING GIST ( {name} )".format(
            name=self.name,
            table_name=self.dataset.table_name,
        )

    def get_drop_index_postgis(self):
        return "drop index if exists {table_name}_{name}_idx".format(
            name=self.name,
            table_name=self.dataset.table_name
        )

    def add(self):
        sql = [self.get_add_postgis()]
        if self.index:
            sql.append(self.get_create_index_postgis())

        self.dataset.execute_sql(sql)

    def drop(self):
        sql = [self.get_drop_postgis()]
        if self.index:
            sql.append(self.get_drop_index_postgis())

        self.dataset.execute_sql(sql)

    def create_index(self):
        if not self.index:
            self.index=True
            self.save()

        self.dataset.execute_sql(self.get_create_index_postgis())

    def drop_index(self):
        if self.index:
            self.index=False
            self.save()

        self.dataset.execute_sql(self.get_drop_index_postgis())


def get_simplefield_kind_choices():
    kinds = [
        ('int','Integer'),
        ('float','Float'),
        ('text','Text'),
        ('json','JSON'),
        ('date','Date/Time'),
    ]
    kinds.extend(getattr(settings, 'POSTGIS_EXTENDED_TYPES', []))
    return tuple(kinds)

class SimpleField(models.Model):
    dataset = models.ForeignKey(StructuredDataset, related_name='simple_fields')
    name = models.CharField(max_length=100)
    kind = models.CharField(max_length=10, choices=get_simplefield_kind_choices())
    index = models.BooleanField(default=False)
    unique = models.BooleanField(default=False)
    not_null = models.BooleanField(default=False)
    default_value = models.TextField(null=True, blank=True)

    @property
    def selection_name(self):
        return self.name

    def extract(self, record, missing_data_value=None):
        if record[self.name] or not missing_data_value:
            return record[self.name]
        else:
            return missing_data_value

    @property
    def default(self):
        if self.default_value:
            if self.kind == 'int':
                return int(self.default_value)
            elif self.kind == 'date':
                return parse_datetime(self.default_value)
            elif self.kind == 'float':
                return float(self.kind)
            elif self.kind == 'json':
                return json.loads(self.default_value)
            elif self.kind == 'hstore':
                return json.loads(self.default_value)
            else:
                return self.default_value
        else:
            return None

    def get_create_table_parameters(self):
        val = ""

        if self.kind in {'int', 'float', 'text', 'date', 'hstore'}:
            val += "{name} {kind}".format(name=self.name, kind=self.kind)
        elif self.kind == 'json':
            val += "{name} text".format(name=self.name)

        if self.unique:
            val += ' unique'

        return val

    def get_post_create_table_statements(self):
        if self.index:
            return [self.get_create_index_postgis()]
        else:
            return []

    def get_add_postgis(self):
        return "alter table {table_name} add column {name} {kind}".format(
            table_name=self.dataset.table_name,
            name=self.name,
            type=self.kind,
        )

    def get_drop_postgis(self):
        return "alter table {table_name} drop column {name}".format(
            table_name=self.dataset.table_name,
            name=self.name,
        )

    def get_create_index_postgis(self):
        return "CREATE INDEX {table_name}_{name}_idx ON {table_name} ( {name} )".format(
            name=self.name,
            table_name=self.dataset.table_name,
        )

    def get_drop_index_postgis(self):
        return "drop index if exists {table_name}_{name}_idx".format(
            name=self.name,
            table_name=self.dataset.table_name
        )

    def add(self):
        sql = [self.get_add_postgis()]
        if self.index:
            sql.append(self.get_create_index_postgis())

        self.dataset.execute_sql(sql)

    def drop(self):
        sql = [self.get_drop_postgis()]
        if self.index:
            sql.append(self.get_drop_index_postgis())

        self.dataset.execute_sql(sql)

    def create_index(self):
        if not self.index:
            self.index=True
            self.save()

        self.dataset.execute_sql(self.get_create_index_postgis())

    def drop_index(self):
        if self.index:
            self.index=False
            self.save()

        self.dataset.execute_sql(self.get_drop_index_postgis())


class ForeignKey(models.Model):
    dataset = models.ForeignKey(StructuredDataset, related_name='foreign_keys')
    name = models.CharField(max_length=100)
    rel_dataset = models.ForeignKey(StructuredDataset, null=True, blank=True)
    rel_field = models.ForeignKey(SimpleField, null=True, blank=True)
    not_null = models.BooleanField(default=False)
    index = models.BooleanField(default=True)
    reverse_name = models.CharField(max_length=100, null=True, blank=True)

    @property
    def selection_name(self):
        return self.name

    def extract(self, record, missing_data_values=None):
        raise NotImplemented()

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if self.rel_dataset is None:
            self.rel_dataset = self.rel_field.dataset

        if self.name is None:
            self.name = "{rel_name}_{rel_field}".format(rel_name=self.rel_dataset.name, rel_field=self.rel_field.name)

        super(ForeignKey, self).save(force_insert=False, force_update=False, using=None, update_fields=None)

    @property
    def kind(self):
        return self.rel_field.kind if self.rel_field else 'int'

    def get_create_table_parameters(self):
        other = self.dataset.all[self.rel_name][self.rel_field]
        kind = other.kind

        val = "{name} {rel_kind} REFERENCES {rel_name} ({rel_field})".format(
            name=self.name,
            rel_name=self.rel_dataset.table_name,
            rel_field=self.rel_field.name if self.rel_field else 'id',
            rel_kind=kind
        )
        return val

    def get_post_create_table_statements(self):
        if self.index:
            return [self.get_create_index_postgis()]
        else:
            return []

    def get_add_postgis(self):
        return "alter table {table_name} add column {name} {kind} references {rel_name} ({rel_field})".format(
            table_name=self.dataset.table_name,
            name=self.name,
            type=self.kind,
            rel_name=self.rel_dataset.table_name,
            rel_field=self.rel_field.name if self.rel_field else 'id'
        )

    def get_drop_postgis(self):
        return "alter table {table_name} drop column {name}".format(
            table_name=self.dataset.table_name,
            name=self.name,
        )

    def get_create_index_postgis(self):
        return "CREATE INDEX {table_name}_{name}_idx ON {table_name} ( {name} )".format(
            name=self.name,
            table_name=self.dataset.table_name,
        )

    def get_drop_index_postgis(self):
        return "drop index if exists {table_name}_{name}_idx".format(
            name=self.name,
            table_name=self.dataset.table_name
        )

    def add(self):
        sql = [self.get_add_postgis()]
        if self.index:
            sql.append(self.get_create_index_postgis())

        self.dataset.execute_sql(sql)

    def drop(self):
        sql = [self.get_drop_postgis()]
        if self.index:
            sql.append(self.get_drop_index_postgis())

        self.dataset.execute_sql(sql)

    def create_index(self):
        if not self.index:
            self.index=True
            self.save()

        self.dataset.execute_sql(self.get_create_index_postgis())

    def drop_index(self):
        if self.index:
            self.index=False
            self.save()

        self.dataset.execute_sql(self.get_drop_index_postgis())

class ManyToManyManager(Manager):
    @method_decorator(atomic)
    def create_m2m(self, **kwargs):
        m = ManyToMany.objects.create(**kwargs)
        if not m.through:
            m.add()
        return m


class ManyToMany(models.Model):
    dataset = models.ForeignKey(StructuredDataset, related_name="relationships")
    name = models.CharField(max_length=100)
    rel_dataset = models.ForeignKey(StructuredDataset, null=True, blank=True)
    through = models.ForeignKey(StructuredDataset, null=True, blank=True)
    through_from_key = models.ForeignKey(SimpleField, null=True, blank=True)
    through_to_key = models.ForeignKey(SimpleField, null=True, blank=True)

    objects = ManyToManyManager()

    def delete(self, using=None):
        self.drop()
        super(ManyToMany, self).delete(using=using)

    def extract(self, record, missing_data_values=None):
        raise NotImplemented()

    def get_add_postgres(self):
        query = []

        if not self.through:
            query = """
                create table {schema}.{myself}_{other} (
                  {myself}_{myself_pk} {myself_kind} REFERENCES {schema}.{myself} ({myself_pk}),
                  {other}_{other_pk} {other_kind} REFERENCES {other_schema}.{other} ({other_pk}),
                );
                create index {schema}.{myself}_{other}_{myself}_{myself_pk}_idx on {schema}.{myself}_{other} ({myself}_{myself_pk});
                create index {schema}.{myself}_{other}_{other}_{other_pk}_idx on {other_schema}.{myself}_{other} ({other}_{other_pk});

            """.format(
                schema=self.dataset.schema_name,
                other_schema=self.rel_dataset.schema_name,
                myself=self.dataset.name,
                other=self.rel_dataset.name,
                myself_pk=self.dataset.pk.name,
                other_pk=self.rel_dataset.pk.name,
                myself_kind=self.dataset.pk.kind,
                other_kind=self.rel_dataset.pk.kind
            ).split(';')
        return query

    def get_drop_postgres(self):
        query = []
        if not self.through:
            query = ["drop table {schema}.{myself_other}".format(
                schema=self.dataset.schema_name,
                myself=self.dataset.name,
                other=self.rel_dataset.name,
            )]

        return query

    def add(self):
        self.dataset.execute_sql(*self.get_add_postgres())

    def drop(self):
        self.dataset.execute_sql(*self.get_drop_postgres())



