import pytest
from terrapyn.features import models
from django.contrib.auth import models as auth
from django.conf import settings
from django.db import connections

default_dbms = getattr(settings, 'TERRAPYN_DEFAULT_DATABASE', 'default')

# fixture for a "person" table.
@pytest.fixture(scope="module")
def persons(request):
    test_persons = models.StructuredDataset.objects.create_dataset(
        models.GeometryField(name='location', kind='Point'),
        models.SimpleField(name='first_name', kind='text', not_null=True),
        models.SimpleField(name='last_name', kind='text', not_null=True),
        models.SimpleField(name='email', kind='text', not_null=True),
        models.SimpleField(name='age', kind='int'),
        models.SimpleField(name='dob', kind='date'),
        models.SimpleField(name='properties', kind='json'),
        name='test_persons',
    )

    @request.add_finalizer
    def teardown():
        test_persons.delete()
    return test_persons

# fixture to test foreign key relations to the persons table
@pytest.fixture(scope="module")
def persons_profiles(persons):
    test_persons_profiles = models.StructuredDataset.objects.create_dataset(
        models.ForeignKey(rel_dataset=persons),
        models.SimpleField(name='address1', kind='text'),
        models.SimpleField(name='address2', kind='text'),
        models.SimpleField(name='zip', kind='text'),
        models.SimpleField(name='phone', kind='text'),
        models.SimpleField(name='role', kind='text'),
        name='test_persons_profiles'
    )
    return test_persons_profiles

# fixture to allow tests of many-to-many relations
@pytest.fixture(scope="module")
def restaurants(request):
    test_restaurants = models.StructuredDataset.objects.create_dataset(
        models.SimpleField(name='name', kind='text'),
        models.GeometryField(name='location', kind='POINT', srid=4326),
        models.SimpleField(name='price_range', kind='int', default_value='1'),
        name='test_restaurants'
    )
    @request.add_finalizer
    def teardown():
        test_restaurants.delete()
    return test_restaurants

# fixture to allow tests of many-to-many through relations
@pytest.fixture(scope="module")
def ratings(test_persons, test_restaurants):
    test_ratings = models.StructuredDataset.objects.create_dataset(
        models.ForeignKey(rel_dataset=test_persons),
        models.ForeignKey(rel_dataset=test_restaurants),
        models.SimpleField(name='rating', kind='float', default_value='2.5'),
        name='test_ratings'
    )
    return test_ratings

@pytest.fixture(scope="module")
def user(request):
    test_user = auth.User.objects.create_user('test_user')

    @request.add_finalizer
    def teardown():
        test_user.delete()
    return test_user

# tests

def _dataset_exists(dataset):
    with dataset.get_cursor() as c:
        sql = """
        SELECT EXISTS(
        SELECT *
        FROM information_schema.tables
        WHERE
          schema_name = '{schema_name}',
          table_name = '{table_name}'
        );
        """.format(
            table_name=dataset.name,
            schema_name=dataset.schema_name
        )
        c.execute(sql)
        row = c.fetchall()
    return row[0]

def _user_exists(user, dbms=default_dbms):
    with connections[dbms].get_cursor() as c:
        sql = """
        SELECT EXISTS(
        SELECT *
        FROM information_schema.tables
        WHERE
          schema_name = '{schema_name}'
        );
        """.format(
            schema_name=user.username
        )
        c.execute(sql)
        row = c.fetchall()
    return row[0]

@pytest.mark.django_db
def test_create_dataset_simple(persons):
    """Make sure that the persons dataset is setup correctly and the table was created."""
    assert persons.primary_key == 'id'
    assert persons.dbms == 'default'
    assert persons.is_layer
    assert persons.geometry_fields.all().exists()
    assert persons.simple_fields.all().exists()
    assert _dataset_exists(persons), 'dataset table not created'


@pytest.mark.django_db
def test_create_dataset_fk(persons_profiles):
    """Make sure that the profiles dataset is setup correctly and the relationship is established"""
    assert persons_profiles in persons_profiles['test_persons_id'].rel_dataset.reverse_keys

@pytest.mark.django_db
def test_create_dataset_m2m(persons, restaurants):
    """Create a new m2m relationships and make sure both datasets report them properly"""
    m2m = models.ManyToMany.create_m2m(dataset1=persons, dataset2=restaurants)

    assert m2m.to_dataset1_name == 'test_persons_set'
    assert m2m.to_dataset2_name == 'test_restaurants_set'
    assert m2m.reverse == True
    assert m2m in persons.relationships
    assert m2m in restaurants.relationships

    m2m.reverse = False
    m2m.save()
    assert m2m not in restaurants.relationships

    m2m.delete()
    assert not _dataset_exists(m2m), 'table not deleted'


@pytest.mark.django_db
def test_m2m_through(test_ratings):
    """Test that through relationships work okay"""
    assert 'test_persons_id' in test_ratings
    assert 'test_restaurants_id' in test_ratings

    m2m = models.ManyToMany.create_through(
        test_ratings,
        test_ratings['test_persons_id'],
        test_ratings['test_restaurants_id'],
    )
    assert m2m in persons.relationships
    assert m2m in restaurants.relationships

    m2m.delete()
    assert _dataset_exists(test_ratings)


def test_create_and_delete_user(user):
    models.StructuredDataset.create_user(user)
    assert _user_exists(user)

    models.StructuredDataset.delete_user(user)
    assert not _user_exists(user)

def test_create_owned_dataset(user):
    owned_dataset = models.StructuredDataset.objects.create_dataset(
        models.SimpleField(name='thingie', kind='int'),
        owner=user,
        name='owned_dataset'
    )
    assert _dataset_exists(owned_dataset)
    models.StructuredDataset.delete_user(user)
    assert not _dataset_exists(owned_dataset)


def test_add_simplefield():
    raise NotImplemented

def test_add_foreignkey():
    raise NotImplemented

def test_add_geographicfield():
    raise NotImplemented

def test_add_manytomany():
    raise NotImplemented

def test_drop_field():
    raise NotImplemented

def test_add_feature():
    raise NotImplemented

def test_delete_feature():
    raise NotImplemented

def test_feature_by_pk():
    raise NotImplemented

def test_features():
    raise NotImplemented

